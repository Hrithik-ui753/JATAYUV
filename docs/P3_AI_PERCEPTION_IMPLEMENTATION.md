# P3 — AI Perception Pipeline

## 1. Objective

P3 integrates genuine pretrained AI models and produces reliable per-frame perception outputs from the P2 selected frames. P3 deliberately excludes camera tracking, SLAM, photogrammetry, point-cloud generation, mesh generation, and georeferencing. Those remain out of scope.

The P3 perception outputs are:

- relative monocular depth from Depth Anything V2 Small
- semantic segmentation from a pretrained segmentation model
- potentially-dynamic object detection/masking from a pretrained detector
- a per-frame perception fusion record binding those artifacts together
- mission-level perception report and model registry entries

P3 does not claim metric depth, real motion detection, or accuracy numbers that have not been measured.

## 2. Repository reality before writing code

### 2.1 Existing AI stack

The backend already has:

- a vendored official Depth Anything V2 implementation in `training/models/depth_anything_v2`
- a depth engine in `backend/app/services/depth_engine.py`
- a depth estimation service in `backend/app/services/depth_estimation.py`
- a segmentation service in `backend/app/services/segmentation.py`
- a damage assessment service in `backend/app/services/damage_assessment.py`
- a model registry singleton in `backend/app/services/model_registry.py`
- Celery app in `backend/app/workers/celery_app.py`
- existing Celery tasks in `backend/app/workers/tasks.py` and `backend/app/workers/video_tasks.py`
- AI model version tracking in `backend/app/models/ai_model_version.py` and `backend/app/api/v1/models.py`

### 2.2 Depth model

The vendored Depth Anything V2 Small preset is:

- encoder: `vits`
- features: `64`
- out_channels: `[48, 96, 192, 384]`
- use_bn: `False`
- use_clstoken: `False`

The vendored factory `training/models/dav2_factory.py` stores:

- official small checkpoint URL: `https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth`
- official SHA256: `715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378`
- expected bytes: `99218434`
- expected parameter count: `24785089`
- expected state dict tensor count: `239`

The backend `depth_engine.py` already predefines two specs:

- `pretrained` → `training/checkpoints/pretrained/depth_anything_v2_vits.pth`
- `jatayuv_drone_v1` → `training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth`

The engine already does:

- strict checkpoint loading
- official hash verification for the pretrained spec
- parameter-count sanity check against `SMALL_PARAM_COUNT`
- device selection with CUDA if available else CPU
- inference in `torch.no_grad()`
- per-inference timing
- relative inverse-depth normalization
- optional calibrated metric conversion only when a calibration dict exists in the checkpoint

### 2.3 Segmentation model

The existing segmentation service in `backend/app/services/segmentation.py` uses a custom architecture `AerialSegmentationModel` with `num_classes=7`. Its classes are:

- 0 background / Other / Unclassified
- 1 building
- 2 vegetation
- 3 road
- 4 water
- 5 soil / bare ground
- 6 vehicle

That service already does strict checkpoint loading, architecture validation, class-count validation, SHA256 recording, CPU/GPU support, and unavailability errors before any artifact is written. It already saves:

- raw class-ID mask
- colorized overlay
- class distribution percentages

### 2.4 Damage model

The existing damage service uses `SiameseDamageAssessmentModel` with `num_damage_classes=4` and xBD-style tiers. That remains P3-adjacent but is not the primary new detection work unless you want a dynamic detector in addition.

### 2.5 Celery conventions

Celery is configured from `backend/app/core/config.py`:

- broker: `redis://localhost:6379/0`
- backend: `redis://localhost:6379/0`

The Celery app is created once in `backend/app/workers/celery_app.py` as `celery_app`. Workers are not started in this environment. The existing video pipeline tasks in `backend/app/workers/video_tasks.py` already use:

- `SessionLocal` per task
- `JobRepository` logging
- job stage / progress updates
- cancellation checks
- `processing_run_id` for idempotent frame operations

### 2.6 Storage conventions

The existing `backend/app/services/storage.py` already provides `MissionStorage`:

- base dir from `settings.STORAGE_DIR`
- per-mission artifact directories
- deterministic path helpers for videos, frames, metadata, camera poses, depth maps, point clouds, meshes, textures, validation reports

P3 should extend this with perception subdirectories rather than inventing a new storage layer.

### 2.7 Database conventions

The SQLAlchemy 2.0 models live in `backend/app/models/`. The relevant existing tables are:

- `jobs`
- `job_logs`
- `artifacts`
- `ai_model_versions`
- `missions`
- `videos`
- `frames`

Frame records already carry P2 fields including `processing_run_id`, `is_selected`, `gps_*`, `presentation_timestamp`, `timestamp_seconds`, `blur_score`, `exposure_score`, `duplicate_status`, `duplicate_hash`, and `quality_status`.

Existing depth/segmentation/damage results are stored in `backend/app/models/inference_result.py` as separate result tables tied to `jobs` and `images`. P3 should mirror this pattern for perception.

### 2.8 Frontend conventions

The frontend is a Next.js 14 app:

- `src/app` with `layout.tsx`, `page.tsx`, `dashboard/page.tsx`, `projects/page.tsx`, `projects/[id]/page.tsx`, `login/page.tsx`
- shared components in `src/components`
- API client in `src/lib/api.ts`
- types in `src/types/index.ts`
- Tailwind-based UI kit (`Button`, `Card`, `Badge`, `Progress`)
- existing viewers: `DepthViewer`, `SegmentationOverlay`, `BeforeAfterSlider`, `AdvancedSpatialViewer3D`

The frontend uses `next.config.js` rewrites so `/api/v1/*` goes to `http://localhost:8000/api/v1/*` and `/storage/*` goes to `http://localhost:8000/storage/*`.

### 2.9 Runtime environment

This environment has:

- Python 3.12
- PyTorch `2.15.0+cpu`, CUDA not available
- `torchvision`, `transformers>=5.22.2`, `onnxruntime`, `av==19.0.2`, `imagehash==4.3.2`, `sqlalchemy>=2.1.8`, `celery`, `pydantic`, `opencv-python-headless`, `numpy`
- no `ultralytics` installed currently
- no `segformer_tools` package installed

Model checkpoints currently present:

- None in `training/checkpoints/pretained`/`finetuned`
- None in `storage/models/checkpoints`

So P3 code must be honest about missing checkpoints.

## 3. Model selection decisions

### 3.1 Depth

Use the existing vendored Depth Anything V2 Small and the existing `depth_engine.py` / `depth_estimation.py`. Do not reintroduce a parallel depth implementation.

Depth output is RELATIVE inverse depth. P3 must not convert it to metres unless a real fitted calibration is present.

### 3.2 Segmentation

Prefer a genuine pretrained SegFormer-style model via Hugging Face `transformers` if a suitable checkpoint is available and compatible with this environment.

Do not invent a SegFormer checkpoint. If the only available segmentation model is the existing `AerialSegmentationModel`, keep it, but document its exact class list and explicit gaps against the P3 requested scene categories:

- Buildings and structures → map to existing `building` where applicable
- Roads and paved surfaces → map to existing `road`
- Vegetation → map to existing `vegetation`
- Ground and terrain → map to existing `soil` plus `background` as needed
- Water → map to existing `water`
- Vehicles → map to existing `vehicle`
- Humans → not supported by the current 7-class aerial model → `UNKNOWN`
- Obstacles → not directly supported → `UNKNOWN` or task-dependent mapping
- Unknown or unsupported → `UNKNOWN`

If a better pretrained segmentation model becomes available, the P3 class mapping layer is the right place to isolate the difference.

### 3.3 Dynamic object detection

Prefer a real pretrained YOLO-style detector or instance segmentation model only if its checkpoint is available and its license permits the JATAYUV use case.

In this environment, `ultralytics` is not installed and no detector checkpoint exists. So the first P3 cut should be:

- a real detector integration path wired through the existing Celery app
- honest unavailability reporting when no detector checkpoint is installed
- a fallback dynamic masking behavior that clearly marks categories as `POTENTIALLY_DYNAMIC` and never claims true motion

