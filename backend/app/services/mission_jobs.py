from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy.orm import Session
from backend.app.models.job import Job
from backend.app.models.job_log import JobLog
from backend.app.repositories.job_repo import JobRepository

MissionStage = (
    "upload_validation"
    "video_processing"
    "depth_estimation"
    "segmentation"
    "camera_tracking"
    "reconstruction"
    "georeferencing"
    "validation"
    "export"
)


class MissionJobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)

    def create_stage_job(
        self,
        *,
        project_id: str,
        mission_id: Optional[str] = None,
        stage: str,
        job_type: str = "mission_stage",
        timeout_seconds: int = 3600,
    ) -> Job:
        job = Job(
            project_id=project_id,
            mission_id=mission_id,
            job_type=job_type,
            stage=stage,
            status="queued",
            progress_pct=0,
            timeout_seconds=timeout_seconds,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        self.repo.add_log(
            job.id, f"Stage '{stage}' queued.", level="INFO"
        )
        return job

    def start_stage(self, job: Job) -> Job:
        if job.status in {"completed", "failed", "cancelled"}:
            return job
        job.status = "processing"
        job.progress_pct = 0
        if not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        self.repo.add_log(job.id, f"Stage '{job.stage}' started.", level="INFO")
        return job

    def update_progress(self, job: Job, progress_pct: int, message: Optional[str] = None) -> Job:
        job.progress_pct = max(0, min(100, int(progress_pct)))
        if message:
            self.repo.add_log(job.id, message, level="INFO")
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_stage(self, job: Job, message: Optional[str] = None) -> Job:
        return self.repo.transition_to_terminal(job, "completed", error_message=message)

    def fail_stage(self, job: Job, error: str) -> Job:
        return self.repo.transition_to_terminal(job, "failed", error_message=error)

    def cancel_stage(self, job: Job, reason: str = "Cancelled by user") -> Job:
        return self.repo.transition_to_terminal(job, "cancelled", error_message=reason)

    def logs(self, job_id: str) -> list[JobLog]:
        return self.repo.get_logs(job_id)
