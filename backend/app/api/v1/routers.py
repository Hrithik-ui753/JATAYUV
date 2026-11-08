from __future__ import annotations

from backend.app.api.v1.mission_video_processing import router as video_processing_router
from backend.app.api.v1.mission_perception import (  # noqa: E402
    router as perception_router,
    router_public as frame_perception_router,
)

__all__ = [
    "video_processing_router",
    "perception_router",
    "frame_perception_router",
]
