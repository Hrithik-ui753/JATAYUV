from __future__ import annotations

import logging
from typing import Any, Dict

log = logging.getLogger("jatayuv.perception")

from backend.app.services.perception.depth import (
    describe_depth_model as _describe_depth_model,
)
from backend.app.services.perception.segmentation import (
    describe_segmentation_model as _describe_segmentation_model,
)
from backend.app.services.perception.dynamic import (
    describe_dynamic_model as _describe_dynamic_model,
)
from backend.app.services.perception import (
    is_depth_available,
    is_segmentation_available,
    is_dynamic_detection_available,
)


def describe_all_perception_models() -> Dict[str, Any]:
    """Return a consolidated description of every P3 model available to this service."""
    return {
        "depth": _describe_depth_model(),
        "segmentation": _describe_segmentation_model(),
        "dynamic_detection": _describe_dynamic_model(),
        "availability": {
            "depth": is_depth_available(),
            "segmentation": is_segmentation_available(),
            "dynamic_detection": is_dynamic_detection_available(),
        },
    }
