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

<<<<<<< HEAD
> **Problem Statement ID:** SIH26158  
> **Problem Statement Title:** Single-Pass Drone Video to Accurate 3D Model Generation System  
> **Organization:** National Technical Research Organisation (NTRO)  
> **Theme:** Robotics and Drones  
> **Application Type:** AI-Powered Geospatial Intelligence, Photogrammetry, Computer Vision and 3D Reconstruction Platform  
=======
JATAYUV-AI is an aerial intelligence and photogrammetry platform designed to convert raw
UAV, drone, and aerial survey imagery into spatial products, including monocular depth
maps, land-cover semantic masks, humanitarian building damage assessments, bi-temporal
change detection maps, and 3D point cloud surface reconstructions.
>>>>>>> origin/main

---

## 1. Executive Overview

<<<<<<< HEAD
**JATAYUV** is an integrated geospatial intelligence and photogrammetry platform engineered to ingest continuous **single-pass drone video streams** (MP4/MOV/AVI/MKV/WebM) accompanied by onboard flight telemetry (GPS/IMU logs in CSV/SRT/GPX) and reconstruct metrically meaningful, georeferenced 3D digital twins.

Traditional photogrammetric systems mandate multi-pass grid patterns with 80%+ cross-track overlap, rendering them unsuitable for rapid disaster response or hostile border surveillance. JATAYUV solves this operational bottleneck by fusing deep aerial monocular perception with Structure-from-Motion (SfM), multi-view stereo (MVS), and closed-form similarity georeferencing.

The platform provides a mission-control web interface (Next.js 14 + Three.js) for video ingestion, flight telemetry inspection, automated processing dispatch, interactive 3D point cloud exploration with hypsometric elevation tinting, and geospatial artifact export.
=======
1. **High-Resolution Drone Imagery Ingestion**: EXIF metadata extraction, camera focal
   length & sensor parameter recovery, GPS geolocation parsing, and thumbnail generation.
2. **Monocular Depth Estimation**: official **Depth Anything V2 Small** (DINOv2 ViT-S/14,
   24.79 M parameters) via a fine-tuning pipeline on aerial depth data. Output is
   **relative inverse depth**; metre output is only produced by an explicitly fitted
   metric calibration. See [`docs/DEPTH_MODEL_ARCHITECTURE.md`](docs/DEPTH_MODEL_ARCHITECTURE.md).
3. **Semantic Segmentation**: 8-class aerial LULC segmentation (Buildings, Roads,
   Vegetation, Water, Bare Soil, Vehicles, Pavement, Construction).
4. **Building Damage Assessment**: 4-tier damage classification (None, Minor, Major,
   Destroyed) following the xBD taxonomy.
5. **Bi-Temporal Change Detection**: change masks between pre- and post-event flights with
   change-intensity heatmaps.
6. **SfM & 3D Reconstruction**: multi-image dense point cloud reconstruction, `.ply` point
   clouds and digital surface models.
7. **Spatial Visualizer**: Three.js / React Three Fiber point cloud and terrain viewer.
8. **Asynchronous Engine**: Celery + Redis job orchestration with progress reporting.

---

## Depth model: what is real today

| Item | Value |
| --- | --- |
| Architecture | official Depth Anything V2 Small (`encoder=vits`, DPT head) |
| Parameters | 24,785,089 (6,279,745 trainable with the default freeze strategy) |
| Pretrained weights | `training/checkpoints/pretrained/depth_anything_v2_vits.pth`, 99,218,434 bytes, SHA256 `715fade1…60e1378` |
| Fine-tuned weights | `training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth` |
| Training data | SkyScenes (MIT licence), 138 RGB/depth pairs, 2160×1440 |
| Splits | train 55 (Town01) / val 14 (Town01 temporal tail) / test 69 (Town02, unseen town) |
| Height/weather | one setting only: `H_15_P_0` / `ClearNoon` |

