import os
from unittest.mock import MagicMock, patch

import pytest
<<<<<<< HEAD
from fastapi import FastAPI
=======
>>>>>>> origin/main
from fastapi.testclient import TestClient

from backend.app.api.v1.reconstruction import router, _get_mission_or_404
from backend.app.api.deps import get_current_active_user
from backend.app.services.recon.readiness import ReconstructionReadiness
from backend.app.models.reconstruction import Reconstruction
from backend.app.models.processing import ProcessingRun


def _fake_user():
    u = MagicMock()
    u.id = "user-1"
    u.is_active = True
    return u


<<<<<<< HEAD
@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_active_user] = _fake_user
    return TestClient(app)


class TestReconstructionAPI:
    def test_start_requires_mission_ownership(self, monkeypatch, client):
=======
class TestReconstructionAPI:
    def test_start_requires_mission_ownership(self, monkeypatch):
        client = TestClient(router)
        monkeypatch.setattr(get_current_active_user, lambda: _fake_user())

>>>>>>> origin/main
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-2"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)

        response = client.post("/api/v1/missions/mission-1/reconstruction/start")
        assert response.status_code == 403

<<<<<<< HEAD
    def test_start_returns_409_when_not_ready(self, monkeypatch, client):
=======
    def test_start_returns_409_when_not_ready(self, monkeypatch):
        client = TestClient(router)
        monkeypatch.setattr(get_current_active_user, lambda: _fake_user())

>>>>>>> origin/main
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.camera_intrinsics_json = None

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)
        monkeypatch.setattr(ReconstructionReadiness, "check", lambda self: {"ready": False})

        response = client.post("/api/v1/missions/mission-1/reconstruction/start")
        assert response.status_code == 409

<<<<<<< HEAD
    def test_status_returns_404_when_no_run(self, monkeypatch, client):
=======
    def test_status_returns_404_when_no_run(self, monkeypatch):
        client = TestClient(router)
        monkeypatch.setattr(get_current_active_user, lambda: _fake_user())

>>>>>>> origin/main
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"

        monkeypatch.setattr(router, "_get_mission_or_404", lambda mid: mission)
        monkeypatch.setattr(ProcessingRun, "query", lambda **kw: MagicMock(first=lambda: None))

        response = client.get("/api/v1/missions/mission-1/reconstruction/status")
        assert response.status_code == 404

<<<<<<< HEAD
    def test_point_cloud_endpoint_returns_404_when_artifact_missing(self, monkeypatch, client):
=======
    def test_point_cloud_endpoint_returns_404_when_artifact_missing(self, monkeypatch):
        client = TestClient(router)
        monkeypatch.setattr(get_current_active_user, lambda: _fake_user())

>>>>>>> origin/main
        rec = MagicMock()
        rec.id = "rec-1"
        rec.mission_id = "mission-1"
        rec.mission.user_id = "user-1"
        rec.point_cloud_path = "/tmp/missing.ply"

        monkeypatch.setattr(Reconstruction, "query", lambda **kw: MagicMock(get=lambda rid: rec if rid == "rec-1" else None))
        monkeypatch.setattr(os.path, "exists", lambda p: False)

        response = client.get("/api/v1/reconstructions/rec-1/point-cloud")
        assert response.status_code == 404
<<<<<<< HEAD

=======
>>>>>>> origin/main
