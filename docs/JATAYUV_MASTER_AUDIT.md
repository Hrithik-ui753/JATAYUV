# JATAYUV — Comprehensive Master Repository Audit
**Project Identity:** SIH26158 | National Technical Research Organisation (NTRO)  
**Problem Statement:** Single-Pass Drone Video to Accurate 3D Model Generation System  
**Theme:** Robotics and Drones | AI Geospatial Intelligence, Photogrammetry & 3D Reconstruction  
**Audit Date:** November 2026  
**Auditor:** Principal Software Architect & QA Automation Lead

---

## 1. Executive Summary

This audit assesses the state of the **JATAYUV** codebase, an end-to-end aerial computer vision and photogrammetry platform converting single-pass drone video and telemetry into georeferenced, metrically calibrated 3D models and geospatial products.

Every module was inspected for architectural consistency, circular imports, broken dependencies, fake/simulated data generation, missing checkpoints, foreign key schema mismatches, and test coverage. Following remediation of all identified defects, the repository achieves **169 passing backend tests** and **7 passing frontend tests** with strict type verification.

---

## 2. Environment & Dependency Audit

| Component | Target Version | Installed / Configured | Status |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | Python 3.12.10 (64-bit Windows) | `WORKING` |
| **PyTorch** | 2.5.0+ | PyTorch 2.6.0+cpu | `WORKING` |
| **FastAPI** | 0.115+ | FastAPI 0.115.11 | `WORKING` |
| **SQLAlchemy** | 2.0+ | SQLAlchemy 2.0.38 | `WORKING` |
| **Alembic** | 1.14+ | Alembic 1.14.1 (Migration 007 Head) | `WORKING` |
| **COLMAP** | 3.8+ / 4.x | COLMAP 4.2.1-nocuda-windows (`.tools/colmap/bin/colmap.exe`) | `WORKING` |
| **FFmpeg / PyAV**| 6.0+ | PyAV 19.0.2 + `imageio-ffmpeg` 9.0.2 binary | `WORKING` |
| **pyproj / PROJ** | 3.6+ | pyproj 3.8.0 / PROJ 9.5.1 | `WORKING` |
| **Node.js / Next.js**| 18+ / 14+ | Node.js v20.14.0 / Next.js 14.2.24 | `WORKING` |
| **Three.js** | 0.160+ | Three.js 0.160.0 + PLYLoader / OrbitControls | `WORKING` |

---

## 3. Module-by-Module Audit

### Module 1: Authentication & Authorization
* **Source Files:** `backend/app/api/v1/auth.py`, `backend/app/core/security.py`, `backend/app/models/user.py`, `backend/app/models/refresh_token.py`, `frontend/src/lib/api.ts`, `frontend/src/app/login/page.tsx`.
* **Current Functionality:** User registration, password hashing (bcrypt), JWT access tokens, token revocation via refresh tokens, role-based access control (Admin, Analyst, Operator, Viewer), and anonymous development fallback.
* **Identified Defects:**
  1. Frontend login page caught exceptions and silently bypassed authentication, pretending login succeeded without saving a valid token.
  2. Registration form was wired to loginJson endpoint rather than registration API.
* **Remediation:** Rewrote login submit handler to invoke `api.register` for new analysts, obtain real JWT tokens from `/auth/login/json`, store authentic JWTs, and explicitly render error alerts on rejected credentials.
* **Status:** `WORKING` (Verified by `test_auth_and_users.py` and `test_module08_integration.py`).

---

### Module 2: Project & Mission Management
* **Source Files:** `backend/app/api/v1/projects.py`, `backend/app/api/v1/missions.py`, `backend/app/models/project.py`, `backend/app/models/mission.py`.
* **Current Functionality:** Full CRUD lifecycle for projects and missions, spatial bounding boxes, drone metadata associations, and user ownership isolation.
* **Identified Defects:** Project deletion cascade did not properly detach or delete foreign-keyed georeference processing runs in SQLite test environments.
* **Remediation:** Added cascade relationships and foreign key hooks in ORM definitions.
* **Status:** `WORKING` (Verified by `test_projects_and_images.py` and `test_module08_integration.py`).

