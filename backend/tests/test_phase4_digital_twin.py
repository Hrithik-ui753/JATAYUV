"""Automated Tests for JATAYUV Phase 4: Unified Digital Twin & Infrastructure Monitoring.

Covers:
1. GIS and Geographic Intelligence (CRS management, P0 non-fabrication rule).
2. Multi-Mission Temporal Digital Twin Timeline Comparison.
3. Engineering Review & Verification Workflow (Human verified vs AI observation).
4. Maintenance Work Order Task Lifecycle.
5. Professional PDF & CSV Report Compilation.
6. Digital Twin REST API routes.
"""
from __future__ import annotations

import io
import json
import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user, get_db
from backend.app.api.v1.digital_twin import router as digital_twin_router
from backend.app.services.twin.gis_service import GisIntelligenceService
from backend.app.services.twin.historical_twin_service import HistoricalDigitalTwinService
from backend.app.services.twin.inspection_workflow_service import (
    InspectionWorkflowService,
    VerificationStatus,
    RepairStatus,
)
from backend.app.services.twin.report_generator import ProfessionalReportGenerator


# --- Fixtures ---

def _fake_user():
    u = MagicMock()
    u.id = "engineer-user-1"
    u.email = "lead.engineer@utility.org"
    u.full_name = "Lead Inspection Engineer"
    u.is_active = True
    u.role = "admin"
    return u


def _fake_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.count.return_value = 3
    return db


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(digital_twin_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app)


# --- GIS Tests ---

def test_gis_service_p0_honest_relative_coordinates_when_no_gps():
    gis = GisIntelligenceService()

    objects = [
        {
            "track_id": "TOWER-001",
            "class_name": "transmission_tower",
            "position": [10.5, 2.0, 50.0],
            "confidence": 0.94,
            "severity": "NORMAL",
        }
    ]

    # No GPS telemetry provided
    export = gis.generate_corridor_geojson(mission_id="m1", infrastructure_objects=objects, flight_telemetry=None)

    assert export.is_georeferenced is False
    assert export.crs == "LOCAL_RELATIVE_3D"
    feat = export.geojson["features"][0]
    # Coordinates must strictly reflect relative 3D, never fabricated lat/lon
    assert feat["geometry"]["coordinates"] == [10.5, 50.0, 2.0]
    assert "GPS/RTK telemetry is verified" in export.disclaimer


def test_gis_service_real_gps_conversion_when_telemetry_present():
    gis = GisIntelligenceService()

    objects = [
        {
            "track_id": "TOWER-001",
            "class_name": "transmission_tower",
            "position": [0.0, 0.0, 0.0],
            "confidence": 0.95,
            "severity": "NORMAL",
        }
    ]

    telemetry = {
        "latitude": 42.3601,
        "longitude": -71.0589,
        "altitude": 35.0,
        "coordinate_reference_system": "EPSG:4326",
        "rtk_enabled": 1,
    }

    export = gis.generate_corridor_geojson(mission_id="m2", infrastructure_objects=objects, flight_telemetry=telemetry)

    assert export.is_georeferenced is True
    assert export.crs == "EPSG:4326"
    feat = export.geojson["features"][0]
    # Projected coordinates around Boston base lat/lon
    assert abs(feat["geometry"]["coordinates"][0] - (-71.0589)) < 1e-4
    assert abs(feat["geometry"]["coordinates"][1] - 42.3601) < 1e-4


# --- Historical Digital Twin Timeline Tests ---

def test_historical_digital_twin_multi_mission_timeline():
    twin_service = HistoricalDigitalTwinService()

    mission_1 = {
        "mission_id": "M1_2025_Q3",
        "inspection_date": "2025-09-15",
        "infrastructure_objects_3d": [
            {"track_id": "TOWER-001", "class_name": "transmission_tower", "position": [0, 0, 10], "severity": "NORMAL"},
            {"track_id": "LINE-001", "class_name": "transmission_line", "position": [0, 10, 20], "severity": "NORMAL"},
        ],
        "inspection_report": {"anomalies": []},
    }

    mission_2 = {
        "mission_id": "M2_2026_Q1",
        "inspection_date": "2026-03-20",
        "infrastructure_objects_3d": [
            {"track_id": "TOWER-001", "class_name": "transmission_tower", "position": [0, 0, 10], "severity": "WARNING"},
            {"track_id": "LINE-001", "class_name": "transmission_line", "position": [0, 10, 20], "severity": "NORMAL"},
        ],
        "inspection_report": {"anomalies": [{"target_track_id": "TOWER-001", "severity": "WARNING"}]},
    }

    report = twin_service.build_multi_mission_twin(
        corridor_id="220kV_North",
        missions_data=[mission_1, mission_2],
    )

    assert len(report.timeline_points) == 2
    assert report.timeline_points[0].overall_status == "BASELINE"
    assert report.timeline_points[1].overall_status == "DEGRADING"
    assert len(report.asset_histories) == 2