Do not fake detections. Do not pretend a missing detector is working.

## 4. Processing flow

For each mission processing run:

1. Persist a `PerceptionRun` record in `PROCESSING` status
2. Select the P2 selected frames for that run
3. For each selected frame:
   - run depth inference and persist depth artifacts and a `FrameDepthResult`
   - run segmentation inference and persist segmentation artifacts and a `FrameSegmentationResult`
   - run dynamic detection/masking and persist the dynamic mask artifact and a `FrameDynamicObjectResult`
   - persist a `PerceptionArtifact` record per artifact type
   - build a `PerceptionRecord` linking frame, artifacts, model ids, checkpoint hashes, GPS where available, timestamps, camera metadata where available
4. Mark the `PerceptionRun` `COMPLETED` and write a mission-level perception report
5. Support cancel, retry isolation, and idempotency by `processing_run_id` and `frame_id`

Processing must be asynchronous via Celery. FastAPI endpoints must not run long inference.

## 5. Depth outputs

For every successfully processed frame, persist:

- raw inverse depth as `.npy`
- normalized visualization image as PNG/JPEG
- model identifier and version
- checkpoint SHA256
- input resolution
- output resolution
- inference device
- inference duration in ms
- preprocessing configuration
- output depth type: `relative` unless a real calibration exists
- confidence/uncertainty only if a real method produces it; otherwise omit and state that explicitly

Save raw depth arrays as NPY because the existing depth service already uses `.npy` for raw depths.

## 6. Semantic segmentation outputs

For every successfully processed frame, persist:

- raw class-ID mask
- colorized visualization
- class distribution
- per-class pixel counts
- model metadata
- inference time

Use real segmentation outputs and the explicit class-mapping layer described above.

## 7. Dynamic object detection outputs

For every selected frame where a detector is available:

- bounding boxes or instance masks where supported
- class labels and detection scores
- a dynamic-object exclusion mask
- detector version and checkpoint hash

Label category-only detections as `POTENTIALLY_DYNAMIC`. Do not claim true motion unless temporal tracking is implemented and validated later.

## 8. Perception fusion

For every selected frame, produce a structured perception record containing:

- mission ID
- frame ID
- processing run ID
- depth artifact reference
- segmentation artifact reference
- dynamic mask artifact reference
- model identifiers
- checkpoint hashes
- processing status
- processing duration
- error and warning details

Do not merge incompatible coordinate systems. Do not imply depth and GPS are already spatially aligned.

## 9. Artifact storage layout

Extend `MissionStorage` with perception subdirectories:

- `storage/missions/{mission_id}/perception/depth/`
- `storage/missions/{mission_id}/perception/depth_visualizations/`
- `storage/missions/{mission_id}/perception/segmentation/`
- `storage/missions/{mission_id}/perception/segmentation_visualizations/`
- `storage/missions/{mission_id}/perception/dynamic_masks/`
- `storage/missions/{mission_id}/perception/reports/`

Use deterministic names, atomic writes, and per-run separation so previous runs are not overwritten.

Record artifact checksums.

## 10. Database additions

Create or extend:

- `PerceptionRun`
- `FrameDepthResult`
- `FrameSegmentationResult`
- `FrameDynamicObjectResult`
- `PerceptionArtifact`

Use foreign keys to `missions`, `frames`, `jobs`, and `perception_runs` where appropriate. Store large binary payloads only as file references. Use JSON columns for structured metadata where it matches existing conventions.

Track statuses:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

Use an additive Alembic migration.

## 11. Celery tasks

Add tasks to the existing Celery app:

1. `perception_depth_inference`
2. `perception_segmentation_inference`
3. `perception_dynamic_detection`
4. `perception_fuse_frame`
5. `perception_mission_report`

Requirements:

- async processing
- progress tracking
- configurable batch size
- GPU memory management where CUDA exists
- CPU fallback
- retry handling
- cancellation
- idempotency
- persistent logs
- failure isolation
- checkpoint verification before processing

Do not create a second Celery app.

## 12. API endpoints

Follow existing auth and mission ownership conventions. Implement or adapt:

- `POST /api/v1/missions/{mission_id}/perception/process`
- `GET /api/v1/missions/{mission_id}/perception/status`
- `GET /api/v1/missions/{mission_id}/perception/report`
- `GET /api/v1/frames/{frame_id}/perception`
- `GET /api/v1/frames/{frame_id}/depth`
- `GET /api/v1/frames/{frame_id}/segmentation`
- `GET /api/v1/frames/{frame_id}/dynamic-mask`
- `GET /api/v1/missions/{mission_id}/perception/models`
- `POST /api/v1/missions/{mission_id}/perception/cancel`

Requirements:

- authorization and mission ownership checks
- pagination where applicable
- real processing status
- proper errors
- no internal filesystem path leakage

## 13. Frontend integration

Add a perception dashboard that shows:

- mission and selected-frame count
- model availability
- checkpoint status
- device availability: CPU/GPU
- inference progress
- processing errors
- processing duration

Add frame-level inspection showing:

- original frame
- depth visualization
- segmentation visualization
- dynamic-object mask
- GPS metadata when available
- timestamp
- model information

Allow switching between original frame and perception outputs.

Use real backend artifacts only. No placeholder heatmaps, synthetic segmentation, random depth maps, or simulated inference progress.

If a checkpoint is unavailable, show the real unavailable status and explain how to configure it.

## 14. Performance

Implement:

- configurable inference batch sizes
- memory-aware processing
- GPU utilization where supported
- CPU fallback
- efficient resize/preprocessing
- reusable model loading within workers
- tensor and GPU memory cleanup
- per-model inference-time measurement

Benchmark on representative P2 selected frames and record:

- hardware
- model/checkpoint
- number of frames
- input dimensions
- batch size
- device
- total runtime
- average inference time per frame
- peak memory when measurable

Do not invent speed or accuracy claims.

## 15. Testing

Create tests for:

- valid Depth Anything V2 Small checkpoint loading
- checkpoint hash mismatch
- missing depth checkpoint
- CPU inference
- GPU inference when available
- depth output dimensions
- relative-depth labeling
- missing segmentation checkpoint
- segmentation class mapping
- unsupported class handling
- dynamic-object detection
- potentially-dynamic labeling
- perception fusion
- artifact persistence
- artifact checksums
- Celery processing
- retry and cancellation
- API authentication
- frontend perception states

Use real pretrained checkpoints when available. If checkpoints are unavailable, skip integration tests explicitly with a clear reason. Do not replace them with random predictions. Unit tests may use controlled fixtures but must not be presented as real accuracy tests.

## 16. Model registry

Register all P3 models with the existing model registry:

- model name
- architecture
- variant
- source
- license
- checkpoint path
- SHA256
- version
- supported task
- supported classes where relevant
- input configuration
- output type
- availability status

Never report a model as `AVAILABLE` when its checkpoint is missing or invalid.

## 17. Documentation updates

Update:

- README.md
- model setup instructions
- checkpoint download instructions using official sources
- model license references
- environment variables
- Docker configuration if needed
- API documentation
- perception architecture
- CPU/GPU requirements
- known limitations

Do not bundle large model weights into Git.

## 18. Final verification

After implementation:

1. run migrations
2. run backend tests
3. run frontend lint
4. run frontend build
5. run perception unit tests
6. run real inference on available sample frames if checkpoints are present
7. inspect actual depth maps
8. inspect actual segmentation masks
9. inspect actual dynamic-object masks
10. verify all artifact files and database records
11. verify missing checkpoints fail honestly
12. search for random predictions, synthetic outputs, hardcoded scores, and fake success messages

## 19. Known limitations for this starting point

- No CUDA device is available in this environment, so real GPU inference cannot be verified here.
- No Depth Anything V2 Small checkpoint is present yet; the pretrained checkpoint must be downloaded or copied into `training/checkpoints/pretrained/`.
- No segmentation or detector checkpoint is present yet.
- `ultralytics` is not installed, so YOLO-based detection requires install/selection work.
- Frontend currently has perception types missing; those must be added before the dashboard can render real artifacts.