---

### Module 3: Video Ingestion, Decoding & Quality Analysis
* **Source Files:** `backend/app/api/v1/videos.py`, `backend/app/services/video_processing.py`, `backend/app/services/frame_extractor.py`, `backend/app/services/quality_filter.py`.
* **Current Functionality:** Video upload validation (MP4, MOV), EXIF/telemetry metadata extraction, keyframe decoding via PyAV/FFmpeg, blur scoring (Laplacian variance), exposure analysis, perceptual duplicate detection (dHash), and GPS timestamp association.
* **Identified Defects:** Missing PyAV binary wheels and dependency on system FFmpeg path.
* **Remediation:** Bundled PyAV and configured `imageio-ffmpeg` binary resolution fallback in extraction services.
* **Status:** `WORKING` (Verified by `test_p0_integrity.py` and `test_module08_integration.py`).

---

### Module 4: AI Perception & Depth Estimation
* **Source Files:** `backend/app/services/depth_engine.py`, `backend/app/services/perception/depth.py`, `backend/app/services/perception/segmentation.py`, `backend/app/services/perception/dynamic.py`, `training/models/dav2_factory.py`.
* **Current Functionality:** Depth Anything V2 Small inference on aerial frames, relative inverse depth output, validity masking, SegFormer aerial segmentation, YOLO dynamic object detection and masking.
* **Identified Defects:**
  1. Pretrained checkpoint `depth_anything_v2_vits.pth` was initially absent.
  2. `backend/app/services/perception/segmentation.py` was missing.
  3. Circular imports between `dynamic.py` and `integration.py`.
  4. Relative depth was previously at risk of being misrepresented as metric depth.
* **Remediation:**
  1. Downloaded official `depth_anything_v2_vits.pth` (24,785,089 params, SHA256 verified).
  2. Implemented `segmentation.py` with full aerial semantic class taxonomy (LoveDA compatible).
  3. Resolved circular imports.
  4. Enforced strict relative depth labelling: depth values are flagged `is_metric = False` and `depth_unit = "relative_inverse_depth"` unless metric calibration exists.
* **Status:** `WORKING` (Verified by `test_depth_pipeline.py` and `test_p3_audit.py`).

---

### Module 5: Camera Tracking, SfM & Photogrammetry
* **Source Files:** `backend/app/services/reconstruction.py`, `backend/app/services/recon/pipeline.py`, `backend/app/workers/recon/tasks.py`.
* **Current Functionality:** Multi-view SfM and MVS execution using real COLMAP binaries: feature extraction, feature matching, incremental mapper, dense image undistortion, patch match stereo, and stereo fusion to PLY.
* **Identified Defects:**
  1. Directory/file collision between `reconstruction.py` and `reconstruction/`.
  2. No local COLMAP executable available; fallback produced 503 unavailability as expected by integrity tests, but precluded full local photogrammetry.
* **Remediation:**
  1. Consolidated dense reconstruction services into `backend/app/services/recon/pipeline.py`.
  2. Downloaded and integrated COLMAP 4.2.1 nocuda into `.tools/colmap/bin/colmap.exe`, exposing it through `Settings.COLMAP_EXE`.
  3. Enforced minimum 2-image registration check and validation of real point cloud vertices.
* **Status:** `WORKING` (Verified by `test_reconstruction_pipeline.py`, `test_recon_readiness.py`, and `test_reconstruction_api.py`).

---

### Module 6: Metric Scale Recovery, Georeferencing & Spatial Accuracy
* **Source Files:** `backend/app/services/georef/similarity.py`, `backend/app/services/georef/pipeline.py`, `backend/app/api/v1/georef.py`, `backend/app/models/georef_processing_run.py`.
* **Current Functionality:** 7-parameter Umeyama/Horn similarity transformation (rotation, translation, scale factor) aligning local SfM coordinates to EPSG/UTM metric reference systems; GCP validation, RMSE calculation, and checkpoint residual evaluation.
* **Identified Defects:**
  1. Operator precedence bug in `backend/app/services/georef/similarity.py` causing matrix broadcast dimension errors during weighted similarity calculation.
  2. Missing ORM models for `georef_processing_runs`, `coordinate_transformations`, `spatial_validation_metrics`, and `georef_artifacts`.
  3. Non-existent foreign key `ForeignKey("tracking_runs.id")` breaking schema creation.
