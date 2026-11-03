import os
import uuid
import json
import mimetypes
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.image import Image
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.image import ImageResponse, ExifTelemetry
from backend.app.services.preprocessor import ImagePreprocessor
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(tags=["Imagery & Ingestion"])

# Valid extensions and corresponding MIME types for aerial imagery
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dng", ".webp"}
ALLOWED_MIME_TYPES = set(settings.ALLOWED_IMAGE_MIME_TYPES) | {"image/tiff", "image/x-tiff", "image/dng"}


def _build_image_response(img: Image) -> ImageResponse:
    telem = None
    if img.telemetry_json:
        try:
            telem = ExifTelemetry(**json.loads(img.telemetry_json))
        except Exception:
            pass
    return ImageResponse(
        id=img.id,
        project_id=img.project_id,
        filename=img.filename,
        file_path=img.file_path,
        thumbnail_path=img.thumbnail_path,
        file_size_bytes=img.file_size_bytes,
        width=img.width,
        height=img.height,
        format=img.format,
        is_preprocessed=img.is_preprocessed,
        preprocessed_path=img.preprocessed_path,
        telemetry=telem,
        created_at=img.created_at,
    )


@router.get("/projects/{project_id}/images", response_model=List[ImageResponse])
def get_project_images(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_project_owner(project_id, db, current_user)
    images = db.query(Image).filter(Image.project_id == project_id).all()
    return [_build_image_response(img) for img in images]


@router.get("/projects/{project_id}/images/{image_id}", response_model=ImageResponse)
def get_single_image(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_project_owner(project_id, db, current_user)
    image = db.query(Image).filter(Image.id == image_id, Image.project_id == project_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return _build_image_response(image)


@router.post(
    "/projects/{project_id}/images/upload",
    response_model=List[ImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_images(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_project_owner(project_id, db, current_user)
    results = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""

        # Extension validation
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File '{file.filename}': unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # Read content to validate size
        content = await file.read()
        file_size = len(content)

        # File-size validation (500 MB cap)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File '{file.filename}' is {file_size / (1024**2):.1f} MB. "
                    f"Maximum allowed size is {settings.MAX_UPLOAD_SIZE_BYTES / (1024**2):.0f} MB."
                ),
            )

        # MIME type validation via content sniffing (best-effort)
        guessed_mime, _ = mimetypes.guess_type(file.filename or "")
        content_mime = file.content_type or ""
        effective_mime = content_mime if content_mime else (guessed_mime or "")
        # We only hard-reject if the server provides a MIME type and it is clearly wrong
        if effective_mime and not any(effective_mime.startswith(m.split("/")[0]) for m in ["image/"]):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File '{file.filename}': content type '{effective_mime}' is not an image.",
            )

        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}_{file.filename}"
        saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        thumb_path = os.path.join(settings.PROCESSED_DIR, f"thumb_{saved_filename}")

        # Persist file
        with open(saved_path, "wb") as f:
            f.write(content)

        # Extract EXIF telemetry & thumbnail
        telemetry = ImagePreprocessor.extract_exif_telemetry(saved_path)
        try:
            ImagePreprocessor.create_thumbnail(saved_path, thumb_path)
        except Exception:
            thumb_path = saved_path

        # Read pixel dimensions
        from PIL import Image as PILImage
        try:
            with PILImage.open(saved_path) as pimg:
                width, height = pimg.size
                img_format = pimg.format or "JPEG"
        except Exception:
            width, height = 0, 0
            img_format = ext.lstrip(".").upper() or "UNKNOWN"

        image_record = Image(
            id=file_id,
            project_id=project_id,
            filename=file.filename,
            file_path=saved_path,
            thumbnail_path=thumb_path,
            file_size_bytes=file_size,
            width=width,
            height=height,
            format=img_format,
            is_preprocessed=False,
            telemetry_json=json.dumps(telemetry),
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)

        results.append(_build_image_response(image_record))

    return results


@router.delete(
    "/projects/{project_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_image(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an uploaded image and its on-disk files. This does not delete analysis results."""
    check_project_owner(project_id, db, current_user)
    image = db.query(Image).filter(Image.id == image_id, Image.project_id == project_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Remove on-disk files (best effort — don't fail if already gone)
    for path in [image.file_path, image.thumbnail_path, image.preprocessed_path]:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.delete(image)
    db.commit()
    return None


@router.post("/images/{image_id}/preprocess", response_model=ImageResponse)
def preprocess_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    check_project_owner(image.project_id, db, current_user)

    processed_path = os.path.join(settings.PROCESSED_DIR, f"prep_{image.filename}")
    ImagePreprocessor.preprocess_aerial_image(image.file_path, processed_path)

    image.is_preprocessed = True
    image.preprocessed_path = processed_path
    db.commit()
    db.refresh(image)

    return _build_image_response(image)
