"""Mission video processing orchestration for P2.

 Coordinates validation, metadata extraction, frame extraction, quality analysis,
 duplicate detection, adaptive selection and GPS association through Celery tasks.

 Keeps the existing job lifecycle semantics: a terminal job cannot be moved back
 to running; retries do not create duplicate frame records or duplicate artifacts.
"""
from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.database import SessionLocal
from backend.app.models.frame import Frame
from backend.app.models.job import Job
from backend.app.models.job_log import JobLog
from backend.app.models.mission import Mission
from backend.app.models.video import Video
from backend.app.repositories.job_repo import JobRepository
from backend.app.services.frame_extractor import FrameExtractionConfig, extract_frames_for_video
from backend.app.services.frame_quality import QualityConfig, analyze_frame_quality, quality_result_to_dict
from backend.app.services.frame_selection import FrameCandidate, SelectionConfig, select_frames
from backend.app.services.gps_association import (
    GPSAssociationConfig,
    FlightMetadata,
    associate_gps_for_frames,
    flight_metadata_to_gps_records,
    parse_csv_telemetry,
)
from backend.app.services.storage import get_mission_storage
from backend.app.services.video_probe import VideoLimits, build_video_report, decode_video_metadata
def _delay_pipeline(**kwargs: Any) -> Any:
    from backend.app.workers.video_tasks import run_full_processing_pipeline
    return run_full_processing_pipeline.delay(**kwargs)


def _new_processing_run_id() -> str:
    return uuid.uuid4().hex


