# JATAYUV — Drone / Aerial Depth Dataset Research

Research date: 2026-11-04. Facts below were taken from official dataset pages, papers and
repository metadata while writing the acquisition catalogue
(`training/datasets/acquisition/catalog.py`). Licence terms must be re-verified on the
official page at download time — this document is planning material, not a licence grant.

The acquisition manager refuses datasets that require registration or author approval and
prints the documented procedure instead. No access control, login, payment or terms form
was bypassed while building this pipeline.

---

## 1. Summary matrix

| Dataset | Depth | Metric depth | Calibration / poses | Licence | Commercial | Access | Size |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **SkyScenes** | dense, relative (uint8) | no | CARLA pose metadata, no intrinsics | MIT | **yes** | open | ~890 GB full; ~1.7 GB per RGB shard |
| **TartanAir** | dense, **metric** | yes | intrinsics + poses | BSD-3-Clause (HF card) | yes | open | ~1.1 TB; 2–7 GB per shard |
| **Mid-Air** | dense, metric | yes | intrinsics + poses + IMU | research agreement | no | registration | ~1.5 TB (per-scene subsets available) |
| **UAVid** | none | – | – | CC BY-NC-SA 4.0 | no | registration | ~4.5 GB |
| **VisDrone** | none | – | – | research only | no | registration (Google Drive) | ~1.4 GB |
| **UAVDT** | none | – | – | academic only | no | registration | ~3 GB |
| **DFC2019** | LiDAR DSM (elevation) | yes (elevation) | satellite stereo | contest terms | no | registration | ~50 GB |
| **ETH3D** | laser-scan GT | yes | calibrated multi-view | non-commercial | no | registration | ~100 GB |
| **KITTI depth** | semi-dense LiDAR | yes | calibration + poses | CC BY-NC-SA 3.0 | no | registration | ~40 GB |
| **DDOS / WildUAV** | depth (synthetic / photogrammetric) | yes (claimed) | partially | **unverified** | unknown | registration | unpublished / ~10 GB |

Detailed records (paper, citation, annotations, suitability) live in the catalogue and are
printed by:

```bash
python -m training.datasets.acquisition.manager --list
python -m training.datasets.acquisition.manager --plan skyscenes
```

---

## 2. Dataset-by-dataset notes

### 2.1 SkyScenes — **downloaded and validated**
* Official page: https://hoffman-group.github.io/SkyScenes/ — paper: Khose et al.,
  *SkyScenes: A Synthetic Dataset for Aerial Scene Understanding*, ECCV 2024
  (arXiv 2312.06719).
* 33,600 images, 2160×1440 PNG, 8 towns × 12 height/pitch settings × 5 weather sets,
  23-class semantic + instance annotations, dense depth.
* **Depth is 8-bit PNG normalised per shard. No metric scale is published.** It is
  therefore `type="relative"`, `unit="normalized_0_1"` in the manifest and can never
  support a metric claim.
* Licence MIT → commercial reuse permitted with attribution.
* Access: direct download from Hugging Face, no login, no form.

### 2.2 TartanAir
* https://tartanair.org/ — Wang et al., IROS 2020 (arXiv 2003.14338). Simulated
  UAS/ground environments; dense metric depth, stereo, segmentation, poses, intrinsics.
* Licence BSD-3-Clause per the Hugging Face card → commercial reuse permitted.
* Each `image_left` / `depth_left` shard is multi-GB (≈1.1 TB total), so it was **not**
  downloaded here; it is a good next source for metric supervision on a machine with
  bandwidth/storage for it.

### 2.3 Mid-Air
* https://midair.ulg.ac.be/ — Fonder & Van Droogenbroeck, CVPR-W 2019
  (arXiv 1811.03080). 420k synthetic frames over 54 scenes, 1024×1024, dense depth,
  stereo, poses, intrinsics — the best-fit **metric** drone supervision source.
* Access requires the official licence agreement form; the manager refuses automatic
  download and prints the procedure. **Status: not acquired.**

### 2.4 UAVid
* https://uavid.nl/ — Lyu et al., ISPRS J. 2020 (arXiv 1912.07755). 300 train / 70 val
  4K frames from 42 sequences + 30 video sequences; 8-class semantic masks; **no depth**.
* CC BY-NC-SA 4.0, non-commercial, registration form required.
* Use case: RGB domain adaptation and teacher pseudo-labelling, not depth supervision.

### 2.5 VisDrone
* https://github.com/VisDrone/VisDrone-Dataset — Zhu et al., TPAMI 2021
  (arXiv 2001.06303). 10,209 images + 288 clips, 14 cities, object annotations only.
* Research-use terms; official links are Google Drive folders. Not auto-downloaded.

### 2.6 UAVDT
* https://sites.google.com/site/daviddo0323/projects/uavdt — Du et al., ECCV 2018.
  100 sequences / 80k frames, 1080×540, object tracking annotations, weather and
  altitude attributes (useful for condition-stratified evaluation). Academic use only.

