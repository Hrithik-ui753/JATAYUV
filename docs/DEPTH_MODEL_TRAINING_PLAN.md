# JATAYUV — Drone Depth Anything V2 Small: Training Plan and Execution Record

Status as of 2026-11-04. This document is both the plan and the truthful record of what
was implemented, downloaded, trained, evaluated and integrated. Nothing in the result
tables below is estimated; every number was produced by a command in section 9.

---

## 1. Repository audit (Phase 1)

### 1.1 What existed

| Area | Finding |
| --- | --- |
| Backend | FastAPI + SQLAlchemy 2.0 + Celery, `backend/app/{api,services,models,schemas,workers}` |
| Frontend | Next.js 14 dashboard with depth/segmentation/damage/change tabs |
| Existing ML training | `backend/app/services/training/` — DeepLabV3 (LoveDA), Siamese (xBD), Bi-temporal (LEVIR-CD). **No depth training existed.** |
| Existing "Depth Anything V2" | `backend/app/services/depth_estimation.py` defined a 3-layer CNN (`DepthEstimationModel`) with BatchNorm and a `Sigmoid` head. Its weights were saved as `storage/models/checkpoints/depth_anything_v2_small.pth` (1,043,362 bytes) with `architecture="DepthAnythingV2Small"`. |
| Fabricated metrics in the repo | `train_all.py` wrote `abs_rel=0.048, rmse=1.95, delta1=0.974` for that CNN; the API seeded a model card claiming `AbsRel=0.043, delta1=0.981` for "Depth Anything V2 — Large"; `depth_estimation.py` converted relative output to "metres" by multiplying the flight altitude. |
| Datasets in repo | Synthetic fixtures only (LoveDA/xBD/LEVIR-CD/5 fake "drone" frames). No real aerial depth. |
| Tests | 63 passing tests, including `test_ai_inference_and_3d.py` which asserted `min_depth_m > 0` on the fabricated metric output. |

### 1.2 Environment (measured)

| Item | Value |
| --- | --- |
| OS | Windows 10/11 (Git Bash), D: drive with ~96 GB free |
| Python | 3.14.3 |
| PyTorch | 2.15.0+cpu (no CUDA build) |
| CUDA available | **No** (`torch.cuda.is_available() == False`) |
| torchvision / timm | 0.29.2+cpu / 1.0.30 |
| OpenCV | 5.0.0 (headless), Pillow 12.1.1, NumPy 2.4.3 |
| COLMAP | **not installed** |
| ffmpeg | **not installed** (video frames are read with OpenCV instead) |
| CPU | 12 logical cores |

**Hardware consequence:** all training and evaluation in this document ran on CPU. A
single 378² image step takes ≈1 s; 518² inference ≈0.19 s/image. CUDA code paths are
implemented (AMP, `peak_gpu_mb`, device selection) but could not be executed here.

### 1.3 What was corrected

* The toy CNN was removed from the depth path entirely. Depth inference now always loads
  the official Small architecture and validates the checkpoint (SHA256 + strict load).
* `altitude_m` is accepted but **ignored** — relative depth is no longer scaled into
  fake metres. API responses carry `depth_type`/`depth_unit` and return `null` metric
  fields for relative output.
* `train_all.py` no longer writes invented depth metrics; it verifies the official
  checkpoint and registers provenance only.
* The seeded API model cards no longer claim accuracy numbers for depth.
* The stale `storage/models/checkpoints/depth_anything_v2_small.pth` (CNN weights labelled
  as DAv2) was deleted.
* New non-destructive DB columns store model id, checkpoint SHA256, input size, latency
  and relative-depth statistics (`ensure_depth_result_schema()` adds them to existing
  SQLite databases).

---

## 2. Base model (Phase 2)

Only the official **Small** model is used: `encoder='vits'`, `features=64`,
`out_channels=[48,96,192,384]`, 24,785,089 parameters, 239 state-dict tensors,
SHA256 `715fade1…60e1378` (99,218,434 bytes). Verified by
`python -m training.models.dav2_factory` (strict load, all keys matched). Full details:
[`DEPTH_MODEL_ARCHITECTURE.md`](./DEPTH_MODEL_ARCHITECTURE.md).

The pretrained checkpoint is preserved separately at
`training/checkpoints/pretrained/depth_anything_v2_vits.pth`; fine-tuned weights are never
written over it.

---

## 3. Data (Phases 3–6)

