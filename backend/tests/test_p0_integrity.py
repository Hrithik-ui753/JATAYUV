"""P0 integrity quarantine tests.

These tests assert what the platform is *allowed* to claim:

1. a missing depth checkpoint fails explicitly,
2. a missing segmentation checkpoint fails explicitly,
3. a missing damage checkpoint fails explicitly,
4. insufficient reconstruction input never creates synthetic geometry,
5. reprojection error is never hardcoded,
6. (empty viewer state / PLY loading / upload failure UI are asserted by
   ``frontend/tests/viewer-integrity.test.mjs``),
7. PLY artifacts are validated (mirrors the viewer's PLY guard),
8. a failed upload returns an error and stores nothing,
9. failed operations generate no fabricated artifacts or records.
"""
from __future__ import annotations

import io
import os
import struct
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.main import app

SERVICES_DIR = Path(__file__).resolve().parents[1] / "app" / "services"


# --------------------------------------------------------------------------- helpers
def _jpeg_bytes(width: int = 48, height: int = 48, value: int = 128) -> bytes:
    image = np.full((height, width, 3), value, dtype=np.uint8)
    cv2.rectangle(image, (8, 8), (width - 8, height - 8), (200, 200, 200), -1)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes()


def _write_image(path: Path, width: int = 48, height: int = 48, value: int = 128) -> str:
    path.write_bytes(_jpeg_bytes(width, height, value))
    return str(path)


def _ascii_ply(n: int = 3) -> str:
    rows = [f"{i}.0 {i * 0.5} {i * 2.0} 255 128 0" for i in range(n)]
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            f"element vertex {n}",
            "property float x",
            "property float y",
            "property float z",
            "property uchar red",
            "property uchar green",
            "property uchar blue",
            "end_header",
            *rows,
            "",
        ]
    )


def _binary_ply(vertices: list[tuple[float, float, float]]) -> bytes:
    header = "\n".join(
        [
            "ply",
            "format binary_little_endian 1.0",
            f"element vertex {len(vertices)}",
            "property float x",
            "property float y",
            "property float z",
            "end_header",
            "",
        ]
    ).encode("ascii")
    body = b"".join(struct.pack("<fff", *vertex) for vertex in vertices)
    return header + body


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient with an isolated SQLite database."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path_factory.mktemp("p0_integrity") / "p0.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    from backend.tests.p0_db import make_isolated_db
    make_isolated_db(db_path)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    if previous is not None:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)


def _create_project(client, name: str) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": name, "description": "P0 integrity", "location_name": "Test Sector"},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _upload(client, project_id: str, count: int) -> list[str]:
    files = [
        ("files", (f"p0_frame_{index}.jpg", io.BytesIO(_jpeg_bytes(value=60 + index * 20)), "image/jpeg"))
        for index in range(count)
    ]
    response = client.post(f"/api/v1/projects/{project_id}/images/upload", files=files)
    assert response.status_code == 201, response.text
    return [image["id"] for image in response.json()]


# =========================================================== 1. depth checkpoint
def test_missing_depth_checkpoint_fails_explicitly(tmp_path, monkeypatch):
    import dataclasses

    from backend.app.services import depth_engine

    spec = dataclasses.replace(
        depth_engine.MODEL_CATALOG["pretrained"],
        checkpoint=str(tmp_path / "absent_depth.pth"),
    )
    monkeypatch.setitem(depth_engine.MODEL_CATALOG, "pretrained", spec)
    depth_engine.DepthEngine._cache.clear()

    engine = depth_engine.DepthEngine(model_id="pretrained", input_size=98, device="cpu")
    with pytest.raises(depth_engine.DepthModelError) as excinfo:
        engine.predict(np.zeros((32, 32, 3), dtype=np.uint8))

    message = str(excinfo.value).lower()
    assert "not found" in message
    assert "checkpoint" in message
    depth_engine.DepthEngine._cache.clear()


