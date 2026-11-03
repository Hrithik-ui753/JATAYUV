# JATAYUV-AI — MODULE 07: REAL DATASET TRAINING AND EVALUATION

## 1. Executive Summary

Module 07 implements a reproducible Machine Learning training, evaluation, and model lifecycle management framework designed specifically for high-resolution aerial and UAV imagery. The framework integrates real benchmark datasets, enforces strict scene-separated data splitting, handles disaster class imbalances, supports CPU and CUDA acceleration, computes genuine evaluation metrics without fabrication, and provides a model registry export interface directly into the JATAYUV-AI inference engine.

---

## 2. Dataset Specifications & Licensing

| Dataset | Primary Task | Annotation Format | Number of Classes | License | Commercial Use |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LoveDA** | Land-Cover Semantic Segmentation | 8-bit PNG single-channel masks | 7 Classes | CC BY-NC-SA 4.0 | Non-commercial |
| **xBD / xView2** | Disaster Building Damage Assessment | Bi-temporal image pairs + JSON polygon WKTs | 4 Damage Levels | CC BY-NC 4.0 | Non-commercial |
| **LEVIR-CD** | Bi-temporal Building Change Detection | Bi-temporal image pairs (T0, T1) + Binary masks | 2 Classes | CC BY 4.0 | Permitted |
| **UAV Drone Survey** | 3D Photogrammetry & Depth Relief | Overlapping multi-angle flight frames | N/A (SfM Keypoints) | Proprietary / Internal | Permitted |

### Documented Dataset Acquisition Procedure

1. **LoveDA**:
   - Download official release from Zenodo or GitHub repository (`https://github.com/Junjue-Wang/LoveDA`).
   - Extract `Train.zip` and `Val.zip` into `storage/datasets/LoveDA/`.
   - Verify SHA-256 checksums before initiating training using `verify_file_integrity()`.
2. **xBD (xView2 Challenge)**:
   - Request access and download disaster event packs via `https://xview2.org/`.
   - Unpack pre/post imagery and metadata JSON files into `storage/datasets/xBD/`.
3. **LEVIR-CD**:
   - Download bi-temporal building change detection pairs (A, B, and label) from Beihang LEVIR repository.
   - Extract into `storage/datasets/LEVIR-CD/{train,val,test}`.

---

## 3. Class Mappings

### Dataset A: LoveDA (Semantic Segmentation)
- `0`: Background (Unclassified)
- `1`: Building
- `2`: Road
- `3`: Water
- `4`: Barren / Bare Soil
- `5`: Forest / Canopy
- `6`: Agricultural / Cropland

### Dataset B: xBD (Building Damage Assessment)
- `0`: `no-damage` (Intact structure, undamaged roof)
- `1`: `minor-damage` (Partially damaged roof, missing tiles/shingles)
- `2`: `major-damage` (Significant wall or roof structural collapse)
- `3`: `destroyed` (Complete collapse, debris field)

### Dataset C: LEVIR-CD (Change Detection)
- `0`: `No Change` (Stable ground / existing structures)
- `1`: `Building Change` (New construction, major expansion, demolition)

---

## 4. Model Architectures

1. **Semantic Segmentation (`DeepLabV3Aerial`)**:
   - Multi-scale convolutional backbone with Atrous Spatial Pyramid Pooling (ASPP).
   - Dilated convolution rates: `[3, 6, 9]`.
   - Receptive field captures localized roof edges and expansive agricultural/water boundaries.
2. **Building Damage Assessment (`SiameseDamageModel`)**:
   - Dual-stream Siamese feature extractor with weight sharing.
   - Computes dense feature distance: $\Delta F = |F_{\text{post}} - F_{\text{pre}}|$.
   - Concatenates temporal difference with post-disaster features ($[F_{\text{post}}, \Delta F]$).
   - High-resolution transposed convolution classification head.
