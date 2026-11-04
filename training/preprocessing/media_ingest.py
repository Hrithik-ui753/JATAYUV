"""Ingest JATAYUV's own drone photographs and videos into a labelled manifest.

Supported inputs: JPG/JPEG, PNG, TIFF, MP4, MOV.

For every accepted frame the pipeline records: source file, flight id, sequence id,
EXIF camera data, GPS (when present), dimensions, blur score, duplicate group, dataset
origin, annotation status and licence. Frames are grouped by flight/sequence so later
splitting can be leakage-free.

Usage::

    python -m training.preprocessing.media_ingest \
        --input D:/drone_flights --output datasets/manifests/own_flights.json \
        --flight-field folder --sample-fps 1.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np

from training.datasets.manifest import (
    CameraInfo,
    DatasetManifest,
    DepthSample,
    GPSCoords,
)
from training.utils.io import REPO_ROOT, ensure_dir, sha256_file, utc_now_iso, write_json

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi"}


# --------------------------------------------------------------------------------------
# Quality / duplicate helpers
# --------------------------------------------------------------------------------------
def blur_score(gray: np.ndarray) -> float:
    """Variance of Laplacian -- higher is sharper. Typical threshold: 60-100."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def dhash(gray: np.ndarray, hash_size: int = 8) -> int:
    """Difference hash used for near-duplicate detection."""
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    bits = np.packbits(diff.flatten())
    return int.from_bytes(bits.tobytes(), "big")


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _gps_from_exif(exif) -> Optional[GPSCoords]:
    try:
        gps_ifd = exif.get_ifd(0x8825)
    except Exception:
        return None
    if not gps_ifd:
        return None

    def _to_deg(value) -> Optional[float]:
        if not value:
            return None
        try:
            deg, minute, sec = (float(v) for v in value[:3])
        except Exception:
            return None
        return deg + minute / 60.0 + sec / 3600.0

    lat = _to_deg(gps_ifd.get(2))
    lon = _to_deg(gps_ifd.get(4))
    if gps_ifd.get(1) in ("S", b"S"):
        lat = -lat if lat is not None else None
    if gps_ifd.get(3) in ("W", b"W"):
        lon = -lon if lon is not None else None
    altitude = gps_ifd.get(6)
    altitude_m = float(altitude) if isinstance(altitude, (int, float)) else None
    if lat is None and lon is None and altitude_m is None:
        return None
    return GPSCoords(latitude=lat, longitude=lon, altitude_m=altitude_m)


