"""Repository layer — thin data-access wrappers over SQLAlchemy sessions.

Separates query logic from route handlers, making it easier to test and swap
the underlying storage without changing API contracts.
"""
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.project_repo import ProjectRepository
from backend.app.repositories.job_repo import JobRepository

__all__ = ["UserRepository", "ProjectRepository", "JobRepository"]