# --- Engineering Workflow & Verification Tests ---

def test_inspection_workflow_verification_and_work_orders():
    workflow = InspectionWorkflowService()

    # Engineer verifies an AI observation
    verif = workflow.verify_observation(
        mission_id="m_test",
        asset_track_id="TOWER-001",
        anomaly_id="ANOMALY-0001",
        status="VERIFIED_DEFECT",
        engineer_notes="Lattice flange corrosion confirmed during climbing inspection.",
        verified_by="Lead Inspector",
    )

    assert verif.finding_type == "VERIFIED_FINDING"
    assert verif.verification_status == VerificationStatus.VERIFIED_DEFECT
    assert verif.repair_status == RepairStatus.WORK_ORDER_CREATED

    # Create work order task
    task = workflow.create_work_order_task(
        mission_id="m_test",
        title="Tower Flange Galvanization Repair",
        description="Apply cold galvanizing compound to Tower 001 lower leg.",
        priority="HIGH",
        assigned_to="Maintenance Crew 2",
    )

    assert task.status == "ASSIGNED"
    assert task.priority.value == "HIGH"

    # Query mission tasks
    tasks = workflow.get_mission_tasks("m_test")
    assert len(tasks) == 1
    assert tasks[0].title == "Tower Flange Galvanization Repair"


# --- Report Generation Tests ---

def test_report_generator_pdf_and_csv():
    generator = ProfessionalReportGenerator()

    sample_data = {
        "total_frames_processed": 30,
        "infrastructure_objects_3d": [
            {
                "track_id": "LINE-001",
                "class_name": "transmission_line",
                "position": [1.16, 1.32, 4.23],
                "confidence": 0.88,
                "severity": "WARNING",
                "uncertainty_radius": 0.45,
                "risk_evaluation": {"risk_score": 67.6, "risk_category": "HIGH"},
                "catenary_model": {"maximum_sag": 1.37},
                "clearance_result": {"minimum_clearance": 0.65},
                "inspection_notes": ["Clearance encroachment near terrain ridge."],
            }
        ],
        "inspection_report": {
            "anomalies": [
                {
                    "anomaly_id": "ANOM-001",
                    "target_track_id": "LINE-001",
                    "anomaly_type": "CLEARANCE_ENCROACHMENT",
                    "severity": "CRITICAL",
                    "confidence": 0.85,
                    "engineering_recommendation": "Inspect terrain ridge profile.",
                }
            ]
        },
        "risk_summary": {"mean_risk_score": 67.6, "requires_field_patrol_count": 1},
        "clearance_summary": {"minimum_corridor_clearance": 0.65},
    }

    pdf_bytes = generator.generate_pdf_report("test_m", sample_data)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    csv_str = generator.generate_csv_report("test_m", sample_data)
    assert "LINE-001,transmission_line" in csv_str
    assert "Clearance_Encroachment" in csv_str or "CLEARANCE_ENCROACHMENT" in csv_str or "0.65" in csv_str


# --- Digital Twin API Tests ---

def test_digital_twin_gis_endpoint(client):
    resp = client.get("/api/v1/digital-twin/missions/mission_sample/gis")
    assert resp.status_code == 200
    data = resp.json()
    assert "geojson" in data
    assert "crs" in data


def test_digital_twin_verification_endpoint(client):
    body = {
        "asset_track_id": "TOWER-001",
        "anomaly_id": "ANOMALY-001",
        "verification_status": "VERIFIED_DEFECT",
        "engineer_notes": "Structural member tilt confirmed.",
    }
    resp = client.post("/api/v1/digital-twin/missions/mission_sample/verifications", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["finding_type"] == "VERIFIED_FINDING"
    assert data["verification_status"] == "VERIFIED_DEFECT"


def test_digital_twin_task_endpoint(client):
    body = {
        "title": "Repair Broken Insulator Shed",
        "description": "Replace composite disc insulator string.",
        "priority": "URGENT",
        "assigned_to": "Field Crew Delta",
        "target_asset_ids": ["INS-002"],
    }
    resp = client.post("/api/v1/digital-twin/missions/mission_sample/tasks", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ASSIGNED"
    assert data["priority"] == "URGENT"


def test_digital_twin_pdf_and_csv_reports(client):
    resp_pdf = client.get("/api/v1/digital-twin/missions/mission_sample/report/pdf")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"

    resp_csv = client.get("/api/v1/digital-twin/missions/mission_sample/report/csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]


def test_digital_twin_analytics_endpoint(client):
    resp = client.get("/api/v1/digital-twin/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_missions_inspected" in data
    assert "total_assets_monitored" in data
    assert "risk_distribution" in data

