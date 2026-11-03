# JATAYUV-AI: API Architecture & Endpoint Specification

**Document Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Protocol:** HTTP/1.1 and HTTP/2 (TLS termination in production)  
**Content-Type:** `application/json` (except multipart file uploads)  

---

## 1. API Design Principles & Conventions

- **RESTful Resource Hierarchy**: Resource collections and sub-resources follow standard pluralized conventions (`/projects/{id}/images`).
- **Strict Typing**: All request and response bodies are validated using Pydantic v2 schemas.
- **Uniform Error Envelope**: Errors follow the RFC 7807 problem details pattern with `detail` and optional error codes.
- **Stateless Authentication**: Protected endpoints require `Authorization: Bearer <JWT_ACCESS_TOKEN>`.
- **CORS Handling**: Whitelisted origins with preflight `OPTIONS` handling.

---

## 2. Global Error Format

```json
{
  "detail": "Error description string explaining the failure condition."
}
```

| HTTP Status Code | Condition |
| :--- | :--- |
| `200 OK` | Request succeeded; response contains requested data. |
| `201 Created` | Resource successfully created (User, Project, Image). |
| `202 Accepted` | Background asynchronous task enqueued (Celery job). |
| `400 Bad Request` | Invalid input payload, missing required parameters, or duplicate entity. |
| `401 Unauthorized` | Missing, expired, or invalid JWT bearer token. |
| `403 Forbidden` | Authenticated user lacks permission to access or modify resource. |
| `404 Not Found` | Requested project, image, or analysis result does not exist. |
| `422 Unprocessable Entity` | Pydantic schema validation error on input JSON fields. |
| `500 Internal Server Error` | Unhandled server exception with structured error logging. |

---

## 3. Detailed Endpoint Directory

### 3.1 Authentication & Profile (`/auth`)

#### `POST /auth/register`
Creates a new analyst or admin user account.
- **Request Body**:
  ```json
  {
    "email": "analyst@jatayuv.ai",
    "password": "SecurePassword123!",
    "full_name": "Dr. Rajesh Rao",
    "role": "analyst"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "id": "c7a8e2b1-4f93-4a11-8e02-9988224411aa",
    "email": "analyst@jatayuv.ai",
    "full_name": "Dr. Rajesh Rao",
    "role": "analyst",
    "is_active": true,
    "created_at": "2026-11-03T10:15:00Z",
    "updated_at": "2026-11-03T10:15:00Z"
  }
  ```

