# JATAYUV — Depth Anything V2 Small: Model and Training Architecture

This document describes the exact model that JATAYUV fine-tunes, what is trained, what
is frozen, how depth is represented, and why each loss term exists. It is the reference
for `training/` and for the backend inference engine.

Everything here was verified against the official implementation and checkpoint on
2026-11-04, not inferred from memory.

---

## 1. Provenance

| Item | Value |
| --- | --- |
| Official repository | `https://github.com/DepthAnything/Depth-Anything-V2` (branch `main`) |
| Vendored code | `training/models/depth_anything_v2/` (unmodified, Apache-2.0) |
| Checkpoint | `https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth` |
| Checkpoint bytes | 99,218,434 |
| Checkpoint SHA256 | `715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378` |
| State-dict tensors | 239 |
| Parameters | 24,785,089 |
| Strict load | `model.load_state_dict(state, strict=True)` → *All keys matched successfully* |

Only the model code is vendored (12 files + licence + provenance JSON). The official
training scripts and datasets are **not** copied; JATAYUV's own training code lives in
`training/`.

The pretrained checkpoint is never overwritten. It is stored at
`training/checkpoints/pretrained/depth_anything_v2_vits.pth`; fine-tuned weights go to
`training/checkpoints/finetuned/<experiment>/`.

---

## 2. Architecture (Small)

`DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])`

```
RGB image (H, W, 3), H/W multiples of 14
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ Encoder: DINOv2 ViT-S/14                                      │
│   embed_dim 384, depth 12 blocks, 6 heads, patch 14           │
│   get_intermediate_layers(idx=[2, 5, 8, 11], cls_token=True)  │
└───────────────────────────────────────────────────────────────┘
        │  four feature maps (384 ch each) + class tokens
        ▼
┌───────────────────────────────────────────────────────────────┐
│ DPT head (``DPTHead``, features=64)                           │
│   projects: 1x1 conv 384 → [48, 96, 192, 384]                 │
│   resize_layers: stride 4 / 2 / identity / stride-2 conv     │
│   scratch: 4 × FeatureFusionBlock (residual conv unit,        │
│            optional BN, 2× bilinear upsample)                 │
│   output_conv1: 3x3 conv 64→32, ReLU                          │
│   output_conv2: 3x3 conv 32→1                                 │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
   ReLU(depth)  →  non-negative inverse-depth map  [H/14*14 grid → full res]
```

Facts that matter for training:

* **Encoder (backbone):** DINOv2 ViT-S/14, 384-dim, 12 transformer blocks, 6 heads.
  22,056,576 parameters (patch embed + tokens 753,024; blocks 0–11 21,302,784; final norm 768).
* **Decoder (head):** DPT-style multi-scale fusion head, 2,728,513 parameters.
* **Total:** 24,785,089 parameters (verified by summing both submodules).
* The vendored model exposes the backbone as `model.pretrained` (the official code uses
  `model.encoder` for the preset *string*). `training/models/dav2_factory.vit_backbone()`
  is the supported accessor.
* `forward()` applies `F.relu`, so predictions are ≥ 0.

---

## 3. Input resolution and preprocessing

The official inference path (`infer_image`) uses **518×518**, aspect ratio preserved,
`ensure_multiple_of=14`, `resize_method='lower_bound'`, bicubic interpolation, then:

| Step | Value |
| --- | --- |
| Colour order | BGR → RGB (OpenCV convention in the official code) |
| Scale | `/255.0` to `[0,1]` |
| Normalisation | ImageNet mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]` |
| Tensor layout | `1×3×H×W` float32 |

The backend engine (`backend/app/services/depth_engine.py`) imports the **official**
`Resize`, `NormalizeImage`, `PrepareForNet` transforms, so API inference and training
share identical preprocessing.

Training uses `data.image_size` (default `378`, a multiple of 14) because the reference
workstation is CPU-only; `518` is the official default and is what the API uses.

---

## 4. Output representation — and what it is not

The network outputs a **relative inverse depth** field: values are non-negative, larger
means nearer, and the absolute scale is undefined. The Depth Anything metric variants
apply `max_depth / prediction`, which only works because the raw output is inverse depth.

Consequences, enforced throughout the code:

1. The API returns `depth_type = "relative"`, `depth_unit = "relative_inverse_depth"`.
   The legacy `min_depth_m` / `max_depth_m` / `mean_depth_m` fields are `None` for
   relative results.
2. `altitude_m` in `DepthEstimationService.estimate_depth` is accepted for backward
   compatibility and **ignored**: scaling relative depth by flight altitude would be a
   fabricated metric.
3. Stored artefacts:
   * 16-bit PNG — normalised inverse depth, `0 = farthest`, `65535 = nearest`;
   * float32 `.npy` — raw (unnormalised) inverse depth, for downstream precision work;
   * TURBO colormap PNG — visualisation;
   * sidecar `.json` — model id, checkpoint path, SHA256, units, inference time.

Metric output exists **only** when a calibration is fitted against real metric ground
truth (section 7). The API then reports `depth_type = "metric_calibrated"`,
`depth_unit = "metre"`, and populates the metric fields.

---

## 5. Training targets

Because the network outputs inverse depth, ground truth is converted as

```
target_inverse = inverse_scale / depth_native
```

* **Metric supervision** (`depth.unit == "metre"`): `inverse_scale = 1.0`, so the target
  is `1/depth` in 1/metre.
* **Relative supervision** (`depth.unit == "normalized_0_1"` or `"arbitrary_scale"`):
  `inverse_scale` is the median native depth of the **training split**, giving targets
  around 1.0. The constant is stored in the manifest and in every checkpoint.

Per sample, targets are median-normalised in the dataset (`training/datasets/drone_depth.py`);
this is legitimate because SILog is scale-invariant, and the un-normalised prediction is
converted back with `depth = inverse_scale / prediction` during evaluation.

Invalid pixels are excluded by the mask: non-finite, `≤ 0`, and — for 8-bit normalised
relative depth — saturated far-plane values, which are clipping artefacts rather than
measurements.

---

## 6. Trainable parameters and freezing

Default configuration: `freeze: last_n_blocks`, `unfreeze_last_n_blocks: 2`.

| Component | Trainable | Parameters |
| --- | --- | --- |
| ViT-S patch embed, tokens, blocks 0–9 (frozen) | no | 18,505,344 |
| ViT-S blocks 10–11 + final norm (trainable) | yes | 3,551,232 |
| DPT head (trainable) | yes | 2,728,513 |
| **Total trainable** | | **6,279,745 / 24,785,089 (25.34 %)** |

(Per-block accounting: blocks 0–9 = 17,752,320; blocks 10–11 = 3,550,464; final norm
768; embeddings/tokens 753,024; head 2,728,513. Sum = 24,785,089.)

Strategies supported by `configure_trainable()`:

| Strategy | Behaviour |
| --- | --- |
| `full` | everything trainable (highest risk of catastrophic forgetting on small aerial sets) |
| `decoder_only` | frozen backbone, DPT head only |
| `last_n_blocks` | frozen backbone except the last N blocks + final norm + head (default) |
| `gradual` | starts like `last_n_blocks`, unfreezes one additional block per epoch (optimiser is rebuilt when that happens, and this is logged) |

Two AdamW parameter groups are created: backbone at `learning_rate × backbone_lr_scale`
(default 0.1) and head at `learning_rate`. Gradients are clipped to norm 1.0.

---

## 7. Losses and why

Configured in YAML (`loss.weights`), recorded in the checkpoint, and reported per term in
`training_history.csv`. Default for relative aerial supervision:

```yaml
silog: 1.0
gradient: 0.5
l1: 0.0
```

| Loss | Where | Why it is used (and when not) |
| --- | --- | --- |
| **SILog** | primary | Supervision scale is unknown (SfM, per-frame-normalised relative depth, teacher labels). SILog is invariant to a global scale factor, so it does not waste capacity fitting an arbitrary constant. `variance_focus=0.85` follows the Depth Anything / MiDaS recipe. |
| **Masked L1** | auxiliary | Interpretable absolute error in inverse-depth space on valid pixels. Enabled for metric or photogrammetry runs (`l1: 0.5`) where absolute agreement is meaningful; off for per-frame-normalised relative data, where absolute inverse values are not comparable across frames. |
| **BerHu** | alternative to L1 | L1 for small residuals, L2 beyond `0.2 × max residual`; robust to the heavy tail of aerial depth (thin poles, sky clipping). Used when a run is dominated by outliers; not combined with L1 by default because both penalise the same residual. |
| **Gradient (Sobel, masked)** | structural | Plain photometric losses over-smooth roofs, kerbs and vegetation boundaries. The term weights the gradient difference by GT edge magnitude (normalised) and is masked so invalid GT never creates edges. |
| **Ordinal** | optional, weight 0 | Pairwise ranking on sampled pixels. Only for ordinal-consistency ablations on relative-only data; default weight is 0 because SILog already encodes ordering. |

Losses are **not** stacked arbitrarily: a run uses either `l1` or `berhu` (not both), and
`ordinal` is off unless an ablation explicitly enables it.

---

## 8. Metric calibration (only path to metres)

`training/evaluation/calibration.py` fits, on a metric ground-truth split:

```
1 / depth ≈ a · pred + b      →      depth = 1 / (a · pred + b)
```

The fit is closed-form least squares over valid pixels; it is validated on a **separate**
metric split and reports AbsRel/RMSE/δ in metres. Coefficients are written into the
checkpoint under the `calibration` key. `DepthEngine.calibrated_metric()` uses them, and
only then does the API report `metric_calibrated`.

Without metric ground truth the calibration command refuses to run — relative data
cannot be calibrated into metres.

---

## 9. Checkpoint format

`training/checkpoints/finetuned/<experiment>/{best_model.pth,last_checkpoint.pth}`
(schema `jatayuv.depth.finetune/1`) records:

* `model_state`, `optimizer_state`, `scheduler_state`, `scaler_state` (resume support);
* `config` (full YAML), `loss_weights`, `freeze_strategy`, `param_counts`;
* `dataset` (manifest path + SHA256, inverse scale, split sizes, depth types);
* `base_checkpoint` (path + SHA256 of the official release);
* `depth_claim: "relative"`, `calibration` (null until fitted);
* `epoch`, `global_step`, `best_val`, `metrics`, `git_commit`, `saved_utc`.

Loading is always `strict=True` against the Small architecture, so a checkpoint of a
different size or a renamed parameter set fails loudly (see `DepthModelError`).
