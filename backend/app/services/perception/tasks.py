from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from celery import shared_task
except ImportError:
    shared_task = None  # type: ignore[assignment]

log = logging.getLogger("jatayuv.perception.tasks")

if shared_task is None:
    shared_task = lambda f: f  # type: ignore[assignment]


def _describe_available_tasks() -> Dict[str, Any]:
    return {
        "description": "P3 perception Celery task helpers are defined here.",
        "note": "Real Celery task definitions for depth/segmentation/dynamic/fuse/report "
        "belong in the existing celery_app bundle; this module only provides helpers "
        "and metadata.",
        "tasks_planned": [
            "depth_inference_task",
            "segmentation_inference_task",
            "dynamic_detection_task",
            "per_frame_perception_fuse_task",
            "mission_perception_report_task",
        ],
    }