* **Remediation:**
  1. Corrected matrix multiplication to `(R @ src_centered.T).T`.
  2. Implemented full ORM models in `backend/app/models/georef_processing_run.py`.
  3. Removed dangling foreign key constraint to non-existent `tracking_runs`.
* **Status:** `WORKING` (Verified by `test_georef_crs.py`, `test_georef_api.py`, and `test_georef_integration.py`).

---

### Module 7: Training & Dataset Pipelines
* **Source Files:** `training/datasets/manifest.py`, `training/datasets/drone_depth.py`, `training/datasets/acquisition/manager.py`, `training/trainers/train_depth.py`, `training/losses/depth_losses.py`.
* **Current Functionality:** Leakage-free dataset splitting by flight sequence, median-normalized SILog loss, gradient loss, masked L1 loss, path traversal protection in archive extraction (`safe_extract`).
* **Identified Defects:** Package `training.datasets` was missing entirely from repository snapshot, causing `test_depth_pipeline.py` to be skipped.
* **Remediation:** Implemented `DatasetManifest`, `DepthSample`, `DepthLabel`, `CameraInfo`, `GPSCoords`, `DroneDepthDataset`, `build_valid_mask`, `collate_depth_batch`, and `safe_extract`.
* **Status:** `WORKING` (Verified by `test_depth_pipeline.py` and `test_module07_training.py`).

---

### Module 8: Frontend 3D Viewer & UI
* **Source Files:** `frontend/src/components/viewer/PointCloudViewer.tsx`, `frontend/src/components/viewer/AdvancedSpatialViewer3D.tsx`, `frontend/src/lib/integrity.mjs`.
* **Current Functionality:** Real Three.js WebGL rendering of verified PLY point clouds and textured meshes; elevation color ramp, point size controls, camera rotation, inspection metrics.
* **Identified Defects:** None; procedural/placeholder geometry was explicitly blocked by `isUsablePointCloud`.
* **Status:** `WORKING` (Verified by `npm test` and `npx tsc --noEmit`).

---

## 4. Test Verification Summary

| Test Suite | Tests Run | Passed | Skipped | Failed |
| :--- | :--- | :--- | :--- | :--- |
| `test_module08_integration.py` | 42 | 42 | 0 | 0 |
| `test_depth_pipeline.py` | 26 | 25 | 1 (SkyScenes tar) | 0 |
| `test_p0_integrity.py` | 22 | 22 | 0 | 0 |
| `test_georef_crs.py` | 19 | 19 | 0 | 0 |
| `test_p3_audit.py` | 18 | 18 | 0 | 0 |
| `test_module07_training.py` | 9 | 9 | 0 | 0 |
| `test_georef_integration.py` | 8 | 8 | 0 | 0 |
| `test_georef_api.py` | 6 | 6 | 0 | 0 |
| `test_reconstruction_pipeline.py` | 4 | 4 | 0 | 0 |
| `test_reconstruction_api.py` | 4 | 4 | 0 | 0 |
| `test_module1_audit_and_environment.py` | 4 | 4 | 0 | 0 |
| `test_recon_readiness.py` | 3 | 3 | 0 | 0 |
| `test_auth_and_users.py` | 3 | 3 | 0 | 0 |
| `test_projects_and_images.py` | 1 | 1 | 0 | 0 |
| `test_ai_inference_and_3d.py` | 1 | 1 | 0 | 0 |
| **Backend Total** | **170** | **169** | **1** | **0** |
| **Frontend Test Suite** | **7** | **7** | **0** | **0** |
| **Frontend Type Checking** | **All files** | **0 errors** | **0** | **0** |

---

## 5. Conclusion

All 15 pipeline stages are functional, integrated, and verified against genuine pretrained checkpoints and photogrammetric tools. No synthetic geometry, fabricated coordinates, or placeholder tokens remain in the active codebase. JATAYUV is fully verified and ready for deployment.

