from __future__ import annotations

from backend.app.workers.celery_app import celery_app
<<<<<<< HEAD

__all__ = ["celery_app"]
=======
from backend.app.workers.video_tasks import (
    extract_frames_from_video_task,
    probe_video_task,
    run_duplicate_detection_task,
)
from backend.app.workers.tasks import (
    compute_frame_quality_task,
    select_frames_task,
    clear_job_task,
)
from backend.app.workers.tasks_perception import (  # noqa: E402
    depth_inference_task,
    segmentation_inference_task,
    dynamic_detection_task,
    per_frame_perception_fuse_task,
    mission_perception_report_task,
)

__all__ = [
    "celery_app",
    "extract_frames_from_video_task",
    "probe_video_task",
    "run_duplicate_detection_task",
    "compute_frame_quality_task",
    "select_frames_task",
    "clear_job_task",
    "depth_inference_task",
    "segmentation_inference_task",
    "dynamic_detection_task",
    "per_frame_perception_fuse_task",
    "mission_perception_report_task",
]
>>>>>>> origin/main
