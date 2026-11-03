# JATAYUV-AI: System Architecture Specification

**Document Version:** 1.0.0  
**Target Platform:** JATAYUV-AI Aerial Intelligence & 3D Photogrammetry Platform  
**Status:** Approved Architectural Blueprint  

---

## 1. System Topology Overview

JATAYUV-AI is designed as a distributed, decoupled, microservice-friendly platform for processing and visualizing complex aerial survey datasets.

```mermaid
flowchart TD
    subgraph Client ["Frontend Tier (Next.js 14 / TypeScript)"]
        UI["Web UI (Tailwind CSS, Lucide)"]
        ThreeCanvas["3D WebGL Point Cloud Viewer (Three.js)"]
        SplitSlider["Before/After Wipe Slider"]
        DepthBlend["Monocular Depth Blend Viewer"]
    end

    subgraph Gateway ["API Gateway Tier (FastAPI)"]
        Router["FastAPI Core & Endpoints"]
        AuthMiddleware["JWT Authentication & RBAC"]
        StorageMount["Static Asset Mount (/storage)"]
        JobTracker["Job State & Progress Engine"]
    end

    subgraph AsyncTier ["Distributed Compute Tier (Celery)"]
        Broker[(Redis Message Broker)]
        WorkerNode1["Celery Worker: AI Computer Vision"]
        WorkerNode2["Celery Worker: 3D Photogrammetry"]
        PreprocEngine["EXIF / Telemetry / CLAHE Pipeline"]
        DepthEngine["Depth Anything V2 Engine"]
        SegEngine["SegFormer Aerial Segmentation Engine"]
        DamageEngine["xBD Siamese Damage Engine"]
        ChangeEngine["Bi-Temporal Difference Engine"]
        SfMEngine["Structure-from-Motion (Open3D / COLMAP)"]
    end

    subgraph DataTier ["Data Persistence Tier"]
        DB[(PostgreSQL / SQLite Database)]
        BlobStorage[("File Storage (/storage/uploads, /processed, /reconstructions)")]
    end

    UI --> Router
    ThreeCanvas --> StorageMount
    SplitSlider --> StorageMount
    DepthBlend --> StorageMount

    Router --> AuthMiddleware
    Router --> DB
    Router --> JobTracker
    JobTracker --> Broker

    Broker --> WorkerNode1
    Broker --> WorkerNode2

    WorkerNode1 --> PreprocEngine
    WorkerNode1 --> DepthEngine
    WorkerNode1 --> SegEngine
    WorkerNode1 --> DamageEngine
    WorkerNode1 --> ChangeEngine
    WorkerNode2 --> SfMEngine

    WorkerNode1 --> BlobStorage
    WorkerNode2 --> BlobStorage
    WorkerNode1 --> DB
    WorkerNode2 --> DB
```

---

## 2. Frontend Architecture

The frontend is built on **Next.js 14 App Router** utilizing strict TypeScript, Tailwind CSS, and Three.js WebGL rendering.

### 2.1 Component Hierarchy
```
frontend/src/
├── app/
│   ├── layout.tsx                # Global Root Layout (Theme, Font, Sticky Header)
│   ├── globals.css               # Design system tokens & animations
│   ├── page.tsx                  # Mission Control Dashboard
│   ├── login/page.tsx            # Authentication Screen
│   ├── projects/page.tsx         # Projects Directory & Search
│   └── projects/[id]/page.tsx    # Multi-tab Mission Workspace
├── components/
│   ├── common/
│   │   └── Header.tsx            # Navigation bar & Engine Status
│   ├── ui/                       # Primitive design tokens
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   └── Progress.tsx
│   ├── viewer/                   # Spatial & Image Viewports
│   │   ├── PointCloudViewer.tsx  # Three.js 3D WebGL Point Cloud Renderer
│   │   ├── BeforeAfterSlider.tsx # Interactive Split Wipe Slider
│   │   ├── DepthViewer.tsx       # False-Color Depth & Blend Viewer
│   │   └── SegmentationOverlay.tsx# Multi-Class LULC Layered Overlay
│   └── damage/
│       └── DamageStatsCard.tsx   # xBD 4-tier damage classification metrics
├── lib/
│   ├── api.ts                    # Strongly-typed REST client
│   └── utils.ts                  # Class merger, formatters, color mappers
└── types/
    └── index.ts                  # Domain TypeScript interfaces
```

