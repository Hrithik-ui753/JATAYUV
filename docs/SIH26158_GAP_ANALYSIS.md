# JATAYUV → SIH26158: Repository Audit & Gap Analysis

**Audit date:** November 8, 2026
**Auditor role:** Lead architect / CV-ML engineer / full-stack
**Scope:** `D:\TBP\JATAYUV` (working tree `C:\Users\admin` host, Windows)
**Method:** static inspection + live execution of the application and test suite. Every finding
below is reproduced from the current checkout; nothing is inferred from documentation claims.
**Status:** audit complete, no application code modified.

---

## 0. One-paragraph conclusion

The repository is a **working image-based aerial intelligence platform** (JATAYUV-AI) built
around single-image depth estimation, LULC segmentation, xBD damage assessment and bi-temporal
change detection. It is **not** a single-pass drone-video-to-georeferenced-3D system.
Three of its most visible capabilities — 3D reconstruction, semantic segmentation and the 3D
viewer — are **not implemented as advertised**: poses and geometry are synthesised, the
segmentation/damage networks carry random weights, and the WebGL viewer ignores the point-cloud
URL and renders procedural noise. The one piece of genuine, well-engineered ML work is the
Depth Anything V2 Small fine-tuning pipeline under `training/`, which is honest about its own
limitations. Roughly 25–30% of the SIH26158 architecture is reusable; the video, camera-tracking,
georeferencing, validation and mission-lifecycle layers do not exist.

---

## 1. Verified environment

| Item | Observed | Note |
| --- | --- | --- |
| Python (`.venv`) | 3.12.10 | `docs/PROJECT_AUDIT.md` claims 3.14.3 — environment drift |
| PyTorch | 2.15.0+cpu, `cuda_available=False` | CPU-only build |
| FastAPI / SQLAlchemy / Celery | 0.162.0 / 2.1.8 / 5.7.0 | app imports cleanly |
| OpenCV / NumPy | present | |
| Open3D | **absent** | Parts 6 & 8 require it |
| rasterio / pyproj / GDAL / shapely | **absent** | no CRS capability at all |
| PyAV / ffmpeg | **absent** (ffmpeg not on PATH) | no video decode path |
| COLMAP | **not on PATH** | referenced but unusable |
| Version control | **no `.git`** | no history, no diffs, no branches |

Application import: **OK** — 36 OpenAPI paths, 8 routers mounted.

## 2. Execution baseline (measured, not claimed)

```
$ python -m pytest backend/tests -q --continue-on-collection-errors
7 failed, 56 passed, 1 error
```

* `ERROR backend/tests/test_depth_pipeline.py` — `ModuleNotFoundError: No module named 'training.datasets'`
  (`backend/tests/test_depth_pipeline.py:23`). The package does not exist; `training/` has no
  `datasets/` subdirectory although `README.md` documents one.
* 6 of the 7 failures are one root cause: the `--continue-on-collection-errors` run reports
  `Depth checkpoint for 'pretrained' not found at .../training/checkpoints/pretrained/depth_anything_v2_vits.pth`.
  Weights are git-ignored and absent, so **depth inference cannot be exercised in this checkout**.
* `test_module08_integration.py::TestJobCancellation::test_cancel_completed_job_returns_409`
  is an independent job-lifecycle defect.
* `training/configs/experiments/exp_b_skyscenes_relative.yaml` is referenced by README's results
  table, but `training/checkpoints/` and `training/experiments/` **do not exist**. The reported
  AbsRel 0.2893 → 0.0710 improvement is therefore **unverifiable from this working tree** —
  report absent, not disproved.

---

## 3. Blocking integrity findings

