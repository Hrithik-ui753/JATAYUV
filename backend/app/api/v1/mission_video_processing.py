from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.user import User
from backend.app.schemas.processing import (
    EnqueueProcessingResponse,
    ProcessingReportResponse,
    VideoMetadataResponse,
    VideoProcessingConfig,
    VideoProcessingStatusResponse,
)
from backend.app.schemas.frame import FrameResponse
from backend.app.schemas.video import VideoResponse
from backend.app.api.deps import get_current_user
from backend.app.services.mission_processing import (
    enqueue_full_processing,
    get_processing_report_for_mission,
    get_processing_status_for_mission,
)
from backend.app.services.video_probe import build_video_report

router = APIRouter(tags=["Mission Video Processing"])


def _require_mission_authority(
    mission_id: str,
    db: Session,
    current_user: User,
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to access this mission",
        )
    return mission


@router.post(
    "/missions/{mission_id}/videos/{video_id}/process",
    response_model=EnqueueProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_video_processing(
    mission_id: str,
    video_id: str,
    config: VideoProcessingConfig = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_mission_authority(mission_id, db, current_user)

    from backend.app.models.video import Video

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.mission_id != mission_id:
        raise HTTPException(status_code=400, detail="Video does not belong to this mission")

    result = enqueue_full_processing(
        mission_id=mission_id,
        video_id=video_id,
        user_id=current_user.id,
        video_processing_config=config.model_dump(exclude_none=True) if config else None,
    )
    return result


@router.get(
    "/missions/{mission_id}/processing-status",
    response_model=VideoProcessingStatusResponse,
)
def processing_status(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_mission_authority(mission_id, db, current_user)
    status_data = get_processing_status_for_mission(
        mission_id,
        db,
        current_user.id,
        current_user.role,
    )
    if "error" in status_data:
        raise HTTPException(status_code=403, detail=status_data["error"])
    return status_data


@router.get(
    "/missions/{mission_id}/processing-report",
    response_model=ProcessingReportResponse,
)
def processing_report(
    mission_id: str,
    processing_run_id: str = Query(None, alias="processing_run_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_mission_authority(mission_id, db, current_user)
    report = get_processing_report_for_mission(
        mission_id,
        db,
        current_user.id,
        current_user.role,
        processing_run_id=processing_run_id,
    )
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@router.get(
    "/missions/{mission_id}/frames/selected",
    response_model=List[FrameResponse],
)
def selected_frames(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    processing_run_id: str = Query(None, alias="processing_run_id"),
):
    _require_mission_authority(mission_id, db, current_user)

    from backend.app.models.frame import Frame

    query = db.query(Frame).filter(Frame.mission_id == mission_id, Frame.is_selected == True)  # noqa: E712
    if processing_run_id:
        query = query.filter(Frame.processing_run_id == processing_run_id)
    frames = query.order_by(Frame.frame_index.asc()).all()
    return [FrameResponse.model_validate(f) for f in frames]


@router.get(
    "/missions/{mission_id}/frames",
    response_model=List[FrameResponse],
)
def list_frames(
    mission_id: str,
    quality_status: str = Query(None, alias="quality_status"),
    duplicate_status: str = Query(None, alias="duplicate_status"),
    is_selected: bool = Query(None, alias="is_selected"),
    has_gps: bool = Query(None, alias="has_gps"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    processing_run_id: str = Query(None, alias="processing_run_id"),
):
    _require_mission_authority(mission_id, db, current_user)

    from backend.app.models.frame import Frame

    query = db.query(Frame).filter(Frame.mission_id == mission_id)
    if quality_status:
        query = query.filter(Frame.quality_status == quality_status)
    if duplicate_status:
        query = query.filter(Frame.duplicate_status == duplicate_status)
    if is_selected is not None:
        query = query.filter(Frame.is_selected == is_selected)
    if has_gps is not None:
        if has_gps:
            query = query.filter(Frame.gps_source.not_() == "none")
        else:
            query = query.filter(Frame.gps_source == "none")
    if processing_run_id:
        query = query.filter(Frame.processing_run_id == processing_run_id)
    frames = query.order_by(Frame.frame_index.asc()).all()
    return [FrameResponse.model_validate(f) for f in frames]


@router.get(
    "/videos/{video_id}/metadata",
    response_model=VideoMetadataResponse,
)
def video_metadata(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.models.video import Video
    from backend.app.models.mission import Mission

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    mission = db.query(Mission).filter(Mission.id == video.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Video mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to view this video",
        )

    report = build_video_report(video.storage_path)
    metadata = report.get("metadata", {})
    return VideoMetadataResponse(
        container_format=metadata.get("container_format"),
        duration_seconds=metadata.get("duration_seconds"),
        width=metadata.get("width"),
        height=metadata.get("height"),
        nominal_fps=metadata.get("nominal_fps"),
        avg_fps=metadata.get("avg_fps"),
        codec_name=metadata.get("codec_name"),
        codec_long_name=metadata.get("codec_long_name"),
        pixel_format=metadata.get("pixel_format"),
        stream_time_base=metadata.get("stream_time_base"),
        nb_frames=metadata.get("nb_frames"),
        probe_duration_method=metadata.get("probe_duration_method"),
        truncated_probe=metadata.get("truncated_probe"),
    )


@router.post(
    "/videos/{video_id}/validate",
    response_model=VideoMetadataResponse,
)
def validate_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.models.video import Video
    from backend.app.models.mission import Mission

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    mission = db.query(Mission).filter(Mission.id == video.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Video mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to validate this video",
        )

    report = build_video_report(video.storage_path)
    if not report.get("valid"):
        raise HTTPException(status_code=400, detail=report.get("violations", ["validation failed"]))

    metadata = report.get("metadata", {})
    return VideoMetadataResponse(
        container_format=metadata.get("container_format"),
        duration_seconds=metadata.get("duration_seconds"),
        width=metadata.get("width"),
        height=metadata.get("height"),
        nominal_fps=metadata.get("nominal_fps"),
        avg_fps=metadata.get("avg_fps"),
        codec_name=metadata.get("codec_name"),
        codec_long_name=metadata.get("codec_long_name"),
        pixel_format=metadata.get("pixel_format"),
        stream_time_base=metadata.get("stream_time_base"),
        nb_frames=metadata.get("nb_frames"),
        probe_duration_method=metadata.get("probe_duration_method"),
        truncated_probe=metadata.get("truncated_probe"),
    )
