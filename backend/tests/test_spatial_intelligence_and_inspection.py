"""Tests for 3D Spatial Intelligence and Asset Inspection Intelligence."""
from __future__ import annotations

import numpy as np
import pytest

from backend.app.services.inspection.infrastructure_inspection import (
    AnomalySeverity,
    FindingType,
    InfrastructureInspectionEngine,
)
from backend.app.services.perception.infrastructure_detector import (
    InfrastructureClass,
    InfrastructureDetection,
)
from backend.app.services.perception.infrastructure_tracker import (
    InfrastructureTrack,
    InfrastructureTracker,
)
from backend.app.services.perception.spatial_intelligence import (
    LocalizedInfrastructure3D,
    SpatialIntelligenceEngine,
)


def test_robust_depth_sampling_avoids_edges_and_sky():
    engine = SpatialIntelligenceEngine()
    # Create synthetic depth map with sky (nan/inf or 0) on edges and foreground depth in center
    h, w = 100, 100
    depth_map = np.zeros((h, w), dtype=np.float32)
    # Background / edge values
    depth_map[:20, :] = 0.0  # Sky / missing
    # Central object foreground
    depth_map[30:70, 30:70] = 18.5

    bbox = [25.0, 20.0, 75.0, 80.0]
    sampled_depth, uv = engine._sample_robust_depth(bbox, depth_map)

    assert sampled_depth is not None
    assert abs(sampled_depth - 18.5) < 1e-3, f"Expected 18.5, got {sampled_depth}"
    assert 30 <= uv[0] <= 70
    assert 30 <= uv[1] <= 70


def test_2d_to_3d_pinhole_and_coordinate_transformation():
    engine = SpatialIntelligenceEngine(
        units="relative_reconstruction_units",
        scale_type="scale_aligned_relative",
        metric_calibrated=False,
    )

    # Mock camera pose: identity rotation, camera at (0, 0, 0)
    class MockPose:
        R = np.eye(3, dtype=np.float64)
        t = np.zeros((3, 1), dtype=np.float64)
        focal_px = 1000.0
        cx = 500.0
        cy = 500.0
        name = "cam_001"

    camera_poses = {0: MockPose()}
    depth_map = np.full((1000, 1000), 20.0, dtype=np.float32)

    tracker = InfrastructureTracker()
    det = InfrastructureDetection(
        class_name=InfrastructureClass.TRANSMISSION_TOWER,
        confidence=0.90,
        bbox=[400.0, 300.0, 600.0, 700.0],
        frame_index=0,
        timestamp_s=0.0,
    )
    track = tracker.update([det], frame_index=0, timestamp_s=0.0)[0]

    localized = engine.localize_tracks_3d(
        tracks=[track],
        camera_poses=camera_poses,
        depth_maps={0: depth_map},
    )

    assert len(localized) == 1
    obj = localized[0]
    assert obj.track_id == track.track_id
    assert obj.class_name == InfrastructureClass.TRANSMISSION_TOWER
    # Center u=500, v=500 -> Xc=0, Yc=0, Zc=20
    # Three.js world frame: X=Xc, Y=-Yc, Z=Zc
    assert abs(obj.position[0]) < 1.0  # Centered X
    assert abs(obj.position[2] - 20.0) < 1.0  # Depth Z=20
    assert engine.units == "relative_reconstruction_units"
    assert engine.metric_calibrated is False


def test_inspection_engine_detects_structural_anomalies():
    inspection_engine = InfrastructureInspectionEngine()

    tower = LocalizedInfrastructure3D(
        track_id="TOWER-001",
        class_name=InfrastructureClass.TRANSMISSION_TOWER,
        position=(10.0, 5.0, 30.0),
        extents=(6.0, 20.0, 6.0),
        uncertainty_radius=6.2,  # High spatial dispersion
        confidence=0.88,
        observations_count=4,
        spatial_observations=[
            type("SpatialObs", (), {"frame_index": i, "timestamp_s": i * 0.1, "point_world": (10.0, 5.0, 30.0)})()
            for i in range(4)
        ],
    )

    report = inspection_engine.analyze_infrastructure(
        mission_id="test_mission",
        objects_3d=[tower],
    )

    assert report.total_components_inspected == 1
    assert report.total_anomalies_detected >= 1
    anomaly = report.anomalies[0]
    assert anomaly.finding_type == FindingType.AI_OBSERVATION
    assert anomaly.requires_field_verification is True
    assert "verification" in report.disclaimer.lower()


def test_inspection_engine_evaluates_catenary_line_sag():
    inspection_engine = InfrastructureInspectionEngine()

    # Power line with significant catenary sag (ends at Y=15, midpoint sag down to Y=8)
    line = LocalizedInfrastructure3D(
        track_id="LINE-001",
        class_name=InfrastructureClass.TRANSMISSION_LINE,
        position=(0.0, 10.0, 50.0),
        extents=(2.0, 7.0, 40.0),
        uncertainty_radius=0.5,
        confidence=0.92,
        observations_count=3,
        line_waypoints=[
            [0.0, 15.0, 30.0],
            [0.0, 8.0, 50.0],   # Sagged mid-span
            [0.0, 15.0, 70.0],
        ],
    )

    report = inspection_engine.analyze_infrastructure(
        mission_id="test_mission_lines",
        objects_3d=[line],
    )

    sag_anomalies = [a for a in report.anomalies if a.anomaly_type == "EXCESSIVE_CATENARY_SAG"]
    assert len(sag_anomalies) == 1
    assert sag_anomalies[0].severity == AnomalySeverity.WARNING