# =================================================== 2. segmentation checkpoint
def test_missing_segmentation_checkpoint_fails_explicitly(tmp_path):
    from backend.app.services.segmentation import (
        SegmentationModelUnavailable,
        SemanticSegmentationService,
    )

    service = SemanticSegmentationService(checkpoint_path=str(tmp_path / "absent_seg.pth"))
    assert service.is_available() is False
    assert service.checkpoint_info()["status"] == "unavailable"

    image_path = _write_image(tmp_path / "aerial.jpg")
    mask_path = tmp_path / "mask.png"
    overlay_path = tmp_path / "overlay.png"

    with pytest.raises(SegmentationModelUnavailable) as excinfo:
        service.segment_aerial_image(image_path, str(mask_path), str(overlay_path))

    assert excinfo.value.status == "unavailable"
    assert excinfo.value.reason == "checkpoint_missing"
    assert "random weights are never used" in str(excinfo.value)
    # No prediction artifact may exist when the model is unavailable.
    assert not mask_path.exists()
    assert not overlay_path.exists()


def test_segmentation_checkpoint_architecture_is_validated(tmp_path):
    from backend.app.services.segmentation import (
        SegmentationModelUnavailable,
        load_verified_model,
    )

    checkpoint = tmp_path / "foreign.pth"
    torch.save(
        {"architecture": "SegformerB4", "num_classes": 7, "model_state": {"x": torch.zeros(1)}},
        checkpoint,
    )
    with pytest.raises(SegmentationModelUnavailable) as excinfo:
        load_verified_model(str(checkpoint), num_classes=7, device=torch.device("cpu"))
    assert excinfo.value.reason == "architecture_mismatch"

    wrong_shapes = tmp_path / "wrong.pth"
    torch.save(
        {
            "architecture": "AerialSegmentationModel",
            "num_classes": 7,
            "model_state": {"backbone.0.weight": torch.zeros(2, 2)},
        },
        wrong_shapes,
    )
    with pytest.raises(SegmentationModelUnavailable) as excinfo:
        load_verified_model(str(wrong_shapes), num_classes=7, device=torch.device("cpu"))
    assert excinfo.value.reason == "state_dict_incompatible"


# ========================================================= 3. damage checkpoint
def test_missing_damage_checkpoint_fails_explicitly(tmp_path):
    from backend.app.services.damage_assessment import (
        DamageAssessmentService,
        DamageModelUnavailable,
    )

    service = DamageAssessmentService(checkpoint_path=str(tmp_path / "absent_damage.pth"))
    assert service.is_available() is False

    pre_path = _write_image(tmp_path / "pre.jpg", value=60)
    post_path = _write_image(tmp_path / "post.jpg", value=200)
    overlay_path = tmp_path / "damage_overlay.jpg"
    geojson_path = tmp_path / "damage.geojson"

    with pytest.raises(DamageModelUnavailable) as excinfo:
        service.assess_damage(
            pre_path, post_path, str(overlay_path), str(geojson_path)
        )

    assert excinfo.value.status == "unavailable"
    assert not overlay_path.exists()
    assert not geojson_path.exists()


# ================================================= 4. reconstruction input gate
def test_insufficient_reconstruction_input_creates_no_geometry(tmp_path):
    from backend.app.services.photogrammetry import (
        ReconstructionInputError,
        photogrammetry_service,
    )

    output = tmp_path / "cloud.ply"
    with pytest.raises(ReconstructionInputError):
        photogrammetry_service.reconstruct_3d_pointcloud([], str(output))
    assert not output.exists()

    single = _write_image(tmp_path / "single.jpg")
    with pytest.raises(ReconstructionInputError) as excinfo:
        photogrammetry_service.reconstruct_3d_pointcloud([single], str(output))
    assert "at least 2" in str(excinfo.value)
    assert not output.exists()


def test_missing_image_file_creates_no_geometry(tmp_path):
    from backend.app.services.photogrammetry import (
        ReconstructionInputError,
        photogrammetry_service,
    )

    real = _write_image(tmp_path / "real.jpg")
    output = tmp_path / "cloud.ply"
    with pytest.raises(ReconstructionInputError):
        photogrammetry_service.reconstruct_3d_pointcloud(
            [real, str(tmp_path / "ghost.jpg")], str(output)
        )
    assert not output.exists()