### 2.2 3D WebGL Point Cloud Rendering Engine
- **Three.js Scene Graph**: PerspectiveCamera with OrbitControls, GridHelper, and Directional lighting.
- **BufferGeometry**: Efficient contiguous Float32Array allocations for vertex positions `(x, y, z)` and vertex RGB colors `(r, g, b)`.
- **Hypsometric Tinting**: Dynamic elevation colormapping calculated in real time based on Z-height gradients.
- **Controls**: Mouse drag orbit rotation, scroll wheel zoom, and animated auto-orbit toggle.

---

## 3. Backend Architecture

The backend follows a layered architecture with clear separation of concerns:

```
[HTTP Request] 
      │
      ▼
[API Routers: backend/app/api/v1/] 
      │ (Validates via Pydantic Schemas: backend/app/schemas/)
      ▼
[Security / Dependencies: backend/app/api/deps.py] 
      │ (Enforces JWT Token & Project Ownership)
      ▼
[Domain Services: backend/app/services/] 
      │ (Executes Computer Vision & Photogrammetry)
      ▼
[Data Layer: backend/app/models/ & database.py] 
      │ (Commits to SQLite / PostgreSQL)
      ▼
[HTTP Response / Storage Asset]
```

### 3.1 Layer Responsibilities
1. **API Router Layer**: Accepts requests, validates input payloads against Pydantic schemas, routes to domain services, and handles HTTP status codes.
2. **Security Layer**: Verifies JWT Bearer tokens, extracts analyst identity, enforces role-based access control (RBAC), and checks resource ownership.
3. **Domain Service Layer**: Stateless compute modules containing actual AI models (Depth, Segmentation, Damage, Change, SfM).
4. **Data Access Layer**: SQLAlchemy 2.0 ORM managing entity lifecycle and database transactions.

---

## 4. Database Schema & Entity Relationships

```mermaid
erDiagram
    User ||--o{ Project : owns
    Project ||--o{ Image : contains
    Project ||--o{ Job : tracks
    Project ||--o{ Reconstruction3D : generates
    Image ||--o{ DepthResult : has
    Image ||--o{ SegmentationResult : has
    Job ||--o{ DepthResult : produces
    Job ||--o{ SegmentationResult : produces
    Job ||--o{ DamageAssessmentResult : produces
    Job ||--o{ ChangeDetectionResult : produces
    Job ||--o{ Reconstruction3D : produces

    User {
        string id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    Project {
        string id PK
        string name
        text description
        string location_name
        float center_lat
        float center_lon
        string owner_id FK
        datetime created_at
        datetime updated_at
    }

    Image {
        string id PK
        string project_id FK
        string filename
        string file_path
        string thumbnail_path
        int file_size_bytes
        int width
        int height
        string format
        boolean is_preprocessed
        string preprocessed_path
        text telemetry_json
        datetime created_at
    }

    Job {
        string id PK
        string project_id FK
        string job_type
        string status
        int progress_pct
        text error_message
        string celery_task_id
        datetime created_at
        datetime updated_at
    }

    DepthResult {
        string id PK
        string job_id FK
        string image_id FK
        string depth_map_path
        string colormap_path
        float min_depth_m
        float max_depth_m
        float mean_depth_m
        string mesh_obj_path
        datetime created_at
    }

    SegmentationResult {
        string id PK
        string job_id FK
        string image_id FK
        string mask_path
        string overlay_path
        text class_distribution_json
        string geojson_path
        datetime created_at
    }

    DamageAssessmentResult {
        string id PK
        string job_id FK
        string pre_image_id FK
        string post_image_id FK
        string damage_overlay_path
        int total_buildings
        text counts_by_level_json
        float damage_percentage
        float severity_index
        string geojson_path
        datetime created_at
    }

    ChangeDetectionResult {
        string id PK
        string job_id FK
        string before_image_id FK
        string after_image_id FK
        string diff_mask_path
        string heatmap_path
        float changed_area_pct
        int changed_pixels
        float significance_score
        datetime created_at
    }

    Reconstruction3D {
        string id PK
        string project_id FK
        string job_id FK
        string pointcloud_ply_path
        string mesh_obj_path
        string dsm_tiff_path
        int num_points
        int camera_count
        float reprojection_error_px
        text bounds_json
        datetime created_at
    }
```

