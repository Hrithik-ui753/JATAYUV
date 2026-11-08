from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.app.services.depth_estimation import depth_service
from backend.app.services.segmentation import (
    SemanticSegmentationService,
    SegmentationModelUnavailable,
)

log = logging.getLogger("jatayuv.perception")

# ---------------------------------------------------------------------------
# SegFormer-style segmentation class mapping
# ---------------------------------------------------------------------------
#
# P3 requests these target scene categories:
#
#   1. Buildings and structures
#   2. Roads and paved surfaces
#   3. Vegetation
#   4. Ground and terrain
#   5. Water
#   6. Vehicles
#   7. Humans
#   8. Obstacles
#   9. Unknown or unsupported classes
#
# The existing backend segmentation service uses a custom AerialSegmentationModel
# with 7 classes: background, building, vegetation, road, water, soil, vehicle.
#
# That model does **not** support humans, generic obstacles, sky, or a dedicated
# "ground/terrain beyond bare soil" class. Those must be mapped to UNKNOWN rather
# than invented.
#
# If a real SegFormer pretrained checkpoint is later installed, this mapping layer
# is the only place that should be adjusted; the rest of P3 must not assume classes
# the checkpoint was not trained to identify.

SEGMENTATION_TARGET_TO_MODEL_CLASS: Dict[str, Optional[int]] = {
    # target category -> existing model class id, or None when unsupported
    "buildings_and_structures": 1,   # building
    "roads_and_paved_surfaces": 3,  # road
    "vegetation": 2,                # vegetation
    "ground_and_terrain": 5,        # soil / bare ground
    "water": 4,                     # water
    "vehicles": 6,                  # vehicle
    "humans": None,                 # unsupported by current model
    "obstacles": None,              # not a trained class
    "unknown_or_unsupported": 0,    # background / unclassified
}


def map_segmentation_target_to_model_class(target: str) -> Optional[int]:
    """Return the existing model class id for a P3 target category, or None."""
    return SEGMENTATION_TARGET_TO_MODEL_CLASS.get(target)


def describe_supported_segmentation_classes() -> Dict[str, Any]:
    """Describe what the currently integrated segmentation model can and cannot do."""
    svc = SemanticSegmentationService()
    info = svc.checkpoint_info()
    return {
        "architecture": info.get("architecture"),
        "num_classes": info.get("num_classes"),
        "checkpoint_available": info.get("checkpoint_available"),
        "checkpoint_path": info.get("checkpoint_path"),
        "checkpoint_sha256": info.get("checkpoint_sha256"),
        "supported_classes": [
            {"id": c["id"], "name": c["name"], "label": c["label"]}
            for c in SemanticSegmentationService.CLASSES
        ],
        "target_mapping": {
            k: ("supported" if v is not None else "unsupported")
            for k, v in SEGMENTATION_TARGET_TO_MODEL_CLASS.items()
        },
        "notes": [
            "This segmentation model does not support 'humans' or generic 'obstacles'.",
            "Unsupported P3 target categories are mapped to UNKNOWN, not invented.",
            "Accuracy metrics are not claimed at inference time.",
        ],
    }


def describe_depth_model() -> Dict[str, Any]:
    """Describe the integrated depth model honestly."""
    models = depth_service.available_models()
    pretrained = models.get("pretrained", {})
    return {
        "model_id": "pretrained",
        "architecture": "DepthAnythingV2Small",
        "variant": "vits",
        "source": "official Depth Anything V2 release",
        "license": "Apache-2.0 (model code; checkpoint license as published by Depth Anything)",
        "checkpoint_path": pretrained.get("checkpoint_path"),
        "checkpoint_available": pretrained.get("checkpoint_available"),
        "checkpoint_sha256": pretrained.get("checkpoint_sha256"),
        "version": pretrained.get("version"),
        "input_resolution": pretrained.get("input_size"),
        "output_type": "relative_inverse_depth",
        "depth_type": "relative",
        "depth_unit": "relative_inverse_depth",
        "is_metric": False,
        "notes": [
            "Output is relative inverse depth, higher = nearer.",
            "This is not metric depth unless a calibrated checkpoint is used.",
            "No accuracy metric is claimed here.",
        ],
    }


def describe_dynamic_detection_model() -> Dict[str, Any]:
    """Describe the currently integrated dynamic object detector honestly.

    In this environment no detector checkpoint is installed yet, and
    `ultralytics` is not present. This function reports that honestly rather
    than fabricating a detector.
    """
    return {
        "model_id": None,
        "architecture": None,
        "variant": None,
        "source": None,
        "license": None,
        "checkpoint_path": None,
        "checkpoint_available": False,
        "checkpoint_sha256": None,
        "supported_categories": [
            "humans",
            "cars",
            "trucks",
            "buses",
            "motorcycles",
            "other_supported_vehicles",
        ],
        "notes": [
            "No dynamic object detector is integrated yet in this environment.",
            "When installed, category-only detections must be labeled POTENTIALLY_DYNAMIC.",
            "True motion detection is out of scope for P3 and requires temporal tracking.",
        ],
    }
