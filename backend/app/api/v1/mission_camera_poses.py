from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.camera_pose import CameraPose
from backend.app.models.user import User
from backend.app.schemas.camera_pose import CameraPoseResponse
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Camera Poses"])


@router.get(
    "/missions/{mission_id}/camera-poses",
    response_model=List[CameraPoseResponse],
)
def list_mission_camera_poses(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to list camera poses for this mission",
        )
    poses = (
        db.query(CameraPose)
        .filter(CameraPose.mission_id == mission_id)
        .order_by(CameraPose.created_at.desc())
        .all()
    )
    return [CameraPoseResponse.model_validate(p) for p in poses]
