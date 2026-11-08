from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.mission import Mission
from backend.app.models.flight_metadata import FlightMetadata
from backend.app.models.video import Video
from backend.app.models.user import User
from backend.app.schemas.flight_metadata import (
    FlightMetadataCreate,
    FlightMetadataResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Flight Metadata"])


def _flight_to_response(fm: FlightMetadata) -> FlightMetadataResponse:
    return FlightMetadataResponse(
        id=fm.id,
        mission_id=fm.mission_id,
        video_id=fm.video_id,
        start_timestamp=fm.start_timestamp,
        end_timestamp=fm.end_timestamp,
        latitude=fm.latitude,
        longitude=fm.longitude,
        altitude=fm.altitude,
        altitude_datum=fm.altitude_datum,
        coordinate_reference_system=fm.coordinate_reference_system,
        horizontal_accuracy=fm.horizontal_accuracy,
        vertical_accuracy=fm.vertical_accuracy,
        camera_make=fm.camera_make,
        camera_model=fm.camera_model,
        focal_length=fm.focal_length,
        sensor_width=fm.sensor_width,
        sensor_height=fm.sensor_height,
        image_width=fm.image_width,
        image_height=fm.image_height,
        camera_intrinsics_json=fm.camera_intrinsics_json,
        imu_data_path=fm.imu_data_path,
        barometric_altitude=fm.barometric_altitude,
        rtk_enabled=bool(fm.rtk_enabled) if fm.rtk_enabled is not None else None,
        ppk_enabled=bool(fm.ppk_enabled) if fm.ppk_enabled is not None else None,
        metadata_source=fm.metadata_source,
        created_at=fm.created_at,
    )


@router.post(
    "/missions/{mission_id}/flight-metadata",
    response_model=FlightMetadataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flight_metadata(
    mission_id: str,
    fm_in: FlightMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to add flight metadata to this mission",
        )

    if fm_in.video_id:
        video = (
            db.query(Video)
            .filter(Video.id == fm_in.video_id, Video.mission_id == mission_id)
            .first()
        )
        if not video:
            raise HTTPException(
                status_code=400, detail="Video not found in this mission"
            )

    fm = FlightMetadata(
        mission_id=mission_id,
        video_id=fm_in.video_id,
        start_timestamp=fm_in.start_timestamp,
        end_timestamp=fm_in.end_timestamp,
        latitude=fm_in.latitude,
        longitude=fm_in.longitude,
        altitude=fm_in.altitude,
        altitude_datum=fm_in.altitude_datum,
        coordinate_reference_system=fm_in.coordinate_reference_system,
        horizontal_accuracy=fm_in.horizontal_accuracy,
        vertical_accuracy=fm_in.vertical_accuracy,
        camera_make=fm_in.camera_make,
        camera_model=fm_in.camera_model,
        focal_length=fm_in.focal_length,
        sensor_width=fm_in.sensor_width,
        sensor_height=fm_in.sensor_height,
        image_width=fm_in.image_width,
        image_height=fm_in.image_height,
        camera_intrinsics_json=fm_in.camera_intrinsics_json,
        imu_data_path=fm_in.imu_data_path,
        barometric_altitude=fm_in.barometric_altitude,
        rtk_enabled=1 if fm_in.rtk_enabled else 0,
        ppk_enabled=1 if fm_in.ppk_enabled else 0,
        metadata_source=fm_in.metadata_source,
    )
    db.add(fm)
    db.commit()
    db.refresh(fm)
    return _flight_to_response(fm)


@router.get(
    "/missions/{mission_id}/flight-metadata",
    response_model=List[FlightMetadataResponse],
)
def list_flight_metadata(
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
            detail="Not authorised to list flight metadata for this mission",
        )
    records = (
        db.query(FlightMetadata)
        .filter(FlightMetadata.mission_id == mission_id)
        .order_by(FlightMetadata.created_at.desc())
        .all()
    )
    return [_flight_to_response(r) for r in records]


@router.patch(
    "/missions/{mission_id}/flight-metadata",
    response_model=List[FlightMetadataResponse],
)
def update_flight_metadata(
    mission_id: str,
    fm_in: FlightMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upsert-style patch: update the single mission flight metadata record or create one."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role != "admin" and mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to update flight metadata for this mission",
        )
    record = (
        db.query(FlightMetadata)
        .filter(FlightMetadata.mission_id == mission_id)
        .first()
    )
    update_kwargs: dict = {}
    for field in (
        "video_id",
        "start_timestamp",
        "end_timestamp",
        "latitude",
        "longitude",
        "altitude",
        "altitude_datum",
        "coordinate_reference_system",
        "horizontal_accuracy",
        "vertical_accuracy",
        "camera_make",
        "camera_model",
        "focal_length",
        "sensor_width",
        "sensor_height",
        "image_width",
        "image_height",
        "camera_intrinsics_json",
        "imu_data_path",
        "barometric_altitude",
        "metadata_source",
    ):
        value = getattr(fm_in, field, None)
        if value is not None:
            update_kwargs[field] = value
    if fm_in.rtk_enabled is not None:
        update_kwargs["rtk_enabled"] = 1 if fm_in.rtk_enabled else 0
    if fm_in.ppk_enabled is not None:
        update_kwargs["ppk_enabled"] = 1 if fm_in.ppk_enabled else 0

    if record:
        for key, value in update_kwargs.items():
            setattr(record, key, value)
    else:
        record = FlightMetadata(mission_id=mission_id, **update_kwargs)
        db.add(record)
    db.commit()
    db.refresh(record)
    return [_flight_to_response(record)]