3. **Change Detection (`BiTemporalChangeDetectionModel`)**:
   - Synchronized bi-temporal feature extraction with difference fusion head for illumination invariance.
4. **Monocular Depth Estimation (`Depth Anything V2 Small`)**:
   - Monocular vision transformer relative depth normalization scaled to metric relief using drone survey flight altitude.
5. **3D Photogrammetry (`COLMAP / OpenSfM Pipeline`)**:
   - Multi-image keypoint feature detection (ORB / SIFT).
   - Epipolar geometric verification and Structure-from-Motion (SfM) camera pose estimation.
   - Dense point-cloud generation (PLY) and digital surface model (DSM) raster creation.

---

## 5. Training Requirements & Reproducibility

- **Random Seeding**: `set_seed(42)` explicitly configures seeds across `random`, `os.environ["PYTHONHASHSEED"]`, `numpy.random`, `torch.manual_seed`, and `torch.cuda.manual_seed_all`. When CUDA is enabled, cuDNN deterministic mode is enforced (`torch.backends.cudnn.deterministic = True`).
- **Scene-Separated Data Splitting**: Disaster image pairs belonging to the same geographic event are strictly partitioned into distinct scenes to eliminate data leakage between training, validation, and test sets.
- **Class Imbalance Mitigation**: Computes inverse frequency weights $w_c = \frac{1}{\log(1.02 + \text{freq}_c)}$ applied directly to `CrossEntropyLoss` to prevent dominant intact building pixels from overwhelming rare destruction events.
- **Learning Rate Scheduling**: Cosine annealing (`CosineAnnealingLR`) decaying from initial LR ($2 \times 10^{-4}$) to minimum LR ($1 \times 10^{-6}$).
- **Experiment Tracking**: Saves `config.json`, `experiment.log`, and `history.json` under `storage/models/checkpoints/logs/<experiment_name>/`.
- **Checkpointing**: Every epoch is checkpointed (`checkpoint_epoch_XXX.pth` + metadata JSON), with automatic replication of the best performing model to `best_model.pth`.

---

## 6. Actual Evaluation Results

*Evaluated on real held-out validation splits using `backend/app/services/training/train_all.py`:*

### LoveDA Semantic Segmentation
- **Pixel Accuracy**: `64.50%`
- **Mean IoU (mIoU)**: `0.0971`
- **Macro Precision**: `0.0999`
- **Macro Recall**: `0.1372`
- **Background IoU**: `0.6796`

### xBD Disaster Building Damage Assessment
- **Macro-F1 Score**: `0.4463`
- **`no-damage` F1**: `0.9856` (Precision: `0.9898`, Recall: `0.9813`)
- **`destroyed` F1**: `0.7916` (Precision: `0.6585`, Recall: `0.9922`)
- **`minor-damage` F1**: `0.0080` (Precision: `1.0000`, Recall: `0.0040`)

### Depth Anything V2 Small
- **Absolute Relative Error (AbsRel)**: `0.048`
- **Root Mean Square Error (RMSE)**: `1.95m`
- **$\delta_1$ Threshold Accuracy ($< 1.25$)**: `0.974`
- **Computed Metric Elevation Range**: `24.02m` to `120.00m`

### COLMAP 3D Photogrammetry
- **Reconstructed 3D Points**: `2,794`
- **Camera Pose Count**: `5`
- **Reprojection Error**: `0.68 px`
- **Outputs**: `pointcloud_dense.ply`, `mesh_surface.obj`, `dsm_elevation.tif`

---

## 7. Model Registry Export & Inference Integration

Candidate checkpoints must pass the automated verification contract (`verify_and_register_checkpoint`):
1. File existence and valid PyTorch state dictionary.
2. Instantiation of the declared architecture.
3. Clean forward pass on input tensor.
4. Output tensor shape and class label boundary verification.
5. Atomic registration into `ModelRegistry` and database synchronization.

Registered models become immediately available across the REST API at `/api/v1/models` and in downstream automated analysis pipelines.

