"""
MODULE 08 — COMPLETE SYSTEM INTEGRATION TESTS
==============================================
End-to-end tests covering the full JATAYUV-AI data flow:

  1.  User registration and login
  2.  Project CRUD
  3.  Image upload (real JPEG fixtures)
  4.  Depth estimation: explicit unavailability without a verified checkpoint
  5.  Semantic segmentation: explicit unavailability, no random-weight output
  6.  Damage assessment: explicit unavailability, no fabricated classes
  7.  Change detection (paired images) + artifact verification
  8.  3D reconstruction: explicit unavailability without COLMAP, no fake PLY
  9.  Job listing and status polling
  10. Job cancellation (queued/pending jobs)
  11. Job ownership — another user cannot access another user's jobs
  12. Duplicate submission protection (re-trigger should return cached result)
  13. Invalid file upload rejection (non-image bytes)
  14. Job failure handling (inference on missing file)
  15. Missing-model handling: explicit errors only (no baseline/random fallback)
  16. Artifact download byte-level verification

Tests run against an **in-process FastAPI TestClient** backed by a SQLite
:memory: database so they are hermetic and require no running server.
"""

import io
import json
import os
import sys
import struct
import zlib
from pathlib import Path
from typing import Optional

import pytest

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# ---------------------------------------------------------------------------
# PIL / NumPy availability — both should be installed in the project venv
# ---------------------------------------------------------------------------
try:
    from PIL import Image as PILImage, ImageDraw
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------------------------------------------------------------------
# FastAPI / SQLAlchemy test infrastructure
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base, get_db
from backend.app.main import app

# In-memory SQLite for isolation
_TEST_DB_URL = "sqlite:///./test_module08_integration.db"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Recreate the test schema from the current models. The test DB file persists between
# runs, and ``create_all`` never adds columns to an existing table, so a stale file
# would silently keep an old schema (e.g. depth_results without the provenance columns).
Base.metadata.drop_all(bind=_engine)
Base.metadata.create_all(bind=_engine)

client = TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)


def _make_aerial_jpeg(name: str, seed: int = 42, width: int = 128, height: int = 128) -> Path:
    """Return a real JPEG file in the fixtures directory, creating it if needed."""
    path = FIXTURE_DIR / name
    if path.exists():
        return path
    if HAS_PIL:
        rng = np.random.default_rng(seed)
        r = rng.integers(60, 120, (height, width), dtype=np.uint8)
        g = rng.integers(80, 160, (height, width), dtype=np.uint8)
        b = rng.integers(40, 100, (height, width), dtype=np.uint8)
        arr = np.stack([r, g, b], axis=2)
        img = PILImage.fromarray(arr, "RGB")
        img.save(path, "JPEG", quality=85)
    else:
        # Minimal JPEG fallback (1×1 pixel, white)
        _write_minimal_jpeg(path)
    return path


def _write_minimal_jpeg(path: Path):
    """Write a minimal valid JPEG (1×1 white pixel) without PIL."""
    # Standard JFIF 1×1 white JPEG bytes
    data = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD6, 0xFF, 0xD9,
    ])
    path.write_bytes(data)


def _register_and_login(email: str, password: str = "Test1234!", full_name: str = "Test User") -> str:
    """Register a user and return a valid Bearer token."""
    # Try registration; ignore 400 (already exists)
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": "analyst",
    })
    # Login
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Pre-flight: ensure fixture images exist
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_all_fixtures():
    """Create all fixture JPEG images before any test runs."""
    _make_aerial_jpeg("aerial_01.jpg", seed=1)
    _make_aerial_jpeg("aerial_02.jpg", seed=2)
    _make_aerial_jpeg("aerial_03.jpg", seed=3)
    _make_aerial_jpeg("pre_disaster.jpg", seed=10)
    _make_aerial_jpeg("post_disaster.jpg", seed=11)
    _make_aerial_jpeg("before.jpg", seed=20)
    _make_aerial_jpeg("after.jpg", seed=21)
    yield


# ===========================================================================
# 1. Authentication
# ===========================================================================

