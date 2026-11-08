from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.mission import Mission
from backend.app.models.video import Video
from backend.app.models.user import User
from backend.app.schemas.video import VideoCreate, VideoUploadResponse, VideoResponse
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(tags=["Mission Videos"])


def _video_to_response(video: Video) -> VideoResponse:
    return VideoResponse(
        id=video.id,
        mission_id=video.mission_id,
        original_filename=video.original_filename,
        storage_path=video.storage_path,
        file_size_bytes=video.file_size_bytes,
        mime_type=video.mime_type,
        duration_seconds=video.duration_seconds,
        width=video.width,
        height=video.height,
        frame_rate=video.frame_rate,
        codec=video.codec,
        checksum_sha256=video.checksum_sha256,
        upload_status=video.upload_status,
        validation_status=video.validation_status,
        created_at=video.created_at,
    )


@router.post(
    "/missions/{mission_id}/videos",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_video(
    mission_id: str,
    video_in: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to add videos to this mission",
        )

    video = Video(
        mission_id=mission_id,
        original_filename=video_in.original_filename,
        storage_path=video_in.storage_path,
        file_size_bytes=video_in.file_size_bytes,
        mime_type=video_in.mime_type,
        duration_seconds=video_in.duration_seconds,
        width=video_in.width,
        height=video_in.height,
        frame_rate=video_in.frame_rate,
        codec=video_in.codec,
        checksum_sha256=video_in.checksum_sha256,
        upload_status="uploaded",
        validation_status="pending",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return VideoUploadResponse(
        id=video.id,
        mission_id=video.mission_id,
        original_filename=video.original_filename,
        file_size_bytes=video.file_size_bytes,
        mime_type=video.mime_type,
        upload_status=video.upload_status,
        validation_status=video.validation_status,
        created_at=video.created_at,
    )


@router.get("/missions/{mission_id}/videos", response_model=List[VideoResponse])
def list_mission_videos(
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
            detail="Not authorised to list videos for this mission",
        )
    videos = (
        db.query(Video)
        .filter(Video.mission_id == mission_id)
        .order_by(Video.created_at.desc())
        .all()
    )
    return [_video_to_response(v) for v in videos]


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    mission = db.query(Mission).filter(Mission.id == video.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Video mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to view this video",
        )
    return _video_to_response(video)