def create_video_processing_job(
    mission_id: str,
    video_id: str,
    *,
    db,
    user_id: str,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Job:
    """Create a video-processing job and return it."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise ValueError("Mission not found")

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError("Video not found")

    cfg = video_processing_config or {}
    job = Job(
        project_id=mission.project_id,
        mission_id=mission_id,
        job_type="video_processing",
        stage="upload_validation",
        status="queued",
        progress_pct=0,
        owner_id=user_id,
        error_message=None,
        timeout_seconds=int(cfg.get("timeout_seconds", 3600)),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_id = _new_processing_run_id()
    job.processing_run_id = run_id
    db.commit()
    db.refresh(job)

    JobRepository(db).add_log(
        job.id,
        f"Video processing queued; processing_run_id={run_id}",
        level="INFO",
    )
    return job


def enqueue_full_processing(
    mission_id: str,
    video_id: str,
    *,
    user_id: str,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate and enqueue the full processing pipeline for a video."""
    db = SessionLocal()
    try:
        job = create_video_processing_job(
            mission_id,
            video_id,
            db=db,
            user_id=user_id,
            video_processing_config=video_processing_config,
        )
        video = db.query(Video).filter(Video.id == video_id).first()
        task_kwargs = _build_pipeline_kwargs(job, video, video_processing_config)
        try:
            async_result = _delay_pipeline(**task_kwargs)
        except Exception as exc:  # broker unreachable or misconfigured
            job.status = "failed"
            job.error_message = (
                "Failed to enqueue processing task (is the Celery broker "
                f"reachable?): {exc}"
            )
            db.commit()
            raise RuntimeError(job.error_message) from exc

        job.celery_task_id = getattr(async_result, "id", None)
        db.refresh(job)
        # In eager/dev mode the task runs inline and may already be terminal;
        # never move a terminal job back to queued.
        if job.status not in ("completed", "failed", "cancelled"):
            job.status = "queued"
        db.commit()
        db.refresh(job)
        return {
            "job_id": job.id,
            "celery_task_id": job.celery_task_id,
            "processing_run_id": job.processing_run_id,
            "status": job.status,
        }
    finally:
        db.close()


def cancel_video_processing(
    video_id: str,
    *,
    db,
    user_id: str,
    role: str,
) -> Dict[str, Any]:
    """Cancel the active video-processing job for a video (cooperative)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError("Video not found")

    mission = db.query(Mission).filter(Mission.id == video.mission_id).first()
    if mission is None:
        raise ValueError("Video mission not found")
    if role != "admin" and mission.user_id != user_id:
        raise PermissionError("Not authorised to cancel processing for this video")

    job = (
        db.query(Job)
        .filter(
            Job.mission_id == video.mission_id,
            Job.job_type == "video_processing",
            Job.status.in_(("queued", "processing", "pending")),
        )
        .order_by(Job.created_at.desc())
        .first()
    )
    if job is None:
        return {"status": "no_active_job", "video_id": video_id}

    if job.celery_task_id:
        try:
            from backend.app.workers.celery_app import celery_app

            celery_app.control.revoke(job.celery_task_id, terminate=False)
        except Exception:
            # The database status is authoritative; workers poll it between
            # stages. Broker failures must not block cancellation.
            pass

    job.status = "cancelled"
    job.cancelled_at = datetime.now(timezone.utc)
    job.error_message = "Cancelled by user"
    db.commit()
    JobRepository(db).add_log(job.id, "Video processing cancelled by user", level="WARN")
    return {"status": "cancelled", "job_id": job.id, "video_id": video_id}


def _build_pipeline_kwargs(
    job: Job,
    video: Video,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = config or {}
    return {
        "job_id": job.id,
        "video_id": video.id,
        "mission_id": video.mission_id,
        "processing_run_id": job.processing_run_id,
        "video_storage_path": video.storage_path,
        "video_processing_config": cfg,
    }


def get_processing_status_for_mission(
    mission_id: str,
    db,
    current_user_id: str,
    role: str,
) -> Dict[str, Any]:
    """Return the current processing status for a mission.

    Returns the most recent video-processing job for the mission and its stage,
    progress and status. Does not expose internal paths to unauthorised callers.
    """
    if role != "admin" and mission_id not in [str(m.id) for m in db.query(Mission).filter(Mission.user_id == current_user_id).all()]:
        return {"error": "not authorised"}

    jobs = (
        db.query(Job)
        .filter(Job.mission_id == mission_id, Job.job_type == "video_processing")
        .order_by(Job.created_at.desc())
        .all()
    )
    if not jobs:
        return {"status": "no_processing", "jobs": []}

    latest = jobs[0]
    return {
        "status": latest.status,
        "stage": latest.stage,
        "progress_pct": latest.progress_pct,
        "celery_task_id": latest.celery_task_id,
        "processing_run_id": getattr(latest, "processing_run_id", None),
        "error_message": latest.error_message,
        "started_at": latest.started_at.isoformat() if latest.started_at else None,
        "completed_at": latest.completed_at.isoformat() if latest.completed_at else None,
        "jobs": [
            {
                "id": j.id,
                "status": j.status,
                "stage": j.stage,
                "progress_pct": j.progress_pct,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }


def get_processing_report_for_mission(
    mission_id: str,
    db,
    current_user_id: str,
    role: str,
    processing_run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a structured processing report for a mission processing run."""
    if role != "admin" and mission_id not in [str(m.id) for m in db.query(Mission).filter(Mission.user_id == current_user_id).all()]:
        return {"error": "not authorised"}

    query = db.query(Job).filter(
        Job.mission_id == mission_id,
        Job.job_type == "video_processing",
    )
    if processing_run_id:
        query = query.filter(Job.processing_run_id == processing_run_id)
    jobs = query.order_by(Job.created_at.desc()).all()
    if not jobs:
        return {"error": "no_processing_found"}

    latest = jobs[0]

    frame_query = db.query(Frame).filter(Frame.mission_id == mission_id)
    if processing_run_id:
        frame_query = frame_query.filter(Frame.processing_run_id == processing_run_id)
    frames = frame_query.all()

    total = len(frames)
    accepted = sum(1 for f in frames if getattr(f, "quality_status", None) == "accepted")
    warning = sum(1 for f in frames if getattr(f, "quality_status", None) == "warning")
    rejected = sum(1 for f in frames if getattr(f, "quality_status", None) in ("rejected", "low_quality"))
    unreviewed = sum(1 for f in frames if getattr(f, "quality_status", None) == "unreviewed")

    duplicate_count = sum(1 for f in frames if getattr(f, "duplicate_status", None) in ("exact_duplicate", "near_duplicate"))
    selected_count = sum(1 for f in frames if getattr(f, "is_selected", False))

    gps_associated = sum(1 for f in frames if getattr(f, "gps_source", None) not in (None, "none"))

    return {
        "mission_id": mission_id,
        "processing_run_id": getattr(latest, "processing_run_id", None),
        "job_id": latest.id,
        "job_status": latest.status,
        "job_stage": latest.stage,
        "progress_pct": latest.progress_pct,
        "total_frames": total,
        "frames_accepted": accepted,
        "frames_warning": warning,
        "frames_rejected": rejected,
        "frames_unreviewed": unreviewed,
        "duplicate_frames": duplicate_count,
        "selected_frames": selected_count,
        "gps_associated_frames": gps_associated,
        "gps_coverage_pct": round((gps_associated / total * 100), 2) if total else 0.0,
        "error_message": latest.error_message,
        "notes": [
            "P2 does not compute camera poses or geometric overlap; those require P4.",
            "GPS association uses available flight telemetry; gaps and missing telemetry are left null.",
        ],
    }