---

## 5. Storage Architecture

All large binary assets (original images, thumbnails, masks, depth maps, PLY point clouds, DSM rasters) are stored outside the relational database on persistent file storage.

### Directory Structure
```
storage/
├── uploads/              # Raw ingested drone imagery ({uuid}_{filename})
├── processed/            # Preprocessed, colormapped, and masked products
│   ├── thumb_*           # Low-resolution thumbnails for web galleries
│   ├── prep_*            # CLAHE & sharpened enhanced imagery
│   ├── depth_*           # 16-bit PNG depth elevation maps
│   ├── colormap_*        # Turbo/Viridis false-color overlays
│   ├── segmask_*         # Discrete class index masks
│   ├── segoverlay_*      # Multi-class alpha-blended overlays
│   ├── damage_*          # Labeled damage overlays & GeoJSON vectors
│   └── diffheat_*        # Bi-temporal change severity heatmaps
├── models/               # Cached PyTorch weights & ONNX checkpoints
└── reconstructions/      # 3D photogrammetric outputs
    ├── pointcloud_*.ply  # Stanford ASCII/Binary 3D point cloud
    ├── mesh_*.obj        # Textured surface mesh
    └── dsm_*.tif         # 16-bit Digital Surface Model elevation raster
```

---

## 6. Background Asynchronous Processing (Celery & Redis)

Long-running compute jobs (multi-image 3D photogrammetry, batch depth estimation, Siamese damage assessment) are decoupled from the API gateway using **Celery** workers backed by **Redis**.

1. **Job Dispatch**: The API router creates a `Job` record with `status="pending"`, enqueues a Celery task via `.delay()`, and immediately returns HTTP 202 with the `job_id`.
2. **Worker Execution**: Celery worker nodes pull tasks from Redis, update job progress (`progress_pct=25, 50, 75`), perform model inference, save artifacts to disk, and update the relational database record.
3. **Failure Handling**: Built-in exponential backoff retry policies for transient failures, and automatic recording of stack traces into `Job.error_message`.
4. **Client Polling**: The Next.js frontend polls `GET /api/v1/jobs/{job_id}` or listens via Server-Sent Events (SSE) until `status="completed"`.

---

## 7. Containerization & Deployment Architecture

```mermaid
flowchart LR
    subgraph Host ["Production Host / VM"]
        subgraph DockerNetwork ["Internal Docker Bridge Network"]
            PG[(PostgreSQL 16)]
            Redis[(Redis 7.2)]
            Backend["FastAPI Container (:8000)"]
            Worker["Celery Worker Container"]
            Frontend["Next.js Container (:3000)"]
        end
        Volumes[("Docker Persistent Volumes: /storage, /pgdata")]
    end

    Internet(("Web Clients / Drone Ground Stations")) --> Frontend
    Frontend --> Backend
    Backend --> PG
    Backend --> Redis
    Worker --> Redis
    Worker --> PG
    Backend --> Volumes
    Worker --> Volumes
```

### Container Responsibilities
- **frontend**: Next.js Node.js server optimized with multi-stage standalone build.
- **backend**: Uvicorn ASGI server running FastAPI application.
- **worker**: Dedicated Python container running Celery worker daemon with PyTorch runtime.
- **db**: PostgreSQL 16 container with persistent data volume.
- **redis**: In-memory message queue and job result backend.
