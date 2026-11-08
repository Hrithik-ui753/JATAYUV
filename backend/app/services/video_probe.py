"""Video validation and metadata extraction for drone video processing.

Uses ffprobe for fast container/stream inspection and PyAV for decode-level
verification where needed. Presentation timestamps (PTS) are preserved from the
stream; timestamps are only derived from frame_index / nominal_fps when a real
PTS is unavailable, and even then they are marked as estimated.

No synthetic frames, GPS values, or quality scores are produced here.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import av

from backend.app.core.config import settings
from backend.app.services.storage import get_mission_storage


# ---------------------------------------------------------------------------
# Supported codec/container limits
# ---------------------------------------------------------------------------

SUPPORTED_VIDEO_CODECS = {"h264", "hevc", "avc1", "vp8", "vp9", "mpeg4", "mjpeg"}

# Practical ingest caps. These are conservative limits to protect workers and
# storage; they can be tuned via settings or task kwargs.
DEFAULT_MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024      # 500 MB
DEFAULT_MAX_DURATION_SECONDS = 1800                    # 30 minutes
DEFAULT_MAX_FRAME_WIDTH = 7680                         # 8K fallback ceiling
DEFAULT_MAX_FRAME_HEIGHT = 4320
DEFAULT_MAX_DECODE_SECONDS = 3600                      # per-video decode budget

# Quality for extracted frame JPEGs.
DEFAULT_FRAME_JPEG_QUALITY = 92


@dataclass
class VideoMetadata:
    container_format: str
    duration_seconds: Optional[float]
    width: Optional[int]
    height: Optional[int]
    nominal_fps: Optional[float]
    avg_fps: Optional[float]
    codec_name: Optional[str]
    codec_long_name: Optional[str]
    pixel_format: Optional[str]
    stream_time_base: Optional[str]
    nb_frames: Optional[int]
    has_video: bool
    ffprobe_exit_code: int
    ffprobe_stderr: str
    ffprobe_json: Dict[str, Any]
    probe_duration_method: Optional[str] = None
    truncated_probe: bool = False


@dataclass
class DecodeResult:
    video_path: str
    metadata: VideoMetadata
    frame_count: int
    first_pts_seconds: Optional[float]
    last_pts_seconds: Optional[float]
    duration_from_packets: Optional[float]
    decode_errors: List[str]
    interrupted: bool
    reached_eof: bool
    decode_wall_seconds: float


# ---------------------------------------------------------------------------
# ffprobe helpers
# ---------------------------------------------------------------------------

_FFPROBE_ENTRIES = (
    "format=format_name,duration,size,bit_rate,duration_ts,val"
    ",start_time:stream=codec_type,codec_name,codec_long_name,width,height,"
    "r_frame_rate,avg_frame_rate,pix_fmt,time_base,nb_frames,profile,level"
)


def _run_ffprobe(path: str) -> Tuple[int, str, Dict[str, Any]]:
    """Run ffprobe and return (returncode, stderr, parsed json)."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", _FFPROBE_ENTRIES,
        "-of", "json",
        path,
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise RuntimeError("ffprobe not found on PATH") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffprobe timed out") from None

    stderr_text = (proc.stderr or "").strip()
    stdout_text = (proc.stdout or "").strip()
    try:
        parsed = json.loads(stdout_text) if stdout_text else {}
    except json.JSONDecodeError:
        parsed = {}

    return proc.returncode, stderr_text, parsed


def _first_format_non_video_error(stderr: str) -> Optional[str]:
    """Pick the first container-level failure from ffprobe stderr if present."""
    needles = [
        "moov atom not found",
        "Invalid data found when processing input",
        "could not find codec parameters",
        "Input file is empty",
        "AddressSanitizer",
    ]
    lowered = stderr.lower()
    for needle in needles:
        if needle.lower() in lowered:
            return needle
    return None