* Acquisition catalogue: 11 datasets with licence/access/metric-depth fields
  (`training/datasets/acquisition/catalog.py`), resumable downloads, SHA256 checks, safe
  extraction, corrupt-file detection, per-dataset `acquisition.json`, global
  `datasets/manifests/acquisition_manifest.json`.
* Research and licences: [`DEPTH_DATASET_RESEARCH.md`](./DEPTH_DATASET_RESEARCH.md).
* Downloaded and pixel-verified: **SkyScenes** (MIT) Town01 + Town02, `H_15_P_0` /
  `ClearNoon` → 138 usable RGB/depth pairs at 2160×1440.
* Supervision available: dense **relative** depth (uint8, no metric scale). No metric
  aerial depth (LiDAR/stereo) has been acquired — Mid-Air/TartanAir are blocked by
  agreement or size.
* Own flight data: **none present in the repository**. `media_ingest.py` is implemented
  and unit-tested on synthetic media; it has not been run on real JATAYUV flights.
* Photogrammetry: `photogrammetry_colmap.py` implements the full COLMAP SfM + MVS + point
  projection pipeline and fails loudly when COLMAP is missing (it is missing here).
* Teacher pseudo-labelling: `teacher_pseudo_depth.py` implemented (with flip-TTA
  confidence), **not executed** — there is no real drone RGB to label.

### Dataset build (executed)

| Split | Samples | Source | Rule |
| --- | --- | --- | --- |
| train | 55 | SkyScenes Town01 | frames 1–55 of the flight |
| val | 14 | SkyScenes Town01 | **temporally last 14 frames** (in-domain early stopping) |
| test | 69 | SkyScenes Town02 | **unseen town**, independent scene |
| **total** | **138** | MIT | no random frame-level splitting anywhere |

`inverse_scale = 0.352941` (median native depth of the training split), mean valid-depth
coverage 0.56, image size 2160×1440 → resized to 378×378 for training.

---

## 4. Fine-tuning strategy (Phase 7)

| Setting | Value |
| --- | --- |
| Optimiser | AdamW, head lr 3e-5, backbone lr 3e-6, weight decay 1e-4 |
| Scheduler | linear warmup 20 steps → cosine to 5 % of base lr |
| Freezing | `last_n_blocks` (2): 6,279,745 / 24,785,089 trainable (25.3 %) |
| Loss | SILog 1.0 + masked gradient 0.5 (inverse-depth space) |
| Batch / accumulation | 2 × 1 |
| Epochs | 5 (no early stop triggered) |
| Precision | fp32 (AMP auto-disabled on CPU) |
| Resolution | 378×378 (multiple of 14) |
| Augmentation | random resized crop 0.7–1.0, horizontal flip, brightness/contrast/gamma/haze |
| Seed | 42, deterministic algorithms, resumable checkpoints |

Why these choices: SILog is the only well-posed objective for scale-ambiguous relative
supervision; freezing all but the last two ViT blocks prevents catastrophic forgetting on
55 training images; the small head LR keeps the pretrained DPT head stable while the
domain shifts. The gradient term preserves roof/kerb edges. Full rationale in
`docs/DEPTH_MODEL_ARCHITECTURE.md` §6–7.

---

## 5. Experiments (Phase 8)

| ID | Arm | Status |
| --- | --- | --- |
| A | Pretrained DAv2-Small baseline (zero-shot) | **executed** (evaluated on the same 69 test frames) |
| B | Fine-tune on dense (relative) aerial depth — SkyScenes | **executed** (5 epochs, CPU) |
| C | Fine-tune on COLMAP photogrammetry depth | blocked: COLMAP not installed, no own flights → config ready (`exp_c_photogrammetry.yaml`) |
| D | Combined real + photogrammetry | blocked for the same reason → config ready |
| E | Teacher pseudo-label training | blocked: no real drone RGB → config ready |

Every arm uses the same independent test split and the same evaluation code.

### Measured results (baseline vs fine-tuned, 69 held-out Town02 frames)

| Metric | Pretrained | JATAYUV fine-tuned | Change | Direction |
| --- | --- | --- | --- | --- |
| raw SILog (inverse space) | 4.5256 | **1.3246** | −70.7 % | lower better |
| AbsRel (scale+shift aligned) | 0.2893 | **0.0710** | −75.5 % | lower better |
| RMSE (aligned, normalised units) | 0.1063 | **0.0346** | −67.5 % | lower better |
| δ<1.25 (aligned) | 0.5342 | **0.9469** | +77.3 % | higher better |
| Ordinal consistency | 0.9275 | 0.9211 | −0.7 % | higher better |
| Latency (CPU, 378², 1 img) | 184.0 ms | 189.4 ms | +2.9 % | – |
| Parameters / size | 24.79 M / 94.6 MB | 24.79 M / 142.1 MB | – | – |