def read_exif(path: str) -> Tuple[Optional[CameraInfo], Optional[GPSCoords], Dict[str, Any]]:
    """Extract camera + GPS metadata; tolerant to missing/corrupt EXIF."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(path) as img:
            exif = img.getexif()
            width, height = img.size
    except Exception:
        return None, None, {}

    tags = {}
    try:
        for tag_id, value in exif.items():
            name = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, (int, float, str)):
                tags[name] = value
    except Exception:
        pass

    camera = CameraInfo(
        make=str(tags.get("Make", "")).strip() or None,
        model=str(tags.get("Model", "")).strip() or None,
        focal_length_mm=float(tags["FocalLength"]) if "FocalLength" in tags else None,
        width=width,
        height=height,
    )
    return camera, _gps_from_exif(exif), tags


# --------------------------------------------------------------------------------------
# Ingestion
# --------------------------------------------------------------------------------------
@dataclass
class IngestConfig:
    min_side: int = 640
    blur_threshold: float = 40.0
    duplicate_hamming: int = 4
    sample_fps: float = 1.0
    max_frames_per_video: Optional[int] = None
    jpeg_quality: int = 95
    license: str = "JATAYUV internal flight data (all rights reserved)"


@dataclass
class IngestStats:
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    rejected_reasons: Dict[str, int] = field(default_factory=dict)

    def reject(self, reason: str) -> None:
        self.rejected += 1
        self.rejected_reasons[reason] = self.rejected_reasons.get(reason, 0) + 1


class MediaIngestor:
    def __init__(self, output_dir: str, config: Optional[IngestConfig] = None):
        self.output_dir = output_dir
        ensure_dir(output_dir)
        self.config = config or IngestConfig()
        self.samples: List[DepthSample] = []
        self._hashes: List[int] = []
        self.stats = IngestStats()

    # ------------------------------------------------------------------ framing
    def _accept(
        self,
        rgb: np.ndarray,
        source_path: str,
        flight_id: str,
        sequence_id: str,
        frame_index: Optional[int] = None,
    ) -> bool:
        h, w = rgb.shape[:2]
        if min(h, w) < self.config.min_side:
            self.stats.reject("low_resolution")
            return False
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        score = blur_score(gray)
        if score < self.config.blur_threshold:
            self.stats.reject("blurred")
            return False
        digest = dhash(gray)
        if any(hamming(digest, other) <= self.config.duplicate_hamming for other in self._hashes):
            self.stats.duplicates += 1
            self.stats.reject("near_duplicate")
            return False

        frame_tag = f"_f{frame_index:06d}" if frame_index is not None else ""
        stem = os.path.splitext(os.path.basename(source_path))[0]
        out_name = f"{stem}{frame_tag}.jpg"
        out_path = os.path.join(self.output_dir, flight_id, out_name)
        ensure_dir(os.path.dirname(out_path))
        cv2.imwrite(
            out_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
            [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality],
        )

        camera, gps, exif_tags = read_exif(source_path)
        self.samples.append(
            DepthSample(
                id=f"{flight_id}_{stem}{frame_tag}",
                image_path=os.path.relpath(out_path, REPO_ROOT),
                width=w,
                height=h,
                source_dataset="jatayuv_own_flights",
                license=self.config.license,
                flight_id=flight_id,
                sequence_id=sequence_id,
                depth=None,
                camera=camera or CameraInfo(width=w, height=h),
                gps=gps,
                annotation_status="none",
                blur_score=round(score, 2),
                extra={
                    "source_file": os.path.abspath(source_path),
                    "source_sha256": sha256_file(source_path),
                    "frame_index": frame_index,
                    "exif": {k: str(v) for k, v in list(exif_tags.items())[:20]},
                },
            )
        )
        self._hashes.append(digest)
        self.stats.accepted += 1
        return True

    # ------------------------------------------------------------------ media
    def ingest_video(
        self,
        path: str,
        flight_id: Optional[str] = None,
        sequence_id: Optional[str] = None,
    ) -> int:
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            print(f"[ingest] cannot open video: {path}")
            return 0
        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(round(fps / max(self.config.sample_fps, 0.01))))
        flight = flight_id or os.path.basename(os.path.dirname(path)) or "flight_unknown"
        sequence = sequence_id or os.path.splitext(os.path.basename(path))[0]
        accepted = 0
        index = 0
        while True:
            ok, frame_bgr = capture.read()
            if not ok:
                break
            if index % step == 0:
                if self.config.max_frames_per_video and accepted >= self.config.max_frames_per_video:
                    break
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                if self._accept(rgb, path, flight, sequence, frame_index=index):
                    accepted += 1
            index += 1
        capture.release()
        print(f"[ingest] {os.path.basename(path)}: {accepted} frames accepted ({index} read, step {step})")
        return accepted

    def ingest_photo(
        self,
        path: str,
        flight_id: Optional[str] = None,
        sequence_id: Optional[str] = None,
    ) -> int:
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            self.stats.reject("unreadable")
            return 0
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        flight = flight_id or os.path.basename(os.path.dirname(path)) or "flight_unknown"
        sequence = sequence_id or os.path.splitext(os.path.basename(path))[0]
        return 1 if self._accept(rgb, path, flight, sequence) else 0

    def ingest_tree(self, input_path: str, flight_field: str = "folder") -> Dict[str, Any]:
        """Walk a directory (or handle a single file) and ingest all supported media."""
        if os.path.isfile(input_path):
            ext = os.path.splitext(input_path)[1].lower()
            if ext in VIDEO_EXTS:
                self.ingest_video(input_path)
            elif ext in IMAGE_EXTS:
                self.ingest_photo(input_path)
            else:
                raise ValueError(f"Unsupported media type: {input_path}")
        else:
            for root, _dirs, files in os.walk(input_path):
                for name in sorted(files):
                    path = os.path.join(root, name)
                    ext = os.path.splitext(name)[1].lower()
                    relative_dir = os.path.relpath(root, input_path)
                    flight = (
                        relative_dir.split(os.sep)[0]
                        if flight_field == "folder" and relative_dir != "."
                        else "flight_root"
                    )
                    try:
                        if ext in VIDEO_EXTS:
                            self.ingest_video(path, flight_id=flight)
                        elif ext in IMAGE_EXTS:
                            self.ingest_photo(path, flight_id=flight)
                    except Exception as exc:  # keep going; report in stats
                        print(f"[ingest] skipped {name}: {exc}")
                        self.stats.reject("exception")
        return self.summary()

    def summary(self) -> Dict[str, Any]:
        by_flight: Dict[str, int] = {}
        for sample in self.samples:
            by_flight[sample.flight_id] = by_flight.get(sample.flight_id, 0) + 1
        return {
            "accepted": self.stats.accepted,
            "rejected": self.stats.rejected,
            "near_duplicates": self.stats.duplicates,
            "rejected_reasons": self.stats.rejected_reasons,
            "flights": by_flight,
            "frames_per_flight": by_flight,
        }

    def build_manifest(self, name: str, path: str) -> DatasetManifest:
        manifest = DatasetManifest(
            name=name,
            version="1.0.0",
            created_at=utc_now_iso(),
            root=self.output_dir,
            description=(
                "JATAYUV own drone media (frames accepted after quality/duplicate filtering). "
                "No depth labels yet: run teacher pseudo-labelling or photogrammetry."
            ),
            samples=self.samples,
            statistics=self.summary(),
        )
        manifest.save(path)
        return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest JATAYUV drone photos/videos")
    parser.add_argument("--input", required=True, help="file or directory with media")
    parser.add_argument("--output", required=True, help="manifest JSON path")
    parser.add_argument("--frames-dir", default="datasets/processed/own_frames")
    parser.add_argument("--sample-fps", type=float, default=1.0)
    parser.add_argument("--min-side", type=int, default=640)
    parser.add_argument("--blur-threshold", type=float, default=40.0)
    parser.add_argument("--duplicate-hamming", type=int, default=4)
    parser.add_argument("--max-frames-per-video", type=int, default=None)
    parser.add_argument("--flight-field", default="folder", choices=["folder"])
    parser.add_argument("--license", default="JATAYUV internal flight data (all rights reserved)")
    args = parser.parse_args(argv)

    config = IngestConfig(
        min_side=args.min_side,
        blur_threshold=args.blur_threshold,
        duplicate_hamming=args.duplicate_hamming,
        sample_fps=args.sample_fps,
        max_frames_per_video=args.max_frames_per_video,
        license=args.license,
    )
    ingestor = MediaIngestor(os.path.join(REPO_ROOT, args.frames_dir), config)
    summary = ingestor.ingest_tree(os.path.abspath(args.input), flight_field=args.flight_field)
    manifest = ingestor.build_manifest("jatayuv_own_flights", os.path.join(REPO_ROOT, args.output))
    print(json.dumps(summary, indent=2))
    print(f"[ingest] manifest written: {os.path.join(REPO_ROOT, args.output)} ({len(manifest.samples)} frames)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
