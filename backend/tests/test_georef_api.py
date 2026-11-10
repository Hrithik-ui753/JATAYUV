from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.v1.georef import router
from backend.app.api.deps import get_current_active_user


def _fake_user():
    u = MagicMock()
    u.id = "user-1"
    u.is_active = True
    return u


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_active_user] = _fake_user
    return TestClient(app)


class TestGeorefAPIOwnership:
    def test_start_requires_mission_ownership(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-2"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        response = client.post("/api/v1/missions/mission-1/georeferencing/start", json={
            "reconstruction_id": "rec-1",
            "target_crs": "EPSG:4326",
        })
        assert response.status_code == 403

    def test_control_point_requires_mission_ownership(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-2"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        response = client.post("/api/v1/missions/mission-1/control-points", json={
            "role": "CONTROL",
            "local_x": 0.0,
            "local_y": 0.0,
            "local_z": 0.0,
        })
        assert response.status_code == 403


class TestGeorefAPIControlPointRoleValidation:
    def test_invalid_role_rejected(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        response = client.post("/api/v1/missions/mission-1/control-points", json={
            "role": "INVALID",
            "local_x": 0.0,
        })
        assert response.status_code == 400


class TestGeorefAPISolvePreconditions:
    def test_solve_fails_without_control_points(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.flight_metadata = None

        reconstruction = MagicMock()
        reconstruction.id = "rec-1"
        reconstruction.mission_id = "mission-1"
        reconstruction.coordinate_reference_system = "EPSG:4326"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)
        monkeypatch.setattr(router, "_get_reconstruction_or_404", lambda rid: reconstruction)

        def fake_control_points_query(*args, **kwargs):
            class Q:
                def all(self):
                    return []
            return Q()

        monkeypatch.setattr(
            "backend.app.models.ground_control_point.GroundControlPoint.query",
            fake_control_points_query,
        )

        response = client.post("/api/v1/missions/mission-1/georeferencing/solve", json={
            "reconstruction_id": "rec-1",
            "method": "similarity_transform",
        })
        assert response.status_code == 409


class TestGeorefAPIValidation:
    def test_validation_returns_not_validated_without_checkpoints(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.flight_metadata = None

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        def fake_checkpoint_query(*args, **kwargs):
            class Q:
                def all(self):
                    return []
            return Q()

        monkeypatch.setattr(
            "backend.app.models.checkpoint_observation.CheckpointObservation.query",
            fake_checkpoint_query,
        )

        response = client.get("/api/v1/missions/mission-1/georeferencing/validation")
        assert response.status_code == 200
        assert response.json()["validation_status"] == "not_validated_no_independent_reference"

    def test_validation_returns_validated_with_checkpoints(self, monkeypatch, client):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.flight_metadata = None

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        obs = MagicMock()
        obs.horizontal_error = 1.0
        obs.vertical_error = 0.5
        obs.horizontal_distance_error = 1.1
        obs.three_d_error = 1.2

        def fake_checkpoint_query(*args, **kwargs):
            class Q:
                def all(self):
                    return [obs]
            return Q()

        monkeypatch.setattr(
            "backend.app.models.checkpoint_observation.CheckpointObservation.query",
            fake_checkpoint_query,
        )

        response = client.get("/api/v1/missions/mission-1/georeferencing/validation")
        assert response.status_code == 200
        assert response.json()["validation_status"] == "validated"