#### `POST /auth/login` (OAuth2 Form) / `POST /auth/login/json`
Authenticates credentials and returns a signed JWT access token.
- **Request Body (JSON)**:
  ```json
  {
    "email": "analyst@jatayuv.ai",
    "password": "SecurePassword123!"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### `GET /auth/me`
Retrieves profile of currently authenticated user.
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Response `200 OK`**: `UserResponse`

---

### 3.2 Projects & Mission Workspaces (`/projects`)

#### `GET /projects`
Retrieves all survey mission projects accessible to the current user.
- **Response `200 OK`**: Array of `ProjectResponse` objects including `image_count`.

#### `POST /projects`
Creates a new aerial survey project.
- **Request Body**:
  ```json
  {
    "name": "Coastal Sector 4 Post-Storm Survey",
    "description": "Multi-temporal drone photogrammetry and damage assessment.",
    "location_name": "Bhubaneswar Coastal Region",
    "center_lat": 19.8135,
    "center_lon": 85.8312
  }
  ```
- **Response `201 Created`**: `ProjectResponse`

#### `GET /projects/{id}`
Retrieves project details, coordinates, and total ingested image count.

#### `PUT /projects/{id}`
Updates project metadata (name, description, location coordinates).

#### `DELETE /projects/{id}`
Deletes project and cascades deletion of associated images and analysis results.

---

### 3.3 Imagery Ingestion & Preprocessing (`/projects/{id}/images` & `/images`)

#### `GET /projects/{project_id}/images`
Lists all images ingested in the project with parsed EXIF telemetry.

#### `POST /projects/{project_id}/images/upload`
Uploads raw aerial drone images (supports batch multipart form data).
- **Request**: `multipart/form-data`, field `files`: `[binary, ...]`
- **Response `201 Created`**:
  ```json
  [
    {
      "id": "img-001",
      "project_id": "proj-01",
      "filename": "DJI_0492.JPG",
      "file_path": "/storage/uploads/img-001_DJI_0492.JPG",
      "thumbnail_path": "/storage/processed/thumb_img-001_DJI_0492.JPG",
      "file_size_bytes": 12450800,
      "width": 4000,
      "height": 3000,
      "format": "JPEG",
      "is_preprocessed": false,
      "telemetry": {
        "camera_make": "DJI",
        "camera_model": "FC330 (Mavic 3E)",
        "focal_length_mm": 24.0,
        "altitude_m": 120.4,
        "latitude": 19.81354,
        "longitude": 85.83121,
        "heading_deg": 182.5,
        "capture_time": "2026-11-02 14:22:10"
      },
      "created_at": "2026-11-03T10:20:00Z"
    }
  ]
  ```

#### `POST /images/{image_id}/preprocess`
Executes CLAHE contrast equalization, bilateral denoising, and unsharp masking.
- **Response `200 OK`**: Updated `ImageResponse` with `is_preprocessed=true`.

---

### 3.4 AI Analysis Services (`/analysis`)

#### `POST /analysis/depth`
Triggers monocular depth estimation on single aerial image.
- **Request Body**: `{"image_id": "img-001"}`
- **Response `200 OK`**:
  ```json
  {
    "id": "depth-01",
    "job_id": "job-01",
    "image_id": "img-001",
    "depth_map_path": "/storage/processed/depth_img-001.png",
    "colormap_path": "/storage/processed/colormap_img-001.png",
    "min_depth_m": 2.8,
    "max_depth_m": 98.4,
    "mean_depth_m": 42.1,
    "mesh_obj_path": "/storage/processed/mesh_img-001.obj",
    "created_at": "2026-11-03T10:25:00Z"
  }
  ```

#### `POST /analysis/segmentation`
Triggers 7-class aerial semantic segmentation.
- **Request Body**: `{"image_id": "img-001"}`
- **Response `200 OK`**:
  ```json
  {
    "id": "seg-01",
    "job_id": "job-02",
    "image_id": "img-001",
    "mask_path": "/storage/processed/segmask_img-001.png",
    "overlay_path": "/storage/processed/segoverlay_img-001.png",
    "class_distribution": {
      "building": 28.4,
      "vegetation": 34.1,
      "road": 16.5,
      "water": 8.2,
      "soil": 9.8,
      "vehicle": 3.0
    },
    "geojson_path": "/storage/processed/buildings_img-001.geojson",
    "created_at": "2026-11-03T10:26:00Z"
  }
  ```

#### `POST /analysis/damage`
Executes xBD humanitarian building damage assessment on Pre- and Post-disaster images.
- **Request Body**:
  ```json
  {
    "pre_image_id": "img-001",
    "post_image_id": "img-002"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "id": "dmg-01",
    "job_id": "job-03",
    "pre_image_id": "img-001",
    "post_image_id": "img-002",
    "damage_overlay_path": "/storage/processed/damage_img-002.png",
    "total_buildings": 342,
    "counts_by_level": {
      "no_damage": 184,
      "minor_damage": 76,
      "major_damage": 54,
      "destroyed": 28
    },
    "damage_percentage": 46.2,
    "severity_index": 0.48,
    "geojson_path": "/storage/processed/damage_img-002.geojson",
    "created_at": "2026-11-03T10:27:00Z"
  }
  ```

#### `POST /analysis/change`
Executes bi-temporal change detection and generates diff mask and heatmap.
- **Request Body**:
  ```json
  {
    "before_image_id": "img-001",
    "after_image_id": "img-002"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "id": "chg-01",
    "job_id": "job-04",
    "before_image_id": "img-001",
    "after_image_id": "img-002",
    "diff_mask_path": "/storage/processed/diffmask_img-002.png",
    "heatmap_path": "/storage/processed/diffheat_img-002.png",
    "changed_area_pct": 14.8,
    "changed_pixels": 1776000,
    "significance_score": 0.62,
    "created_at": "2026-11-03T10:28:00Z"
  }
  ```

---

### 3.5 3D Photogrammetry & Reconstruction (`/reconstruction`)

#### `POST /reconstruction/3d`
Triggers multi-image Structure-from-Motion (SfM) point cloud reconstruction.
- **Request Body**:
  ```json
  {
    "project_id": "proj-01",
    "image_ids": ["img-001", "img-002", "img-003"]
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "id": "recon-01",
    "project_id": "proj-01",
    "job_id": "job-05",
    "pointcloud_ply_path": "/storage/reconstructions/pointcloud_proj-01.ply",
    "mesh_obj_path": "/storage/reconstructions/mesh_proj-01.obj",
    "dsm_tiff_path": "/storage/reconstructions/dsm_proj-01.tif",
    "num_points": 48200,
    "camera_count": 3,
    "reprojection_error_px": 0.68,
    "bounds": {
      "min_x": -10.5, "max_x": 18.2,
      "min_y": 0.0, "max_y": 7.4,
      "min_z": -8.1, "max_z": 15.6
    },
    "created_at": "2026-11-03T10:30:00Z"
  }
  ```

#### `GET /reconstruction/3d/{project_id}`
Retrieves existing 3D reconstruction model, point cloud path, and bounding box.
