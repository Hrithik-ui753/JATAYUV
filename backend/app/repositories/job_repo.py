"""Job repository — all job-related database operations."""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.job import Job
from backend.app.models.job_log import JobLog


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id: str) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def list_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Job]:
        return (
            self.db.query(Job)
            .filter(Job.project_id == project_id)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 200) -> List[Job]:
        return self.db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, project_id: str, job_type: str, timeout_seconds: int = 3600) -> Job:
        job = Job(
            project_id=project_id,
            job_type=job_type,
            status="queued",
            progress_pct=0,
            timeout_seconds=timeout_seconds,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_status(
        self,
        job: Job,
        status: str,
        progress_pct: int = None,
        error_message: str = None,
    ) -> Job:
        job.status = status
        if progress_pct is not None:
            job.progress_pct = progress_pct
        if error_message is not None:
            job.error_message = error_message
        if status == "processing" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed", "cancelled"):
            job.completed_at = datetime.now(timezone.utc)
        if status == "cancelled":
            job.cancelled_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def add_log(self, job_id: str, message: str, level: str = "INFO") -> JobLog:
        log_entry = JobLog(job_id=job_id, message=message, level=level)
        self.db.add(log_entry)
        self.db.commit()
        return log_entry

    def get_logs(self, job_id: str) -> List[JobLog]:
        return (
            self.db.query(JobLog)
            .filter(JobLog.job_id == job_id)
            .order_by(JobLog.created_at.asc())
            .all()
        )

    def cancel(self, job: Job) -> Job:
        if job.status in ("pending", "queued", "processing"):
            return self.update_status(job, "cancelled")
        return job