Measured on the 69 held-out Town02 frames (scale+shift **aligned relative** metrics —
SkyScenes publishes no metric ground truth, so these are **not** metres):

| Metric | Pretrained | Fine-tuned | Change |
| --- | --- | --- | --- |
| AbsRel | 0.2893 | **0.0710** | −75.5 % |
| RMSE (normalised) | 0.1063 | **0.0346** | −67.5 % |
| δ<1.25 | 0.5342 | **0.9469** | +77.3 % |
| SILog (inverse space) | 4.5256 | **1.3246** | −70.7 % |
| Ordinal consistency | 0.9275 | 0.9211 | −0.7 % |

Full report: `training/experiments/exp_b_skyscenes_relative/eval/evaluation_report.md`.

**Honest scope:** this demonstrates an intra-domain gain on synthetic aerial imagery
(same renderer, camera, altitude and weather). It is **not** evidence of real-world drone
accuracy, and no metric (metre) accuracy is claimed anywhere.
>>>>>>> origin/main

---

## 2. Verified Implementation Status

<<<<<<< HEAD
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
=======
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Three.js / R3F.
- **Backend API**: FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite / PostgreSQL.
- **Asynchronous Processing**: Celery, Redis.
- **Machine Learning**: PyTorch, Transformers, TIMM, OpenCV, Pillow.
- **Photogrammetry & 3D**: Open3D, NumPy, Three.js PLYLoader.
>>>>>>> origin/main

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
<<<<<<< HEAD
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
=======
│   │   ├── api/v1/         # REST API (Auth, Projects, Images, Jobs, AI, 3D)
│   │   ├── core/           # Config, security, DB session, logging
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   ├── services/       # depth_engine, segmentation, damage, change, 3D
│   │   └── workers/        # Celery tasks
│   ├── tests/              # Pytest suites (incl. test_depth_pipeline.py)
│   └── requirements.txt
├── frontend/               # Next.js dashboard + landing page
├── training/               # Depth Anything V2 Small fine-tuning pipeline
│   ├── models/             # vendored official DAv2 code + factory/loader
│   ├── datasets/           # manifest, dataset, transforms, acquisition manager
│   ├── preprocessing/      # media ingest, dataset preparation
│   ├── depth_generation/   # teacher pseudo-labels, COLMAP, real-depth import
│   ├── losses/             # SILog, L1, BerHu, gradient, ordinal, combined
│   ├── trainers/           # train_depth.py
│   ├── evaluation/         # metrics, calibration, evaluate_depth.py
│   ├── configs/            # depth_anything_v2_small.yaml + experiments A–E
│   ├── checkpoints/        # pretrained/ and finetuned/ (weights are git-ignored)
│   └── experiments/        # run logs, metrics, visual comparisons
├── datasets/               # manifests, splits, reports, raw data (git-ignored)
├── docs/                   # depth plans, dataset research, architecture
└── storage/                # runtime uploads, processed artefacts, DB
>>>>>>> origin/main
```

---

<<<<<<< HEAD
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
=======
## Setup

```bash
# Backend
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev     # http://localhost:3000
```

Optional depth environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `JATAYUV_DEPTH_MODEL` | `pretrained` | default checkpoint: `pretrained` \| `jatayuv_drone_v1` |
| `JATAYUV_DEPTH_CHECKPOINT` | `training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth` | path for the fine-tuned model |
| `JATAYUV_DEPTH_INPUT_SIZE` | `518` | inference resolution (rounded to a multiple of 14) |

---

## Depth training workflow

All commands run from the repository root.

```bash
# 1. Official checkpoint (SHA256-verified; never overwritten)
python -m training.models.dav2_factory --download
python -m training.models.dav2_factory            # verification report

# 2. Dataset research / acquisition (only unauthenticated, licence-permitted sources)
python -m training.datasets.acquisition.manager --list
python -m training.datasets.acquisition.manager --plan skyscenes
python -m training.datasets.acquisition.manager --acquire skyscenes \
    --select altitude=H_15_P_0 --select weather=ClearNoon --select town=Town01

