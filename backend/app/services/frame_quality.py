"""Frame quality analysis for extracted drone frames.

 Implements:
 * blur detection via variance of Laplacian on grayscale
 * exposure analysis via mean luminance with under/overexposure bands
 * minimum resolution checks
 * perceptual duplicate detection using ImageHash dHash

 All scores are measured from the saved frame image. No synthetic values are
 produced.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from imagehash import dhash, hex_to_hash


@dataclass
class QualityResult:
    frame_id: str
    blur_score: Optional[float]
    blur_threshold: float
    blur_status: str  # sharp | soft | severely_blurred
    mean_luminance: Optional[float]
    exposure_low: Optional[float]
    exposure_high: Optional[float]
    exposure_status: str  # normal | underexposed | overexposed
    width: int
    height: int
    min_width: Optional[int]
    min_height: Optional[int]
    resolution_status: str  # ok | too_small
    duplicate_hash: Optional[str]
    duplicate_status: str  # unique | exact_duplicate | near_duplicate
    duplicate_of_frame_id: Optional[str]
    duplicate_distance: Optional[int]
    classification: str  # accepted | warning | rejected
    reasons: List[str]


@dataclass
class QualityConfig:
    blur_threshold: float = 100.0
    severe_blur_threshold: float = 10.0
    exposure_low: float = 25.0
    exposure_high: float = 230.0
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    dhash_size: int = 8
    near_duplicate_hamming_max: int = 2
    allow_warning_on_exposure: bool = True
    allow_warning_on_blur: bool = True


def _grayscale(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read frame for quality analysis: {path}")
    return img


def blur_score_from_path(path: str) -> float:
    gray = _grayscale(path)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())


def luminance_stats_from_path(path: str) -> Tuple[float, float, float]:
    """Return (mean, min, max) of grayscale luminance."""
    gray = _grayscale(path)
    return float(gray.mean()), float(gray.min()), float(gray.max())


def perceptual_hash(path: str, size: int = 8) -> str:
    gray = _grayscale(path)
    h = dhash(gray, size=size)
    return str(h)


def duplicate_status_between_hashes(
    hash_a: str,
    hash_b: str,
    *,
    max_near_distance: int = 2,
) -> Tuple[str, int]:
    """Return (status, hamming_distance).

    exact_duplicate when identical, near_duplicate when within threshold,
    otherwise unique.
    """
    ha = hex_to_hash(hash_a) if isinstance(hash_a, str) else hash_a
    hb = hex_to_hash(hash_b) if isinstance(hash_b, str) else hash_b
    dist = int((ha - hb))
    if dist == 0:
        return "exact_duplicate", dist
    if dist <= max_near_distance:
        return "near_duplicate", dist
    return "unique", dist


def analyze_frame_quality(
    frame_id: str,
    storage_path: str,
    *,
    config: Optional[QualityConfig] = None,
) -> QualityResult:
    """Analyze one saved frame and return measured quality results."""
    config = config or QualityConfig()

    reasons: List[str] = []
    blur_score: Optional[float] = None
    blur_status = "sharp"
    mean_luminance: Optional[float] = None
    exposure_status = "normal"
    resolution_status = "ok"
    duplicate_status = "unique"
    duplicate_of_frame_id: Optional[str] = None
    duplicate_distance: Optional[int] = None
    duplicate_hash: Optional[str] = None

    try:
        blur_score = blur_score_from_path(storage_path)
        if blur_score < config.severe_blur_threshold:
            blur_status = "severely_blurred"
            reasons.append("severely_blurred")
        elif blur_score < config.blur_threshold:
            blur_status = "soft"
            if config.allow_warning_on_blur:
                reasons.append("soft_focus")
    except Exception as exc:
        reasons.append(f"blur_analysis_error: {exc}")

    try:
        mean, mn, mx = luminance_stats_from_path(storage_path)
        mean_luminance = mean
        if mean < config.exposure_low:
            exposure_status = "underexposed"
            reasons.append("underexposed")
        elif mean > config.exposure_high:
            exposure_status = "overexposed"
            reasons.append("overexposed")
    except Exception as exc:
        reasons.append(f"exposure_analysis_error: {exc}")

    width = 0
    height = 0
    try:
        img = cv2.imread(storage_path)
        if img is not None:
            height, width = img.shape[:2]
    except Exception:
        pass

    if config.min_width and width < config.min_width:
        resolution_status = "too_small"
        reasons.append("width_below_minimum")
    if config.min_height and height < config.min_height:
        resolution_status = "too_small"
        reasons.append("height_below_minimum")

    if resolution_status == "too_small":
        reasons.append("low_resolution")

    # Duplicate detection requires a hash and a comparison corpus; this function
    # only computes the hash here. Comparison is performed by the duplicate
    # detection stage.
    try:
        duplicate_hash = perceptual_hash(storage_path, size=config.dhash_size)
    except Exception as exc:
        # If we cannot hash, treat as unique for now but record the error.
        reasons.append(f"duplicate_hash_error: {exc}")

    # Classification rules
    classification = "accepted"
    if resolution_status == "too_small":
        classification = "rejected"
    elif blur_status == "severely_blurred":
        classification = "rejected"
    elif exposure_status in ("underexposed", "overexposed"):
        if config.allow_warning_on_exposure:
            classification = "warning"
    elif blur_status == "soft":
        if config.allow_warning_on_blur:
            classification = "warning"

    return QualityResult(
        frame_id=frame_id,
        blur_score=blur_score,
        blur_threshold=config.blur_threshold,
        blur_status=blur_status,
        mean_luminance=mean_luminance,
        exposure_low=config.exposure_low,
        exposure_high=config.exposure_high,
        exposure_status=exposure_status,
        width=width,
        height=height,
        min_width=config.min_width,
        min_height=config.min_height,
        resolution_status=resolution_status,
        duplicate_hash=duplicate_hash,
        duplicate_status=duplicate_status,
        duplicate_of_frame_id=duplicate_of_frame_id,
        duplicate_distance=duplicate_distance,
        classification=classification,
        reasons=reasons,
    )


def quality_result_to_dict(r: QualityResult) -> Dict[str, Any]:
    return {
        "frame_id": r.frame_id,
        "blur_score": r.blur_score,
        "blur_threshold": r.blur_threshold,
        "blur_status": r.blur_status,
        "mean_luminance": r.mean_luminance,
        "exposure_low": r.exposure_low,
        "exposure_high": r.exposure_high,
        "exposure_status": r.exposure_status,
        "width": r.width,
        "height": r.height,
        "min_width": r.min_width,
        "min_height": r.min_height,
        "resolution_status": r.resolution_status,
        "duplicate_hash": r.duplicate_hash,
        "duplicate_status": r.duplicate_status,
        "duplicate_of_frame_id": r.duplicate_of_frame_id,
        "duplicate_distance": r.duplicate_distance,
        "classification": r.classification,
        "reasons": r.reasons,
    }
