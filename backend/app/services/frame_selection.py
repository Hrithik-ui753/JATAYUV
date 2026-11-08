"""Adaptive frame selection for later camera tracking and 3D reconstruction.

 Selects a useful subset of extracted frames using heuristics such as temporal
 spacing, sharpness, near-duplicate suppression and simple motion/scene-change
 proxies.

 IMPORTANT: This stage estimates usefulness for downstream tracking/reconstruction
 but does NOT compute accurate camera poses or geometric overlap. Those require
 P4 camera tracking and structure from motion.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class SelectionConfig:
    min_temporal_spacing_seconds: float = 1.0
    max_selected_frames: Optional[int] = None
    min_sharpness: Optional[float] = None
    max_near_duplicate_count_per_cluster: int = 1
    motion_proxy_enabled: bool = True
    scene_change_proxy_enabled: bool = True
    motion_threshold: float = 25.0
    scene_change_threshold: float = 25.0
    keep_duplicate_representative: bool = True


@dataclass
class FrameCandidate:
    frame_id: str
    video_id: str
    mission_id: str
    processing_run_id: str
    frame_index: int
    presentation_timestamp: Optional[float]
    timestamp_seconds: Optional[float]
    storage_path: str
    blur_score: Optional[float]
    mean_luminance: Optional[float]
    width: int
    height: int
    duplicate_status: str
    duplicate_hash: Optional[str]
    duplicate_of_frame_id: Optional[str]


def _frame_to_gray(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read frame for selection: {path}")
    return img


def _mean_abs_diff(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return 0.0
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def estimate_motion_proxy(
    prev_path: Optional[str],
    cur_path: str,
    prev_gray: Optional[np.ndarray],
) -> Optional[float]:
    """Simple frame-difference motion proxy.

    Returns mean absolute difference to the previous frame, or None if not
    computable. This is NOT a camera-motion or optical-flow estimate.
    """
    try:
        gray = _frame_to_gray(cur_path)
    except Exception:
        return None

    if prev_gray is None:
        return None

    return _mean_abs_diff(prev_gray, gray)


def estimate_scene_change_proxy(
    prev_path: Optional[str],
    cur_path: str,
    prev_gray: Optional[np.ndarray],
    cur_gray: Optional[np.ndarray] = None,
) -> Optional[float]:
    """Simple brightness/edge-distribution scene-change proxy.

    Uses mean absolute difference between grayscale frames; this is a weak proxy
    and does not detect all scene changes.
    """
    if prev_gray is None:
        return None
    if cur_gray is None:
        try:
            cur_gray = _frame_to_gray(cur_path)
        except Exception:
            return None
    return _mean_abs_diff(prev_gray, cur_gray)


def select_frames(
    candidates: List[FrameCandidate],
    *,
    config: Optional[SelectionConfig] = None,
) -> List[Dict[str, Any]]:
    """Select useful frames from a candidate list.

    Returns selected frame records with selection_reason populated.
    """
    cfg = config or SelectionConfig()
    if not candidates:
        return []

    # Sort by presentation timestamp where available, else frame_index.
    def sort_key(c: FrameCandidate):
        t = c.presentation_timestamp if c.presentation_timestamp is not None else float(c.frame_index)
        return t

    ordered = sorted(candidates, key=sort_key)

    selected: List[Dict[str, Any]] = []
    last_ts: Optional[float] = None
    prev_gray: Optional[np.ndarray] = None
    prev_path: Optional[str] = None
    cluster_rep: Dict[str, Optional[str]] = {}  # hash -> representative frame_id

    for c in ordered:
        if cfg.max_selected_frames is not None and len(selected) >= cfg.max_selected_frames:
            break

        t = c.presentation_timestamp if c.presentation_timestamp is not None else float(c.frame_index)

        # Temporal spacing
        if last_ts is not None and cfg.min_temporal_spacing_seconds > 0:
            if (t - last_ts) < cfg.min_temporal_spacing_seconds - 1e-6:
                continue

        # Sharpness gate
        if cfg.min_sharpness is not None and c.blur_score is not None:
            if c.blur_score < cfg.min_sharpness:
                continue

        # Near-duplicate suppression: keep one representative per hash cluster.
        if c.duplicate_status in ("exact_duplicate", "near_duplicate") and c.duplicate_hash:
            rep = cluster_rep.get(c.duplicate_hash)
            if rep is not None:
                continue
            if cfg.keep_duplicate_representative:
                cluster_rep[c.duplicate_hash] = c.frame_id

        reason_parts: List[str] = []
        motion: Optional[float] = None
        scene_change: Optional[float] = None

        if cfg.motion_proxy_enabled:
            motion = estimate_motion_proxy(prev_path, c.storage_path, prev_gray)
            if motion is not None and motion < cfg.motion_threshold:
                # Skip low-motion frames if motion proxy is enabled and threshold not met
                if last_ts is None:
                    pass
                else:
                    continue
            if motion is not None:
                reason_parts.append(f"motion_proxy={motion:.2f}")

        if cfg.scene_change_proxy_enabled and prev_gray is not None:
            scene_change = estimate_scene_change_proxy(prev_path, c.storage_path, prev_gray)
            if scene_change is not None and scene_change < cfg.scene_change_threshold:
                continue
            if scene_change is not None:
                reason_parts.append(f"scene_change_proxy={scene_change:.2f}")

        # Build record
        record = {
            "frame_id": c.frame_id,
            "video_id": c.video_id,
            "mission_id": c.mission_id,
            "processing_run_id": c.processing_run_id,
            "frame_index": c.frame_index,
            "presentation_timestamp": c.presentation_timestamp,
            "timestamp_seconds": c.timestamp_seconds,
            "storage_path": c.storage_path,
            "blur_score": c.blur_score,
            "mean_luminance": c.mean_luminance,
            "width": c.width,
            "height": c.height,
            "duplicate_status": c.duplicate_status,
            "duplicate_hash": c.duplicate_hash,
            "duplicate_of_frame_id": c.duplicate_of_frame_id,
            "is_selected": True,
            "selection_reason": "; ".join(reason_parts) if reason_parts else "selected_by_pipeline",
        }
        selected.append(record)

        last_ts = t
        try:
            prev_gray = _frame_to_gray(c.storage_path)
        except Exception:
            prev_gray = None
        prev_path = c.storage_path

    return selected
