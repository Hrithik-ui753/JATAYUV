"""Celery tasks implementing the P2 drone video processing pipeline.

 Tasks are idempotent: re-running does not create duplicate Frame records or
 duplicate artifacts. Each run is tagged with a processing_run_id and frame
 records are keyed by video_id + frame_index within that run.

 Cancellation is cooperative: tasks poll the job status and abort when cancelled.
"""
from __future__ import annotations

<<<<<<< HEAD
import json
=======
>>>>>>> origin/main
import os
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import celery

from backend.app.core.database import SessionLocal
<<<<<<< HEAD
from backend.app.models.flight_metadata import FlightMetadata
=======
>>>>>>> origin/main
from backend.app.models.frame import Frame
from backend.app.models.job import Job
from backend.app.models.job_log import JobLog
from backend.app.models.video import Video
from backend.app.repositories.job_repo import JobRepository
<<<<<<< HEAD
from backend.app.services.duplicate_detector import detect_duplicates_in_batch
=======
>>>>>>> origin/main
from backend.app.services.frame_extractor import FrameExtractionConfig
from backend.app.services.frame_quality import QualityConfig, analyze_frame_quality, quality_result_to_dict
from backend.app.services.frame_selection import FrameCandidate, SelectionConfig, select_frames
from backend.app.services.gps_association import (
    GPSAssociationConfig,
    associate_gps_for_frames,
    flight_metadata_to_gps_records,
    parse_csv_telemetry,
)
<<<<<<< HEAD
=======
def _new_processing_run_id() -> str:
    import uuid
    return uuid.uuid4().hex
>>>>>>> origin/main
from backend.app.services.storage import get_mission_storage
from backend.app.services.video_probe import (
    VideoLimits,
    build_video_report,
    decode_video_metadata,
)
from backend.app.workers.celery_app import celery_app


<<<<<<< HEAD
def _new_processing_run_id() -> str:
    import uuid

    return uuid.uuid4().hex


=======
>>>>>>> origin/main
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(job_id: str, db, message: str, level: str = "INFO") -> None:
    repo = JobRepository(db)
    repo.add_log(job_id, message, level=level)


