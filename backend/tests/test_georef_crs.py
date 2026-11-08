from __future__ import annotations

import json
import numpy as np
import pytest

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
from backend.app.services.georef.service import (
    estimate_scale_from_control_points,
    transform_camera_pose,
    validate_spatial_accuracy,
)


class TestCRS:
    def test_wgs84_crs_is_4326(self):
        crs = wgs84_crs()
        assert crs.to_epsg() == 4326

    def test_utm_zone_from_lat_lon_northern(self):
        zone = utm_zone_from_lat_lon(48.8566, 2.3522)  # Paris
        assert zone is not None
        assert "UTM" in zone.upper() or "EPSG" in zone.upper()

    def test_utm_zone_from_lat_lon_southern(self):
        zone = utm_zone_from_lat_lon(-33.8688, 151.2093)  # Sydney
        assert zone is not None

    def test_create_transformer_non_default(self):
        transformer = create_transformer("EPSG:4326", "EPSG:3857")
        x, y = transformer.transform(2.3522, 48.8566)
        assert x != 2.3522
        assert y != 48.8566

    def test_transform_point_2d(self):
        transformer = create_transformer("EPSG:4326", "EPSG:3857")
        x, y = transform_point(transformer, 2.3522, 48.8566)
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_transform_point_3d(self):
        transformer = create_transformer("EPSG:4326", "EPSG:3857")
        x, y, z = transform_point(transformer, 2.3522, 48.8566, 100.0)
        assert isinstance(z, float)


class TestSimilarityTransform:
    def test_identity_transform(self):
        np.random.seed(0)
        points = np.random.randn(100, 3)
        _, _, _, residuals = compute_similarity_transform(points.copy(), points.copy())
        assert np.allclose(residuals, 0.0, atol=1e-6)

    def test_scaled_transform(self):
        np.random.seed(1)
        points = np.random.randn(50, 3)
        scaled = points * 2.0
        scale, _, _, residuals = compute_similarity_transform(points, scaled)
        assert abs(scale - 2.0) < 1e-6
        assert np.allclose(residuals, 0.0, atol=1e-6)

    def test_rotated_transform(self):
        np.random.seed(2)
        points = np.random.randn(50, 3)
        R = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)
        rotated = points @ R.T
        scale, R_est, _, residuals = compute_similarity_transform(points, rotated)
        assert abs(scale - 1.0) < 1e-6
        assert np.allclose(residuals, 0.0, atol=1e-6)
        # Rotation should be applied (orientation change).
        assert not np.allclose(R_est, np.eye(3), atol=1e-6)

    def test_weighted_transform(self):
        np.random.seed(3)
        points = np.random.randn(30, 3)
        scaled = points * 3.0
        weights = np.ones(30)
        scale, _, _, _, _residual_var = compute_weighted_similarity_transform(points, scaled, weights=weights)
        assert abs(scale - 3.0) < 1e-6

    def test_reflection_rejection(self):
        np.random.seed(4)
        points = np.random.randn(20, 3)
        reflected = points.copy()
        reflected[:, 0] *= -1
        _, R, _, _ = compute_similarity_transform(points, reflected)
        assert np.linalg.det(R) > 0  # ensure rotation, not reflection

    def test_degenerate_control_points_rejected(self):
        points = np.random.randn(2, 3)
        with pytest.raises(AssertionError):
            compute_similarity_transform(points, points)


class TestScaleRecoveryService:
    def test_estimate_scale_from_control_points(self):
        local = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        target = local * 5.0
        info = estimate_scale_from_control_points(local, target)
        assert abs(info["scale"] - 5.0) < 1e-6

    def test_estimate_scale_with_weights(self):
        local = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        target = local * 7.0
        weights = np.array([1.0, 1.0, 1.0])
        info = estimate_scale_from_control_points(local, target, weights=weights)
        assert abs(info["scale"] - 7.0) < 1e-6


class TestPoseTransformation:
    def test_transform_camera_pose_without_data(self):
        from unittest.mock import MagicMock

        pose = MagicMock(
            position_x=None,
            position_y=None,
            position_z=None,
            rotation_matrix_json=None,
            coordinate_frame="world",
        )
        result = transform_camera_pose(pose, target_coordinate_frame="local")
        assert result["status"] == "missing_position"
        assert result["transformed"] is None

    def test_transform_camera_pose_with_values(self):
        from unittest.mock import MagicMock

        pose = MagicMock(
            position_x=1.0,
            position_y=2.0,
            position_z=3.0,
            rotation_matrix_json=None,
            coordinate_frame="world",
        )
        result = transform_camera_pose(
            pose,
            scale=2.0,
            rotation=np.eye(3),
            translation=np.array([10, 0, 0], dtype=np.float64),
            target_coordinate_frame="local",
        )
        assert result["status"] == "transformed"
        assert result["position_x"] == pytest.approx(12.0, abs=1e-6)
        assert result["position_y"] == pytest.approx(4.0, abs=1e-6)
        assert result["position_z"] == pytest.approx(6.0, abs=1e-6)
        assert result["coordinate_frame"] == "local"

    def test_transform_camera_pose_rotation_and_json(self):
        from unittest.mock import MagicMock

        R_old = np.eye(3, dtype=np.float64)
        pose = MagicMock(
            position_x=1.0,
            position_y=0.0,
            position_z=0.0,
            rotation_matrix_json=json.dumps(R_old.tolist()),
            coordinate_frame="world",
        )
        R_new = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)
        result = transform_camera_pose(
            pose,
            rotation=R_new,
            target_coordinate_frame="rotated",
        )
        assert result["status"] == "transformed"
        rot_json = np.array(result["rotation_matrix_json"], dtype=np.float64)
        expected = R_new @ R_old
        assert np.allclose(rot_json, expected, atol=1e-6)


class TestSpatialValidation:
    def test_validate_spatial_accuracy_with_checkpoints(self):
        observations = [
            {"horizontal_error": 1.0, "vertical_error": 0.5, "horizontal_distance_error": 1.1, "three_d_error": 1.2},
            {"horizontal_error": 2.0, "vertical_error": 0.3, "horizontal_distance_error": 2.0, "three_d_error": 2.0},
            {"horizontal_error": 1.5, "vertical_error": 0.4, "horizontal_distance_error": 1.5, "three_d_error": 1.5},
        ]
        report = validate_spatial_accuracy(observations)
        assert report.validation_status == "validated"
        metrics = json.loads(report.metrics_json)
        assert metrics["checkpoint_count"] == 3
        assert metrics["horizontal_rmse"] is not None
        assert metrics["horizontal_rmse"] > 0
        assert metrics["vertical_rmse"] is not None

    def test_validate_spatial_accuracy_no_checkpoints(self):
        report = validate_spatial_accuracy([])
        assert report.validation_status == "not_validated_no_independent_reference"
        metrics = json.loads(report.metrics_json)
        assert metrics["checkpoint_count"] == 0
        assert metrics["horizontal_rmse"] is None
