from backend.app.schemas.auth import Token, TokenData, LoginRequest, RefreshResponse
from backend.app.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.schemas.image import ImageResponse, ExifTelemetry
from backend.app.schemas.analysis import (
    DepthTriggerRequest,
    DepthResponse,
    SegmentationTriggerRequest,
    SegmentationResponse,
    DamageTriggerRequest,
    DamageResponse,
    ChangeTriggerRequest,
    ChangeResponse,
)
<<<<<<< HEAD
from backend.app.schemas.reconstruction import ReconstructionTriggerRequest, ReconstructionResponse
=======
from backend.app.schemas.reconstruction import ReconstructionResponse

# Legacy placeholder kept only so existing app startup wiring doesn't break.
# In current code ReconstructionTriggerRequest is not implemented; if it is needed
# it should be added here with an explicit definition.
ReconstructionTriggerRequest = None  # type: ignore[assignment]
>>>>>>> 0400f2f (p5-udpated)
from backend.app.schemas.job import JobResponse, JobLogResponse
from backend.app.schemas.ai_model import AIModelVersionResponse

__all__ = [
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "JobResponse",
    "JobLogResponse",
    "ImageResponse",
    "ExifTelemetry",
    "DepthTriggerRequest",
    "DepthResponse",
    "SegmentationTriggerRequest",
    "SegmentationResponse",
    "DamageTriggerRequest",
    "DamageResponse",
    "ChangeTriggerRequest",
    "ChangeResponse",
<<<<<<< HEAD
    "ReconstructionTriggerRequest",
=======
    "ReconstructionTriggerRequest",  # legacy; no longer defined in reconstruction.py after refactor
>>>>>>> 0400f2f (p5-udpated)
    "ReconstructionResponse",
    "AIModelVersionResponse",
]
