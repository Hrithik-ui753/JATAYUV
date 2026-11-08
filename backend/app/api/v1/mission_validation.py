from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.validation_report import ValidationReport
from backend.app.models.user import User
from backend.app.schemas.validation_report import ValidationReportResponse
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Validation"])


@router.get(
    "/missions/{mission_id}/validation",
    response_model=List[ValidationReportResponse],
)
def list_mission_validation(
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
            detail="Not authorised to list validation for this mission",
        )
    reports = (
        db.query(ValidationReport)
        .filter(ValidationReport.mission_id == mission_id)
        .order_by(ValidationReport.generated_at.desc().nulls_last())
        .all()
    )
    return [ValidationReportResponse.model_validate(r) for r in reports]
