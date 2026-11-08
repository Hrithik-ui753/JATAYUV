from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.reconstruction import Reconstruction
from backend.app.models.user import User
from backend.app.schemas.reconstruction import ReconstructionResponse
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Reconstructions"])


@router.get(
    "/missions/{mission_id}/reconstructions",
    response_model=List[ReconstructionResponse],
)
def list_mission_reconstructions(
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
            detail="Not authorised to list reconstructions for this mission",
        )
    recos = (
        db.query(Reconstruction)
        .filter(Reconstruction.mission_id == mission_id)
        .order_by(Reconstruction.created_at.desc())
        .all()
    )
    return [ReconstructionResponse.model_validate(r) for r in recos]