These violate SIH26158 Development Rules 5, 6 and Part 11 ("no simulated metrics or fake
reconstruction results"). They must be treated as defects, not features.

### 3.1 `photogrammetry.py` fabricates the entire reconstruction

`backend/app/services/photogrammetry.py` is presented as "Structure-from-Motion (SfM)". It
performs no matching and no triangulation.

| Line | Code | Effect |
| --- | --- | --- |
| 40–43 | `cam_x = float(i * 3.5)`, `cam_y = 12.0`, `cam_z = float(i * 1.2)` | "Camera pose simulation (drone flight trajectory)" — a linear ramp by frame index, identical for every dataset |
| 56 | `local_elev = gray[py, px] / 255.0 * 5.0` | **pixel brightness used as elevation** |
| 44–58 | `norm_x = (px/w - 0.5)*16.0 + cam_x` | 3D point from pixel position plus a fixed 16 m plane; no ray intersection |
| 62–66 | `if len(points) < 500:` → `np.sin(rx*0.4)*np.cos(rz*0.4)*2.0 + 1.5` | synthesises a sinusoidal terrain grid when data is sparse |
| 99 | `"reprojection_error_px": 0.68` | **hardcoded constant** reported as a measured quality metric |

This is the source of every PLY, OBJ and DSM the UI can display. The `Reconstruction3D` row and
`GET /api/v1/reconstruction/3d/{project_id}` therefore serve fabricated geometry with a
fabricated accuracy figure.

### 3.2 Segmentation and damage networks have random weights

`backend/app/services/segmentation.py:9–54` and
`backend/app/services/damage_assessment.py:9–56` define bespoke 3-layer CNNs and instantiate them
directly:

```python
self.model = AerialSegmentationModel(num_classes=len(self.CLASSES)).to(self.device)
```

A repository-wide search for `load_state_dict`, `from_pretrained`, `torch.load` and `.pth` across
`backend/app/services/` returns **no matches**, and no `manual_seed` is set. Both models are
randomly initialised per process. Every segmentation mask, class distribution, damage tier count
and severity index produced by the platform is noise presented as analysis. `README.md` advertises
"8-class aerial LULC segmentation" and "4-tier damage classification" on this basis.

### 3.3 The 3D viewer never loads a point cloud

* `frontend/src/components/viewer/AdvancedSpatialViewer3D.tsx:33` accepts `plyUrl` and never
  references it again; lines 131–144 generate vertices with `Math.random()` and inject three
  hardcoded "buildings" via `inBldg1/2/3` bounding boxes.
* `frontend/src/components/viewer/PointCloudViewer.tsx:16` — same pattern, plus a
  `sin/cos` hill function.
* Neither component imports `PLYLoader` or `GLTFLoader`. Both viewers are mounted in production
  surfaces (`dashboard/page.tsx:484, 1013`; `projects/[id]/page.tsx:170`).

### 3.4 Upload failure is reported to the user as success

`frontend/src/app/dashboard/page.tsx:221`:
```tsx
} catch (err: any) {
  setUploadStatus("Upload completed with local simulation.");
}
```
A failed HTTP upload is displayed as completed. This is a false-success path on the primary
workflow entry point.

### 3.5 Long-running work is synchronous, contradicting the architecture docs

`docs/SYSTEM_ARCHITECTURE.md` §6 specifies Celery dispatch. In practice:

* `api/v1/analysis.py:108, 198, 277, 373` call `depth_service`, `segmentation_service`,
  `damage_service`, `change_service` **inline in the request thread**.
* `api/v1/reconstruction.py:52` calls `photogrammetry_service` inline.
* `workers/tasks.py` defines only `task_preprocess_image` and `task_run_depth_estimation`, and
  nothing in the API dispatches to them.

### 3.6 Dead, broken COLMAP service

`backend/app/services/reconstruction.py`:
* line 9 `from ..core.celery_app import celery_app` — the module lives at
  `backend/app/workers/celery_app.py`, so this import is invalid.
* line 71 invokes `stereo_fusion` without `patch_match_stereo`, so the dense path cannot work
  even with COLMAP installed, and `poisson_mesher` is then fed a non-existent `fused.ply`.
* **No module imports `services.reconstruction`.** It is unreachable code that nonetheless
  appears in the roadmap as delivered.

---

## 4. What is genuinely real and reusable

Build on these; do not rewrite them.

| Asset | Evidence | Reuse for SIH26158 |
| --- | --- | --- |
| Official DAv2 Small architecture, vendored | `training/models/depth_anything_v2/dpt.py`, `dinov2.py`, `util/` | Part 3 backbone |
| Checkpoint factory with SHA-256 pinning, never overwrites official weights | `training/models/dav2_factory.py` | Part 9 registry provenance |
| Honest relative-vs-metric separation | `depth_engine.py` (`depth_type`, `depth_unit`, `is_metric`, `relative_min/max/mean`), `DepthResult` columns | Part 3 discipline, already correct |
| Refuses to fabricate metres when uncalibrated | `depth_engine.py` metric fields `None` unless calibration in checkpoint | keep exactly this |
| Fails loudly on missing weights | observed in test run (explicit "checkpoint not found" error) | good failure mode |
| FastAPI + SQLAlchemy 2.0 + JWT + RBAC | 36 paths; `api/deps.py`, `core/security.py` | Parts 1 & 10 |
| Job model with lifecycle | `models/job.py`: `status`, `progress_pct`, `error_message`, `celery_task_id`, `started_at`, `completed_at`, `cancelled_at`, `retry_count`, `timeout_seconds` | Part 10 |
| Job logs + cancel endpoint | `models/job_log.py`, `api/v1/jobs.py` (`/cancel`, `/logs`) | Part 10 |
| Artifact registry | `models/artifact.py` (`artifact_type`, `file_path`, size, mime) | Part 8/10 |
| Model version registry | `models/ai_model_version.py` (`weights_path`, `accuracy_metrics` JSON, `is_active`) | Part 9 |
| Typed API client | `frontend/src/lib/api.ts` (380 lines) | Part 11 |
| Premium dark cinematic design system | `globals.css`, `components/ui/*`, landing/* | Part 11 (preserve) |
| COLMAP invocation harness | `services/photogrammetry.py` / `services/reconstruction.py` structure | salvage as Tier-A driver after fixes |

---

## 5. Module-to-SIH26158 gap matrix

Legend — **REAL**: works as advertised. **PARTIAL**: exists but incomplete. **FAKE**: produces
output that is not derived from the input. **ABSENT**: no implementation.
**BLOCKED**: implemented but cannot execute in this checkout.

| # | SIH26158 module | Status | Evidence | Gap |
| --- | --- | --- | --- | --- |
| 1 | Dashboard | **PARTIAL** | `app/page.tsx` (88), `app/dashboard/page.tsx` (1348) | KPIs/mission table read real `/projects` + `/jobs`; but embedded 3D panel is FAKE (§3.3) |
| 2 | Mission Management | **PARTIAL** | `models/project.py`, `api/v1/projects.py` | `Project` = name/location/center_lat/lon only. No mission lifecycle, no flight record, no workflow state |
| 3 | Drone Video Upload | **ABSENT** | `api/v1/images.py` `ALLOWED_EXTENSIONS = {jpg,jpeg,png,tif,tiff,dng,webp}`; `config.py` `ALLOWED_IMAGE_MIME_TYPES` = `image/*` | No `Video` entity, no MP4/MOV acceptance, no chunked/resumable upload, no checksum |
| 4 | Flight Metadata | **ABSENT** | `Image.telemetry_json` (Text blob), `Project.center_lat/lon` | No structured `flight_metadata` table: no altitude, no datum, no gimbal, no speed, no over-lap, no RTK/PPK flags |
| 5 | Video Processing | **ABSENT** | no decoder dependency; `ffmpeg` not on PATH | No frame extraction, sampling, timestamps, blur, duplicate, exposure, motion estimation, quality scoring |
| 6 | AI Depth Estimation | **PARTIAL / BLOCKED** | `depth_engine.py` (346), `training/models/dav2_factory.py` | Real architecture + honest relative/metric split, but (a) weights absent, (b) image-level only, (c) no per-frame sequence handling, (d) no depth confidence, (e) no drone-specific checkpoint registered |
| 7 | Semantic Segmentation | **FAKE** | `services/segmentation.py:9–54` | Random-weight CNN, no pretrained ADE20K/SegFormer, no dynamic-object masking, 7 classes ≠ required 8 (missing humans, obstacles) |
| 8 | Camera Tracking & SLAM | **ABSENT** | `photogrammetry.py:40–43` | Poses are `i*3.5`. No VO, no SfM, no BA, no intrinsics handling, no IMU, no GPS constraints, no `camera_poses` table |
| 9 | 3D Reconstruction | **FAKE** | `photogrammetry.py:44–99` | No matching/triangulation/MVS. COLMAP service dead & broken (§3.6). No Open3D. No tiered fallback, no observability mask |
| 10 | Georeferencing | **ABSENT** | deps: no `pyproj`/`rasterio`/GDAL | No CRS, no ENU, no Umeyama scale solve, no datum handling, no GPS quality reporting |
| 11 | Model Validation | **ABSENT** | only `reprojection_error_px: 0.68` constant | No coverage, no density, no checkpoint residuals, no scale confidence, no per-region uncertainty |
| 12 | 3D Viewer | **FAKE** | `AdvancedSpatialViewer3D.tsx:33,131`, `PointCloudViewer.tsx:16` | Procedural noise; no PLY/GLB loading; measurements computed on fake geometry |
| 13 | Export & Reports | **PARTIAL** | `_write_ply`, `_write_dsm_raster`, GeoJSON writers | PLY/OBJ/GeoJSON/TIFF emitters exist; no GLB, no georeferenced metadata, no quality report, no bundle |
| 14 | Model Development & Training | **PARTIAL** | `training/**` (real DAv2 fine-tune CLI); `backend/app/services/training/**` (LeVir-CD/LoveDA/xBD satellite) | Two unrelated training subsystems. Root `training/` is genuine but CLI-only and dataset-absent. Backend `/training/*` is a **different problem domain**. No UI, no checkpoint registry linkage, no pretrained-vs-finetuned comparison surface |

Additional required-capability checks:

| Requirement | Status |
| --- | --- |
| Point cloud (PLY) | Real file writer, fabricated content |
| Mesh (OBJ) | `mesh_obj_path` written by depth service; no mesh is ever generated in the 3D flow |
| GLB/glTF | ABSENT |
| Camera trajectory output | ABSENT |
| Async job dispatch for all stages | ABSENT (§3.5) |
| Job cancellation | PARTIAL — endpoint exists, revoke is best-effort, task never checks for cancel |
| Checkpointed recovery | ABSENT |
| Tests for major modules | 56 pass, 7 fail, 1 collection error; tests assert against the fabricated geometry |
| Repository under version control | ABSENT |

---

## 6. Root architectural mismatch

The existing system answers a **different problem statement**: given *overlapping still images*,
produce per-image maps plus damage/change analytics. SIH26158 asks: given *one video from one
flight*, produce a *georeferenced metric 3D model* with a defensible accuracy report.

Consequences that cannot be patched around:

1. **Entity mismatch.** `Project → Image`. SIH26158 needs `Mission → Video → FlightMetadata →
   Frames → Poses → Reconstruction → GeorefSolution → ValidationReport`. Every downstream table
   (`DepthResult`, `SegmentationResult`, `Reconstruction3D`) keys on `image_id`, not on a
   time-ordered frame sequence.
2. **No temporal model.** Nothing preserves timestamps, ordering, or inter-frame baseline —
   the quantity that decides whether SfM/MVS is even possible.
3. **No metric frame.** Without CRS/ENU, "measurement tools" in the viewer (§3.3) and the OBJ/PLY
   outputs are in arbitrary units. Any number they show is meaningless.
4. **Quality claims are constants.** Three independent fabricated or hardcoded accuracy figures
   (0.68 px reprojection, random-weight class distributions, procedural geometry) sit exactly
   where Part 7 requires measured values.

---

## 7. Remediation order (gated)

**P0 — Integrity quarantine** *(must precede any demo)*
Remove or hard-gate the fabricated paths so no user can obtain a "reconstruction" or
"segmentation" that is not derived from input: delete the synthetic pose/terrain fallbacks and
the `0.68` constant; refuse to run segmentation/damage without verified weights (mirror
`DepthModelError`); make the viewer render an explicit "no reconstruction available" state until
`plyUrl` is genuinely loaded; fix the false-success upload message. Gate: repository contains no
execution path that emits a metric it did not measure.

**P1 — Data spine**
`Mission`, `Video`, `FlightMetadata` (datum-tagged altitude), `Frame`, `CameraPose`,
`GeorefSolution`, `ValidationReport`; content-addressed artifacts; job state machine with stages,
cancel checks and resume. Gate: an end-to-end mission can be created, cancelled mid-run and
resumed without recomputation.

**P2 — Video pipeline**
FFmpeg/PyAV decode with PTS, keyframe selection by inter-frame baseline, blur/duplicate/exposure
gates, quality rows before any model sees a frame, GPS/SRT association. Gate: real 4K flight
processed; measured along-track overlap reported (this decides whether Tier A is achievable).

**P3 — Perception**
DAv2 Small (Apache-2.0 weights only) per-frame relative depth with explicit labelling;
pretrained segmentation (ADE20K mapping to the 8 required classes) + class-agnostic dynamic
masking. Gate: no fabricated class output; checkpoint hashes recorded.

**P4 — Geometry**
Sequential COLMAP + BA; open3d for fusion/meshing; Tier A/B/C selection driven by measured
overlap/parallax; observability mask. Gate: a forced-insufficient-overlap input produces a
refusal, not an empty "complete" mesh.

**P5 — Georeferencing & validation**
ENU anchor, Umeyama similarity solve, scale σ, checkpoint residuals, coverage/density metrics,
per-region uncertainty. Gate: report contains measured values or explicit `null`.

**P6 — Viewer & export**
PLY/GLB loading, layered visibility incl. unobserved regions, measurements shown with uncertainty;
PLY/OBJ/GLB/metadata/quality bundle. Gate: on-screen measurement matches a DB-backed check distance
inside reported σ.

**P7 — Model Development**
Reuse the real `training/` pipeline; restore missing `training/datasets` package; expose
pretrained-vs-finetuned comparison and checkpoint registration in the UI; keep mission processing
independent of training runs.

---

## 8. Limitations of this audit

1. No drone video, no flight metadata and no ground-truth survey data exist in the repository, so
   Parts 2, 6, 7 and 12 **could not be exercised at all**.
2. Depth inference could not be executed (weights git-ignored and absent); the `depth_engine.py`
   code path is assessed statically plus by its documented refusal behaviour.
3. The README's fine-tuned metric table cannot be verified — `training/experiments/` and
   `training/checkpoints/` are absent. Absence of evidence, not evidence of fabrication.
4. Frontend behaviour was inspected in source only; the app was not served in a browser for this
   audit, and `frontend/.next` build output was not rebuilt.
5. With no `.git`, there is no history to distinguish deliberate placeholders from regressions.
