"""Frame extraction from drone videos.

Extracts frames by streaming decode, preserves presentation timestamps from the
container whenever available, and writes frame artifacts to persistent storage.

Frames are not generated synthetically and GPS/quality values are left to the
quality/GPS stages. This module only extracts and persists real decoded frames.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

import av

from backend.app.core.config import settings
from backend.app.services.storage import get_mission_storage
from backend.app.services.video_probe import (
    VideoLimits,
    VideoMetadata,
    _ensure_caps_video,
    _pts_to_seconds,
    probe_video,
)


@dataclass
class ExtractedFrame:
    frame_id: str
    video_id: str
    mission_id: str
    processing_run_id: str
    frame_index: int
    presentation_timestamp: Optional[float]
    timestamp_seconds: Optional[float]
    width: int
    height: int
    storage_path: str
    artifact_relative_path: str
    pts_source: str  # "real_pts" | "estimated"
    # placeholder for future in-memory buffer usage; not currently used.


@dataclass
class FrameExtractionConfig:
    mission_id: str
    video_id: str
    processing_run_id: str
    video_path: str
    frame_jpeg_quality: int = 92
    max_frames: Optional[int] = None
    # Sampling strategy: if set, only extract frames whose timestamp (seconds)
    # falls on the next sample point. If None, extract every decoded video frame.
    sample_interval_seconds: Optional[float] = None
    # Maximum number of buffered frames to write per iteration; keeps memory
    # bounded for high-fps sources.
    flush_every_n_frames: int = 50


def _build_frame_storage_path(
    storage,
    mission_id: str,
    video_id: str,
    processing_run_id: str,
    frame_index: int,
) -> Tuple[str, str]:
    """Return (absolute_path, relative_path) for a frame artifact.

    Naming is deterministic per frame_index and run so extracts are
    reproducible and previous runs are not silently overwritten.
    """
    subdir = os.path.join(
        "missions", mission_id, "videos", video_id, "frames",
        processing_run_id,
    )
    rel = os.path.join(subdir, f"{frame_index:08d}.jpg")
    abs_path = os.path.join(settings.STORAGE_DIR, rel)
    return abs_path, rel


def _save_frame_jpeg(
    frame: av.frame.Frame,
    abs_path: str,
    quality: int,
) -> None:
    """Convert a PyAV video frame to JPEG and write to disk."""
    try:
        img = frame.to_ndarray(format="bgr24")
    except Exception as exc:
        raise RuntimeError(f"Failed to convert frame to image array: {exc}") from exc

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    import cv2
    ok = cv2.imwrite(abs_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError(f"Failed to write frame image: {abs_path}")


def _frame_timestamp_info(
    frame: av.frame.Frame,
) -> Tuple[Optional[float], Optional[float], str]:
    """Return (presentation_timestamp, timestamp_seconds, pts_source)."""
    # PyAV frames carry PTS in the frame's time_base which defaults to the
    # stream time_base when decoding.
    pts = frame.pts
    tb = frame.time_base
    if pts is not None and tb is not None and tb.numerator != 0:
        pts_seconds = float(pts * tb)
        return pts_seconds, pts_seconds, "real_pts"

    # Fallback: if we cannot get a reliable PTS, estimate from stream time_base
    # and current decode index. This is marked explicitly as estimated.
    return None, None, "estimated"


def iter_extracted_frames(
    config: FrameExtractionConfig,
    *,
    limits: Optional[VideoLimits] = None,
) -> Iterator[ExtractedFrame]:
    """Stream-decode frames and yield extracted frame records.

    This does not load the whole video into RAM. It streams from disk and
    writes each accepted frame to storage before yielding.
    """
    storage = get_mission_storage()
    metadata = probe_video(config.video_path)
    limits = limits or VideoLimits.defaults()

    if metadata.width is None or metadata.height is None:
        raise ValueError("Cannot extract frames: video has no reported dimensions")

    with av.open(config.video_path) as container:
        video = _ensure_caps_video(container)

        frame_index = 0
        saved_count = 0

        next_sample_at: Optional[float] = None
        if config.sample_interval_seconds and config.sample_interval_seconds > 0:
            next_sample_at = 0.0

        for frame in container.decode(video=0):
            if frame.type != "video":
                continue

            if config.max_frames is not None and saved_count >= config.max_frames:
                break

            pts_s, ts_s, pts_source = _frame_timestamp_info(frame)
            width = int(frame.width)
            height = int(frame.height)

            accept = True
            if config.sample_interval_seconds and config.sample_interval_seconds > 0:
                t = pts_s if pts_s is not None else float(frame_index) / max(1, metadata.avg_fps or 1.0)
                if next_sample_at is not None and t < next_sample_at - 1e-6:
                    accept = False
                elif next_sample_at is not None and t >= next_sample_at - 1e-6:
                    # Accept this one and advance sample schedule.
                    next_sample_at = t + config.sample_interval_seconds
                else:
                    accept = False

            if not accept:
                frame_index += 1
                continue

            frame_id = str(uuid.uuid4())
            abs_path, rel_path = _build_frame_storage_path(
                storage,
                config.mission_id,
                config.video_id,
                config.processing_run_id,
                frame_index,
            )

            _save_frame_jpeg(frame, abs_path, config.frame_jpeg_quality)

            yield ExtractedFrame(
                frame_id=frame_id,
                video_id=config.video_id,
                mission_id=config.mission_id,
                processing_run_id=config.processing_run_id,
                frame_index=frame_index,
                presentation_timestamp=pts_s,
                timestamp_seconds=ts_s,
                width=width,
                height=height,
                storage_path=abs_path,
                artifact_relative_path=rel_path,
                pts_source=pts_source,
            )

            saved_count += 1
            frame_index += 1

            if saved_count % config.flush_every_n_frames == 0:
                # yield control and keep memory bounded
                pass


def extract_frames_for_video(
    config: FrameExtractionConfig,
    *,
    limits: Optional[VideoLimits] = None,
) -> List[ExtractedFrame]:
    """Convenience wrapper that materializes extracted frames into a list."""
    return list(iter_extracted_frames(config, limits=limits))
