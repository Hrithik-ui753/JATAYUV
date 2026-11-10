<<<<<<< HEAD
"""Integration checks for the AI endpoints and 3D reconstruction (P0 integrity).

The platform no longer fabricates model output or geometry, so this test asserts the
integrity contract end to end:

* depth, segmentation and damage inference fail explicitly (503) when their verified
  checkpoint is absent, and persist neither records nor artifacts,
* 3D reconstruction reports the missing COLMAP backend instead of writing a fake PLY,
* genuinely model-free image processing (change detection) still completes.
"""

=======
<<<<<<< HEAD
import os
>>>>>>> origin/main
import io
import os

import cv2
import numpy as np
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import depth_engine

client = TestClient(app)

<<<<<<< HEAD

=======
=======
"""Integration checks for the AI endpoints and 3D reconstruction (P0 integrity).

The platform no longer fabricates model output or geometry, so this test asserts the
integrity contract end to end:

* depth, segmentation and damage inference fail explicitly (503) when their verified
  checkpoint is absent, and persist neither records nor artifacts,
* 3D reconstruction reports the missing COLMAP backend instead of writing a fake PLY,
* genuinely model-free image processing (change detection) still completes.
"""

import io
import os

import cv2
import numpy as np
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import depth_engine

client = TestClient(app)


>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
def create_aerial_image_pair():
    # Pre-disaster: Intact building
    img_pre = np.zeros((250, 250, 3), dtype=np.uint8)
    img_pre[:] = (34, 139, 34)  # vegetation
    cv2.rectangle(img_pre, (50, 50), (180, 180), (220, 220, 220), -1)  # intact roof
    cv2.rectangle(img_pre, (70, 70), (160, 160), (150, 75, 0), -1)

    # Post-disaster: Damaged roof with debris
    img_post = img_pre.copy()
    # Structural debris / holes
    cv2.rectangle(img_post, (80, 80), (150, 150), (30, 30, 30), -1)
    cv2.circle(img_post, (120, 120), 40, (10, 10, 10), -1)

    buf_pre = io.BytesIO()
    PILImage.fromarray(cv2.cvtColor(img_pre, cv2.COLOR_BGR2RGB)).save(buf_pre, format="JPEG")
    buf_pre.seek(0)

    buf_post = io.BytesIO()
    PILImage.fromarray(cv2.cvtColor(img_post, cv2.COLOR_BGR2RGB)).save(buf_post, format="JPEG")
    buf_post.seek(0)

    return buf_pre, buf_post

<<<<<<< HEAD
=======
<<<<<<< HEAD
def test_full_ai_inference_pipeline_and_photogrammetry():
=======
>>>>>>> origin/main

def _unavailable_resp(response):
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "unavailable"
    return detail


def test_ai_endpoints_fail_explicitly_and_change_detection_still_works(tmp_path, monkeypatch):
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    # 1. Setup project
    proj_resp = client.post(
        "/api/v1/projects",
        json={
<<<<<<< HEAD
            "name": "P0 Integrity Evaluation",
            "description": "Validates honest unavailability of AI services",
=======
<<<<<<< HEAD
            "name": "Disaster Response AI Evaluation",
            "description": "Validation test for depth, segmentation, damage and 3D",
=======
            "name": "P0 Integrity Evaluation",
            "description": "Validates honest unavailability of AI services",
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
            "location_name": "Disaster Sector A-1",
        },
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Upload Pre and Post image pair
    buf_pre, buf_post = create_aerial_image_pair()
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/images/upload",
        files=[
            ("files", ("flight_pre.jpg", buf_pre, "image/jpeg")),
            ("files", ("flight_post.jpg", buf_post, "image/jpeg")),
        ],
    )
    assert upload_resp.status_code == 201
    images = upload_resp.json()
    assert len(images) == 2
    pre_id = images[0]["id"]
    post_id = images[1]["id"]

