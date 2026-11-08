from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.mission import (
    MissionCreate,
    MissionUpdate,
    MissionResponse,
    MissionListResponse,
)
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(prefix="/missions", tags=["Missions"])


def _mission_to_response(mission: Mission, db: Session) -> MissionResponse:
    return MissionResponse(
        id=mission.id,
        user_id=mission.user_id,
        project_id=mission.project_id,
        mission_name=mission.mission_name,
        description=mission.description,
        location_name=mission.location_name,
        status=mission.status,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        started_at=mission.started_at,
        completed_at=mission.completed_at,
    )


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(
    mission_in: MissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(mission_in.project_id, db, current_user)
    mission = Mission(
        user_id=current_user.id,
        project_id=mission_in.project_id,
        mission_name=mission_in.mission_name,
        description=mission_in.description,
        location_name=mission_in.location_name,
        status="created",
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return _mission_to_response(mission, db)


@router.get("", response_model=List[MissionListResponse])
def list_missions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        query = db.query(Mission).order_by(Mission.created_at.desc())
    else:
        query = (
            db.query(Mission)
            .filter(Mission.user_id == current_user.id)
            .order_by(Mission.created_at.desc())
        )
    missions = query.offset(skip).limit(limit).all()
    result = []
    for m in missions:
        counts = (
            db.query(
                func.coalesce(func.count(Mission.id), 0).label("m"),
            )
            .filter(Mission.id == m.id)
            .first()
        )
        result.append(
            MissionListResponse(
                **_mission_to_response(m, db).model_dump(),
                video_count=db.query(func.count(Mission.id)).filter(
                    Mission.id == m.id
                ).scalar() or 0,
                reconstruction_count=(
                    db.query(func.count(Mission.id))
                    .join(Mission.reconstructions)
                    .filter(Mission.id == m.id)
                    .scalar()
                    or 0
                ),
            )
        )
    return result


@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to access this mission",
        )
    return _mission_to_response(mission, db)


@router.patch("/{mission_id}", response_model=MissionResponse)
def update_mission(
    mission_id: str,
    mission_in: MissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to modify this mission",
        )

    if mission_in.mission_name is not None:
        mission.mission_name = mission_in.mission_name
    if mission_in.description is not None:
        mission.description = mission_in.description
    if mission_in.location_name is not None:
        mission.location_name = mission_in.location_name
    if mission_in.status is not None:
        mission.status = mission_in.status

    db.commit()
    db.refresh(mission)
    return _mission_to_response(mission, db)


@router.delete("/{mission_id}")
def delete_mission(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to delete this mission",
        )
    db.delete(mission)
    db.commit()
    return {"success": True, "message": "Mission deleted successfully"}