def _parse_rational(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    m = re.match(r"^\s*(?P<num>\d+)\s*/\s*(?P<den>\d+)\s*$", text)
    if not m:
        return None
    num = int(m.group("num"))
    den = int(m.group("den"))
    if den == 0:
        return None
    return num / den


def probe_video(path: str) -> VideoMetadata:
    """Inspect container and streams without decoding frames."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Video file not found: {path}")

    size = os.path.getsize(path)
    if size == 0:
        raise ValueError("Video file is empty")

    returncode, stderr_text, parsed = _run_ffprobe(path)

    fmt = parsed.get("format", {})
    streams = parsed.get("streams", []) or []

    video_streams = [s for s in streams if str(s.get("codec_type", "")).lower() == "video"]
    has_video = len(video_streams) > 0

    first_video = video_streams[0] if video_streams else {}
    duration_text = fmt.get("duration")
    duration = float(duration_text) if duration_text not in (None, "", "N/A") else None

    # ffprobe sometimes reports duration estimation method via logging; keep a
    # lightweight flag for "estimated from bitrate" style warnings.
    probe_duration_method = None
    lowered = stderr_text.lower()
    if "estimating duration from bitrate" in lowered:
        probe_duration_method = "estimated_from_bitrate"
    if "moov atom not found" in lowered or "invalid data found when processing input" in lowered:
        pass

    truncated_probe = bool(
        returncode != 0
        or _first_format_non_video_error(stderr_text)
        or (duration is not None and duration <= 0.0)
    )

    return VideoMetadata(
        container_format=fmt.get("format_name", "unknown"),
        duration_seconds=duration,
        width=first_video.get("width"),
        height=first_video.get("height"),
        nominal_fps=_parse_rational(first_video.get("r_frame_rate")),
        avg_fps=_parse_rational(first_video.get("avg_frame_rate")),
        codec_name=first_video.get("codec_name"),
        codec_long_name=first_video.get("codec_long_name"),
        pixel_format=first_video.get("pix_fmt"),
        stream_time_base=first_video.get("time_base"),
        nb_frames=first_video.get("nb_frames"),
        has_video=has_video,
        ffprobe_exit_code=returncode,
        ffprobe_stderr=stderr_text[:4000],
        ffprobe_json=parsed,
        probe_duration_method=probe_duration_method,
        truncated_probe=truncated_probe,
    )


def validate_video_probe(path: str) -> Dict[str, Any]:
    """Validate a video file using probe-only checks.

    Returns a report suitable for API responses. Does not decode frames.
    """
    if not os.path.isfile(path):
        return {"valid": False, "reason": "file not found", "path": path}

    size = os.path.getsize(path)
    if size == 0:
        return {"valid": False, "reason": "empty file", "path": path}

    metadata = probe_video(path)

    reasons: List[str] = []

    if metadata.ffprobe_exit_code != 0:
        reasons.append("ffprobe exited non-zero")

    if not metadata.has_video:
        reasons.append("no video stream found")

    if metadata.duration_seconds is None or metadata.duration_seconds <= 0:
        reasons.append("duration missing or non-positive")

    if _first_format_non_video_error(metadata.ffprobe_stderr):
        reasons.append("container-level error detected")

    # Codec support check should be done against probed codec; be lenient with
    # codec_name aliases by checking a small normalized set.
    codec = (metadata.codec_name or "").lower()
    if codec and codec not in SUPPORTED_VIDEO_CODECS:
        # Additional alias handling for common MP4 h264/hevc labels.
        if codec not in {"avc1", "hvc1", "hev1"}:
            reasons.append(f"unsupported codec: {codec!r}")

    if reasons:
        return {
            "valid": False,
            "reason": "; ".join(reasons),
            "path": path,
            "metadata": _metadata_to_dict(metadata),
        }

    return {
        "valid": True,
        "reason": "probe checks passed",
        "path": path,
        "metadata": _metadata_to_dict(metadata),
    }


def _metadata_to_dict(m: VideoMetadata) -> Dict[str, Any]:
    return {
        "container_format": m.container_format,
        "duration_seconds": m.duration_seconds,
        "width": m.width,
        "height": m.height,
        "nominal_fps": m.nominal_fps,
        "avg_fps": m.avg_fps,
        "codec_name": m.codec_name,
        "codec_long_name": m.codec_long_name,
        "pixel_format": m.pixel_format,
        "stream_time_base": m.stream_time_base,
        "nb_frames": m.nb_frames,
        "has_video": m.has_video,
        "probe_duration_method": m.probe_duration_method,
        "truncated_probe": m.truncated_probe,
    }


# ---------------------------------------------------------------------------
# Decode-level verification / extraction
# ---------------------------------------------------------------------------

def _pts_to_seconds(frame: av.frame.Frame) -> Optional[float]:
    """Convert a PyAV frame to seconds using its PTS and time_base."""
    if frame.pts is None:
        return None
    tb = frame.time_base
    if tb is None or tb.numerator == 0:
        return None
    return float(frame.pts * tb)


def _ensure_caps_video(container: av.container.InputContainer) -> av.stream.VideoStream:
    """Return the first video stream or raise."""
    video_streams = [s for s in container.streams if s.type == "video"]
    if not video_streams:
        raise ValueError("No video stream found in container")
    return video_streams[0]


def decode_video_metadata(
    video_path: str,
    *,
    max_decode_seconds: Optional[float] = None,
) -> DecodeResult:
    """Decode video to verify it is playable and collect real PTS timing.

    This is intentionally lightweight and bounded; it does not extract images.
    It is useful for detecting truncation/corruption that probe-only checks miss.
    """
    t0 = datetime.now(timezone.utc)
    metadata = probe_video(video_path)
    decode_errors: List[str] = []
    interrupted = False
    reached_eof = False

    try:
        with av.open(video_path) as container:
            video = _ensure_caps_video(container)

            first_pts: Optional[float] = None
            last_pts: Optional[float] = None
            frame_count = 0
            duration_from_packets: Optional[float] = None

            max_decode = max_decode_seconds or DEFAULT_MAX_DECODE_SECONDS
            deadline = t0.timestamp() + max_decode

            for frame in container.decode(video=0):
                if frame.type != "video":
                    continue

                now = datetime.now(timezone.utc).timestamp()
                if now > deadline:
                    interrupted = True
                    decode_errors.append("decode budget exceeded")
                    break

                pts_s = _pts_to_seconds(frame)
                if pts_s is not None:
                    if first_pts is None:
                        first_pts = pts_s
                    last_pts = pts_s

                frame_count += 1

                if frame_count % 2500 == 0:
                    # periodic sanity check, keep memory bounded by not storing frames
                    if now > deadline:
                        interrupted = True
                        decode_errors.append("decode budget exceeded during loop")
                        break

            if frame_count > 0 and first_pts is not None and last_pts is not None:
                duration_from_packets = last_pts - first_pts

            reached_eof = not interrupted and frame_count > 0

    except av.AVError as exc:
        decode_errors.append(f"av open/decode error: {exc}")
    except Exception as exc:  # noqa: BLE001
        decode_errors.append(f"unexpected decode error: {exc}")

    wall = (datetime.now(timezone.utc) - t0).total_seconds()
    return DecodeResult(
        video_path=video_path,
        metadata=metadata,
        frame_count=frame_count,
        first_pts_seconds=first_pts,
        last_pts_seconds=last_pts,
        duration_from_packets=duration_from_packets,
        decode_errors=decode_errors,
        interrupted=interrupted,
        reached_eof=reached_eof,
        decode_wall_seconds=wall,
    )


# ---------------------------------------------------------------------------
# Limits enforcement
# ---------------------------------------------------------------------------

@dataclass
class VideoLimits:
    max_file_size_bytes: int
    max_duration_seconds: float
    max_width: int
    max_height: int
    max_decode_seconds: float
    min_frame_width: Optional[int]
    min_frame_height: Optional[int]
    max_frames: Optional[int]

    @classmethod
    def defaults(cls) -> "VideoLimits":
        return cls(
            max_file_size_bytes=DEFAULT_MAX_FILE_SIZE_BYTES,
            max_duration_seconds=DEFAULT_MAX_DURATION_SECONDS,
            max_width=DEFAULT_MAX_FRAME_WIDTH,
            max_height=DEFAULT_MAX_FRAME_HEIGHT,
            max_decode_seconds=DEFAULT_MAX_DECODE_SECONDS,
            min_frame_width=None,
            min_frame_height=None,
            max_frames=None,
        )


def check_video_limits(
    path: str,
    limits: VideoLimits,
    metadata: Optional[VideoMetadata] = None,
) -> List[str]:
    """Return a list of limit violations for the given video."""
    errors: List[str] = []
    if metadata is None:
        metadata = probe_video(path)

    size = os.path.getsize(path)
    if size > limits.max_file_size_bytes:
        errors.append(
            f"file size {size} exceeds limit {limits.max_file_size_bytes}"
        )

    if metadata.duration_seconds is not None and metadata.duration_seconds > limits.max_duration_seconds:
        errors.append(
            f"duration {metadata.duration_seconds:.2f}s exceeds limit {limits.max_duration_seconds}s"
        )

    if metadata.width is not None and metadata.width > limits.max_width:
        errors.append(
            f"width {metadata.width} exceeds limit {limits.max_width}"
        )

    if metadata.height is not None and metadata.height > limits.max_height:
        errors.append(
            f"height {metadata.height} exceeds limit {limits.max_height}"
        )

    if limits.min_frame_width and metadata.width is not None and metadata.width < limits.min_frame_width:
        errors.append(
            f"width {metadata.width} below minimum {limits.min_frame_width}"
        )

    if limits.min_frame_height and metadata.height is not None and metadata.height < limits.min_frame_height:
        errors.append(
            f"height {metadata.height} below minimum {limits.min_frame_height}"
        )

    if metadata.codec_name and metadata.codec_name.lower() not in SUPPORTED_VIDEO_CODECS:
        alias = metadata.codec_name.lower()
        if alias not in {"avc1", "hvc1", "hev1"}:
            errors.append(f"unsupported codec: {metadata.codec_name!r}")

    if not metadata.has_video:
        errors.append("no video stream found")

    if metadata.duration_seconds is not None and metadata.duration_seconds <= 0:
        errors.append("non-positive duration")

    return errors


# ---------------------------------------------------------------------------
# Public API used by the processing pipeline
# ---------------------------------------------------------------------------

def build_video_report(
    path: str,
    *,
    limits: Optional[VideoLimits] = None,
) -> Dict[str, Any]:
    """Validate and describe a video without extracting frames."""
    limits = limits or VideoLimits.defaults()
    metadata = probe_video(path)
    violations = check_video_limits(path, limits, metadata=metadata)

    report: Dict[str, Any] = {
        "path": path,
        "valid": len(violations) == 0,
        "violations": violations,
        "metadata": _metadata_to_dict(metadata),
    }
    return report
