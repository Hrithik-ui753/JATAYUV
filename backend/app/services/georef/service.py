from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np

from backend.app.services.georef.crs import (
    wgs84_crs,
    utm_zone_from_lat_lon,
    create_transformer,
    transform_point,
)
from backend.app.services.georef.similarity import (
    compute_similarity_transform,
    compute_weighted_similarity_transform,
)

from backend.app.models.georef_solution import GeorefSolution
from backend.app.models.validation_report import ValidationReport
from backend.app.models.camera_pose import CameraPose
from backend.app.models.reconstruction import Reconstruction


def create_georef_solution(
    mission_id: str,
    reconstruction_id: str,
    *,
    coordinate_reference_system: Optional[str] = None,
    horizontal_datum: Optional[str] = None,
    vertical_datum: Optional[str] = None,
    scale_factor: Optional[float] = None,
    translation: Optional[List[float]] = None,
    rotation_matrix: Optional[List[List[float]]] = None,
    scale_uncertainty: Optional[float] = None,
    horizontal_residual: Optional[float] = None,
    vertical_residual: Optional[float] = None,
    control_point_count: Optional[int] = None,
    solution_method: Optional[str] = None,
    confidence: Optional[float] = None,
) -> GeorefSolution:
    solution = GeorefSolution(
        mission_id=mission_id,
        reconstruction_id=reconstruction_id,
        coordinate_reference_system=coordinate_reference_system,
        horizontal_datum=horizontal_datum,
        vertical_datum=vertical_datum,
        scale_factor=scale_factor,
        translation_json=(
            json.dumps(translation) if translation else None
        ),
        rotation_json=(
            json.dumps(rotation_matrix) if rotation_matrix else None
        ),
        scale_uncertainty=scale_uncertainty,
        horizontal_residual=horizontal_residual,
        vertical_residual=vertical_residual,
        control_point_count=control_point_count,
        solution_method=solution_method,
        confidence=confidence,
    )
    return solution


def estimate_scale_from_control_points(
    local_points: np.ndarray,
    target_points: np.ndarray,
    *,
    weights: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    if weights is None:
        scale, R, t, residuals = compute_similarity_transform(local_points, target_points)
    else:
        scale, R, t, residuals, _residual_var = compute_weighted_similarity_transform(
            local_points, target_points, weights=weights
        )
    return {
        "scale": float(scale),
        "rotation": R.tolist() if isinstance(R, np.ndarray) else R,
        "translation": t.tolist() if isinstance(t, np.ndarray) else t,
        "residuals": residuals.tolist() if isinstance(residuals, np.ndarray) else residuals,
    }


def transform_camera_pose(
    pose: CameraPose,
    *,
    scale: Optional[float] = None,
    rotation: Optional[np.ndarray] = None,
    translation: Optional[np.ndarray] = None,
    target_coordinate_frame: Optional[str] = None,
) -> Dict[str, Any]:
    if pose.position_x is None or pose.position_y is None or pose.position_z is None:
        return {"status": "missing_position", "transformed": None}

    pos = np.array([pose.position_x, pose.position_y, pose.position_z], dtype=np.float64)
    if scale is not None and scale != 1.0:
        pos = pos * scale
    if rotation is not None:
        pos = rotation @ pos
    if translation is not None:
        pos = pos + translation

    result: Dict[str, Any] = {
        "status": "transformed",
        "position_x": float(pos[0]),
        "position_y": float(pos[1]),
        "position_z": float(pos[2]),
        "coordinate_frame": target_coordinate_frame or pose.coordinate_frame,
    }

    if pose.rotation_matrix_json and rotation is not None:
        R_old = np.array(json.loads(pose.rotation_matrix_json), dtype=np.float64)
        R_new = rotation @ R_old
        result["rotation_matrix_json"] = R_new.tolist()
    return result


def georeference_reconstruction(
    reconstruction_id: str,
    *,
    solution: GeorefSolution,
    target_crs: Optional[str] = None,
    source_coordinate_frame: Optional[str] = None,
    target_coordinate_frame: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "reconstruction_id": reconstruction_id,
        "solution_id": solution.id,
        "target_crs": target_crs,
        "source_coordinate_frame": source_coordinate_frame,
        "target_coordinate_frame": target_coordinate_frame,
        "scale_factor": solution.scale_factor,
        "status": "planned",
    }


def validate_spatial_accuracy(
    checkpoint_observations: List[Dict[str, Any]],
    *,
    vertical_datum_compatible: bool = True,
) -> ValidationReport:
    h_errors = [
        o["horizontal_error"]
        for o in checkpoint_observations
        if o.get("horizontal_error") is not None
    ]
    v_errors = [
        o["vertical_error"]
        for o in checkpoint_observations
        if o.get("vertical_error") is not None
    ]
    d_errors = [
        o.get("horizontal_distance_error")
        for o in checkpoint_observations
        if o.get("horizontal_distance_error") is not None
    ]
    t_errors = [
        o.get("three_d_error")
        for o in checkpoint_observations
        if o.get("three_d_error") is not None
    ]

    def mean_err(vals: List[float]) -> Optional[float]:
        return float(np.mean(vals)) if vals else None

    def rmse(vals: List[float]) -> Optional[float]:
        vals = np.array(vals, dtype=np.float64)
        return float(np.sqrt(np.mean(vals ** 2))) if vals.size else None

    horizontal_rmse = rmse(h_errors) if h_errors else None
    vertical_rmse = rmse(v_errors) if v_errors else None
    horizontal_mean = mean_err(h_errors)
    vertical_mean = mean_err(v_errors)

    metrics: Dict[str, Any] = {
        "horizontal_mean_error": horizontal_mean,
        "horizontal_rmse": horizontal_rmse,
        "vertical_mean_error": vertical_mean,
        "vertical_rmse": vertical_rmse,
        "checkpoint_count": len(checkpoint_observations),
        "horizontal_units": "metres",
        "vertical_units": "metres",
    }
    if d_errors:
        metrics["horizontal_distance_rmse"] = rmse(d_errors)
        metrics["horizontal_distance_mean_error"] = mean_err(d_errors)
    if t_errors and vertical_datum_compatible:
        metrics["three_d_rmse"] = rmse(t_errors)
        metrics["three_d_mean_error"] = mean_err(t_errors)

    status = (
        "validated"
        if checkpoint_observations
        else "not_validated_no_independent_reference"
    )

    return ValidationReport(
        mission_id="",
        reconstruction_id="",
        validation_status=status,
        spatial_accuracy=metrics.get("horizontal_rmse"),
        metrics_json=json.dumps(metrics),
        validation_method="independent_checkpoint_comparison",
        reference_data_source="checkpoint_observations",
        uncertainty_json=json.dumps(
            {"note": "Uncertainty estimates depend on checkpoint measurement uncertainties"}
        ),
    )
