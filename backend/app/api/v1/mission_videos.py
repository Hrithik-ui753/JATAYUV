<<<<<<< HEAD
import hashlib
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
=======
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
>>>>>>> origin/main
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.mission import Mission
from backend.app.models.video import Video
from backend.app.models.user import User
<<<<<<< HEAD
from backend.app.models.flight_metadata import FlightMetadata
=======
>>>>>>> origin/main
from backend.app.schemas.video import VideoCreate, VideoUploadResponse, VideoResponse
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(tags=["Mission Videos"])

<<<<<<< HEAD
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}

=======
>>>>>>> origin/main

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
<<<<<<< HEAD
    "/missions/{mission_id}/videos/upload",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_mission_video(
    mission_id: str,
    file: UploadFile = File(...),
    telemetry_file: Optional[UploadFile] = File(None),
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

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video extension '{ext}'. Supported: {sorted(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    upload_dir = os.path.join(settings.STORAGE_DIR, "uploads", "videos")
    os.makedirs(upload_dir, exist_ok=True)
    video_id = str(uuid.uuid4())
    safe_name = f"{video_id}_{file.filename}"
    saved_path = os.path.join(upload_dir, safe_name)

    hasher = hashlib.sha256()
    file_size = 0
    try:
        with open(saved_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Video exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024**2):.0f} MB.",
                    )
                hasher.update(chunk)
                f_out.write(chunk)
    except Exception:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise

    checksum = hasher.hexdigest()

    width = None
    height = None
    duration_seconds = None
    frame_rate = None
    codec = None
    validation_status = "valid"

    try:
        from backend.app.services.video_probe import probe_video
        meta = probe_video(saved_path)
        width = meta.width
        height = meta.height
        duration_seconds = int(meta.duration_seconds) if meta.duration_seconds is not None else None
        frame_rate = int(round(meta.nominal_fps or meta.avg_fps or 0)) or None
        codec = meta.codec_name
    except Exception:
        pass

    video = Video(
        id=video_id,
        mission_id=mission_id,
        original_filename=file.filename or f"drone_video{ext}",
        storage_path=saved_path,
        file_size_bytes=file_size,
        mime_type=file.content_type or f"video/{ext.lstrip('.')}",
        duration_seconds=duration_seconds,
        width=width,
        height=height,
        frame_rate=frame_rate,
        codec=codec,
        checksum_sha256=checksum,
        upload_status="uploaded",
        validation_status=validation_status,
    )
    db.add(video)
    mission.status = "uploaded"
    db.commit()
    db.refresh(video)

    if telemetry_file and telemetry_file.filename:
        t_ext = os.path.splitext(telemetry_file.filename)[1].lower()
        t_path = os.path.join(upload_dir, f"{video_id}_telemetry{t_ext}")
        with open(t_path, "wb") as t_out:
            while t_chunk := await telemetry_file.read(512 * 1024):
                t_out.write(t_chunk)
        f_meta = FlightMetadata(
            video_id=video.id,
            source_file_path=t_path,
            has_telemetry=True,
            metadata_source="uploaded_file",
        )
        db.add(f_meta)
        db.commit()

    return _video_to_response(video)


@router.post(
    "/projects/{project_id}/videos/upload",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_video(
    project_id: str,
    file: UploadFile = File(...),
    telemetry_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(project_id, db, current_user)
    mission = db.query(Mission).filter(Mission.project_id == project_id).first()
    if not mission:
        mission = Mission(
            user_id=current_user.id,
            project_id=project_id,
            mission_name=f"{project.name} - Single-Pass Flight",
            description="Auto-created mission for single-pass drone video",
            location_name=project.location_name,
            status="created",
        )
        db.add(mission)
        db.commit()
        db.refresh(mission)
    return await upload_mission_video(
        mission_id=mission.id,
        file=file,
        telemetry_file=telemetry_file,
        db=db,
        current_user=current_user,
    )


@router.post(
=======
>>>>>>> origin/main
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