### 2.7 DFC2019 (IEEE GRSS Data Fusion Contest)
* Track 3 provides WorldView-3 stereo + LiDAR DSM/DTM over Jacksonville, 2000×2000
  tiles. Elevation-derived supervision only; not nadir UAV RGB. Registration required.

### 2.8 ETH3D
* https://www.eth3d.net/ — Schöps et al., CVPR 2017 (arXiv 1704.03660). Calibrated
  multi-view sets with laser-scanned ground truth; best used to validate an MVS /
  photogrammetry depth pipeline, not an aerial domain. Registration required.

### 2.9 KITTI depth
* http://www.cvlibs.net/datasets/kitti/eval_depth.php — semi-dense LiDAR depth,
  1242×375, calibration and poses, CC BY-NC-SA 3.0. Ground-vehicle domain: supplementary
  cross-domain experiments only (explicitly not a substitute for drone evaluation).

### 2.10 Other sources reviewed
* **DDOS** (Drone Depth & Obstacle Segmentation, arXiv 2312.12494): synthetic drone depth;
  licence unverified — must be confirmed with the authors before any use.
* **WildUAV** (CVPR-W 2022): real UAV flights with photogrammetric 3D reference; promising
  for the COLMAP-style pipeline once access terms are confirmed.
* **UAVScenes / MARS-LVIG**: LiDAR + camera UAV data, registration required.

---

## 3. What was actually acquired

| Dataset | Files on disk | Verified | Licence | Purpose |
| --- | --- | --- | --- | --- |
| SkyScenes `H_15_P_0/ClearNoon/Town01` | 69 RGB + 70 depth + 69 metadata | yes (pixel-level decode) | MIT | fine-tuning + temporal validation |
| SkyScenes `H_15_P_0/ClearNoon/Town02` | 69 RGB + 70 depth | yes | MIT | held-out test town |

Storage: 3.2 GB of downloaded shard archives (`datasets/raw/skyscenes/_archives/`, kept
for re-extraction and integrity re-checks) + 569 MB of extracted frames
(`datasets/raw/skyscenes/H_15_P_0/`). Counts: see
`datasets/reports/skyscenes_relative_summary.md`; the acquisition record is
`datasets/raw/skyscenes/acquisition.json` (`--verify skyscenes` → `ok`, 6 files).

### Integrity finding (important)

Each SkyScenes RGB shard on Hugging Face contains one **malformed tar member**: the GNU
`@LongLink` header is written as a regular file with a bogus multi-GB size. Extraction with
`tar` or Python's `tarfile` yields one 1.3–1.4 GB junk file named after the first frame.
The pipeline rejects it (PNG signature check + image decode) and uses the remaining 69
valid frames per town; the depth shards are unaffected (70 files). This is recorded here
so the loss of one frame per shard is not mistaken for a pipeline bug.

The depth shard contains one more frame than the RGB shard, so 69 RGB/depth pairs per town
are used (138 total).

---

## 4. Recommended acquisition plan (in order)

1. **Mid-Air** — request access now; it is the only realistic source of *metric* aerial
   depth. Needed to run Experiments B-metric and to fit a real metric calibration.
2. **Own JATAYUV flights** — the pipeline in `training/preprocessing/media_ingest.py`
   handles JPG/PNG/TIFF/MP4/MOV, quality filtering, EXIF/GPS, and flight grouping. With
   ≥ 100 overlapping frames per flight, COLMAP MVS (Phase 5B) produces relative depth.
3. **TartanAir** (metric synthetic, BSD-3) — if 2–3 GB per shard is acceptable, it gives
   metric targets much closer to a real UAV camera than SkyScenes' 8-bit maps.
4. **UAVid / VisDrone** — RGB-only; use for teacher pseudo-labels and real-domain
   evaluation once registration is completed.
5. **UAVScenes / WildUAV / DDOS** — after confirming licence terms.

Estimated storage: ~20 GB is enough for the current recipe; a full metric fine-tune with
TartanAir or Mid-Air needs 100–500 GB. Training the Small model needs ~2 GB of GPU RAM at
378² and batch 2 (≈6 GB at 518² with AMP).

---

## 5. Licensing and attribution

* **SkyScenes** — MIT. Cite: Khose, Pal, Agarwal, Deepanshi, Hoffman, Chattopadhyay,
  *SkyScenes: A Synthetic Dataset for Aerial Scene Understanding*, ECCV 2024.
* **Depth Anything V2** — model code Apache-2.0; official checkpoint released by the
  Depth Anything team (Yang et al., *Depth Anything V2*, NeurIPS 2024). Cite it in any
  derivative work.
* Any dataset marked non-commercial (UAVid, VisDrone, UAVDT, KITTI, ETH3D, Mid-Air,
  DFC2019) must not be used to train a commercially deployed JATAYUV model without
  written permission from the dataset owner.

The manifest records `license` per sample, and every dataset summary report repeats it.
