"""Automated Tests for JATAYUV Phase 3: Advanced Infrastructure Inspection & Risk Intelligence.

Covers:
1. Tower Component Instance Segmentation (body, legs, crossarms, bracing members, insulator attachments, ground wire peak).
2. Power-Line Reconstruction & 3D Catenary Curve Modeling.
3. Insulator Integrity & Defect Inspection with Evidence Image Generation.
4. Conductor-to-Terrain 3D Spatial Clearance Estimation with cKDTree.
5. AI Multi-Factor Transparent Risk Assessment Engine.
6. Historical Inspection Multi-Temporal Comparison with Scale Alignment.
7. Regulatory Disclaimers and Non-Fabrication Invariants.
"""
import os
import shutil
import tempfile
import numpy as np
import pytest

from backend.app.services.inspection.tower_component_segmentation import (
    TowerComponentSegmenter,
    TowerComponentType,
)
from backend.app.services.inspection.power_line_reconstruction import (
    PowerLineReconstructor,
)
from backend.app.services.inspection.insulator_inspection import (
    InsulatorInspectionEngine,
    InsulatorDefectType,
)
from backend.app.services.inspection.conductor_clearance import (
    ConductorClearanceEstimator,
)
from backend.app.services.inspection.risk_assessment import (
    RiskAssessmentEngine,
    RiskCategory,
)
from backend.app.services.inspection.historical_comparison import (
    HistoricalComparisonEngine,
)


def test_tower_component_segmentation_polygon_and_completeness():
    segmenter = TowerComponentSegmenter()
    # Create a synthetic tower image (300 x 150)
    img = np.full((300, 150, 3), 120, dtype=np.uint8)
    # Draw simple lattice lines
    img[20:280, 50:100] = 60

    result = segmenter.segment_tower(
        frame_bgr=img,
        tower_bbox=[20, 10, 130, 290],
        tower_track_id="TOWER-001",
        frame_index=0,
    )

    assert result.tower_track_id == "TOWER-001"
    assert result.total_components_segmented >= 4
    assert result.structural_completeness_pct > 50.0

    # Verify component types and polygon vertices
    comp_types = [c.component_type for c in result.components]
    assert TowerComponentType.GROUND_WIRE_PEAK in comp_types
    assert TowerComponentType.CROSSARM in comp_types
    assert TowerComponentType.TOWER_BODY in comp_types
    assert TowerComponentType.TOWER_LEGS in comp_types

    # Ensure polygons have at least 3 vertices
    for comp in result.components:
        assert len(comp.contour_polygon) >= 3
        assert comp.confidence > 0.0
        assert comp.area_px > 0


def test_power_line_catenary_reconstruction():
    reconstructor = PowerLineReconstructor()

    # Create a parabolic/catenary set of waypoints with nominal sag (< 4.5)
    z_coords = np.linspace(0.0, 40.0, 15)
    waypoints = []
    for z in z_coords:
        y = 0.005 * ((z - 20.0) ** 2) + 8.0
        x = 5.0
        waypoints.append([x, y, z])

    cat_model = reconstructor.reconstruct_conductor_span(
        line_track_id="LINE-001",
        waypoints_3d=waypoints,
        confidence=0.91,
    )

    assert cat_model.line_track_id == "LINE-001"
    assert cat_model.is_continuous is True
    assert cat_model.continuity_status == "CONTINUOUS"
    assert cat_model.span_length > 35.0
    assert cat_model.maximum_sag > 0.0
    assert cat_model.parameter_a > 10.0

    # Verify separation of measured vs interpolated geometry
    assert len(cat_model.measured_points) == len(waypoints)
    for mp in cat_model.measured_points:
        assert mp.is_measured is True

    assert len(cat_model.interpolated_points) == 30
    for ip in cat_model.interpolated_points:
        assert ip.is_measured is False


def test_power_line_discontinuity_detection():
    reconstructor = PowerLineReconstructor()

    # Gap in the middle representing severed conductor
    waypoints = [
        [0.0, 10.0, 0.0],
        [0.0, 9.8, 5.0],
        # Gap from z=5 to z=35
        [0.0, 9.8, 35.0],
        [0.0, 10.0, 40.0],
    ]

    cat_model = reconstructor.reconstruct_conductor_span(
        line_track_id="LINE-BROKEN",
        waypoints_3d=waypoints,
        confidence=0.85,
    )

    assert cat_model.is_continuous is False
    assert cat_model.continuity_status == "DISCONTINUITY_FLAGGED"
    assert cat_model.discontinuity_gap_units > 15.0


