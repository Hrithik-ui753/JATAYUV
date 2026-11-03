# JATAYUV-AI: Integrated Aerial Intelligence Platform

[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15-EE4C2C.svg)](https://pytorch.org/)
[![Three.js](https://img.shields.io/badge/Three.js-0.165-black.svg)](https://threejs.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()

JATAYUV-AI is an aerial intelligence and photogrammetry platform designed to convert raw UAV, drone, and aerial survey imagery into spatial products, including monocular depth maps, land-cover semantic masks, humanitarian building damage assessments, bi-temporal change detection maps, and 3D point cloud surface reconstructions.

---

## Key Capabilities

1. **High-Resolution Drone Imagery Ingestion**: Automated EXIF metadata extraction, camera focal length & sensor parameter recovery, GPS geolocation tag parsing, and dynamic thumbnail generation.
2. **Monocular Depth Estimation**: Zero-shot depth inference powered by Depth Anything V2 with surface normal extraction and 3D relief mesh projection.
3. **Semantic Segmentation**: 8-class aerial land-use and land-cover (LULC) segmentation (Buildings, Roads, Vegetation, Water, Bare Soil, Vehicles, Pavement, Construction).
4. **Building Damage Assessment**: Objective 4-tier damage classification (None, Minor, Major, Destroyed) conforming to the xBD disaster response taxonomy.
5. **Bi-Temporal Change Detection**: High-sensitivity change masks between pre- and post-event flight surveys with automated change intensity heatmaps.
6. **Structure from Motion (SfM) & 3D Reconstruction**: Multi-image dense point cloud reconstruction (Open3D / COLMAP pipeline), generating standard `.ply` point clouds and Digital Surface Models (DSM).
7. **Spatial Visualizer**: Browser-based Three.js & React Three Fiber point cloud and terrain viewer with interactive camera orbits, slice planes, and spatial measurement tools.
8. **Asynchronous Distributed Engine**: Celery + Redis pipeline with fault-tolerant job orchestration, live task progress reporting, and persistent disk caching.

---

## Platform Architecture

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide React, Three.js, React Three Fiber.
- **Backend API**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, SQLite / PostgreSQL.
- **Asynchronous Processing**: Celery, Redis.
- **Machine Learning**: PyTorch, Hugging Face Transformers, TIMM, ONNX Runtime, OpenCV, Pillow.
- **Photogrammetry & 3D**: Open3D, SciPy, NumPy, Three.js PLYLoader.

---

## Directory Structure

```
JATAYUV/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # REST API endpoints (Auth, Projects, Images, Jobs, AI, 3D)
│   │   ├── core/           # Configuration, Security, DB session, Logging
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic v2 request/response validation schemas
│   │   ├── services/       # AI inference, image preprocessing, 3D photogrammetry
│   │   └── workers/        # Celery task definitions and worker configuration
│   ├── tests/              # Pytest automated test suites
│   └── requirements.txt    # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router pages and layouts
│   │   ├── components/     # UI, 3D Viewer, Damage Assessment, Dashboard
│   │   ├── lib/            # API client, Auth state, Utilities
│   │   └── types/          # TypeScript interface definitions
│   ├── package.json        # Frontend dependencies
│   └── tailwind.config.js  # Styling and theme configuration
├── storage/                # Persistent file storage (Uploads, Models, Reconstructions)
├── docs/                   # Architectural blueprints and API documentation
└── docker/                 # Containerization files (Dockerfiles & docker-compose)
```

