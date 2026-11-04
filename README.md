# JATAYUV-AI: Integrated Aerial Intelligence Platform

[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C.svg)](https://pytorch.org/)
[![Three.js](https://img.shields.io/badge/Three.js-0.165-black.svg)](https://threejs.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()

JATAYUV-AI is an aerial intelligence and photogrammetry platform designed to convert raw
UAV, drone, and aerial survey imagery into spatial products, including monocular depth
maps, land-cover semantic masks, humanitarian building damage assessments, bi-temporal
change detection maps, and 3D point cloud surface reconstructions.

---

## Key Capabilities

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

---

## Platform Architecture

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Three.js / R3F.
- **Backend API**: FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite / PostgreSQL.
- **Asynchronous Processing**: Celery, Redis.
- **Machine Learning**: PyTorch, Transformers, TIMM, OpenCV, Pillow.
- **Photogrammetry & 3D**: Open3D, NumPy, Three.js PLYLoader.

---

## Directory Structure

```
JATAYUV/
├── backend/
│   ├── app/
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
```

---

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