def test_no_colmap_backend_reports_unavailable_without_artifacts(tmp_path, monkeypatch):
    from backend.app.services import reconstruction as reconstruction_module
    from backend.app.services.photogrammetry import (
        ReconstructionUnavailable,
        photogrammetry_service,
    )

    monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", None)

    first = _write_image(tmp_path / "f1.jpg", value=40)
    second = _write_image(tmp_path / "f2.jpg", value=180)
    output = tmp_path / "cloud.ply"

    with pytest.raises(ReconstructionUnavailable) as excinfo:
        photogrammetry_service.reconstruct_3d_pointcloud(
            [first, second], str(output), str(tmp_path / "mesh.ply")
        )

    assert excinfo.value.status == "unavailable"
    assert "COLMAP" in str(excinfo.value)
    assert not output.exists()
    assert not (tmp_path / "mesh.ply").exists()


def test_colmap_command_validation_rejects_missing_executable(tmp_path):
    from backend.app.services.reconstruction import ColmapUnavailable, ReconstructionService

    service = ReconstructionService()
    service.colmap_exe = str(tmp_path / "not-colmap")
    with pytest.raises(ColmapUnavailable):
        service._require_colmap()


# ================================================ 5. reprojection error honesty
def test_reprojection_error_comes_only_from_colmap_output():
    from backend.app.services.reconstruction import _parse_model_analyzer

    output = "\n".join(
        [
            "Cameras: 1",
            "Images: 3",
            "Registered images: 3",
            "Points: 4211",
            "Mean reprojection error: 0.74321px",
        ]
    )
    stats = _parse_model_analyzer(output)
    assert stats["num_points"] == 4211
    assert stats["camera_count"] == 1
    assert stats["reprojection_error_px"] == pytest.approx(0.74321)

    # When COLMAP does not report an error, the value stays None (never a placeholder).
    missing = _parse_model_analyzer("Points: 10\nCameras: 1\n")
    assert missing["reprojection_error_px"] is None


def test_photogrammetry_source_contains_no_fabricated_geometry():
    source = (SERVICES_DIR / "photogrammetry.py").read_text(encoding="utf-8")

    for forbidden in (
        "np.sin",
        "np.cos",
        "np.random",
        "np.linspace",
        "0.68",  # former hardcoded reprojection error
        "local_elev",
        "Camera pose simulation",
    ):
        assert forbidden not in source, f"fabricated-geometry marker {forbidden!r} still present"

    segmentation = (SERVICES_DIR / "segmentation.py").read_text(encoding="utf-8")
    assert "np.random" not in segmentation
    assert "torch.randn" not in segmentation

    damage = (SERVICES_DIR / "damage_assessment.py").read_text(encoding="utf-8")
    assert "np.random" not in damage
    assert "torch.randn" not in damage


# ============================================================ 7. PLY validation
def test_inspect_ply_reads_a_valid_ascii_cloud(tmp_path):
    from backend.app.services.photogrammetry import inspect_ply

    path = tmp_path / "valid.ply"
    path.write_text(_ascii_ply(4), encoding="ascii")

    info = inspect_ply(str(path))
    assert info["num_vertices"] == 4
    assert info["bounds"]["min_x"] == 0.0
    assert info["bounds"]["max_x"] == 3.0
    assert info["bounds"]["max_z"] == 6.0


def test_inspect_ply_reads_a_valid_binary_cloud(tmp_path):
    from backend.app.services.photogrammetry import inspect_ply

    path = tmp_path / "binary.ply"
    path.write_bytes(_binary_ply([(0.0, 1.0, 2.0), (4.0, 5.0, 6.0)]))

    info = inspect_ply(str(path))
    assert info["num_vertices"] == 2
    assert info["bounds"]["min_y"] == 1.0
    assert info["bounds"]["max_y"] == 5.0


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"this is not a ply file",
        b"ply\nformat ascii 1.0\nend_header\n",
        b"ply\nformat ascii 1.0\nelement vertex 0\nend_header\n",
    ],
)
def test_inspect_ply_rejects_invalid_files(tmp_path, payload):
    from backend.app.services.photogrammetry import inspect_ply

    path = tmp_path / "invalid.ply"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        inspect_ply(str(path))