def test_insulator_inspection_and_evidence_crop():
    inspector = InsulatorInspectionEngine()
    temp_dir = tempfile.mkdtemp()

    try:
        # Generate synthetic insulator image with periodic disc sheds
        img = np.full((120, 60, 3), 180, dtype=np.uint8)
        # Draw periodic dark disc rims
        for y_disc in [20, 35, 50, 65, 80, 95]:
            img[y_disc : y_disc + 3, :] = 40

        audit = inspector.inspect_insulator_roi(
            frame_bgr=img,
            insulator_bbox=[10, 10, 50, 110],
            insulator_track_id="INSULATOR-001",
            evidence_save_dir=temp_dir,
        )

        assert audit.insulator_track_id == "INSULATOR-001"
        assert audit.total_discs_detected >= 3
        assert audit.string_integrity_score_pct > 0.0

        # Check evidence image was written to disk
        expected_crop = os.path.join(temp_dir, "evidence_INSULATOR-001.jpg")
        assert os.path.isfile(expected_crop)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_conductor_terrain_clearance_ckdtree():
    estimator = ConductorClearanceEstimator()

    # Catenary points in 3D: mid-span at y = 6.0, z = 20.0
    conductor_curve = [
        (0.0, 12.0, 0.0),
        (0.0, 6.0, 20.0),  # Lowest mid-span point
        (0.0, 12.0, 40.0),
    ]

    # Flat ground terrain points at y = 1.0
    terrain_pts = []
    for x in np.linspace(-10, 10, 10):
        for z in np.linspace(-5, 45, 20):
            terrain_pts.append([x, 1.0, z])
    terrain_arr = np.array(terrain_pts, dtype=np.float64)

    clearance_result = estimator.estimate_span_clearance(
        line_track_id="LINE-001",
        conductor_curve_points=conductor_curve,
        terrain_points=terrain_arr,
        uncertainty_radius=0.45,
    )

    assert clearance_result.line_track_id == "LINE-001"
    # Expected clearance around y_cond(6.0) - y_terr(1.0) = 5.0
    assert 4.5 <= clearance_result.minimum_clearance <= 5.5
    assert clearance_result.bottleneck.conductor_point_3d[1] == 6.0
    assert clearance_result.bottleneck.terrain_point_3d[1] == 1.0

    # Verify safety disclaimer exists
    assert "nesc" in clearance_result.disclaimer.lower() or "rtk" in clearance_result.disclaimer.lower()


def test_ai_risk_assessment_engine():
    risk_engine = RiskAssessmentEngine()

    # 1. Clean asset with no defects
    clean_eval = risk_engine.evaluate_asset_risk(
        asset_id="TOWER-CLEAN",
        class_name="transmission_tower",
        confidence=0.95,
        anomaly_severities=[],
        uncertainty_radius=0.25,
        frame_observations_count=6,
    )
    assert clean_eval.risk_score <= 15.0
    assert clean_eval.risk_category == RiskCategory.NEGLIGIBLE
    assert clean_eval.requires_human_verification is False

    # 2. Asset with Critical severity anomaly
    crit_eval = risk_engine.evaluate_asset_risk(
        asset_id="LINE-CRIT",
        class_name="transmission_line",
        confidence=0.92,
        anomaly_severities=["CRITICAL"],
        uncertainty_radius=0.85,
        frame_observations_count=5,
        historical_anomaly_count_delta=1,
    )
    assert crit_eval.risk_score >= 61.0
    assert crit_eval.risk_category in (RiskCategory.HIGH, RiskCategory.CRITICAL)
    assert "critical" in crit_eval.contributing_factors[0].lower()
    assert crit_eval.severity_weight >= 40.0
    assert crit_eval.to_dict()["factor_breakdown"]["severity_weight"] >= 40.0
    assert crit_eval.requires_human_verification is True


def test_historical_comparison_engine_scale_and_matching():
    comparator = HistoricalComparisonEngine()

    mission_a = {
        "mission_id": "MISSION-A-BASELINE",
        "infrastructure_objects_3d": [
            {"track_id": "TOWER-001", "class_name": "transmission_tower", "position": [10.0, 0.0, 50.0], "confidence": 0.90, "severity": "NORMAL"},
            {"track_id": "LINE-001", "class_name": "transmission_line", "position": [10.0, 15.0, 80.0], "confidence": 0.88, "severity": "NORMAL"},
        ],
        "inspection_report": {"anomalies": []},
    }

    # Mission B has slightly different scale (1.05x) and a new defect on TOWER-001
    mission_b = {
        "mission_id": "MISSION-B-CURRENT",
        "infrastructure_objects_3d": [
            {"track_id": "TOWER-B01", "class_name": "transmission_tower", "position": [10.5, 0.0, 52.5], "confidence": 0.93, "severity": "WARNING"},
            {"track_id": "LINE-B01", "class_name": "transmission_line", "position": [10.5, 15.75, 84.0], "confidence": 0.89, "severity": "NORMAL"},
        ],
        "inspection_report": {"anomalies": [{"target_track_id": "TOWER-B01", "severity": "WARNING"}]},
    }

    report = comparator.compare_missions(mission_a, mission_b)

    assert report.total_matched_assets == 2
    assert report.new_anomalies_count == 1
    assert report.overall_health_trend == "DEGRADING"

    matched_tower = next(p for p in report.matched_pairs if p.class_name == "transmission_tower")
    assert matched_tower.status_change == "NEW_DEFECT"
