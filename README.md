# JATAYUV — Single-Pass Drone Video to Georeferenced 3D Model Generation System

[![SIH26158](https://img.shields.io/badge/SIH-26158-orange.svg)](https://www.sih.gov.in/)
[![Organization: NTRO](https://img.shields.io/badge/Organization-NTRO-003366.svg)]()
[![Theme: Robotics and Drones](https://img.shields.io/badge/Theme-Robotics%20%26%20Drones-darkgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C.svg)](https://pytorch.org/)
[![COLMAP](https://img.shields.io/badge/COLMAP-4.2.1-blue.svg)](https://colmap.github.io/)
[![Three.js](https://img.shields.io/badge/Three.js-0.165-black.svg)](https://threejs.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()

> **Problem Statement ID:** SIH26158  
> **Problem Statement Title:** Single-Pass Drone Video to Accurate 3D Model Generation System  
> **Organization:** National Technical Research Organisation (NTRO)  
> **Theme:** Robotics and Drones  
> **Application Type:** AI-Powered Geospatial Intelligence, Photogrammetry, Computer Vision and 3D Reconstruction Platform  

---

## 1. Executive Overview

**JATAYUV** is an integrated geospatial intelligence and photogrammetry platform engineered to ingest continuous **single-pass drone video streams** (MP4/MOV/AVI/MKV/WebM) accompanied by onboard flight telemetry (GPS/IMU logs in CSV/SRT/GPX) and reconstruct metrically meaningful, georeferenced 3D digital twins.

Traditional photogrammetric systems mandate multi-pass grid patterns with 80%+ cross-track overlap, rendering them unsuitable for rapid disaster response or hostile border surveillance. JATAYUV solves this operational bottleneck by fusing deep aerial monocular perception with Structure-from-Motion (SfM), multi-view stereo (MVS), and closed-form similarity georeferencing.

The platform provides a mission-control web interface (Next.js 14 + Three.js) for video ingestion, flight telemetry inspection, automated processing dispatch, interactive 3D point cloud exploration with hypsometric elevation tinting, and geospatial artifact export.

---

## 2. Verified Implementation Status

JATAYUV has completed an exhaustive codebase audit, architectural repair, and multi-tier verification process:

1. **Official Pretrained Depth Checkpoint Verified**:
   - Official **Depth Anything V2 Small** checkpoint (`depth_anything_v2_vits.pth`, 99,218,434 bytes, SHA-256 `715fade13be8...`) downloaded and strictly verified across all 24,785,089 parameters.
2. **Relative Inverse Depth Enforced**:
   - Depth predictions are strictly typed as `relative_inverse_depth` with `is_metric = False`. The platform never claims metric meter depth without an explicit physical ground calibration.
3. **Genuine COLMAP 4.2.1 Integration**:
   - Integrated the official COLMAP 4.2.1 no-CUDA binary at `.tools/colmap/bin/colmap.exe` for sequential image matching, incremental bundle adjustment, and dense PatchMatch stereo fusion.
4. **Zero Procedural / Dummy Geometry Fallbacks**:
   - Purged all synthetic cubes, procedural spheres, and mock geometry generators. If photogrammetry dependencies are missing, the system returns an honest HTTP 503 rather than fabricated reconstructions.
5. **Database Schema & Alembic Migrations Repaired**:
   - Replaced fragmented schema states with cohesive Alembic migrations (revisions `000` through `007` head). Cleaned all duplicate index declarations across SQLite and PostgreSQL targets.
6. **Drone Depth Dataset Architecture**:
   - Implemented `training.datasets.manifest`, PyTorch `DroneDepthDataset`, dynamic batch collation, and safe zip/tar archive extractors for robust aerial model training.
7. **Repaired Georeferencing & CRS Projection**:
   - Repaired the 7-parameter Umeyama/Horn Procrustes similarity transformation matrix operator precedence. Integrated `pyproj` for WGS84 (EPSG:4326) to Cartesian metric UTM projection.
8. **Cryptographic JWT Authentication**:
   - Enforced genuine cryptographic JWT token validation with signature verification across all protected endpoints. Silent demo session bypasses are completely eliminated.
9. **Interactive Three.js 3D PLY Viewer**:
   - Implemented an interactive WebGL point cloud viewer with OrbitControls, particle point-size sliders, camera reset, and hypsometric elevation heatmaps.

---

## 3. Verified Test Results

All verification suites have been executed and passed:

| Verification Suite | Test Target | Executed | Passed | Skipped | Failed |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Backend Pytest** | Architecture, Endpoints, Video Ingest, Depth Pipeline, Losses, P0 Data Integrity, Georeferencing, Models | 170 | **169** | 1* | **0** |
| **Frontend Tests** | Video Ingestion Hub, Dashboard, 3D Viewer Components | 7 | **7** | 0 | **0** |
| **TypeScript Compilation** | Full Frontend (`npx tsc --noEmit`) | Full | **0 Errors** | 0 | **0** |
| **Total Automated Tests** | End-to-End Application Integrity | **177** | **176** | **1** | **0** |

*\*Note: The single skipped backend test requires the multi-gigabyte raw SkyScenes archive, which is intentionally not bundled in the source repository.*

---

## 4. End-to-End Pipeline Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                    INPUT: SINGLE-PASS DRONE VIDEO                                  |
|                         (4K/1080p MP4/MOV) + Flight Telemetry Log (CSV/SRT/GPX)                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. VIDEO INGESTION & STORAGE                                                                       |
|    • Multipart chunked upload (POST /api/v1/missions/{id}/videos/upload)                           |
|    • Container inspection via PyAV/FFprobe (fps, codec, duration, frame count)                     |
|    • Atomic SHA-256 integrity checksum & storage persistence                                      |
+----------------------------------------------------------------------------------------------------+
                         │                                                 │
                         ▼                                                 ▼
+---------------------------------------------------+     +------------------------------------------+
| 2. QUALITY ANALYSIS & FRAME SELECTION             |     | 3. TELEMETRY & GPS SYNCHRONIZATION       |
|    • Sub-second stream demuxing with PTS          |     |    • Temporal interpolation (dt ≤ 1.0s)  |
|    • Laplacian variance blur scoring              |     |    • WGS84 geodetic coordinate mapping   |
|    • Perceptual dHash redundancy filtering        |     |    • Camera altitude & gimbal pitch/roll |
+---------------------------------------------------+     +------------------------------------------+
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. DEEP AERIAL PERCEPTION (PyTorch)                                                                |
|    • Monocular Relative Depth: Depth Anything V2 Small (DINOv2 ViT-S/14, 24.78M parameters)        |
|    • Land-Cover Classification: SegFormer (8-class aerial taxonomy: buildings, roads, vegetation)  |
|    • Dynamic Object Exclusion: YOLO vehicle & personnel masks (prevents ghosting artifacts)        |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. PHOTOGRAMMETRY & MULTI-VIEW STEREO (COLMAP 4.2.1)                                               |
|    • SIFT feature detection & sequential pairwise correspondence matching                          |
|    • Incremental bundle adjustment mapper (sparse camera poses + 3D tie points)                    |
|    • Lens radial distortion rectification & dense PatchMatch MVS depth estimation                  |
|    • Dense stereo fusion generating validated .ply point clouds                                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. METRIC SCALE RECOVERY & GEOREFERENCING (pyproj + Umeyama)                                       |
|    • 7-DoF similarity transformation: [sR | t] aligning SfM coordinates to metric UTM reference   |
|    • Ground Control Point (GCP) alignment & independent checkpoint RMSE validation                 |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 7. 3D VISUALIZATION & SPATIAL EXPORT (Three.js / WebGL)                                            |
|    • Interactive point cloud rendering with hypsometric elevation tinting & OrbitControls          |
|    • Mesh generation (Poisson reconstruction) & export formats (PLY, OBJ, GeoTIFF elevation)       |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide React, Three.js (`PLYLoader`, `OrbitControls`), Axios.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL / SQLite.
- **Asynchronous Workers**: Celery, Redis, PyAV / FFmpeg.
- **Computer Vision & AI**: PyTorch, Torchvision, Depth Anything V2 Small (DINOv2 ViT-S/14), SegFormer, OpenCV, NumPy, SciPy.
- **Photogrammetry & GIS**: COLMAP 4.2.1 (no-CUDA x64), `pyproj`, `shapely`, `open3d`.

---

## 6. Repository Layout

```
JATAYUV/
├── .tools/
│   └── colmap/                  # Official COLMAP 4.2.1 no-CUDA binary
├── backend/
│   ├── alembic/                 # Database migration scripts (000_initial to 007_head)
│   ├── app/
│   │   ├── api/v1/              # REST Endpoints (Auth, Videos, Missions, 3D, Perception)
│   │   ├── core/                # App configuration, security, database sessions
│   │   ├── models/              # SQLAlchemy models (User, Project, Mission, Frame, 3D)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Perception, COLMAP SfM, Georeferencing, Video demux
│   │   └── workers/             # Celery background tasks
│   ├── tests/                   # Pytest automated test suites (170 tests)
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router (dashboard, landing page, viewer)
│   │   ├── components/          # React UI components (VideoIngestionHub, PlyViewer)
│   │   └── lib/                 # API client & state management
│   ├── package.json
│   └── tsconfig.json
├── training/
│   ├── checkpoints/             # Official pretrained & finetuned model weights
│   ├── datasets/                # Drone depth manifests, PyTorch loaders, acquisition
│   ├── models/                  # Depth Anything V2 Small architecture definitions
│   └── trainers/                # Aerial model fine-tuning loops
├── docs/                        # Formal architecture & audit documentation
│   ├── JATAYUV_MASTER_AUDIT.md
│   ├── JATAYUV_FINAL_IMPLEMENTATION_REPORT.md
│   ├── JATAYUV_PRESENTATION_SLIDES.md
│   ├── DEPTH_MODEL_ARCHITECTURE.md
│   └── DEPTH_MODEL_TRAINING_PLAN.md
└── storage/                     # Persistent upload containers, video frames, .ply models
```

---

## 7. Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12.10)
- Node.js 18+ (tested on Node.js v20.14.0) & npm
- Redis Server (for Celery background tasks)

### Backend Setup

```bash
# 1. Activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Apply database migrations
alembic -c backend/alembic.ini upgrade head

# 4. Verify Depth Anything V2 Small weights
python -m training.models.dav2_factory

# 5. Start the FastAPI development server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Background Worker

```bash
# In a separate terminal session:
celery -A backend.app.workers.tasks worker --loglevel=info
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Launch Next.js dev server
npm run dev
# Dashboard available at http://localhost:3000/dashboard
```

---

## 8. API Reference (Single-Pass Video & 3D Reconstruction)

### Video Ingestion & Container Inspection
```http
POST /api/v1/missions/{mission_id}/videos/upload
Content-Type: multipart/form-data
```
Uploads a raw drone video stream (`.mp4`, `.mov`, etc.) and optional telemetry file (`.csv`, `.srt`, `.gpx`). Computes SHA-256 checksum, probes container parameters via PyAV/FFprobe, and initializes database tracking records.

### Automated Video Demuxing & Processing
```http
POST /api/v1/videos/{video_id}/process
```
Dispatches Celery background worker to:
1. Extract video frames preserving Presentation Time Stamps (PTS).
2. Calculate Laplacian blur variance and filter unsharp frames.
3. Drop redundant hover frames via perceptual dHash hamming distances.
4. Execute Depth Anything V2 Small relative depth inference.
5. Trigger COLMAP SfM feature matching and incremental mapper.

### 3D Reconstruction Artifacts
```http
GET /api/v1/reconstruction/{mission_id}/artifacts
```
Returns generated 3D assets (`.ply` dense point cloud, `.obj` mesh, reprojection error diagnostics, registered camera count).

---

## 9. Scientific Integrity & Operational Limitations

To maintain absolute academic and engineering honesty, JATAYUV strictly enforces the following principles:

1. **Software Test Verification $\neq$ Real-World Physical Accuracy**:
   - The 169 passing unit and integration tests verify software correctness, data integrity, error handling, and component interoperability.
   - Real-world field accuracy requires physical ground-truth survey validation with RTK-GPS survey equipment.
2. **Relative Inverse Depth Scope**:
   - Depth Anything V2 Small produces rich relative relief, ordinal disparity, and structural boundaries. It does not output physical metric distances (meters) without external ground-scale calibration.
3. **Epipolar Geometry & Single-Pass Flight Constraints**:
   - Reconstructing 3D geometry from a single-pass video requires continuous camera translation to create baseline parallax.
   - Pure forward flight with camera pointed dead-ahead produces degenerate epipolar geometry (focus of expansion singularity). Oblique downward gimbal angles (45°–60°) are recommended for single-pass passes.
   - Extreme motion blur or textureless terrain (e.g., flat water bodies, thick snow) cannot be triangulated by SIFT feature matchers.
4. **Future Field Validation**:
   - Performance targets, processing speeds, and physical centimeter-level accuracies are documented as future field validation targets rather than unmeasured marketing claims.

---

## 10. Audit & Documentation Index

- **Master System Audit**: [`docs/JATAYUV_MASTER_AUDIT.md`](docs/JATAYUV_MASTER_AUDIT.md)
- **Final Implementation Report**: [`docs/JATAYUV_FINAL_IMPLEMENTATION_REPORT.md`](docs/JATAYUV_FINAL_IMPLEMENTATION_REPORT.md)
- **Official 10-Slide Presentation Deck**: [`docs/JATAYUV_PRESENTATION_SLIDES.md`](docs/JATAYUV_PRESENTATION_SLIDES.md)
- **Depth Model Architecture**: [`docs/DEPTH_MODEL_ARCHITECTURE.md`](docs/DEPTH_MODEL_ARCHITECTURE.md)
- **Depth Training Plan & Evaluation**: [`docs/DEPTH_MODEL_TRAINING_PLAN.md`](docs/DEPTH_MODEL_TRAINING_PLAN.md)
- **Aerial Depth Dataset Research**: [`docs/DEPTH_DATASET_RESEARCH.md`](docs/DEPTH_DATASET_RESEARCH.md)

---

**JATAYUV — National Technical Research Organisation (NTRO) | SIH26158**  
*Single-Pass Drone Video to Accurate 3D Model Generation System*
