"""Perceptual duplicate detection for extracted frame artifacts.

 Detects exact and near-duplicate frames using ImageHash dHash and a bounded
 temporal window so the work stays O(n * window) instead of O(n^2) on large
 frame sets. Original frame records are preserved; only duplicate status and
 related frame ids are recorded.
"""
from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.frame_quality import (
    QualityConfig,
    duplicate_status_between_hashes,
    perceptual_hash,
)


@dataclass
class DuplicateDecision:
    frame_id: str
    duplicate_hash: str
    duplicate_status: str  # unique | exact_duplicate | near_duplicate
    duplicate_of_frame_id: Optional[str]
    duplicate_distance: Optional[int]
    reason: Optional[str]


@dataclass
class DuplicateDetectorConfig:
    quality_config: QualityConfig
    temporal_window_frames: int = 90
    temporal_window_seconds: Optional[float] = None
    prefer_keep_newer: bool = False
    # If True, exact duplicates are paired regardless of temporal window.
    exact_anywhere: bool = True


def _make_quality_config(dc: DuplicateDetectorConfig) -> QualityConfig:
    qc = dc.quality_config
    # Duplicate detection uses dhash config from the quality config.
    return QualityConfig(
        blur_threshold=qc.blur_threshold,
        severe_blur_threshold=qc.severe_blur_threshold,
        exposure_low=qc.exposure_low,
        exposure_high=qc.exposure_high,
        min_width=qc.min_width,
        min_height=qc.min_height,
        dhash_size=qc.dhash_size,
        near_duplicate_hamming_max=qc.near_duplicate_hamming_max,
        allow_warning_on_exposure=qc.allow_warning_on_exposure,
        allow_warning_on_blur=qc.allow_warning_on_blur,
    )


def detect_duplicates_in_batch(
    frames: List[Dict[str, Any]],
    *,
    config: Optional[DuplicateDetectorConfig] = None,
) -> List[DuplicateDecision]:
    """Detect duplicates among a batch of frames.

    `frames` is a list of dicts with at least:
     * frame_id
     * storage_path
     * frame_index (for temporal windowing)
     * presentation_timestamp (optional)
    """
    cfg = config or DuplicateDetectorConfig()
    qc = _make_quality_config(cfg)

    # We keep a running index of recent hashes keyed by frame_index for the
    # temporal-window near-dup scan, and an exact-dup index for exact matches.
    hash_to_frame: Dict[str, Optional[str]] = {}
    recent: List[Tuple[int, str, str, Optional[float]]] = []  # (index, frame_id, hash, pts)

    decisions: List[DuplicateDecision] = []

    for frame in frames:
        fid = frame["frame_id"]
        path = frame["storage_path"]
        findex = int(frame.get("frame_index", 0))
        pts = frame.get("presentation_timestamp")

        try:
            h = perceptual_hash(path, size=qc.dhash_size)
        except Exception:
            # If we cannot hash, treat as unique and skip comparison.
            decisions.append(
                DuplicateDecision(
                    frame_id=fid,
                    duplicate_hash="",
                    duplicate_status="unique",
                    duplicate_of_frame_id=None,
                    duplicate_distance=None,
                    reason="hash_failed",
                )
            )
            continue

        status = "unique"
        dup_of: Optional[str] = None
        dist: Optional[int] = None
        reason: Optional[str] = None

        # Exact check (global) if enabled.
        if cfg.exact_anywhere and h in hash_to_frame:
            existing = hash_to_frame[h]
            if existing is not None:
                status = "exact_duplicate"
                dup_of = existing
                dist = 0
                reason = "exact_duplicate"
        else:
            # Near-duplicate check within temporal window.
            keep_newer = cfg.prefer_keep_newer
            for rindex, rid, rhash, rpts in list(recent):
                if cfg.temporal_window_seconds is not None and pts is not None and rpts is not None:
                    if abs(pts - rpts) > cfg.temporal_window_seconds:
                        continue
                if abs(findex - rindex) > cfg.temporal_window_frames:
                    continue
                pair_status, pair_dist = duplicate_status_between_hashes(
                    h, rhash, max_near_distance=qc.near_duplicate_hamming_max
                )
                if pair_status in ("exact_duplicate", "near_duplicate"):
                    if status == "exact_duplicate" and pair_status != "exact_duplicate":
                        continue
                    if status != "exact_duplicate" or pair_status == "exact_duplicate":
                        status = pair_status
                        dup_of = rid
                        dist = pair_dist
                        reason = "near_duplicate" if pair_status == "near_duplicate" else "exact_duplicate"

        if status == "unique":
            reason = None

        hash_to_frame[h] = fid if status in ("unique", "near_duplicate") or cfg.prefer_keep_newer else hash_to_frame.get(h)

        # Update recent list.
        recent.append((findex, fid, h, pts))
        if cfg.temporal_window_frames:
            cutoff_index = findex - cfg.temporal_window_frames
            recent = [(i, f, hh, p) for (i, f, hh, p) in recent if i >= cutoff_index]

        decisions.append(
            DuplicateDecision(
                frame_id=fid,
                duplicate_hash=h,
                duplicate_status=status,
                duplicate_of_frame_id=dup_of,
                duplicate_distance=dist,
                reason=reason,
            )
        )

    return decisions


def apply_duplicate_decisions(
    decisions: List[DuplicateDecision],
    frames: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge duplicate decisions back into frame dicts (in-place return copy)."""
    by_id = {f["frame_id"]: f for f in frames}
    result: List[Dict[str, Any]] = []
    for d in decisions:
        f = by_id.get(d.frame_id)
        if not f:
            continue
        merged = dict(f)
        merged["duplicate_status"] = d.duplicate_status
        merged["duplicate_hash"] = d.duplicate_hash
        merged["duplicate_of_frame_id"] = d.duplicate_of_frame_id
        merged["duplicate_distance"] = d.duplicate_distance
        merged["duplicate_reason"] = d.reason
        result.append(merged)
    return result
