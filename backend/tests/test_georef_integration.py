from __future__ import annotations

import json
import numpy as np
import pytest

from backend.app.services.georef.similarity import (
    compute_similarity_transform,
    compute_weighted_similarity_transform,
)
from backend.app.services.georef.service import (
    estimate_scale_from_control_points,
    transform_camera_pose,
    validate_spatial_accuracy,
)


class TestGeorefIntegrationScaleRecovery:
    def test_full_control_point_transform_pipeline(self):
        local = np.array([
            [0, 0, 0],
            [10, 0, 0],
            [0, 10, 0],
            [10, 10, 0],
        ], dtype=np.float64)
        target = local * 2.0

        scale_info = estimate_scale_from_control_points(local, target)
        assert abs(scale_info["scale"] - 2.0) < 1e-6

        R = np.array(scale_info["rotation"], dtype=np.float64)
        t = np.array(scale_info["translation"], dtype=np.float64)
        assert np.allclose(R, np.eye(3), atol=1e-6)
        assert np.allclose(t, 0.0, atol=1e-6)

    def test_scale_recovery_with_weighted_observations(self):
        local = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        target = local * 7.0
        weights = np.array([10.0, 1.0, 1.0])
        info = estimate_scale_from_control_points(local, target, weights=weights)
        # Weighted least squares still recovers scale reasonably.
        assert abs(info["scale"] - 7.0) < 1e-3


class TestGeorefIntegrationPoseTransformation:
    def test_transform_pose_chain(self):
        from unittest.mock import MagicMock

        pose = MagicMock(
            position_x=5.0,
            position_y=-3.0,
            position_z=2.0,
            rotation_matrix_json=None,
            coordinate_frame="world",
        )
        result = transform_camera_pose(
            pose,
            scale=0.5,
            rotation=np.eye(3),
            translation=np.array([100, 0, 0], dtype=np.float64),
            target_coordinate_frame="georeferenced",
        )
        assert result["status"] == "transformed"
        assert result["position_x"] == pytest.approx(102.5, abs=1e-6)
        assert result["position_y"] == pytest.approx(-1.5, abs=1e-6)
        assert result["position_z"] == pytest.approx(1.0, abs=1e-6)
        assert result["coordinate_frame"] == "georeferenced"

    def test_transform_pose_missing_position_yields_missing_status(self):
        from unittest.mock import MagicMock

        pose = MagicMock(
            position_x=5.0,
            position_y=None,
            position_z=2.0,
            rotation_matrix_json=None,
            coordinate_frame="world",
        )
        result = transform_camera_pose(pose, target_coordinate_frame="geo")
        assert result["status"] == "missing_position"
        assert result["transformed"] is None


class TestGeorefIntegrationValidationMetrics:
    def test_horizontal_and_vertical_rmse_computed_from_checkpoints(self):
        observations = [
            {"horizontal_error": 0.5, "vertical_error": 0.2},
            {"horizontal_error": 1.5, "vertical_error": 0.4},
            {"horizontal_error": 1.0, "vertical_error": 0.3},
        ]
        report = validate_spatial_accuracy(observations)
        metrics = json.loads(report.metrics_json)
        assert report.validation_status == "validated"
        assert metrics["horizontal_rmse"] == pytest.approx(
            np.sqrt(np.mean([0.5 ** 2, 1.5 ** 2, 1.0 ** 2])), abs=1e-6
        )
        assert metrics["vertical_rmse"] == pytest.approx(
            np.sqrt(np.mean([0.2 ** 2, 0.4 ** 2, 0.3 ** 2])), abs=1e-6
        )

    def test_3d_rmse_requires_compatible_datum(self):
        observations = [
            {"horizontal_error": 1.0, "vertical_error": 0.5, "three_d_error": 1.2},
        ]
        report = validate_spatial_accuracy(observations, vertical_datum_compatible=True)
        metrics = json.loads(report.metrics_json)
        assert metrics["three_d_rmse"] is not None
        assert metrics["three_d_rmse"] == pytest.approx(1.2, abs=1e-6)

    def test_3d_rmse_absent_when_datum_incompatible(self):
        observations = [
            {"horizontal_error": 1.0, "vertical_error": 0.5, "three_d_error": 1.2},
        ]
        report = validate_spatial_accuracy(observations, vertical_datum_compatible=False)
        metrics = json.loads(report.metrics_json)
        assert "three_d_rmse" not in metrics

    def test_horizontal_distance_rmse_when_available(self):
        observations = [
            {"horizontal_error": 0.5, "vertical_error": 0.2, "horizontal_distance_error": 0.6},
            {"horizontal_error": 1.5, "vertical_error": 0.4, "horizontal_distance_error": 1.6},
        ]
        report = validate_spatial_accuracy(observations)
        metrics = json.loads(report.metrics_json)
        assert metrics["horizontal_distance_rmse"] == pytest.approx(
            np.sqrt(np.mean([0.6 ** 2, 1.6 ** 2])), abs=1e-6
        )