**Interpretation, and what these numbers are not:**

* Ground truth is SkyScenes' normalised relative depth, so AbsRel/RMSE here are
  *scale+shift aligned relative* errors. They are **not** metric accuracy in metres.
* The test town (Town02) was never trained on, but it shares the CARLA renderer,
  camera, weather and altitude with the training town. This measures intra-domain
  improvement on synthetic aerial data, not real-world drone accuracy.
* Ordinal consistency (a scale-free ranking measure) is flat, which is expected: the
  pretrained model already ranks pixels well; fine-tuning mostly fixes scale/shape.
* One seed, one dataset, 55 training images. No variance estimate across seeds.

Artefacts: `training/experiments/exp_b_skyscenes_relative/{metrics.json,
training_history.csv, experiment_config.yaml, eval/metrics.json, eval/evaluation_report.md,
eval/comparisons/*.png}`; checkpoints at
`training/checkpoints/finetuned/exp_b_skyscenes_relative/`.

---

## 6. Integration (Phase 10)

* `backend/app/services/depth_engine.py` — lazy, thread-safe engine; `pretrained` and
  `jatayuv_drone_v1` checkpoints; strict validation; rejects a "fine-tuned" checkpoint
  that is byte-identical to the official release; CPU/CUDA; configurable input size
  (`JATAYUV_DEPTH_INPUT_SIZE`, default 518).
* `backend/app/services/depth_estimation.py` — keeps the historic
  `estimate_depth(...)` signature used by the API and Celery; saves 16-bit normalised
  inverse-depth PNG, TURBO colormap, raw float32 `.npy`, optional OBJ mesh and a JSON
  sidecar with checkpoint provenance.
* API:
  * `POST /api/v1/analysis/depth` accepts optional `model_id` and `input_size`,
    returns `depth_type`, `depth_unit`, `is_metric`, `relative_*`, `model_*`,
    `checkpoint_sha256`, `inference_ms`, and `null` metric fields for relative output;
  * `GET /api/v1/analysis/depth/models` lists both checkpoints with availability;
  * `GET /api/v1/analysis/depth/{image_id}` returns the same shape.
* Celery: `task_run_depth_estimation(..., model_id, input_size)` persists the same
  provenance and fails cleanly with a reason when a checkpoint is missing.
* Frontend: the dashboard labels the model and depth type instead of claiming
  "relative-to-metric elevation".

---

## 7. Tests (Phase 11)

`backend/tests/test_depth_pipeline.py` (26 tests) covers dataset loading, RGB/depth/mask
alignment under resize and augmentation, target normalisation, invalid/saturated masks,
checkpoint loading and strict rejection of foreign checkpoints, parameter counts and
freeze strategies, a forward pass, every loss, scale+shift alignment and relative
evaluation, metric-calibration guards, split leakage (synthetic and the real SkyScenes
manifest), safe archive extraction, own-flight media ingestion, and the depth-engine
catalogue (`list_models`, alias resolution, relative-only output, no calibration ⇒ no
metres).

The API contract itself (relative result ⇒ `min_depth_m is null`, `depth_type ==
"relative"`, model provenance present) is asserted end-to-end in
`backend/tests/test_ai_inference_and_3d.py` and `backend/tests/test_module08_integration.py`.

No CUDA-specific test is included because no CUDA device exists on the reference machine;
CUDA code paths (`amp`, `peak_gpu_mb`, device selection) are therefore unverified.

Full suite: `89 passed` (63 pre-existing + 26 new), 2026-11-04.

---

## 8. Hardware and storage requirements

| Task | CPU (this machine) | GPU (recommended) |
| --- | --- | --- |
| Fine-tune, 55 imgs, 378², 5 epochs | ~38 s/epoch, 3.6 min total on 12 cores (measured 10:04:28→10:08:05) | < 1 min total |
| Full 518² batch-4 fine-tune | not practical | ~6–8 GB VRAM with AMP |
| Inference | 185 ms/image | ~15–30 ms/image |
| Disk: checkpoints | 94.6 MB pretrained + 142 MB per fine-tuned checkpoint | same |
| Disk: current dataset | ~3.8 GB (3.2 GB shard archives + 569 MB extracted frames) | – |

---

## 9. Exact commands

