import os
import io
import pytest
import numpy as np
import cv2
from PIL import Image as PILImage
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_sample_aerial_image_bytes():
    # Create synthetic 200x200 aerial pattern image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    # Background grass
    img[:] = (34, 139, 34)
    # Building rooftop
    cv2.rectangle(img, (40, 40), (140, 140), (180, 50, 50), -1)
    # Road
    cv2.rectangle(img, (0, 160), (200, 190), (128, 128, 128), -1)

    pil_img = PILImage.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf

def test_project_crud_and_image_upload():
    # 1. Create project
    proj_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "Integration Test Survey Alpha",
            "description": "Validation test mission for image ingestion and EXIF",
            "location_name": "Test Sector Grid 7",
            "center_lat": 17.3850,
            "center_lon": 78.4867,
        },
    )
    assert proj_resp.status_code == 201
    project = proj_resp.json()
    project_id = project["id"]
    assert project["name"] == "Integration Test Survey Alpha"

    # 2. List projects
    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    all_projects = list_resp.json()
    assert any(p["id"] == project_id for p in all_projects)

    # 3. Upload Aerial Image
    img_bytes = create_sample_aerial_image_bytes()
    upload_resp = client.post(
        f"/api/v1/projects/{project_id}/images/upload",
        files=[("files", ("survey_flight_01.jpg", img_bytes, "image/jpeg"))],
    )
    assert upload_resp.status_code == 201
    uploaded_images = upload_resp.json()
    assert len(uploaded_images) == 1
    image_record = uploaded_images[0]
    assert image_record["filename"] == "survey_flight_01.jpg"
    assert os.path.exists(image_record["file_path"])
    assert os.path.exists(image_record["thumbnail_path"])
    image_id = image_record["id"]

    # 4. Preprocess Image
    prep_resp = client.post(f"/api/v1/images/{image_id}/preprocess")
    assert prep_resp.status_code == 200
    prepped = prep_resp.json()
    assert prepped["is_preprocessed"] is True
    assert os.path.exists(prepped["preprocessed_path"])

