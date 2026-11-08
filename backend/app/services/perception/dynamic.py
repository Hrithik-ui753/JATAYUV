from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import numpy.typing as npt

from backend.app.services.perception import describe_dynamic_detection_model

log = logging.getLogger("jatayuv.perception.dynamic")

Detection = Dict[str, Any]


@dataclass
class DynamicDetectionResult:
    detections: List[Detection]
    model_id: Optional[str]
    model_version: Optional[str]
    checkpoint_sha256: Optional[str]
    inference_device: str
    inference_duration_ms: float
    preprocessing_json: Dict[str, Any]
    dynamic_label_policy: str


def infer_dynamic_objects(
    frame_bgr: np.ndarray,
    *,
    model_id: Optional[str] = None,
) -> DynamicDetectionResult:
    """Run dynamic object detection on a single BGR frame.

    In this environment there is no installed detector checkpoint, so this
    function does not fabricate detections. It returns an explicit "detector
    unavailable" result so pipeline logic can decide how to proceed.
    """
    frame_h, frame_w = frame_bgr.shape[:2]

    # Honest unavailability path. We do not attempt to install or download a
    # detector here; that decision is documented in the P3 plan and left to a
    # separate deployment/ops step.
    return DynamicDetectionResult(
        detections=[],
        model_id=None,
        model_version=None,
        checkpoint_sha256=None,
        inference_device="unavailable",
        inference_duration_ms=0.0,
        preprocessing_json={"detector_model_id": model_id, "detector_available": False},
        dynamic_label_policy="POTENTIALLY_DYNAMIC",
    )


def build_dynamic_exclusion_mask(
    frame_bgr: np.ndarray,
    detections: List[Detection],
) -> np.ndarray:
    """Build a per-frame dynamic exclusion mask from detector output.

    Where a detector returns instance masks or boxes, this mask marks those
    bounding regions as dynamic. If a detector does not produce masks, boxes
    are expanded into conservative rectangular masks.

    Do not mark the whole image dynamic just because a detector is present.
    Do not classify unsupported categories as known dynamic classes.
    """
    h, w = frame_bgr.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    for det in detections:
        category = det.get("category", "")
        if category not in _DYNAMIC_CATEGORIES:
            continue
        box = det.get("box") or det.get("bbox") or det.get("xyxy")
        if box is None:
            continue
        x1, y1, x2, y2 = [int(v) for v in box]
        x1 = max(0, min(w, x1))
        y1 = max(0, min(h, y1))
        x2 = max(0, min(w, x2))
        y2 = max(0, min(h, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)
    return mask


def is_dynamic_detection_available() -> bool:
    from backend.app.services.perception.dynamic import (
        describe_dynamic_detection_model as _describe,
    )

    info = _describe()
    return bool(info.get("checkpoint_available")) and bool(info.get("model_id"))


def describe_dynamic_model() -> Dict[str, Any]:
    return describe_dynamic_detection_model()


_DYNAMIC_CATEGORIES = {
    "humans",
    "person",
    "people",
    "car",
    "cars",
    "vehicle",
    "vehicles",
    "truck",
    "trucks",
    "bus",
    "buses",
    "motorcycle",
    "motorcycles",
    "bicycle",
    "bicycles",
}