```bash
# 0. environment (repo root)
python -m pip install -r backend/requirements.txt

# 1. verify / download the official checkpoint (SHA256-checked)
python -m training.models.dav2_factory --download
python -m training.models.dav2_factory        # prints verification report

# 2. dataset research / acquisition (permitted sources only)
python -m training.datasets.acquisition.manager --list
python -m training.datasets.acquisition.manager --plan skyscenes
python -m training.datasets.acquisition.manager --acquire skyscenes \
    --select altitude=H_15_P_0 --select weather=ClearNoon --select town=Town01

# 3. build manifest + leakage-free splits + summary report
python -m training.preprocessing.prepare_dataset \
    --config training/configs/depth_anything_v2_small.yaml

# 4. fine-tune (reproducible; resumable)
python -m training.trainers.train_depth \
    --config training/configs/depth_anything_v2_small.yaml
#   resume:  --resume training/checkpoints/finetuned/<exp>/last_checkpoint.pth

# 5. evaluate pretrained vs fine-tuned on the identical test split
python -m training.evaluation.evaluate_depth \
    --config training/configs/depth_anything_v2_small.yaml \
    --checkpoint training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth

# 6. own flights (when available)
python -m training.preprocessing.media_ingest \
    --input <flight_dir> --output datasets/manifests/own_flights.json
python -m training.depth_generation.teacher_pseudo_depth \
    --input datasets/manifests/own_flights.json \
    --output datasets/manifests/own_flights_pseudo.json
python -m training.depth_generation.photogrammetry_colmap \
    --images datasets/processed/own_frames/<flight> --output-dir datasets/depth_maps/colmap

# 7. tests
python -m pytest backend/tests -q
```

---

## 10. Deliverable status

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Dataset research report | done (`DEPTH_DATASET_RESEARCH.md`) |
| 2 | Acquisition scripts | done (`training/datasets/acquisition/`) |
| 3 | Video frame extraction pipeline | done, unit-tested on synthetic video |
| 4 | Depth-label generation | teacher + COLMAP + real-depth import implemented; teacher/COLMAP **not executed** (no data / no binary) |
| 5 | Dataset preparation | done, executed (138 samples, 3 splits) |
| 6 | DAv2-Small fine-tuning implementation | done, executed (5 epochs) |
| 7 | Training configuration | done (`configs/*.yaml`, 5 experiments) |
| 8 | Evaluation implementation | done, executed |
| 9 | Baseline vs fine-tuned report | done, measured |
| 10 | Visual depth comparison samples | done (`eval/comparisons/*.png`) |
| 11 | Best/last checkpoints | done (best 142 MB, last 142 MB) |
| 12 | Inference API integration | done, tested on CPU |
| 13 | Unit/integration tests | done (`test_depth_pipeline.py`) |
| 14 | Training instructions | this document + README |
| 15 | Hardware/storage requirements | §8 |
| 16 | Dataset licences/attribution | research doc §5 |
| 17 | Known limitations | §11 |

---

## 11. Known limitations and blockers

1. **No metric aerial ground truth.** Every accuracy number here is relative/aligned.
   Mid-Air or a LiDAR-equipped JATAYUV flight is required before any metre-level claim.
   The metric calibration code exists and refuses to run without metric GT.
2. **Synthetic domain only.** SkyScenes is CARLA-rendered; the large alignment error of
   the pretrained model (AbsRel 0.289) reflects that domain gap. Real drone imagery
   (VisDrone/UAVid/own flights) is needed to measure real-world benefit.
3. **Tiny training set** (55 frames, one town, one altitude, one weather set). No
   altitude/weather robustness study could be run — only one shard configuration is on
   disk. Adding `H_35_P_*`/`H_60_P_*` and other weather shards is a config change plus
   ~1.7 GB per shard.
4. **No own-flight data and no COLMAP** on this workstation, so Experiments C/D/E were
   not executed; COLMAP's MVS path is therefore untested against a real reconstruction.
5. **CPU-only environment**: AMP, CUDA memory reporting and CUDA tests are implemented
   but unverified on hardware. Timing numbers are CPU numbers.
6. **Validation split is a temporal tail of the training flight**, not an independent
   location (only two towns were downloaded). The test split *is* an independent town.
7. **Single seed / single run**; no confidence intervals. The run was reproduced twice
   with identical metrics, which confirms determinism but not statistical robustness.
8. **`altitude_m` is deliberately ignored.** Any consumer expecting metric output from a
   relative checkpoint will now get `null` instead of a fabricated number — this is
   intentional and documented in the API schema.
