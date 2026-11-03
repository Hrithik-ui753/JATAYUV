"""Project repository — all project-related database operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def list_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return self.db.query(Project).offset(skip).limit(limit).all()

    def create(self, owner_id: str, name: str, description: str = "", location: str = "") -> Project:
        project = Project(
            owner_id=owner_id,
            name=name,
            description=description,
            location=location,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project: Project, **kwargs) -> Project:
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

