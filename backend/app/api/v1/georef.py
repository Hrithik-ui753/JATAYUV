from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from backend.app.api.deps import CurrentUser, get_current_active_user
from backend.app.models.mission import Mission
from backend.app.models.georef_solution import GeorefSolution
from backend.app.models.validation_report import ValidationReport
from backend.app.models.reconstruction import Reconstruction
from backend.app.services.georef.service import (
    create_georef_solution,
    estimate_scale_from_control_points,
    transform_camera_pose,
    georeference_reconstruction,
    validate_spatial_accuracy,
)
from backend.app.core.database import db

router = APIRouter(prefix="/api/v1/missions")


def _get_mission_or_404(mission_id: str):
    mission = Mission.query.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


def _get_reconstruction_or_404(reconstruction_id: str):
    rec = Reconstruction.query.get(reconstruction_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Reconstruction not found")
    return rec


class GeorefStartRequest(BaseModel):
    reconstruction_id: str
    target_crs: Optional[str] = None
    vertical_datum: Optional[str] = None


class ControlPointRequest(BaseModel):
    label: Optional[str] = None
    category: Optional[str] = None
    role: str
    local_x: Optional[float] = None
    local_y: Optional[float] = None
    local_z: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    elevation: Optional[float] = None
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_z: Optional[float] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    measurement_source: Optional[str] = None
    measurement_method: Optional[str] = None


class GeorefSolveRequest(BaseModel):
    reconstruction_id: str
    method: str = "similarity_transform"
    use_gps: bool = False
    use_rtk: bool = False


@router.post(
    "/{mission_id}/georeferencing/start",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}, 409: {"model": None}},
    tags=["georeferencing"],
)
def georef_start(
    mission_id: str = Path(...),
    payload: GeorefStartRequest = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    reconstruction = _get_reconstruction_or_404(payload.reconstruction_id)
    if reconstruction.mission_id != mission_id:
        raise HTTPException(status_code=404, detail="Reconstruction not found for this mission")

    solution = create_georef_solution(
        mission_id=mission_id,
        reconstruction_id=payload.reconstruction_id,
        coordinate_reference_system=payload.target_crs,
        vertical_datum=payload.vertical_datum,
        solution_method="manual_start",
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    return {
        "georef_solution_id": solution.id,
        "mission_id": mission_id,
        "reconstruction_id": payload.reconstruction_id,
        "status": "started",
        "created_at": solution.created_at,
    }


@router.get(
    "/{mission_id}/georeferencing/status",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def georef_status(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    solutions = GeorefSolution.query(
        mission_id=mission_id, order_by="created_at", desc=True
    ).all()
    if not solutions:
        raise HTTPException(status_code=404, detail="No georeferencing solution found")
    latest = solutions[0]
    return {
        "georef_solution_id": latest.id,
        "mission_id": mission_id,
        "reconstruction_id": latest.reconstruction_id,
        "coordinate_reference_system": latest.coordinate_reference_system,
        "horizontal_datum": latest.horizontal_datum,
        "vertical_datum": latest.vertical_datum,
        "scale_factor": latest.scale_factor,
        "solution_method": latest.solution_method,
        "confidence": latest.confidence,
        "created_at": latest.created_at,
    }


@router.post(
    "/{mission_id}/control-points",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def add_control_point(
    mission_id: str = Path(...),
    payload: ControlPointRequest = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if payload.role not in ("CONTROL", "CHECKPOINT", "REFERENCE_DISTANCE"):
        raise HTTPException(status_code=400, detail="Invalid control point role")

    from backend.app.models.ground_control_point import GroundControlPoint

    gcp = GroundControlPoint(
        mission_id=mission_id,
        label=payload.label,
        category=payload.category,
        role=payload.role,
        local_x=payload.local_x,
        local_y=payload.local_y,
        local_z=payload.local_z,
        lat=payload.lat,
        lon=payload.lon,
        elevation=payload.elevation,
        target_x=payload.target_x,
        target_y=payload.target_y,
        target_z=payload.target_z,
        horizontal_accuracy=payload.horizontal_accuracy,
        vertical_accuracy=payload.vertical_accuracy,
        measurement_source=payload.measurement_source,
        measurement_method=payload.measurement_method,
        observed_at=datetime.now(timezone.utc),
    )
    db.add(gcp)
    db.commit()
    db.refresh(gcp)
    return {"control_point_id": gcp.id, "role": gcp.role, "created_at": gcp.created_at}


@router.get(
    "/{mission_id}/control-points",
    response_model=List[Dict[str, Any]],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def list_control_points(
    mission_id: str = Path(...),
    role: Optional[str] = Query(None, regex="^(CONTROL|CHECKPOINT|REFERENCE_DISTANCE)$"),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from backend.app.models.ground_control_point import GroundControlPoint

    query = GroundControlPoint.query(mission_id=mission_id)
    if role:
        query = query.filter_by(role=role)
    points = query.all()
    return [
        {
            "control_point_id": p.id,
            "label": p.label,
            "category": p.category,
            "role": p.role,
            "local_x": p.local_x,
            "local_y": p.local_y,
            "local_z": p.local_z,
            "lat": p.lat,
            "lon": p.lon,
            "elevation": p.elevation,
            "target_x": p.target_x,
            "target_y": p.target_y,
            "target_z": p.target_z,
            "horizontal_accuracy": p.horizontal_accuracy,
            "vertical_accuracy": p.vertical_accuracy,
            "measurement_source": p.measurement_source,
            "measurement_method": p.measurement_method,
            "created_at": p.created_at,
        }
        for p in points
    ]


@router.patch(
    "/control-points/{control_point_id}",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def update_control_point(
    control_point_id: str = Path(...),
    payload: ControlPointRequest = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    from backend.app.models.ground_control_point import GroundControlPoint

    gcp = GroundControlPoint.query.get(control_point_id)
    if gcp is None:
        raise HTTPException(status_code=404, detail="Control point not found")
    if gcp.mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field in (
        "label",
        "category",
        "role",
        "local_x",
        "local_y",
        "local_z",
        "lat",
        "lon",
        "elevation",
        "target_x",
        "target_y",
        "target_z",
        "horizontal_accuracy",
        "vertical_accuracy",
        "measurement_source",
        "measurement_method",
    ):
        val = getattr(payload, field, None)
        if val is not None:
            setattr(gcp, field, val)

    gcp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(gcp)
    return {"control_point_id": gcp.id, "updated_at": gcp.updated_at}


@router.delete(
    "/control-points/{control_point_id}",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def delete_control_point(
    control_point_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    from backend.app.models.ground_control_point import GroundControlPoint

    gcp = GroundControlPoint.query.get(control_point_id)
    if gcp is None:
        raise HTTPException(status_code=404, detail="Control point not found")
    if gcp.mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(gcp)
    db.commit()
    return {"control_point_id": control_point_id, "deleted": True}


@router.post(
    "/{mission_id}/georeferencing/solve",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}, 409: {"model": None}},
    tags=["georeferencing"],
)
def georef_solve(
    mission_id: str = Path(...),
    payload: GeorefSolveRequest = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    reconstruction = _get_reconstruction_or_404(payload.reconstruction_id)
    if reconstruction.mission_id != mission_id:
        raise HTTPException(status_code=404, detail="Reconstruction not found for this mission")

    from backend.app.models.ground_control_point import GroundControlPoint

    control_points = GroundControlPoint.query(
        mission_id=mission_id, role="CONTROL"
    ).all()
    if not control_points:
        raise HTTPException(status_code=409, detail="No control points available to solve")

    local_arr = []
    target_arr = []
    for p in control_points:
        if p.local_x is not None and p.local_y is not None and p.local_z is not None:
            local_arr.append([p.local_x, p.local_y, p.local_z])
        if p.target_x is not None and p.target_y is not None and p.target_z is not None:
            target_arr.append([p.target_x, p.target_y, p.target_z])

    scale_info: Dict[str, Any] = {}
    if local_arr and target_arr:
        import numpy as np

        local_np = np.array(local_arr, dtype=np.float64)
        target_np = np.array(target_arr, dtype=np.float64)
        scale_info = estimate_scale_from_control_points(local_np, target_np)

    solution = create_georef_solution(
        mission_id=mission_id,
        reconstruction_id=payload.reconstruction_id,
        coordinate_reference_system=reconstruction.coordinate_reference_system,
        horizontal_datum=(
            mission.flight_metadata.horizontal_datum
            if mission.flight_metadata
            else None
        ),
        vertical_datum=(
            mission.flight_metadata.vertical_datum
            if mission.flight_metadata
            else None
        ),
        scale_factor=scale_info.get("scale"),
        translation=scale_info.get("translation"),
        rotation_matrix=scale_info.get("rotation"),
        control_point_count=len(control_points),
        solution_method=payload.method,
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    return {
        "georef_solution_id": solution.id,
        "mission_id": mission_id,
        "reconstruction_id": payload.reconstruction_id,
        "method": payload.method,
        "scale_factor": solution.scale_factor,
        "control_point_count": len(control_points),
        "residuals": scale_info.get("residuals"),
        "status": "solved",
    }


@router.get(
    "/{mission_id}/georeferencing/validation",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def georef_validation(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from backend.app.models.checkpoint_observation import CheckpointObservation

    observations = CheckpointObservation.query(mission_id=mission_id).all()
    report = validate_spatial_accuracy(
        [
            {
                "horizontal_error": o.horizontal_error,
                "vertical_error": o.vertical_error,
                "horizontal_distance_error": o.horizontal_distance_error,
                "three_d_error": o.three_d_error,
            }
            for o in observations
        ],
        vertical_datum_compatible=(
            mission.flight_metadata.vertical_datum == "orthometric"
            if mission.flight_metadata
            else True
        ),
    )
    report.mission_id = mission_id
    report.reconstruction_id = (
        report.reconstruction_id or ""
    )
    db.add(report)
    db.commit()

    return {
        "validation_report_id": report.id,
        "mission_id": mission_id,
        "validation_status": report.validation_status,
        "metrics": json.loads(report.metrics_json or "{}"),
        "uncertainty": json.loads(report.uncertainty_json or "{}"),
        "checkpoint_count": report.control_point_count,
    }


@router.get(
    "/{mission_id}/georeferencing/report",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def georef_report(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    solutions = GeorefSolution.query(
        mission_id=mission_id, order_by="created_at", desc=True
    ).all()
    if not solutions:
        raise HTTPException(status_code=404, detail="No georeferencing solution found")

    latest = solutions[0]
    report = ValidationReport.query(
        reconstruction_id=latest.reconstruction_id
    ).order_by("generated_at", desc=True).first()

    return {
        "georef_solution_id": latest.id,
        "mission_id": mission_id,
        "reconstruction_id": latest.reconstruction_id,
        "coordinate_reference_system": latest.coordinate_reference_system,
        "horizontal_datum": latest.horizontal_datum,
        "vertical_datum": latest.vertical_datum,
        "scale_factor": latest.scale_factor,
        "scale_uncertainty": latest.scale_uncertainty,
        "horizontal_residual": latest.horizontal_residual,
        "vertical_residual": latest.vertical_residual,
        "control_point_count": latest.control_point_count,
        "solution_method": latest.solution_method,
        "confidence": latest.confidence,
        "validation_status": report.validation_status if report else None,
        "validation_metrics": json.loads(report.metrics_json) if report else None,
        "created_at": latest.created_at,
    }


@router.post(
    "/{mission_id}/georeferencing/cancel",
    response_model=Dict[str, Any],
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
    tags=["georeferencing"],
)
def georef_cancel(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    mission = _get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    solutions = GeorefSolution.query(
        mission_id=mission_id, order_by="created_at", desc=True
    ).all()
    if not solutions:
        raise HTTPException(status_code=404, detail="No georeferencing solution found")

    latest = solutions[0]
    return {
        "georef_solution_id": latest.id,
        "mission_id": mission_id,
        "cancelled": True,
        "status": latest.solution_method,
    }