<<<<<<< HEAD
    # 3. Depth: force a definitely-missing checkpoint, then require an explicit 503.
    import dataclasses
=======
<<<<<<< HEAD
    # 3. Monocular Depth Estimation
    depth_resp = client.post("/api/v1/analysis/depth", json={"image_id": pre_id})
    assert depth_resp.status_code == 200
    depth_data = depth_resp.json()
    assert os.path.exists(depth_data["depth_map_path"])
    assert os.path.exists(depth_data["colormap_path"])
    # Depth Anything V2 Small predicts RELATIVE inverse depth. The API must not
    # present it as metres: metric fields are null and the relative range is given
    # in normalised inverse-depth units instead.
    assert depth_data["depth_type"] == "relative"
    assert depth_data["depth_unit"] == "relative_inverse_depth"
    assert depth_data["is_metric"] is False
    assert depth_data["min_depth_m"] is None
    assert depth_data["max_depth_m"] is None
    assert depth_data["mean_depth_m"] is None
    assert 0.0 <= depth_data["relative_min"] <= depth_data["relative_max"] <= 1.0
    assert 0.0 < depth_data["relative_mean"] <= 1.0
    assert depth_data["model_id"] in {"pretrained", "jatayuv_drone_v1"}
    assert len(depth_data["checkpoint_sha256"]) == 64
    assert depth_data["inference_ms"] > 0
>>>>>>> origin/main

    missing_depth = str(tmp_path / "absent_depth.pth")
    spec = dataclasses.replace(
        depth_engine.MODEL_CATALOG["pretrained"], checkpoint=missing_depth
    )
    monkeypatch.setitem(depth_engine.MODEL_CATALOG, "pretrained", spec)
    depth_engine.DepthEngine._cache.clear()
    try:
        depth_resp = client.post(
            "/api/v1/analysis/depth", json={"image_id": pre_id, "model_id": "pretrained"}
        )
        detail = _unavailable_resp(depth_resp)
        assert "checkpoint" in detail["message"].lower()
        assert client.get(f"/api/v1/analysis/depth/{pre_id}").status_code == 404
        assert not os.path.exists(
            os.path.join(
                os.path.dirname(images[0]["file_path"]), "..", "processed", f"depth_{pre_id}.png"
            )
        )
    finally:
        depth_engine.DepthEngine._cache.clear()

    # 4. Segmentation: no verified checkpoint -> explicit 503, nothing persisted.
    from backend.app.services.segmentation import segmentation_service

    monkeypatch.setattr(segmentation_service, "_checkpoint_path", str(tmp_path / "none.pth"))
    seg_resp = client.post("/api/v1/analysis/segmentation", json={"image_id": pre_id})
    detail = _unavailable_resp(seg_resp)
    assert detail["service"] == "semantic_segmentation"
    assert client.get(f"/api/v1/analysis/segmentation/{pre_id}").status_code == 404

<<<<<<< HEAD
=======
    # 5. Building Damage Assessment (xBD)
=======
    # 3. Depth: force a definitely-missing checkpoint, then require an explicit 503.
    import dataclasses

    missing_depth = str(tmp_path / "absent_depth.pth")
    spec = dataclasses.replace(
        depth_engine.MODEL_CATALOG["pretrained"], checkpoint=missing_depth
    )
    monkeypatch.setitem(depth_engine.MODEL_CATALOG, "pretrained", spec)
    depth_engine.DepthEngine._cache.clear()
    try:
        depth_resp = client.post(
            "/api/v1/analysis/depth", json={"image_id": pre_id, "model_id": "pretrained"}
        )
        detail = _unavailable_resp(depth_resp)
        assert "checkpoint" in detail["message"].lower()
        assert client.get(f"/api/v1/analysis/depth/{pre_id}").status_code == 404
        assert not os.path.exists(
            os.path.join(
                os.path.dirname(images[0]["file_path"]), "..", "processed", f"depth_{pre_id}.png"
            )
        )
    finally:
        depth_engine.DepthEngine._cache.clear()

    # 4. Segmentation: no verified checkpoint -> explicit 503, nothing persisted.
    from backend.app.services.segmentation import segmentation_service

    monkeypatch.setattr(segmentation_service, "_checkpoint_path", str(tmp_path / "none.pth"))
    seg_resp = client.post("/api/v1/analysis/segmentation", json={"image_id": pre_id})
    detail = _unavailable_resp(seg_resp)
    assert detail["service"] == "semantic_segmentation"
    assert client.get(f"/api/v1/analysis/segmentation/{pre_id}").status_code == 404

