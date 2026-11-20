"""Tests for Spatial Intelligence REST API Endpoints."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user, get_db
from backend.app.api.v1.spatial_intelligence import router
from backend.app.models.mission import Mission
from backend.app.services.spatial_pipeline import SpatialPipelineResult


def _fake_user():
    u = MagicMock()
    u.id = "test-user-1"
    u.is_active = True
    u.role = "admin"
    return u


def _fake_db():
    db = MagicMock()
    return db


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app)


def test_spatial_intelligence_get_not_found(client, tmp_path, monkeypatch):
    # When no artifact exists, returns 404
    with patch("os.path.isfile", return_value=False), patch("glob.glob", return_value=[]):
        resp = client.get("/api/v1/missions/non_existent_mission/spatial-intelligence")
        assert resp.status_code == 404


def test_spatial_intelligence_get_existing_artifact(client, tmp_path, monkeypatch):
    artifact = {
        "mission_id": "mission-42",
        "total_frames_processed": 10,
        "total_tracked_objects": 2,
        "infrastructure_objects_3d": [
            {
                "track_id": "TOWER-001",
                "class_name": "transmission_tower",
                "position": [0.0, 10.0, 20.0],
                "extents": [5.0, 18.0, 5.0],
                "uncertainty_radius": 0.45,
                "confidence": 0.94,
                "observations_count": 5,
                "severity": "NORMAL",
                "inspection_notes": ["Stable structural axis."],
                "requires_field_verification": False,
            }
        ],
        "inspection_report": {
            "mission_id": "mission-42",
            "total_components_inspected": 2,
            "total_anomalies_detected": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "risk_index_pct": 0.0,
            "disclaimer": "AI observation only.",
            "anomalies": [],
        },
        "scale_metadata": {
            "units": "relative_reconstruction_units",
            "scale_type": "scale_aligned_relative",
            "metric_calibrated": False,
        },
    }

    raw_json = json.dumps(artifact)
    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data=raw_json)):
        resp = client.get("/api/v1/missions/mission-42/spatial-intelligence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mission_id"] == "mission-42"
        assert len(data["infrastructure_objects_3d"]) == 1
        assert data["infrastructure_objects_3d"][0]["track_id"] == "TOWER-001"

        # Check inspection report endpoint
        resp_insp = client.get("/api/v1/missions/mission-42/spatial-intelligence/inspection-report")
        assert resp_insp.status_code == 200
        insp_data = resp_insp.json()
        assert insp_data["total_components_inspected"] == 2

        # Check track detail endpoint
        resp_track = client.get("/api/v1/missions/mission-42/spatial-intelligence/tracks/TOWER-001")
        assert resp_track.status_code == 200
        assert resp_track.json()["track_id"] == "TOWER-001"

        # Check Phase 3 clearance endpoint
        resp_clearance = client.get("/api/v1/missions/mission-42/spatial-intelligence/clearance")
        assert resp_clearance.status_code == 200
        assert resp_clearance.json()["mission_id"] == "mission-42"

        # Check Phase 3 export endpoint (JSON)
        resp_export_json = client.get("/api/v1/missions/mission-42/spatial-intelligence/export?format=json")
        assert resp_export_json.status_code == 200
        assert resp_export_json.json()["mission_id"] == "mission-42"

        # Check Phase 3 export endpoint (CSV)
        resp_export_csv = client.get("/api/v1/missions/mission-42/spatial-intelligence/export?format=csv")
        assert resp_export_csv.status_code == 200
        assert "Asset_ID,Class" in resp_export_csv.text

        # Check Phase 3 historical comparison endpoint
        resp_comp = client.post("/api/v1/missions/mission-42/compare/mission-42")
        assert resp_comp.status_code == 200
        comp_data = resp_comp.json()
        assert comp_data["mission_id_a"] == "mission-42"
        assert comp_data["total_matched_assets"] == 1