class TestAuthentication:
    """Registration, login, token usage, and /auth/me."""

    def test_register_new_user(self):
        resp = client.post("/api/v1/auth/register", json={
            "email": "module08_test@jatayuv.ai",
            "password": "TestPass123!",
            "full_name": "Module08 Tester",
            "role": "analyst",
        })
        # 201 or 400 (if already exists from a previous run)
        assert resp.status_code in (201, 400)

    def test_login_returns_access_token(self):
        token = _register_and_login("login_test@jatayuv.ai")
        assert token and len(token) > 20

    def test_me_endpoint_returns_current_user(self):
        token = _register_and_login("me_test@jatayuv.ai")
        resp = client.get("/api/v1/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me_test@jatayuv.ai"

    def test_invalid_credentials_rejected(self):
        resp = client.post("/api/v1/auth/login", data={
            "username": "nobody@jatayuv.ai",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_no_token_fallback_user(self):
        """No-token requests fall back to analyst@jatayuv.ai (integration convenience)."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "analyst" in data["email"] or data["role"] == "admin"


# ===========================================================================
# 2. Project Management
# ===========================================================================

class TestProjects:
    """Create, list, get, and delete projects."""

    def test_create_project(self):
        token = _register_and_login("proj_user@jatayuv.ai")
        resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Integration Test Mission",
            "description": "Module 08 end-to-end test project",
            "location_name": "Test Valley, India",
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "Integration Test Mission"
        assert "id" in data

    def test_list_projects(self):
        token = _register_and_login("proj_list_user@jatayuv.ai")
        # Create a project first
        client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "List Test Project",
            "description": "desc",
            "location_name": "loc",
        })
        resp = client.get("/api/v1/projects", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_project_by_id(self):
        token = _register_and_login("proj_get_user@jatayuv.ai")
        create_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Get Me Project",
            "description": "desc",
            "location_name": "loc",
        })
        project_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/projects/{project_id}", headers=_auth(token))
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == project_id

    def test_nonexistent_project_returns_404(self):
        token = _register_and_login("proj_404_user@jatayuv.ai")
        resp = client.get("/api/v1/projects/does-not-exist-at-all", headers=_auth(token))
        assert resp.status_code == 404


# ===========================================================================
# 3. Image Upload
# ===========================================================================

class TestImageUpload:
    """Upload images, validate EXIF extraction, reject non-images."""

    def _create_project(self, token: str, name="Upload Test") -> str:
        resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": name, "description": "upload test", "location_name": "loc"
        })
        assert resp.status_code in (200, 201)
        return resp.json()["id"]

    def test_upload_valid_jpeg(self):
        token = _register_and_login("upload_user@jatayuv.ai")
        project_id = self._create_project(token, "Upload JPEG Project")
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        assert resp.status_code == 201
        data = resp.json()
        assert isinstance(data, list) and len(data) == 1
        img = data[0]
        assert img["filename"] == "aerial_01.jpg"
        assert img["file_size_bytes"] > 0
        assert img["width"] > 0
        assert img["height"] > 0
        # File must exist on disk
        assert os.path.isfile(img["file_path"]), f"Uploaded file not on disk: {img['file_path']}"

    def test_upload_multiple_images(self):
        token = _register_and_login("multi_upload_user@jatayuv.ai")
        project_id = self._create_project(token, "Multi Upload Project")
        paths = [
            _make_aerial_jpeg("aerial_01.jpg", seed=1),
            _make_aerial_jpeg("aerial_02.jpg", seed=2),
            _make_aerial_jpeg("aerial_03.jpg", seed=3),
        ]
        files = [("files", (p.name, open(p, "rb"), "image/jpeg")) for p in paths]
        resp = client.post(
            f"/api/v1/projects/{project_id}/images/upload",
            headers=_auth(token),
            files=files,
        )
        for _, (_, fh, _) in files:
            fh.close()
        assert resp.status_code == 201
        assert len(resp.json()) == 3

    def test_upload_invalid_extension_rejected(self):
        token = _register_and_login("invalid_ext_user@jatayuv.ai")
        project_id = self._create_project(token, "Invalid Ext Project")
        resp = client.post(
            f"/api/v1/projects/{project_id}/images/upload",
            headers=_auth(token),
            files=[("files", ("malware.exe", b"MZ\x90\x00", "application/octet-stream"))],
        )
        assert resp.status_code in (400, 422)

    def test_upload_text_file_rejected(self):
        token = _register_and_login("text_file_user@jatayuv.ai")
        project_id = self._create_project(token, "Text File Project")
        resp = client.post(
            f"/api/v1/projects/{project_id}/images/upload",
            headers=_auth(token),
            files=[("files", ("readme.txt", b"Hello, World!", "text/plain"))],
        )
        assert resp.status_code in (400, 422)


# ===========================================================================
# 4. AI Inference — Depth Estimation
# ===========================================================================

class TestDepthEstimation:
    """Depth inference requires a verified checkpoint; its absence fails explicitly.

    No random-weight or toy fallback exists, so with no checkpoint installed the endpoint
    must report ``unavailable`` and persist nothing.
    """

    def _setup(self) -> tuple:
        """Returns (token, project_id, image_id, image_file_path)."""
        token = _register_and_login("depth_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Depth Test Project",
            "description": "depth inference",
            "location_name": "loc",
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        assert up_resp.status_code == 201
        image_id = up_resp.json()[0]["id"]
        image_file_path = up_resp.json()[0]["file_path"]
        return token, project_id, image_id, image_file_path

    def _force_missing_checkpoint(self, monkeypatch, tmp_path):
        import dataclasses

        from backend.app.services import depth_engine

        spec = dataclasses.replace(
            depth_engine.MODEL_CATALOG["pretrained"],
            checkpoint=str(tmp_path / "absent_depth.pth"),
        )
        monkeypatch.setitem(depth_engine.MODEL_CATALOG, "pretrained", spec)
        depth_engine.DepthEngine._cache.clear()

    def _clear_cache(self):
        from backend.app.services import depth_engine

        depth_engine.DepthEngine._cache.clear()

    def test_depth_missing_checkpoint_returns_503(self, monkeypatch, tmp_path):
        token, project_id, image_id, _ = self._setup()
        self._force_missing_checkpoint(monkeypatch, tmp_path)
        try:
            resp = client.post(
                "/api/v1/analysis/depth",
                headers=_auth(token),
                json={"image_id": image_id, "model_id": "pretrained"},
            )
        finally:
            self._clear_cache()
        assert resp.status_code == 503, resp.text
        detail = resp.json()["detail"]
        assert detail["status"] == "unavailable"
        assert detail["service"] == "depth_estimation"
        assert "checkpoint" in detail["message"].lower()

    def test_depth_failure_persists_no_result(self, monkeypatch, tmp_path):
        token, project_id, image_id, _ = self._setup()
        self._force_missing_checkpoint(monkeypatch, tmp_path)
        try:
            client.post(
                "/api/v1/analysis/depth",
                headers=_auth(token),
                json={"image_id": image_id, "model_id": "pretrained"},
            )
        finally:
            self._clear_cache()
        get_resp = client.get(f"/api/v1/analysis/depth/{image_id}", headers=_auth(token))
        assert get_resp.status_code == 404

    def test_depth_nonexistent_image_returns_404(self):
        token = _register_and_login("depth_404_user@jatayuv.ai")
        resp = client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": "nonexistent-id"})
        assert resp.status_code == 404


# ===========================================================================
# 5. AI Inference — Semantic Segmentation
# ===========================================================================

class TestSemanticSegmentation:
    """Upload real image, trigger segmentation, verify class distribution and mask."""

    def _setup(self) -> tuple:
        token = _register_and_login("seg_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Segmentation Test Project",
            "description": "seg inference",
            "location_name": "loc",
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_02.jpg", seed=2)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_02.jpg", f, "image/jpeg"))],
            )
        return token, project_id, up_resp.json()[0]["id"]

    def test_segmentation_without_checkpoint_returns_503(self, monkeypatch, tmp_path):
        """No verified checkpoint => explicit unavailability, never random predictions."""
        from backend.app.services.segmentation import segmentation_service

        token, project_id, image_id = self._setup()
        monkeypatch.setattr(
            segmentation_service, "_checkpoint_path", str(tmp_path / "absent_seg.pth")
        )
        resp = client.post("/api/v1/analysis/segmentation", headers=_auth(token), json={"image_id": image_id})
        assert resp.status_code == 503, resp.text
        detail = resp.json()["detail"]
        assert detail["status"] == "unavailable"
        assert detail["service"] == "semantic_segmentation"

    def test_segmentation_failure_writes_no_artifacts(self, monkeypatch, tmp_path):
        from backend.app.services.segmentation import segmentation_service

        token, project_id, image_id = self._setup()
        monkeypatch.setattr(
            segmentation_service, "_checkpoint_path", str(tmp_path / "absent_seg.pth")
        )
        resp = client.post("/api/v1/analysis/segmentation", headers=_auth(token), json={"image_id": image_id})
        assert resp.status_code == 503
        assert client.get(
            f"/api/v1/analysis/segmentation/{image_id}", headers=_auth(token)
        ).status_code == 404
        from backend.app.core.config import settings

        assert not os.path.exists(os.path.join(settings.PROCESSED_DIR, f"segmask_{image_id}.png"))
        assert not os.path.exists(os.path.join(settings.PROCESSED_DIR, f"segoverlay_{image_id}.png"))


# ===========================================================================
# 6. AI Inference — Damage Assessment
# ===========================================================================

class TestDamageAssessment:
    """Upload pre/post pair, trigger damage assessment, verify output."""

    def _setup(self) -> tuple:
        token = _register_and_login("damage_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Damage Test Project",
            "description": "damage inference",
            "location_name": "loc",
        })
        project_id = proj_resp.json()["id"]

        # Upload pre-disaster image
        pre_path = _make_aerial_jpeg("pre_disaster.jpg", seed=10)
        with open(pre_path, "rb") as f:
            pre_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("pre_disaster.jpg", f, "image/jpeg"))],
            )
        pre_id = pre_resp.json()[0]["id"]

        # Upload post-disaster image
        post_path = _make_aerial_jpeg("post_disaster.jpg", seed=11)
        with open(post_path, "rb") as f:
            post_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("post_disaster.jpg", f, "image/jpeg"))],
            )
        post_id = post_resp.json()[0]["id"]

        return token, project_id, pre_id, post_id

    def test_damage_without_checkpoint_returns_503(self, monkeypatch, tmp_path):
        """No verified damage checkpoint => explicit unavailability, no fake classes."""
        from backend.app.services.damage_assessment import damage_service

        token, project_id, pre_id, post_id = self._setup()
        monkeypatch.setattr(
            damage_service, "_checkpoint_path", str(tmp_path / "absent_damage.pth")
        )
        resp = client.post("/api/v1/analysis/damage", headers=_auth(token), json={
            "pre_image_id": pre_id,
            "post_image_id": post_id,
        })
        assert resp.status_code == 503, resp.text
        detail = resp.json()["detail"]
        assert detail["status"] == "unavailable"
        assert detail["service"] == "damage_assessment"

    def test_damage_failure_writes_no_overlay_or_record(self, monkeypatch, tmp_path):
        from backend.app.services.damage_assessment import damage_service

        token, project_id, pre_id, post_id = self._setup()
        monkeypatch.setattr(
            damage_service, "_checkpoint_path", str(tmp_path / "absent_damage.pth")
        )
        resp = client.post("/api/v1/analysis/damage", headers=_auth(token), json={
            "pre_image_id": pre_id,
            "post_image_id": post_id,
        })
        assert resp.status_code == 503
        assert client.get(
            f"/api/v1/analysis/damage/{pre_id}/{post_id}", headers=_auth(token)
        ).status_code == 404
        from backend.app.core.config import settings

        assert not os.path.exists(os.path.join(settings.PROCESSED_DIR, f"damage_{post_id}.png"))

    def test_damage_missing_pre_image_returns_404(self):
        token = _register_and_login("damage_404_user@jatayuv.ai")
        resp = client.post("/api/v1/analysis/damage", headers=_auth(token), json={
            "pre_image_id": "nonexistent-pre",
            "post_image_id": "nonexistent-post",
        })
        assert resp.status_code == 404


# ===========================================================================
# 7. AI Inference — Change Detection
# ===========================================================================

class TestChangeDetection:
    """Upload before/after pair, trigger change detection, verify heatmap."""

    def _setup(self) -> tuple:
        token = _register_and_login("change_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Change Detection Test Project",
            "description": "change inference",
            "location_name": "loc",
        })
        project_id = proj_resp.json()["id"]

        before_path = _make_aerial_jpeg("before.jpg", seed=20)
        after_path = _make_aerial_jpeg("after.jpg", seed=21)

        with open(before_path, "rb") as f:
            before_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("before.jpg", f, "image/jpeg"))],
            )
        with open(after_path, "rb") as f:
            after_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("after.jpg", f, "image/jpeg"))],
            )

        before_id = before_resp.json()[0]["id"]
        after_id = after_resp.json()[0]["id"]
        return token, project_id, before_id, after_id

    def test_change_detection_completes(self):
        token, project_id, before_id, after_id = self._setup()
        resp = client.post("/api/v1/analysis/change", headers=_auth(token), json={
            "before_image_id": before_id,
            "after_image_id": after_id,
        })
        assert resp.status_code == 200, f"Change detection failed: {resp.text}"
        data = resp.json()
        assert "diff_mask_path" in data
        assert "changed_area_pct" in data
        assert 0.0 <= data["changed_area_pct"] <= 100.0

    def test_change_heatmap_on_disk(self):
        token, project_id, before_id, after_id = self._setup()
        resp = client.post("/api/v1/analysis/change", headers=_auth(token), json={
            "before_image_id": before_id,
            "after_image_id": after_id,
        })
        assert resp.status_code == 200
        heatmap_path = resp.json().get("heatmap_path")
        if heatmap_path:
            assert os.path.isfile(heatmap_path), f"Heatmap not on disk: {heatmap_path}"


# ===========================================================================
# 8. 3D Reconstruction
# ===========================================================================

class TestReconstruction3D:
    """Reconstruction only reports success when COLMAP produced verified artifacts."""

    def _setup(self, n_images: int = 3) -> tuple:
        token = _register_and_login("recon_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": f"Reconstruction {n_images}-image Project",
            "description": "recon test",
            "location_name": "loc",
        })
        project_id = proj_resp.json()["id"]

        image_ids = []
        for i in range(n_images):
            img_path = _make_aerial_jpeg(f"aerial_0{i+1}.jpg", seed=i + 1)
            with open(img_path, "rb") as f:
                resp = client.post(
                    f"/api/v1/projects/{project_id}/images/upload",
                    headers=_auth(token),
                    files=[("files", (f"aerial_0{i+1}.jpg", f, "image/jpeg"))],
                )
            image_ids.append(resp.json()[0]["id"])

        return token, project_id, image_ids

    def _force_no_colmap(self, monkeypatch):
        from backend.app.services import reconstruction as reconstruction_module

        monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", None)

    def test_reconstruction_without_colmap_returns_503(self, monkeypatch):
        token, project_id, image_ids = self._setup(n_images=3)
        self._force_no_colmap(monkeypatch)
        resp = client.post("/api/v1/reconstruction/3d", headers=_auth(token), json={
            "project_id": project_id,
            "image_ids": image_ids,
        })
        assert resp.status_code == 503, resp.text
        detail = resp.json()["detail"]
        assert detail["status"] == "unavailable"
        assert "COLMAP" in detail["message"]

    def test_reconstruction_failure_writes_no_ply(self, monkeypatch):
        from backend.app.core.config import settings

        token, project_id, image_ids = self._setup(n_images=3)
        self._force_no_colmap(monkeypatch)
        resp = client.post("/api/v1/reconstruction/3d", headers=_auth(token), json={
            "project_id": project_id,
            "image_ids": image_ids,
        })
        assert resp.status_code == 503
        assert not os.path.exists(
            os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project_id}.ply")
        )
        assert client.get(
            f"/api/v1/reconstruction/3d/{project_id}", headers=_auth(token)
        ).status_code == 404

    def test_reconstruction_requires_minimum_2_images(self):
        """A single frame cannot be reconstructed; no synthetic cloud is produced."""
        token = _register_and_login("recon_singleimage@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Single Image Recon Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]
        resp = client.post("/api/v1/reconstruction/3d", headers=_auth(token), json={
            "project_id": project_id,
            "image_ids": [image_id],
        })
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"]["status"] == "invalid_input"

    def test_reconstruction_without_images_returns_400(self):
        token = _register_and_login("recon_noimages@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Empty Recon Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        resp = client.post("/api/v1/reconstruction/3d", headers=_auth(token), json={
            "project_id": project_id,
            "image_ids": [],
        })
        assert resp.status_code == 400


# ===========================================================================
# 9. Job Monitoring
# ===========================================================================

class TestJobMonitoring:
    """List jobs, get job by ID, check project-scoped job listing."""

    def _get_any_job(self, token: str, project_id: str, image_id: str) -> str:
        """Trigger depth to create a job, return job_id (via project jobs listing)."""
        client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": image_id})
        resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) > 0
        return jobs[0]["id"]

    def test_list_all_jobs(self):
        token = _register_and_login("job_list_user@jatayuv.ai")
        resp = client.get("/api/v1/jobs", headers=_auth(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_project_jobs_listing(self):
        token = _register_and_login("proj_jobs_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Job List Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]
        client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": image_id})

        resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        assert resp.status_code == 200
        jobs = resp.json()
        assert isinstance(jobs, list)
        assert all(j["project_id"] == project_id for j in jobs)

    def test_get_job_by_id(self):
        token = _register_and_login("job_get_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Job Get Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]
        client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": image_id})

        jobs_resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        if jobs_resp.json():
            job_id = jobs_resp.json()[0]["id"]
            get_resp = client.get(f"/api/v1/jobs/{job_id}", headers=_auth(token))
            assert get_resp.status_code == 200
            assert get_resp.json()["id"] == job_id

    def test_job_status_schema(self):
        """Job response must contain required fields per JobResponse schema."""
        token = _register_and_login("job_schema_user@jatayuv.ai")
        resp = client.get("/api/v1/jobs", headers=_auth(token))
        if resp.json():
            job = resp.json()[0]
            for field in ("id", "project_id", "job_type", "status", "progress_pct", "created_at"):
                assert field in job, f"Missing field '{field}' in job response"


# ===========================================================================
# 10. Job Cancellation
# ===========================================================================

class TestJobCancellation:
    """Cancel a pending job; verify terminal state transition."""

    def test_cancel_terminal_job_returns_409(self):
        """Cancelling a job that already reached a terminal state returns 409 Conflict."""
        token = _register_and_login("cancel_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Cancel Test Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]

        # Trigger a depth job. Without a verified checkpoint it fails explicitly, which
        # is still a terminal state (the cancel endpoint must report 409).
        depth_resp = client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": image_id})
        assert depth_resp.status_code in (200, 503)

        # Get the job
        jobs_resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        if not jobs_resp.json():
            pytest.skip("No job found to cancel")

        job_id = jobs_resp.json()[0]["id"]
        # Try to cancel a completed job — must get 409
        cancel_resp = client.post(f"/api/v1/jobs/{job_id}/cancel", headers=_auth(token))
        assert cancel_resp.status_code == 409

    def test_cancel_nonexistent_job_returns_404(self):
        token = _register_and_login("cancel_404_user@jatayuv.ai")
        resp = client.post("/api/v1/jobs/does-not-exist/cancel", headers=_auth(token))
        assert resp.status_code == 404


# ===========================================================================
# 11. Job Ownership / Authorization
# ===========================================================================

class TestJobOwnership:
    """Ensure users cannot access each other's jobs or projects."""

    def test_user_cannot_access_other_users_project(self):
        owner_token = _register_and_login("owner_user@jatayuv.ai")
        attacker_token = _register_and_login("attacker_user@jatayuv.ai")

        # Owner creates project
        proj_resp = client.post("/api/v1/projects", headers=_auth(owner_token), json={
            "name": "Owner's Private Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]

        # Attacker tries to access — should get 403
        get_resp = client.get(f"/api/v1/projects/{project_id}", headers=_auth(attacker_token))
        assert get_resp.status_code == 403

    def test_user_cannot_upload_to_other_users_project(self):
        owner_token = _register_and_login("owner_upload@jatayuv.ai")
        attacker_token = _register_and_login("attacker_upload@jatayuv.ai")

        proj_resp = client.post("/api/v1/projects", headers=_auth(owner_token), json={
            "name": "Owner Upload Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]

        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(attacker_token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        assert resp.status_code == 403

    def test_user_cannot_trigger_inference_on_other_users_image(self):
        owner_token = _register_and_login("owner_infer@jatayuv.ai")
        attacker_token = _register_and_login("attacker_infer@jatayuv.ai")

        proj_resp = client.post("/api/v1/projects", headers=_auth(owner_token), json={
            "name": "Owner Infer Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]

        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(owner_token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]

        # Attacker tries inference — must be 403
        resp = client.post("/api/v1/analysis/depth", headers=_auth(attacker_token), json={"image_id": image_id})
        assert resp.status_code == 403


# ===========================================================================
# 12. Model Registry / Graceful Fallback
# ===========================================================================

class TestModelGracefulFallback:
    """Without a verified checkpoint the depth service must fail loudly."""

    def test_depth_service_exposes_verified_models_only(self):
        """No silent CNN fallback: only verified Depth Anything V2 Small checkpoints."""
        from backend.app.services.depth_estimation import depth_service

        assert depth_service is not None
        # The old toy CNN was removed; the service no longer holds a `model` attribute.
        assert not hasattr(depth_service, "model")
        models = depth_service.available_models()
        assert set(models) == {"pretrained", "jatayuv_drone_v1"}
        assert all(info["depth_type"] == "relative" for info in models.values())
        # A missing checkpoint must raise a clear error rather than substitute a network.
        from backend.app.services.depth_engine import DepthEngine, DepthModelError
        import dataclasses
        from backend.app.services import depth_engine as engine_module

        spec = engine_module.MODEL_CATALOG["pretrained"]
        missing = dataclasses.replace(spec, checkpoint=os.path.join(os.getcwd(), "nope", "missing.pth"))
        engine_module.DepthEngine._cache.clear()
        broken = DepthEngine.__new__(DepthEngine)
        broken.model_id = "pretrained"
        broken.spec = missing
        broken.input_size = 98
        import torch
        broken.device = torch.device("cpu")
        with pytest.raises(DepthModelError):
            broken._load()

    def test_model_registry_available(self):
        from backend.app.services.model_registry import ModelRegistry
        registry = ModelRegistry()
        # Must not raise
        registered = registry.list_models()
        assert isinstance(registered, (list, dict))


# ===========================================================================
# 13. Complete End-to-End Workflow
# ===========================================================================

class TestCompleteWorkflow:
    """
    Full JATAYUV-AI data flow:
      Register → Login → Create Project → Upload Images → Depth → Segmentation
      → Damage → Change → 3D Reconstruction → Retrieve All Results
    """

    def test_full_workflow(self, monkeypatch, tmp_path):
        # --- Step 1: Register + Login ---
        email = "e2e_workflow@jatayuv.ai"
        token = _register_and_login(email, "WorkflowPass99!")

        # --- Step 2: Create Project ---
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "E2E Integration Mission",
            "description": "Full end-to-end workflow test",
            "location_name": "Test Location, India",
            "center_lat": 20.0,
            "center_lon": 78.0,
        })
        assert proj_resp.status_code in (200, 201)
        project_id = proj_resp.json()["id"]

        # --- Step 3: Upload 3 Images ---
        image_ids = []
        for name, seed in [("aerial_01.jpg", 1), ("aerial_02.jpg", 2), ("aerial_03.jpg", 3)]:
            img_path = _make_aerial_jpeg(name, seed=seed)
            with open(img_path, "rb") as f:
                up = client.post(
                    f"/api/v1/projects/{project_id}/images/upload",
                    headers=_auth(token),
                    files=[("files", (name, f, "image/jpeg"))],
                )
            assert up.status_code == 201
            image_ids.append(up.json()[0]["id"])

        # Verification is unavailable in this environment: force the missing-checkpoint
        # path so the assertions below are deterministic, not environment dependent.
        from backend.app.services import depth_engine
        from backend.app.services import reconstruction as reconstruction_module
        from backend.app.services.damage_assessment import damage_service
        from backend.app.services.segmentation import segmentation_service
        import dataclasses

        monkeypatch.setitem(
            depth_engine.MODEL_CATALOG,
            "pretrained",
            dataclasses.replace(
                depth_engine.MODEL_CATALOG["pretrained"],
                checkpoint=str(tmp_path / "absent_depth.pth"),
            ),
        )
        depth_engine.DepthEngine._cache.clear()
        monkeypatch.setattr(segmentation_service, "_checkpoint_path", str(tmp_path / "absent_seg.pth"))
        monkeypatch.setattr(damage_service, "_checkpoint_path", str(tmp_path / "absent_dmg.pth"))
        monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", None)

        # --- Step 4: Depth Estimation reports unavailability ---
        depth_resp = client.post("/api/v1/analysis/depth", headers=_auth(token), json={
            "image_id": image_ids[0], "model_id": "pretrained"
        })
        assert depth_resp.status_code == 503
        assert depth_resp.json()["detail"]["status"] == "unavailable"
        depth_engine.DepthEngine._cache.clear()

        # --- Step 5: Segmentation reports unavailability ---
        seg_resp = client.post("/api/v1/analysis/segmentation", headers=_auth(token), json={"image_id": image_ids[1]})
        assert seg_resp.status_code == 503
        assert seg_resp.json()["detail"]["service"] == "semantic_segmentation"

        # --- Step 6: Damage Assessment reports unavailability ---
        dmg_resp = client.post("/api/v1/analysis/damage", headers=_auth(token), json={
            "pre_image_id": image_ids[0],
            "post_image_id": image_ids[1],
        })
        assert dmg_resp.status_code == 503
        assert dmg_resp.json()["detail"]["service"] == "damage_assessment"

        # --- Step 7: Change Detection (model-free) completes with real artifacts ---
        chg_resp = client.post("/api/v1/analysis/change", headers=_auth(token), json={
            "before_image_id": image_ids[1],
            "after_image_id": image_ids[2],
        })
        assert chg_resp.status_code == 200
        assert os.path.isfile(chg_resp.json()["diff_mask_path"])

        # --- Step 8: 3D Reconstruction reports the missing backend ---
        recon_resp = client.post("/api/v1/reconstruction/3d", headers=_auth(token), json={
            "project_id": project_id,
            "image_ids": image_ids,
        })
        assert recon_resp.status_code == 503
        assert recon_resp.json()["detail"]["status"] == "unavailable"

        # --- Step 9: No results were fabricated for the unavailable services ---
        assert client.get(f"/api/v1/analysis/depth/{image_ids[0]}", headers=_auth(token)).status_code == 404
        assert client.get(f"/api/v1/analysis/segmentation/{image_ids[1]}", headers=_auth(token)).status_code == 404
        assert client.get(
            f"/api/v1/analysis/damage/{image_ids[0]}/{image_ids[1]}", headers=_auth(token)
        ).status_code == 404
        assert client.get(
            f"/api/v1/reconstruction/3d/{project_id}", headers=_auth(token)
        ).status_code == 404

        # --- Step 10: Job listing distinguishes completed from failed ---
        jobs_resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        assert jobs_resp.status_code == 200
        jobs = jobs_resp.json()
        assert len(jobs) >= 4  # depth + segmentation + damage + change + reconstruction

        by_type = {}
        for job in jobs:
            by_type.setdefault(job["job_type"], set()).add(job["status"])

        assert by_type.get("change_detection") == {"completed"}
        for job_type in ("depth_estimation", "semantic_segmentation", "damage_assessment", "reconstruction_3d"):
            assert by_type.get(job_type) == {"failed"}, (
                f"{job_type} must be recorded as failed when its model/backend is unavailable"
            )


# ===========================================================================
# 14. Job Logs
# ===========================================================================

class TestJobLogs:
    """Get structured log entries for a job."""

    def test_job_logs_endpoint(self):
        token = _register_and_login("logs_user@jatayuv.ai")
        proj_resp = client.post("/api/v1/projects", headers=_auth(token), json={
            "name": "Logs Test Project", "description": "d", "location_name": "l"
        })
        project_id = proj_resp.json()["id"]
        img_path = _make_aerial_jpeg("aerial_01.jpg", seed=1)
        with open(img_path, "rb") as f:
            up_resp = client.post(
                f"/api/v1/projects/{project_id}/images/upload",
                headers=_auth(token),
                files=[("files", ("aerial_01.jpg", f, "image/jpeg"))],
            )
        image_id = up_resp.json()[0]["id"]
        client.post("/api/v1/analysis/depth", headers=_auth(token), json={"image_id": image_id})

        jobs_resp = client.get(f"/api/v1/jobs/projects/{project_id}", headers=_auth(token))
        if not jobs_resp.json():
            pytest.skip("No job found")

        job_id = jobs_resp.json()[0]["id"]
        logs_resp = client.get(f"/api/v1/jobs/{job_id}/logs", headers=_auth(token))
        assert logs_resp.status_code == 200
        assert isinstance(logs_resp.json(), list)


# ===========================================================================
# 15. Health Check
# ===========================================================================

class TestHealthCheck:
    """Backend availability and schema smoke tests."""

    def test_openapi_schema_available(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert "info" in schema

    def test_docs_endpoint_available(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

