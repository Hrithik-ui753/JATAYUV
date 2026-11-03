from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.project import Project
from backend.app.models.image import Image
from backend.app.models.user import User
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        projects = db.query(Project).all()
    else:
        projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    
    result = []
    for p in projects:
        img_count = db.query(Image).filter(Image.project_id == p.id).count()
        resp = ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            location_name=p.location_name,
            center_lat=p.center_lat,
            center_lon=p.center_lon,
            owner_id=p.owner_id,
            image_count=img_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        result.append(resp)
    return result

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        name=project_in.name,
        description=project_in.description,
        location_name=project_in.location_name,
        center_lat=project_in.center_lat,
        center_lon=project_in.center_lon,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        location_name=project.location_name,
        center_lat=project.center_lat,
        center_lon=project.center_lon,
        owner_id=project.owner_id,
        image_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

@router.get("/{id}", response_model=ProjectResponse)
def get_project(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(id, db, current_user)
    img_count = db.query(Image).filter(Image.project_id == project.id).count()
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        location_name=project.location_name,
        center_lat=project.center_lat,
        center_lon=project.center_lon,
        owner_id=project.owner_id,
        image_count=img_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

@router.put("/{id}", response_model=ProjectResponse)
def update_project(
    id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(id, db, current_user)
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.location_name is not None:
        project.location_name = project_in.location_name
    if project_in.center_lat is not None:
        project.center_lat = project_in.center_lat
    if project_in.center_lon is not None:
        project.center_lon = project_in.center_lon
    
    db.commit()
    db.refresh(project)
    img_count = db.query(Image).filter(Image.project_id == project.id).count()
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        location_name=project.location_name,
        center_lat=project.center_lat,
        center_lon=project.center_lon,
        owner_id=project.owner_id,
        image_count=img_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

@router.delete("/{id}")
def delete_project(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(id, db, current_user)
    db.delete(project)
    db.commit()
    return {"success": True, "message": "Project deleted successfully"}

