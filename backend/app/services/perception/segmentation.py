from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from backend.app.services.segmentation import (
    SemanticSegmentationService,
    SegmentationModelUnavailable,
)

log = logging.getLogger("jatayuv.perception.segmentation")

# Explicit mapping from JATAYUV domain target classes to LoveDA/aerial model indices
_TARGET_TO_MODEL_CLASS: Dict[str, Optional[int]] = {
    "buildings_and_structures": 1,
    "roads_and_paved_surfaces": 2,
    "vegetation": 3,
    "ground_and_terrain": 4,
    "water": 5,
    "vehicles": 6,
    "humans": None,
    "obstacles": None,
    "unknown_or_unsupported": None,
}

_SUPPORTED_CLASSES = [
    "background",
    "building",
    "road",
    "water",
    "barren",
    "forest",
    "agriculture",
]

_UNSUPPORTED_CLASS_HANDLING = {
    "humans": "mapped_to_unknown",
    "obstacles": "mapped_to_unknown",
    "unknown_or_unsupported": "mapped_to_unknown",
}


@dataclass
class SegmentationInferenceResult:
    mask_path: Optional[str] = None
    colored_mask_path: Optional[str] = None
    model_id: Optional[str] = "aerial_segmentation_v1"
    model_version: Optional[str] = "1.0.0"
    checkpoint_sha256: Optional[str] = None
    inference_duration_ms: float = 0.0
    class_distribution: Dict[str, float] = field(default_factory=dict)
    per_class_pixel_counts: Dict[str, int] = field(default_factory=dict)
    unsupported_class_handling: Dict[str, str] = field(
        default_factory=lambda: dict(_UNSUPPORTED_CLASS_HANDLING)
    )
    confidence_json: Dict[str, Any] = field(default_factory=dict)


def map_segmentation_target_to_model_class(target: str) -> Optional[int]:
    """Map a general geospatial label to the specific integer class id of the model."""
    return _TARGET_TO_MODEL_CLASS.get(target)


def describe_supported_segmentation_classes() -> Dict[str, Any]:
    return {
        "supported_classes": list(_SUPPORTED_CLASSES),
        "target_mapping": dict(_TARGET_TO_MODEL_CLASS),
        "unsupported_handling": dict(_UNSUPPORTED_CLASS_HANDLING),
    }


def is_segmentation_available() -> bool:
    try:
        service = SemanticSegmentationService()
        return service.is_available()
    except Exception:
        return False


def describe_segmentation_model() -> Dict[str, Any]:
    available = is_segmentation_available()
    return {
        "model_id": "aerial_segmentation_loveda",
        "model_name": "DeepLabV3+ / LoveDA Aerial Segmentation",
        "version": "1.0.0",
        "checkpoint_available": available,
        "classes": list(_SUPPORTED_CLASSES),
        "status": "available" if available else "unavailable",
    }


def infer_segmentation(
    frame_bgr: np.ndarray,
    *,
    model_id: Optional[str] = None,
) -> SegmentationInferenceResult:
    """Run aerial semantic segmentation on a single BGR frame."""
    h, w = frame_bgr.shape[:2]
    total_pixels = h * w

    service = SemanticSegmentationService()
    if service.is_available():
        # Verified checkpoint loaded
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
            in_path = tmp_in.name
        mask_path = in_path + ".mask.png"
        try:
            cv2.imwrite(in_path, frame_bgr)
            metrics = service.segment_aerial_image(in_path, mask_path)
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            classes, counts = np.unique(mask, return_counts=True)
            counts_dict = {str(int(c)): int(cnt) for c, cnt in zip(classes, counts)}
            dist_dict = {str(int(c)): float(cnt / total_pixels) for c, cnt in zip(classes, counts)}
            return SegmentationInferenceResult(
                mask_path=mask_path,
                model_id="aerial_segmentation_loveda",
                checkpoint_sha256=service.checkpoint_info().get("sha256"),
                inference_duration_ms=float(metrics.get("inference_time_ms", 0.0)),
                class_distribution=dist_dict,
                per_class_pixel_counts=counts_dict,
                unsupported_class_handling=dict(_UNSUPPORTED_CLASS_HANDLING),
            )
        finally:
            if os.path.exists(in_path):
                os.remove(in_path)
    else:
        # Checkpoint is unavailable: report honest unclassified / background distribution
        counts_dict = {"0": total_pixels}
        dist_dict = {"0": 1.0}
        return SegmentationInferenceResult(
            mask_path=None,
            model_id=None,
            checkpoint_sha256=None,
            inference_duration_ms=0.0,
            class_distribution=dist_dict,
            per_class_pixel_counts=counts_dict,
            unsupported_class_handling=dict(_UNSUPPORTED_CLASS_HANDLING),
        )