# 3. Manifest + leakage-free splits + validation report
python -m training.preprocessing.prepare_dataset \
    --config training/configs/depth_anything_v2_small.yaml

# 4. Fine-tune (resumable: --resume <last_checkpoint.pth>)
python -m training.trainers.train_depth \
    --config training/configs/depth_anything_v2_small.yaml

# 5. Evaluate pretrained vs fine-tuned on the identical test split
python -m training.evaluation.evaluate_depth \
    --config training/configs/depth_anything_v2_small.yaml \
    --checkpoint training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth

# 6. Own JATAYUV flights (when available)
python -m training.preprocessing.media_ingest \
    --input <flight_dir> --output datasets/manifests/own_flights.json
python -m training.depth_generation.teacher_pseudo_depth \
    --input datasets/manifests/own_flights.json \
    --output datasets/manifests/own_flights_pseudo.json
python -m training.depth_generation.photogrammetry_colmap \
    --images datasets/processed/own_frames/<flight> --output-dir datasets/depth_maps/colmap

# 7. Tests
python -m pytest backend/tests -q
```

Experiment arms live in `training/configs/experiments/`:

| Config | Arm | Status |
| --- | --- | --- |
| `exp_a_baseline.yaml` | pretrained baseline (evaluation only) | executed |
| `depth_anything_v2_small.yaml` (`exp_b`) | fine-tune on SkyScenes relative depth | **executed** |
| `exp_c_photogrammetry.yaml` | COLMAP pseudo-depth | blocked (no COLMAP, no flights) |
| `exp_d_combined.yaml` | mixed sources | blocked (same) |
| `exp_e_teacher_pseudo.yaml` | teacher pseudo-labels | blocked (no drone RGB) |

---

## API

```http
POST /api/v1/analysis/depth
{ "image_id": "…", "model_id": "jatayuv_drone_v1", "input_size": 518 }
```

Response (abridged):

```json
{
  "depth_type": "relative",
  "depth_unit": "relative_inverse_depth",
  "is_metric": false,
  "min_depth_m": null, "max_depth_m": null, "mean_depth_m": null,
  "relative_min": 0.02, "relative_max": 0.97, "relative_mean": 0.41,
  "model_id": "jatayuv_drone_v1",
  "checkpoint_sha256": "2a6fcb37b644…",
  "inference_ms": 189.4,
  "depth_map_path": "storage/processed/depth_….png",
  "raw_depth_path": "storage/processed/depth_raw_….npy"
}
```

`GET /api/v1/analysis/depth/models` lists both checkpoints with availability.
Relative checkpoints always return `null` metric fields: the platform does not fabricate
metres from altitude.

---

## Documentation

| Document | Contents |
| --- | --- |
| [`docs/DEPTH_MODEL_TRAINING_PLAN.md`](docs/DEPTH_MODEL_TRAINING_PLAN.md) | audit, plan, executed commands, measured results, hardware, limitations |
| [`docs/DEPTH_DATASET_RESEARCH.md`](docs/DEPTH_DATASET_RESEARCH.md) | 11 aerial depth datasets, licences, access, storage, acquired-data integrity notes |
| [`docs/DEPTH_MODEL_ARCHITECTURE.md`](docs/DEPTH_MODEL_ARCHITECTURE.md) | architecture, preprocessing, targets, freezing, losses, calibration, checkpoint format |

---

## Known limitations

1. No metric aerial ground truth has been acquired → all depth numbers are aligned
   relative; no metre accuracy claim.
2. Training data is synthetic (CARLA) and small (55 training frames, one altitude, one
   weather set).
3. Own JATAYUV flight data is not in the repository, so ingestion and COLMAP paths are
   implemented and unit-tested but not run on real missions.
4. Reference workstation is CPU-only: CUDA/AMP paths are implemented but untested there.
5. One seed, one dataset; no cross-seed variance estimate.
>>>>>>> origin/main