def _update_job(
    db,
    job: Job,
    *,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    progress_pct: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Job:
    if status is not None:
        job.status = status
    if stage is not None:
        job.stage = stage
    if progress_pct is not None:
        job.progress_pct = progress_pct
    if error_message is not None:
        job.error_message = error_message
    db.commit()
    db.refresh(job)
    return job


def _check_cancelled(db, job: Job) -> bool:
<<<<<<< HEAD
    # Cancellation is written by another request/session, so refresh the row
    # before deciding whether the worker should stop.
    try:
        db.refresh(job)
    except Exception:
        pass
    return job.status in ("cancelled",)
=======
    if job.status in ("cancelled",):
        return True
    return False
>>>>>>> origin/main


def _ensure_processing_run(job: Job, db) -> str:
    run_id = getattr(job, "processing_run_id", None)
    if not run_id:
        run_id = _new_processing_run_id()
        job.processing_run_id = run_id
        db.commit()
        db.refresh(job)
    return run_id


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.validate_video")
def validate_video_task(
    self,
    job_id: str,
    video_id: str,
    video_storage_path: str,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            _update_job(db, job, status="failed", error_message="Video not found")
            return {"status": "failed", "reason": "video not found"}

        _update_job(db, job, stage="upload_validation", status="processing", progress_pct=10)
        _log(job_id, db, "Starting video validation")

        config = video_processing_config or {}
        limits = VideoLimits.defaults()
        report = build_video_report(video_storage_path, limits=limits)

        if not report["valid"]:
            reasons = report.get("violations", [])
            msg = "Video validation failed: " + "; ".join(reasons)
            _log(job_id, db, msg, level="ERROR")
            _update_job(db, job, stage="upload_validation", status="failed", error_message=msg)
            return {"status": "failed", "reason": msg}

        _log(job_id, db, "Video validation passed", level="INFO")
        _update_job(
            db,
            job,
            stage="metadata_extraction",
            status="queued",
            error_message=None,
        )
        video.validation_status = "valid"
        db.commit()
        return {"status": "completed", "valid": True, "report": report}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Validation error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Metadata extraction
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.extract_video_metadata")
def extract_metadata_task(
    self,
    job_id: str,
    video_id: str,
    video_storage_path: str,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            _update_job(db, job, status="failed", error_message="Video not found")
            return {"status": "failed", "reason": "video not found"}

        _update_job(db, job, stage="metadata_extraction", status="processing", progress_pct=25)
        _log(job_id, db, "Extracting video metadata")

        decode = decode_video_metadata(video_storage_path)
        metadata = decode.metadata

        # Persist probed/extracted metadata to the Video record where possible.
        updated = False
        if metadata.width:
            video.width = metadata.width
            updated = True
        if metadata.height:
            video.height = metadata.height
            updated = True
        if metadata.duration_seconds is not None:
            video.duration_seconds = int(metadata.duration_seconds)
            updated = True
        if metadata.codec_name:
            video.codec = metadata.codec_name
            updated = True
        if metadata.nominal_fps is not None:
            video.frame_rate = int(round(metadata.nominal_fps))
            updated = True

        if updated:
            db.commit()

        _log(
            job_id,
            db,
            f"Metadata: duration={metadata.duration_seconds}, {metadata.width}x{metadata.height}, "
            f"codec={metadata.codec_name}, nominal_fps={metadata.nominal_fps}",
        )
        _update_job(db, job, stage="frame_extraction", status="queued", progress_pct=35)
        return {
            "status": "completed",
            "metadata": {
                "duration_seconds": metadata.duration_seconds,
                "width": metadata.width,
                "height": metadata.height,
                "codec_name": metadata.codec_name,
                "nominal_fps": metadata.nominal_fps,
                "avg_fps": metadata.avg_fps,
                "pixel_format": metadata.pixel_format,
                "stream_time_base": metadata.stream_time_base,
            },
        }
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Metadata extraction error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Frame extraction
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.extract_frames")
def extract_frames_task(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    video_storage_path: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            _update_job(db, job, status="failed", error_message="Video not found")
            return {"status": "failed", "reason": "video not found"}

        run_id = processing_run_id or _ensure_processing_run(job, db)

        _update_job(db, job, stage="frame_extraction", status="processing", progress_pct=40)
        _log(job_id, db, f"Starting frame extraction; run={run_id}")

        config = video_processing_config or {}
        max_frames = config.get("max_frames")
        sample_interval_seconds = config.get("sample_interval_seconds")

        extraction_config = FrameExtractionConfig(
            mission_id=mission_id,
            video_id=video_id,
            processing_run_id=run_id,
            video_path=video_storage_path,
            max_frames=max_frames,
            sample_interval_seconds=sample_interval_seconds,
        )

        extracted = extract_frames_for_video(extraction_config)
        _log(job_id, db, f"Extracted {len(extracted)} frames")

        frame_objs = []
        for ef in extracted:
            existing = (
                db.query(Frame)
                .filter(Frame.video_id == video_id, Frame.frame_index == ef.frame_index)
                .first()
            )
            if existing:
                frame_objs.append(existing)
                continue
            frame = Frame(
                id=ef.frame_id,
                mission_id=mission_id,
                video_id=video_id,
                frame_index=ef.frame_index,
                presentation_timestamp=ef.presentation_timestamp,
                timestamp_seconds=ef.timestamp_seconds,
                storage_path=ef.storage_path,
                width=ef.width,
                height=ef.height,
                processing_run_id=run_id,
                duplicate_status="unique",
                quality_status="unreviewed",
            )
            db.add(frame)
            frame_objs.append(frame)

        db.commit()
        # refresh to get ids
        for f in frame_objs:
            db.refresh(f)

        _update_job(db, job, stage="quality_analysis", status="queued", progress_pct=55)
        return {"status": "completed", "extracted_count": len(extracted), "run_id": run_id}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Frame extraction error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Quality analysis
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.analyze_quality")
def analyze_quality_task(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        run_id = processing_run_id or getattr(job, "processing_run_id", None)
        if not run_id:
            return {"status": "failed", "reason": "no processing_run_id"}

        frames = (
            db.query(Frame)
            .filter(Frame.video_id == video_id, Frame.processing_run_id == run_id)
            .order_by(Frame.frame_index)
            .all()
        )
        if not frames:
            _log(job_id, db, "No frames found for quality analysis", level="WARN")
            _update_job(db, job, stage="duplicate_detection", status="queued", progress_pct=70)
            return {"status": "completed", "analyzed_count": 0}

        _update_job(db, job, stage="quality_analysis", status="processing", progress_pct=60)
        _log(job_id, db, f"Analyzing quality for {len(frames)} frames")

        config = video_processing_config or {}
        qc_config = QualityConfig(
            blur_threshold=float(config.get("blur_threshold", QualityConfig().blur_threshold)),
            severe_blur_threshold=float(config.get("severe_blur_threshold", QualityConfig().severe_blur_threshold)),
            exposure_low=float(config.get("exposure_low", QualityConfig().exposure_low)),
            exposure_high=float(config.get("exposure_high", QualityConfig().exposure_high)),
            min_width=config.get("min_width"),
            min_height=config.get("min_height"),
            dhash_size=int(config.get("dhash_size", QualityConfig().dhash_size)),
            near_duplicate_hamming_max=int(config.get("near_duplicate_hamming_max", QualityConfig().near_duplicate_hamming_max)),
        )

        count = 0
        for frame in frames:
            if _check_cancelled(db, job):
                _log(job_id, db, "Cancelled during quality analysis")
                _update_job(db, job, status="cancelled")
                return {"status": "cancelled"}

            result = analyze_frame_quality(frame.id, frame.storage_path, config=qc_config)
            frame.blur_score = result.blur_score
            frame.exposure_score = result.mean_luminance
            frame.duplicate_hash = result.duplicate_hash
            frame.quality_status = result.classification
            frame.quality_details_json = json.dumps(quality_result_to_dict(result), default=str)
            db.commit()
            count += 1

            if count % 50 == 0:
                _log(job_id, db, f"Quality progress: {count}/{len(frames)}")

        _log(job_id, db, f"Quality analysis complete: {count} frames")
        _update_job(db, job, stage="duplicate_detection", status="queued", progress_pct=70)
        return {"status": "completed", "analyzed_count": count}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Quality analysis error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Duplicate detection
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.detect_duplicates")
def detect_duplicates_task(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        run_id = processing_run_id or getattr(job, "processing_run_id", None)
        if not run_id:
            return {"status": "failed", "reason": "no processing_run_id"}

        frames = (
            db.query(Frame)
            .filter(Frame.video_id == video_id, Frame.processing_run_id == run_id)
            .order_by(Frame.frame_index)
            .all()
        )
        if not frames:
            _log(job_id, db, "No frames found for duplicate detection", level="WARN")
            _update_job(db, job, stage="frame_selection", status="queued", progress_pct=80)
            return {"status": "completed", "duplicate_decisions_count": 0}

        _update_job(db, job, stage="duplicate_detection", status="processing", progress_pct=75)
        _log(job_id, db, f"Detecting duplicates among {len(frames)} frames")

        config = video_processing_config or {}
        from backend.app.services.duplicate_detector import DuplicateDetectorConfig
        dcfg = DuplicateDetectorConfig(
            quality_config=QualityConfig(
                blur_threshold=float(config.get("blur_threshold", QualityConfig().blur_threshold)),
                severe_blur_threshold=float(config.get("severe_blur_threshold", QualityConfig().severe_blur_threshold)),
                exposure_low=float(config.get("exposure_low", QualityConfig().exposure_low)),
                exposure_high=float(config.get("exposure_high", QualityConfig().exposure_high)),
                min_width=config.get("min_width"),
                min_height=config.get("min_height"),
                dhash_size=int(config.get("dhash_size", QualityConfig().dhash_size)),
                near_duplicate_hamming_max=int(config.get("near_duplicate_hamming_max", QualityConfig().near_duplicate_hamming_max)),
            ),
            temporal_window_frames=int(config.get("temporal_window_frames", 90)),
            prefer_keep_newer=bool(config.get("prefer_keep_newer", False)),
        )

        frame_dicts = [
            {
                "frame_id": f.id,
                "storage_path": f.storage_path,
                "frame_index": f.frame_index,
                "presentation_timestamp": f.presentation_timestamp,
            }
            for f in frames
        ]
        decisions = detect_duplicates_in_batch(frame_dicts, config=dcfg)

        for d in decisions:
            frame = db.query(Frame).filter(Frame.id == d.frame_id).first()
            if not frame:
                continue
            frame.duplicate_status = d.duplicate_status
            if d.duplicate_of_frame_id:
                frame.duplicate_of_frame_id = d.duplicate_of_frame_id
            frame.duplicate_distance = d.duplicate_distance
            frame.duplicate_reason = d.reason
            db.commit()

        dup_count = sum(1 for d in decisions if d.duplicate_status in ("exact_duplicate", "near_duplicate"))
        _log(job_id, db, f"Duplicate detection complete: {dup_count} duplicates")
        _update_job(db, job, stage="frame_selection", status="queued", progress_pct=85)
        return {"status": "completed", "duplicate_decisions_count": len(decisions), "duplicates": dup_count}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Duplicate detection error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Frame selection
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.select_frames")
def select_frames_task(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        run_id = processing_run_id or getattr(job, "processing_run_id", None)
        if not run_id:
            return {"status": "failed", "reason": "no processing_run_id"}

        frames = (
            db.query(Frame)
            .filter(Frame.video_id == video_id, Frame.processing_run_id == run_id)
            .order_by(Frame.frame_index)
            .all()
        )
        if not frames:
            _log(job_id, db, "No frames found for selection", level="WARN")
            _update_job(db, job, stage="gps_association", status="queued", progress_pct=90)
            return {"status": "completed", "selected_count": 0}

        _update_job(db, job, stage="frame_selection", status="processing", progress_pct=88)
        _log(job_id, db, f"Selecting frames from {len(frames)} candidates")

        config = video_processing_config or {}
        sc = SelectionConfig(
            min_temporal_spacing_seconds=float(config.get("min_temporal_spacing_seconds", SelectionConfig().min_temporal_spacing_seconds)),
            max_selected_frames=config.get("max_selected_frames"),
            min_sharpness=config.get("min_sharpness"),
            motion_proxy_enabled=bool(config.get("motion_proxy_enabled", SelectionConfig().motion_proxy_enabled)),
            scene_change_proxy_enabled=bool(config.get("scene_change_proxy_enabled", SelectionConfig().scene_change_proxy_enabled)),
            motion_threshold=float(config.get("motion_threshold", SelectionConfig().motion_threshold)),
            scene_change_threshold=float(config.get("scene_change_threshold", SelectionConfig().scene_change_threshold)),
        )

        candidates: List[FrameCandidate] = []
        for f in frames:
            candidates.append(
                FrameCandidate(
                    frame_id=f.id,
                    video_id=f.video_id,
                    mission_id=f.mission_id,
                    processing_run_id=f.processing_run_id or run_id,
                    frame_index=f.frame_index,
                    presentation_timestamp=f.presentation_timestamp,
                    timestamp_seconds=f.timestamp_seconds,
                    storage_path=f.storage_path,
                    blur_score=f.blur_score,
                    mean_luminance=f.exposure_score,
                    width=f.width,
                    height=f.height,
                    duplicate_status=f.duplicate_status,
                    duplicate_hash=f.duplicate_hash,
                    duplicate_of_frame_id=getattr(f, "duplicate_of_frame_id", None),
                )
            )

        selected = select_frames(candidates, config=sc)
        selected_ids = {s["frame_id"] for s in selected}

        for f in frames:
            if f.id in selected_ids:
                sel = next(s for s in selected if s["frame_id"] == f.id)
                f.is_selected = True
                f.selection_reason = sel["selection_reason"]
            else:
                f.is_selected = False
                if f.selection_reason is None:
                    f.selection_reason = None
            db.commit()

        _log(job_id, db, f"Frame selection complete: {len(selected)} selected")
        _update_job(db, job, stage="gps_association", status="queued", progress_pct=92)
        return {"status": "completed", "selected_count": len(selected)}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Frame selection error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# GPS association
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.associate_gps")
def associate_gps_task(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
    telemetry_csv_path: Optional[str] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        run_id = processing_run_id or getattr(job, "processing_run_id", None)
        if not run_id:
            return {"status": "failed", "reason": "no processing_run_id"}

        frames = (
            db.query(Frame)
            .filter(Frame.video_id == video_id, Frame.processing_run_id == run_id)
            .order_by(Frame.frame_index)
            .all()
        )
        if not frames:
            _log(job_id, db, "No frames found for GPS association", level="WARN")
            _update_job(db, job, status="completed", progress_pct=100)
            return {"status": "completed", "associated_count": 0}

        _update_job(db, job, stage="gps_association", status="processing", progress_pct=95)
        _log(job_id, db, "Associating GPS with frames")

        config = video_processing_config or {}
        telemetry_records: List[Any] = []

        # Use P1 FlightMetadata first.
        fms = db.query(FlightMetadata).filter(FlightMetadata.mission_id == mission_id).all()
        telemetry_records.extend(flight_metadata_to_gps_records(fms))

        # Also support an optional CSV telemetry file.
        if telemetry_csv_path and os.path.isfile(telemetry_csv_path):
            csv_records = parse_csv_telemetry(telemetry_csv_path)
            telemetry_records.extend(csv_records)

        if not telemetry_records:
            _log(job_id, db, "No telemetry available for GPS association", level="INFO")
        else:
            _log(job_id, db, f"Using {len(telemetry_records)} telemetry records")

        frame_dicts = [
            {
                "frame_id": f.id,
                "storage_path": f.storage_path,
                "frame_index": f.frame_index,
                "presentation_timestamp": f.presentation_timestamp,
                "timestamp_seconds": f.timestamp_seconds,
            }
            for f in frames
        ]
        associated = associate_gps_for_frames(frame_dicts, telemetry_records, config=GPSAssociationConfig(
            max_gap_seconds=float(config.get("gps_max_gap_seconds", GPSAssociationConfig().max_gap_seconds)),
            allow_interpolation=bool(config.get("gps_allow_interpolation", GPSAssociationConfig().allow_interpolation)),
            interpolation_max_gap_seconds=float(config.get("gps_interpolation_max_gap_seconds", GPSAssociationConfig().interpolation_max_gap_seconds)),
        ))

        associated_count = 0
        for rec in associated:
            frame = db.query(Frame).filter(Frame.id == rec["frame_id"]).first()
            if not frame:
                continue
            frame.gps_latitude = rec.get("gps_latitude")
            frame.gps_longitude = rec.get("gps_longitude")
            frame.altitude = rec.get("altitude")
            frame.altitude_datum = rec.get("altitude_datum")
            frame.gps_timestamp_seconds = rec.get("gps_timestamp_seconds")
            frame.gps_timestamp_str = rec.get("gps_timestamp_str")
            frame.gps_quality = rec.get("gps_quality")
            frame.gps_source = rec.get("gps_source")
            frame.gps_association_gap_seconds = rec.get("gps_association_gap_seconds")
            if rec.get("gps_source") not in (None, "none"):
                associated_count += 1
            db.commit()

        _log(job_id, db, f"GPS association complete: {associated_count} frames associated")
        _update_job(db, job, status="completed", progress_pct=100, error_message=None)
        return {"status": "completed", "associated_count": associated_count, "telemetry_records": len(telemetry_records)}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"GPS association error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Full pipeline wrapper
# ------------------------------------------------------------------


@celery_app.task(bind=True, name="jatayuv.run_full_processing_pipeline")
def run_full_processing_pipeline(
    self,
    job_id: str,
    video_id: str,
    mission_id: str,
    video_storage_path: str,
    processing_run_id: Optional[str] = None,
    video_processing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the full video processing pipeline in sequence.

    Each stage is executed as a separate sub-task call so retries are isolated,
    but this wrapper runs them synchronously within a single worker for simple
    cases. In production you may prefer to chain them as separate tasks.
    """
    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}

        run_id = processing_run_id or _ensure_processing_run(job, db)

        # Stage 1: validate
        validate_result = validate_video_task.delay(
            job_id=job_id,
            video_id=video_id,
            video_storage_path=video_storage_path,
            video_processing_config=video_processing_config,
        ).get(timeout=600)
        if validate_result.get("status") != "completed":
            _log(job_id, db, "Validation stage failed")
            return validate_result

        # Stage 2: metadata
        meta_result = extract_metadata_task.delay(
            job_id=job_id,
            video_id=video_id,
            video_storage_path=video_storage_path,
            video_processing_config=video_processing_config,
        ).get(timeout=600)
        if meta_result.get("status") != "completed":
            _log(job_id, db, "Metadata stage failed")
            return meta_result

        # Stage 3: extract frames
        extract_result = extract_frames_task.delay(
            job_id=job_id,
            video_id=video_id,
            mission_id=mission_id,
            video_storage_path=video_storage_path,
            processing_run_id=run_id,
            video_processing_config=video_processing_config,
        ).get(timeout=1800)
        if extract_result.get("status") != "completed":
            _log(job_id, db, "Frame extraction stage failed")
            return extract_result

        # Stage 4: quality
        quality_result = analyze_quality_task.delay(
            job_id=job_id,
            video_id=video_id,
            mission_id=mission_id,
            processing_run_id=run_id,
            video_processing_config=video_processing_config,
        ).get(timeout=1800)
        if quality_result.get("status") != "completed":
            _log(job_id, db, "Quality stage failed")
            return quality_result

        # Stage 5: duplicates
        dup_result = detect_duplicates_task.delay(
            job_id=job_id,
            video_id=video_id,
            mission_id=mission_id,
            processing_run_id=run_id,
            video_processing_config=video_processing_config,
        ).get(timeout=1800)
        if dup_result.get("status") != "completed":
            _log(job_id, db, "Duplicate detection stage failed")
            return dup_result

        # Stage 6: selection
        sel_result = select_frames_task.delay(
            job_id=job_id,
            video_id=video_id,
            mission_id=mission_id,
            processing_run_id=run_id,
            video_processing_config=video_processing_config,
        ).get(timeout=1800)
        if sel_result.get("status") != "completed":
            _log(job_id, db, "Selection stage failed")
            return sel_result

        # Stage 7: GPS association
        gps_result = associate_gps_task.delay(
            job_id=job_id,
            video_id=video_id,
            mission_id=mission_id,
            processing_run_id=run_id,
            video_processing_config=video_processing_config,
            telemetry_csv_path=video_processing_config.get("telemetry_csv_path") if video_processing_config else None,
        ).get(timeout=1200)
        if gps_result.get("status") != "completed":
            _log(job_id, db, "GPS association stage failed")
            return gps_result

        _log(job_id, db, "Full pipeline completed")
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        tb = traceback.format_exc()
        _log(job_id, db, f"Pipeline error: {exc}\n{tb}", level="ERROR")
        if job:
            _update_job(db, job, status="failed", error_message=str(exc))
        raise
    finally:
        db.close()


# ------------------------------------------------------------------
# Cancel
# ------------------------------------------------------------------


@celery_app.task(name="jatayuv.cancel_video_processing")
def cancel_video_processing_task(job_id: str) -> Dict[str, Any]:
    """Mark a video processing job as cancelled."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "failed", "reason": f"Job {job_id} not found"}
        if job.status in ("completed", "failed", "cancelled"):
            return {"status": "conflict", "reason": f"Job already terminal: {job.status}"}
        job = _update_job(db, job, status="cancelled", error_message="Cancelled by user")
        _log(job_id, db, "Video processing cancelled")
        return {"status": "cancelled", "job_id": job.id}
    finally:
        db.close()
