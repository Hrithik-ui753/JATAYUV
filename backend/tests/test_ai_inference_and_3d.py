import os
import io
import pytest
import numpy as np
import cv2
from PIL import Image as PILImage
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

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

def test_full_ai_inference_pipeline_and_photogrammetry():
    # 1. Setup project
    proj_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "Disaster Response AI Evaluation",
            "description": "Validation test for depth, segmentation, damage and 3D",
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

    # 4. Semantic Segmentation
    seg_resp = client.post("/api/v1/analysis/segmentation", json={"image_id": pre_id})
    assert seg_resp.status_code == 200
    seg_data = seg_resp.json()
    assert os.path.exists(seg_data["mask_path"])
    assert os.path.exists(seg_data["overlay_path"])
    assert isinstance(seg_data["class_distribution"], dict)
    assert "building" in seg_data["class_distribution"]

    # 5. Building Damage Assessment (xBD)
    damage_resp = client.post(
        "/api/v1/analysis/damage",
        json={"pre_image_id": pre_id, "post_image_id": post_id},
    )
    assert damage_resp.status_code == 200
    damage_data = damage_resp.json()
    assert os.path.exists(damage_data["damage_overlay_path"])
    assert "no_damage" in damage_data["counts_by_level"]
    assert "destroyed" in damage_data["counts_by_level"]
    assert 0.0 <= damage_data["severity_index"] <= 1.0

    # 6. Bi-Temporal Change Detection
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

    # 7. Multi-Image 3D Photogrammetry
    recon_resp = client.post(
        "/api/v1/reconstruction/3d",
        json={"project_id": project_id, "image_ids": [pre_id, post_id]},
    )
    assert recon_resp.status_code == 200
    recon_data = recon_resp.json()
    assert os.path.exists(recon_data["pointcloud_ply_path"])
    assert recon_data["num_points"] > 0
    assert recon_data["reprojection_error_px"] < 1.0
    assert "min_x" in recon_data["bounds"]

