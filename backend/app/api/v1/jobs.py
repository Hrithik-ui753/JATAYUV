"""Jobs API — list, poll, cancel background analysis jobs and stream logs."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.job import Job
from backend.app.models.job_log import JobLog
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.job import JobResponse, JobLogResponse
from backend.app.api.deps import get_current_user, check_project_owner
from backend.app.repositories.job_repo import JobRepository

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        project_id=job.project_id,
        job_type=job.job_type,
        status=job.status,
        progress_pct=job.progress_pct,
        error_message=job.error_message,
        celery_task_id=job.celery_task_id,
        started_at=job.started_at,
        completed_at=job.completed_at,
        cancelled_at=getattr(job, "cancelled_at", None),
        retry_count=getattr(job, "retry_count", 0),
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("", response_model=List[JobResponse])
def list_all_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all jobs visible to the current user (admin sees all; analyst sees own projects)."""
    repo = JobRepository(db)
    if current_user.role == "admin":
        jobs = repo.list_all(skip=skip, limit=limit)
    else:
        # Collect project IDs owned by this user
        owned_ids = {p.id for p in db.query(Project).filter(Project.owner_id == current_user.id).all()}
        jobs = [j for j in repo.list_all(skip=0, limit=10000) if j.project_id in owned_ids]
        jobs = jobs[skip : skip + limit]
    return [_job_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Authorization: user must own the project or be admin
    if current_user.role != "admin":
        check_project_owner(job.project_id, db, current_user)
    return _job_to_response(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a queued or running job (best-effort; Celery task may already be executing)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current_user.role != "admin":
        check_project_owner(job.project_id, db, current_user)

    if job.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is already in terminal state: {job.status}",
        )

    # Attempt to revoke Celery task if one is running
    if job.celery_task_id:
        try:
            from backend.app.workers.celery_app import celery_app
            celery_app.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")
        except Exception:
            pass  # Best-effort — log but do not fail the request

    repo = JobRepository(db)
    repo.add_log(job.id, "Job cancelled by user request.", level="WARN")
    job = repo.cancel(job)
    return _job_to_response(job)


@router.get("/{job_id}/logs", response_model=List[JobLogResponse])
def get_job_logs(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return structured log entries for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if current_user.role != "admin":
        check_project_owner(job.project_id, db, current_user)

    repo = JobRepository(db)
    logs = repo.get_logs(job_id)
    return [
        JobLogResponse(
            id=log.id,
            job_id=log.job_id,
            level=log.level,
            message=log.message,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/projects/{project_id}", response_model=List[JobResponse])
def list_project_jobs(
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_project_owner(project_id, db, current_user)
    repo = JobRepository(db)
    jobs = repo.list_by_project(project_id, skip=skip, limit=limit)
    return [_job_to_response(j) for j in jobs]
