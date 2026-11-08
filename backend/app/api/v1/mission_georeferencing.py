from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.georef_solution import GeorefSolution
from backend.app.models.user import User
from backend.app.schemas.georef_solution import GeorefSolutionResponse
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Georeferencing"])


@router.get(
    "/missions/{mission_id}/georeferencing",
    response_model=List[GeorefSolutionResponse],
)
def list_mission_georeferencing(
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
            detail="Not authorised to list georeferencing for this mission",
        )
    solutions = (
        db.query(GeorefSolution)
        .filter(GeorefSolution.mission_id == mission_id)
        .order_by(GeorefSolution.created_at.desc())
        .all()
    )
    return [GeorefSolutionResponse.model_validate(s) for s in solutions]