# ========================================================= 8. upload failures
def test_failed_upload_returns_error_and_stores_nothing(client):
    project_id = _create_project(client, "P0 Failed Upload Mission")
    before = client.get(f"/api/v1/projects/{project_id}/images")
    assert before.status_code == 200
    original_count = len(before.json())

    response = client.post(
        f"/api/v1/projects/{project_id}/images/upload",
        files=[("files", ("notes.txt", b"not an image at all", "text/plain"))],
    )
    assert response.status_code in (400, 422)

    after = client.get(f"/api/v1/projects/{project_id}/images")
    assert len(after.json()) == original_count
    assert all(image["filename"] != "notes.txt" for image in after.json())


# ============================================ API gating for unavailable models
def test_segmentation_endpoint_reports_unavailable_and_persists_nothing(
    client, tmp_path, monkeypatch
):
    from backend.app.services.segmentation import segmentation_service

    project_id = _create_project(client, "P0 Segmentation Gating")
    image_id = _upload(client, project_id, 1)[0]
    monkeypatch.setattr(segmentation_service, "_checkpoint_path", str(tmp_path / "none.pth"))

    response = client.post("/api/v1/analysis/segmentation", json={"image_id": image_id})
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "unavailable"
    assert detail["service"] == "semantic_segmentation"
    assert "checkpoint" in detail["message"].lower()

    assert client.get(f"/api/v1/analysis/segmentation/{image_id}").status_code == 404
    assert not os.path.exists(
        os.path.join(settings.PROCESSED_DIR, f"segmask_{image_id}.png")
    )
    assert not os.path.exists(
        os.path.join(settings.PROCESSED_DIR, f"segoverlay_{image_id}.png")
    )


def test_damage_endpoint_reports_unavailable_and_persists_nothing(
    client, tmp_path, monkeypatch
):
    from backend.app.services.damage_assessment import damage_service

    project_id = _create_project(client, "P0 Damage Gating")
    pre_id, post_id = _upload(client, project_id, 2)
    monkeypatch.setattr(damage_service, "_checkpoint_path", str(tmp_path / "none.pth"))

    response = client.post(
        "/api/v1/analysis/damage",
        json={"pre_image_id": pre_id, "post_image_id": post_id},
    )
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "unavailable"
    assert detail["service"] == "damage_assessment"

    assert client.get(f"/api/v1/analysis/damage/{pre_id}/{post_id}").status_code == 404
    assert not os.path.exists(
        os.path.join(settings.PROCESSED_DIR, f"damage_{post_id}.png")
    )


def test_reconstruction_endpoint_reports_unavailable_and_persists_nothing(
    client, monkeypatch
):
    from backend.app.services import reconstruction as reconstruction_module

    project_id = _create_project(client, "P0 Reconstruction Gating")
    image_ids = _upload(client, project_id, 2)
    monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", None)

    response = client.post(
        "/api/v1/reconstruction/3d",
        json={"project_id": project_id, "image_ids": image_ids},
    )
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "unavailable"
    assert "COLMAP" in detail["message"]

    # No reconstruction record and no PLY/DSM artifacts may be created.
    assert client.get(f"/api/v1/reconstruction/3d/{project_id}").status_code == 404
    assert not os.path.exists(
        os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project_id}.ply")
    )
    assert not os.path.exists(
        os.path.join(settings.RECONSTRUCTION_DIR, f"dsm_{project_id}.tif")
    )


def test_reconstruction_endpoint_rejects_single_image(client, monkeypatch):
    from backend.app.services import reconstruction as reconstruction_module

    project_id = _create_project(client, "P0 Single Image Gating")
    image_ids = _upload(client, project_id, 1)
    # Even with a COLMAP binary configured, one image cannot be reconstructed.
    monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", "colmap")

    response = client.post(
        "/api/v1/reconstruction/3d",
        json={"project_id": project_id, "image_ids": image_ids},
    )
    assert response.status_code == 400, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "invalid_input"
    assert "at least 2" in detail["message"].lower()
    assert not os.path.exists(
        os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project_id}.ply")
    )


def test_reconstruction_backend_status_endpoint(client):
    response = client.get("/api/v1/reconstruction/backend")
    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "colmap"
    assert payload["status"] in {"available", "unavailable"}
    assert payload["available"] is bool(payload["executable"])