>>>>>>> origin/main
    # 5. Damage: no verified checkpoint -> explicit 503, nothing persisted.
    from backend.app.services.damage_assessment import damage_service

    monkeypatch.setattr(damage_service, "_checkpoint_path", str(tmp_path / "none.pth"))
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    damage_resp = client.post(
        "/api/v1/analysis/damage",
        json={"pre_image_id": pre_id, "post_image_id": post_id},
    )
<<<<<<< HEAD
    detail = _unavailable_resp(damage_resp)
    assert detail["service"] == "damage_assessment"
    assert client.get(f"/api/v1/analysis/damage/{pre_id}/{post_id}").status_code == 404

    # 6. Change detection is genuine image processing (no learned weights) and completes.
=======
<<<<<<< HEAD
    assert damage_resp.status_code == 200
    damage_data = damage_resp.json()
    assert os.path.exists(damage_data["damage_overlay_path"])
    assert "no_damage" in damage_data["counts_by_level"]
    assert "destroyed" in damage_data["counts_by_level"]
    assert 0.0 <= damage_data["severity_index"] <= 1.0

    # 6. Bi-Temporal Change Detection
=======
    detail = _unavailable_resp(damage_resp)
    assert detail["service"] == "damage_assessment"
    assert client.get(f"/api/v1/analysis/damage/{pre_id}/{post_id}").status_code == 404

    # 6. Change detection is genuine image processing (no learned weights) and completes.
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    change_resp = client.post(
        "/api/v1/analysis/change",
        json={"before_image_id": pre_id, "after_image_id": post_id},
    )
    assert change_resp.status_code == 200
    change_data = change_resp.json()
    assert os.path.exists(change_data["diff_mask_path"])
    assert os.path.exists(change_data["heatmap_path"])
    assert change_data["changed_pixels"] > 0
    assert change_data["changed_area_pct"] > 0

<<<<<<< HEAD
=======
<<<<<<< HEAD
    # 7. Multi-Image 3D Photogrammetry
=======
>>>>>>> origin/main
    # 7. 3D reconstruction without COLMAP: explicit 503, no PLY and no record.
    from backend.app.services import reconstruction as reconstruction_module

    monkeypatch.setattr(reconstruction_module.reconstruction_service, "colmap_exe", None)
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    recon_resp = client.post(
        "/api/v1/reconstruction/3d",
        json={"project_id": project_id, "image_ids": [pre_id, post_id]},
    )
<<<<<<< HEAD
=======
<<<<<<< HEAD
    assert recon_resp.status_code == 200
    recon_data = recon_resp.json()
    assert os.path.exists(recon_data["pointcloud_ply_path"])
    assert recon_data["num_points"] > 0
    assert recon_data["reprojection_error_px"] < 1.0
    assert "min_x" in recon_data["bounds"]

=======
>>>>>>> origin/main
    detail = _unavailable_resp(recon_resp)
    assert "COLMAP" in detail["message"]
    assert client.get(f"/api/v1/reconstruction/3d/{project_id}").status_code == 404
    assert not os.path.exists(
        os.path.join(
            os.path.dirname(os.path.dirname(images[0]["file_path"])),
            "reconstructions",
            f"pointcloud_{project_id}.ply",
        )
    )
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
