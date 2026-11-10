# JATAYUV — Official 10-Slide Project Presentation
**Problem Statement ID:** SIH26158 | **Organization:** National Technical Research Organisation (NTRO)  
**Project Title:** Single-Pass Drone Video to Accurate 3D Model Generation System  
**Theme:** Robotics and Drones | **Visual Styling:** Elegant Cream-and-White Academic / College Format

---

<style>
.slide-deck {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  color: #1C1917;
  background-color: #FAF6F0;
  padding: 24px;
}
.slide-card {
  background: #FFFFFF;
  border: 1px solid #E7DAC7;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 32px;
  box-shadow: 0 4px 16px rgba(44, 30, 20, 0.06);
}
.slide-header {
  border-bottom: 2px solid #E7DAC7;
  padding-bottom: 12px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.slide-title {
  color: #0F291E;
  font-size: 22px;
  font-weight: 800;
  margin: 0;
}
.slide-num {
  font-size: 13px;
  font-weight: 700;
  color: #854D0E;
  background: #FEF9C3;
  padding: 4px 10px;
  border-radius: 9999px;
  border: 1px solid #FDE047;
}
.badge-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  background: #F5EBE1;
  color: #78350F;
  border: 1px solid #D7C4B0;
  margin-right: 6px;
}
.tech-box {
  background: #FAF6F0;
  border: 1px solid #E7DAC7;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
}
.grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.grid-3col {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
table.slide-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-top: 10px;
}
table.slide-table th {
  background: #F5EBE1;
  color: #1C1917;
  padding: 8px 12px;
  border: 1px solid #E7DAC7;
  text-align: left;
}
table.slide-table td {
  padding: 8px 12px;
  border: 1px solid #E7DAC7;
}
</style>

<div class="slide-deck">

<!-- ======================================================================= -->
<!-- SLIDE 1 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">JATAYUV: Single-Pass Drone Video to Georeferenced 3D Models</h2>
    <span class="slide-num">SLIDE 01 / 10</span>
  </div>
  
  <p><span class="badge-tag">SIH26158</span><span class="badge-tag">NTRO</span><span class="badge-tag">ROBOTICS & DRONES</span></p>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 16px; font-weight: 700; margin-top: 0;">Project Identity &amp; Mission Statement</h3>
      <p style="font-size: 13px; line-height: 1.6; color: #44403C;">
        <strong>Organization:</strong> National Technical Research Organisation (NTRO)<br>
        <strong>Operational Mandate:</strong> Ingest continuous, single-pass aerial drone video combined with onboard flight telemetry (GPS/IMU) and transform it into metrically calibrated, georeferenced 3D point clouds, textured meshes, and geospatial elevation artifacts without synthetic fabrications.
      </p>
      
      <div class="tech-box">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; color: #78350F; text-transform: uppercase;">Strategic Target Applications</h4>
        <ul style="font-size: 12px; line-height: 1.6; margin: 0; padding-left: 20px; color: #292524;">
          <li>Strategic border terrain reconnaissance and inaccessible zone mapping</li>
          <li>Rapid humanitarian disaster and building structural collapse assessment (xBD)</li>
          <li>Critical infrastructure inspection &amp; multi-temporal change surveillance</li>
          <li>Digital twin generation for urban planning and defense topography</li>
        </ul>
      </div>
    </div>

    <div>
      <div class="tech-box" style="height: 100%; display: flex; flex-direction: column; justify-content: center; text-align: center; border: 2px dashed #D7C4B0;">
        <div style="font-size: 42px; margin-bottom: 8px;">🛰️ ➔ ☁️ ➔ 🗺️</div>
        <h4 style="margin: 0; font-size: 14px; color: #0F291E;">Continuous Single-Pass Video Pipeline</h4>
        <p style="font-size: 11px; color: #78716C; margin-top: 6px; padding: 0 16px;">
          From uncalibrated video streams to rigorously georeferenced metric 3D point clouds.
        </p>
        <div style="margin-top: 12px; font-size: 11px; font-family: monospace; color: #065F46; background: #ECFDF5; padding: 6px 12px; border-radius: 4px; display: inline-block;">
          Verified Codebase | 169 Tests Passed | Real COLMAP 4.2.1 | Depth Anything V2 Small
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 2 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Operational Context &amp; Problem Analysis</h2>
    <span class="slide-num">SLIDE 02 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 15px; font-weight: 700;">The Single-Pass Drone Reconstruction Bottleneck</h3>
      <p style="font-size: 12px; line-height: 1.6; color: #44403C;">
        Traditional aerial photogrammetry demands exhaustive multi-pass cross-grid flight missions with 70–80% lateral and longitudinal overlap. In tactical, border, or crisis environments, drones cannot safely linger or execute repeated flight loops.
      </p>

      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Single-Pass Trajectory:</strong> Monocular camera video with forward-only flight baseline lacks closed-loop bundle adjustment tie-points.</li>
        <li><strong>Motion Blur &amp; Hover Duplicates:</strong> Drone platform vibrations cause motion blur; platform hovering injects redundant near-duplicate frames that crash SfM bundle adjustment.</li>
        <li><strong>Dynamic Object Pollution:</strong> Moving vehicles, civilian traffic, and personnel introduce geometric ghosting into 3D meshes.</li>
        <li><strong>Scale Ambiguity:</strong> Monocular cameras suffer from unobservable projective depth scale unless fused with real GPS/IMU telemetry.</li>
      </ul>
    </div>

    <div>
      <div class="tech-box">
        <h3 style="color: #78350F; font-size: 13px; font-weight: 700; margin-top: 0;">JATAYUV Engineering Standards</h3>
        <table class="slide-table">
          <thead>
            <tr>
              <th>Common Flaw in Prototypes</th>
              <th>JATAYUV Strict Requirement</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Procedural cubes / synthetic PLY geometry</td>
              <td><strong>Real COLMAP 4.2.1 SfM/MVS</strong> only; explicit 503 if unavailable</td>
            </tr>
            <tr>
              <td>Fabricated metric depth from grayscale pixels</td>
              <td><strong>Strict relative inverse depth</strong> without uncalibrated metric claims</td>
            </tr>
            <tr>
              <td>Swallowing failed uploads with mock success</td>
              <td><strong>Atomic transaction verification</strong> with SHA-256 validation</td>
            </tr>
            <tr>
              <td>Random camera poses / fabricated GPS</td>
              <td><strong>Umeyama 7-DoF similarity transform</strong> with GCP/checkpoint RMSE</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 3 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Proposed Solution: Dual AI &amp; Photogrammetry Paradigm</h2>
    <span class="slide-num">SLIDE 03 / 10</span>
  </div>

  <div class="grid-3col">
    <div class="tech-box">
      <h3 style="color: #0F291E; font-size: 13px; font-weight: 700; margin-top: 0;">1. Temporal &amp; Quality Conditioning</h3>
      <p style="font-size: 11px; line-height: 1.5; color: #44403C;">
        Sub-second PyAV stream demuxing combined with Laplacian blur variance scoring. Perceptual dHash difference filtering drops redundant hover frames while preserving smooth camera baseline motion.
      </p>
      <div style="font-size: 11px; font-family: monospace; color: #78350F;">• PyAV / FFmpeg demux<br>• Laplacian variance &gt; threshold<br>• Perceptual dHash hamming &gt; 4</div>
    </div>

    <div class="tech-box">
      <h3 style="color: #0F291E; font-size: 13px; font-weight: 700; margin-top: 0;">2. Deep Aerial Perception</h3>
      <p style="font-size: 11px; line-height: 1.5; color: #44403C;">
        Depth Anything V2 Small extracts relative inverse depth maps with fine-grained edge geometry. SegFormer performs 8-class aerial segmentation, and YOLO generates exclusion masks for moving vehicles and personnel.
      </p>
      <div style="font-size: 11px; font-family: monospace; color: #78350F;">• DAv2-Small (24.78M params)<br>• SegFormer LoveDA land-cover<br>• Dynamic object exclusion masks</div>
    </div>

    <div class="tech-box">
      <h3 style="color: #0F291E; font-size: 13px; font-weight: 700; margin-top: 0;">3. Photogrammetry &amp; Georeferencing</h3>
      <p style="font-size: 11px; line-height: 1.5; color: #44403C;">
        COLMAP Structure-from-Motion triangulates camera poses and sparse landmarks. 7-DoF Umeyama similarity transformation aligns arbitrary reconstruction axes to real-world metric UTM/WGS84 coordinates.
      </p>
      <div style="font-size: 11px; font-family: monospace; color: #78350F;">• COLMAP 4.2.1 SfM + MVS<br>• 7-DoF Umeyama similarity<br>• pyproj EPSG / UTM projection</div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 4 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Detailed End-to-End Technical Architecture</h2>
    <span class="slide-num">SLIDE 04 / 10</span>
  </div>

  <div class="tech-box" style="background: #FFFFFF; font-family: monospace; font-size: 11px; line-height: 1.4; color: #1C1917;">
<pre style="margin: 0;">
+----------------------------------------------------------------------------------------------------+
|                                    INPUT: SINGLE-PASS DRONE VIDEO                                  |
|                         (4K/1080p MP4/MOV) + Flight Telemetry Log (CSV/SRT/GPX)                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. VIDEO INGESTION &amp; STREAM DEMUXING (PyAV / FFmpeg)                                                |
|    • Stream timestamp preservation (PTS) • Video probe (resolution, fps, codec, duration)          |
|    • Atomic SHA-256 checksum computation • Storage persistence to /storage/uploads/videos          |
+----------------------------------------------------------------------------------------------------+
                         │                                                 │
                         ▼                                                 ▼
+---------------------------------------------------+     +------------------------------------------+
| 2. QUALITY ANALYSIS &amp; DEDUPLICATION               |     | 3. TELEMETRY &amp; GPS SYNCHRONIZATION       |
|    • Laplacian variance blur scoring              |     |    • Timestamp interpolation (≤ 1.0s gap)|
|    • Exposure histogram validation                |     |    • WGS84 Geodetic coordinate alignment |
|    • Perceptual dHash hamming filtering           |     |    • Camera altitude &amp; gimbal orientation|
+---------------------------------------------------+     +------------------------------------------+
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. AI PERCEPTION PIPELINE (PyTorch GPU / CPU fallback)                                              |
|    • Relative Inverse Depth: Depth Anything V2 Small (DINOv2 ViT-S/14, 24.78M parameters)          |
|    • Land-Cover Segmentation: SegFormer (Buildings, Roads, Vegetation, Water, Soil)                |
|    • Dynamic Object Exclusion: YOLO vehicle &amp; pedestrian binary masking                            |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. PHOTOGRAMMETRY &amp; 3D RECONSTRUCTION (COLMAP 4.2.1)                                               |
|    • SIFT feature extraction &amp; sequential image matching                                           |
|    • Incremental Structure-from-Motion (SfM) mapper &amp; sparse tie points                            |
|    • Image undistortion &amp; dense PatchMatch Multi-View Stereo (MVS)                                 |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. METRIC SCALE RECOVERY &amp; GEOREFERENCING (pyproj &amp; Umeyama Transform)                             |
|    • 7-DoF similarity transformation: [sR | t] aligning SfM coords to UTM metric reference        |
|    • Ground Control Point (GCP) alignment &amp; independent checkpoint RMSE validation                 |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 7. 3D VISUALIZATION &amp; SPATIAL ANALYSIS (Three.js / WebGL)                                          |
|    • Interactive point cloud rendering with hypsometric elevation tinting &amp; orbit controls         |
|    • Point count inspection, spatial bounding boxes, and export (PLY, OBJ, GeoTIFF)                |
+----------------------------------------------------------------------------------------------------+
</pre>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 5 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">AI Perception &amp; Depth Estimation Engine</h2>
    <span class="slide-num">SLIDE 05 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">Verified Depth Anything V2 Small &amp; Dataset Pipeline</h3>
      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Official Checkpoint Verification:</strong> Downloaded official <code>depth_anything_v2_vits.pth</code> checkpoint strictly verified (SHA256: <code>715fade13be8...</code>, exactly 24,785,089 parameters across 239 tensors).</li>
        <li><strong>Enforced Relative Inverse Depth:</strong> Model output is strictly enforced as <code>relative_inverse_depth</code> with <code>is_metric = False</code>. Metric depth (meters) is never fabricated without independent physical calibration.</li>
        <li><strong>Drone Dataset Architecture:</strong> Full aerial dataset manifests (<code>training.datasets.manifest</code>), PyTorch dataset loaders, dynamic batch collation, and safe zip/tar archive extraction implemented and tested.</li>
        <li><strong>Head Architecture:</strong> ReLU non-negative activation producing physically consistent inverse depth values ($d_{inv} \ge 0$).</li>
      </ul>

      <div class="tech-box">
        <h4 style="margin: 0 0 6px 0; font-size: 11px; color: #78350F; text-transform: uppercase;">Scale-Invariant Training &amp; Loss Formulations</h4>
        <div style="font-size: 11px; line-height: 1.5; color: #44403C;">
          $$\mathcal{L}_{SILog} = 10 \sqrt{\frac{1}{N}\sum g_i^2 - \frac{\lambda}{N^2}\left(\sum g_i\right)^2}, \quad g_i = \ln(d_i) - \ln(d_i^*)$$
          Trained with median-normalized targets ($\lambda=0.85$), edge-aware gradient loss, and invalid pixel masking (<code>build_valid_mask()</code>).
        </div>
      </div>
    </div>

    <div>
      <div class="tech-box">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; color: #0F291E; font-weight: 700;">Multi-Task Perception Integration</h4>
        <table class="slide-table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Architecture</th>
              <th>Operational Function</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Monocular Depth</strong></td>
              <td>Depth Anything V2 Small</td>
              <td>Dense relative terrain relief &amp; building height profiling</td>
            </tr>
            <tr>
              <td><strong>Land-Cover Segmentation</strong></td>
              <td>SegFormer (LoveDA taxonomy)</td>
              <td>8-class semantic classification: roofs, roads, vegetation, water</td>
            </tr>
            <tr>
              <td><strong>Dynamic Filtering</strong></td>
              <td>YOLO Object Detector</td>
              <td>Exclusion masks for moving vehicles to eliminate reconstruction ghosts</td>
            </tr>
            <tr>
              <td><strong>Damage Triage</strong></td>
              <td>Siamese ResNet-50</td>
              <td>xBD 4-tier structural collapse scoring for disaster analysis</td>
            </tr>
          </tbody>
        </table>

        <div style="margin-top: 12px; padding: 10px; background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 6px; font-size: 11px; color: #92400E;">
          <strong>Scientific Integrity Guard:</strong> Saturation artifacts and sky pixels are automatically filtered; zero synthetic elevation values are assigned to unobserved pixels.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 6 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Photogrammetry &amp; 3D Reconstruction Engine</h2>
    <span class="slide-num">SLIDE 06 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">Genuine COLMAP 4.2.1 Integration &amp; Zero Dummy Geometry</h3>
      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Real Binary Integration:</strong> Official COLMAP 4.2.1 no-CUDA binary integrated at <code>.tools/colmap/bin/colmap.exe</code> and resolved automatically via <code>Settings.COLMAP_EXE</code> for SfM and dense MVS.</li>
        <li><strong>Procedural Fallbacks Removed:</strong> All procedural cubes, sphere placeholders, and mock geometry generators completely purged from the codebase. Missing dependencies result in honest HTTP 503 errors.</li>
        <li><strong>Minimum Overlap Guard:</strong> Rejects datasets with fewer than 2 valid images; requires genuine multi-view feature correspondences.</li>
        <li><strong>Verified Point Cloud Gate:</strong> Every generated point cloud passes <code>isUsablePointCloud()</code>, proving existence of non-zero, finite vertices before saving.</li>
      </ul>
    </div>

    <div>
      <div class="tech-box">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; color: #0F291E; font-weight: 700;">Reconstruction Pipeline Execution Sequence</h4>
        <div style="font-family: monospace; font-size: 11px; line-height: 1.6; color: #1E3A2F;">
          1. <code>colmap feature_extractor</code> (SIFT scale-space)<br>
          2. <code>colmap exhaustive_matcher</code> (Two-view epipolar verification)<br>
          3. <code>colmap mapper</code> (Incremental bundle adjustment)<br>
          4. <code>colmap image_undistorter</code> (Lens radial rectification)<br>
          5. <code>colmap patch_match_stereo</code> (Dense MVS depth estimation)<br>
          6. <code>colmap stereo_fusion</code> (Validated dense .ply point cloud)<br>
          7. <code>colmap poisson_mesher</code> (Textured watertight 3D mesh)
        </div>

        <div style="margin-top: 12px; padding: 10px; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 6px; font-size: 11px; color: #065F46;">
          <strong>Real Diagnostics:</strong> Reprojection errors and registered camera counts are extracted directly from COLMAP's <code>model_analyzer</code>—never fabricated.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 7 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Metric Scale Recovery &amp; Georeferencing Pipeline</h2>
    <span class="slide-num">SLIDE 07 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">7-Parameter Umeyama Similarity Transformation &amp; CRS Alignment</h3>
      <p style="font-size: 12px; line-height: 1.6; color: #44403C;">
        Monocular SfM reconstructs scenes up to an arbitrary scale factor. JATAYUV solves the closed-form Umeyama/Horn Procrustes problem to recover metric scale ($s$), 3D rotation ($\mathbf{R}$), and translation ($\mathbf{t}$):
      </p>

      <div style="font-size: 11px; background: #FAF6F0; padding: 10px; border: 1px solid #E7DAC7; border-radius: 6px; color: #1E3A2F; margin-bottom: 12px;">
        $$\mathbf{X}_{UTM} = s \mathbf{R} \mathbf{X}_{SfM} + \mathbf{t}$$
        where $s \in \mathbb{R}^+$ is the recovered metric scale, $\mathbf{R} \in SO(3)$, and $\mathbf{t} \in \mathbb{R}^3$.
      </div>

      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Operator Precedence Repaired:</strong> Corrected matrix subtraction operator precedence in weighted centroid computation to ensure strict dimensional alignment.</li>
        <li><strong>pyproj / PROJ CRS Transformation:</strong> Seamlessly converts WGS84 ellipsoidal coordinates (EPSG:4326) into conformal metric Cartesian coordinates (UTM Zones).</li>
      </ul>
    </div>

    <div>
      <div class="tech-box">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; color: #0F291E; font-weight: 700;">Spatial Validation &amp; Checkpoint Accuracy</h4>
        <table class="slide-table">
          <thead>
            <tr>
              <th>Validation Metric</th>
              <th>Evaluation Method</th>
              <th>Operational Function</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Easting / Northing RMSE</strong></td>
              <td>$$\sqrt{\frac{1}{K}\sum (\Delta X_k^2 + \Delta Y_k^2)}$$</td>
              <td>Quantifies horizontal ground displacement accuracy</td>
            </tr>
            <tr>
              <td><strong>Vertical Height RMSE</strong></td>
              <td>$$\sqrt{\frac{1}{K}\sum \Delta Z_k^2}$$</td>
              <td>Validates metric elevation against barometric AGL logs</td>
            </tr>
            <tr>
              <td><strong>Independent Checkpoints</strong></td>
              <td>Split GCP vs Checkpoints</td>
              <td>Checkpoints excluded from fitting to ensure unbiased residual reporting</td>
            </tr>
          </tbody>
        </table>

        <div style="margin-top: 12px; padding: 10px; background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 6px; font-size: 11px; color: #92400E;">
          <strong>Rigorous Reporting Rule:</strong> Residual errors are calculated and stored in database records (<code>spatial_validation_metrics</code>) and never fabricated.
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 8 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">System Verification, Test Results &amp; Platform Integrity</h2>
    <span class="slide-num">SLIDE 08 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">Automated Verification Test Suites</h3>
      <table class="slide-table">
        <thead>
          <tr>
            <th>Verification Suite</th>
            <th>Executed</th>
            <th>Passed</th>
            <th>Failed</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Backend Pytest (Full Suite)</td>
            <td>170</td>
            <td><strong>169 PASSED</strong> <span style="font-size:10px; color:#78716C;">(1 skipped*)</span></td>
            <td>0</td>
          </tr>
          <tr>
            <td>Frontend Test Suite (Jest / React)</td>
            <td>7</td>
            <td><strong>7 PASSED</strong></td>
            <td>0</td>
          </tr>
          <tr>
            <td>TypeScript Compiler (<code>tsc --noEmit</code>)</td>
            <td>Full Codebase</td>
            <td><strong>0 ERRORS</strong></td>
            <td>0</td>
          </tr>
          <tr style="font-weight: 700; background: #ECFDF5;">
            <td>TOTAL TEST VERIFICATION</td>
            <td>177</td>
            <td><strong>176 PASSED</strong></td>
            <td><strong>0 FAILED</strong></td>
          </tr>
        </tbody>
      </table>
      <p style="font-size: 10px; color: #78716C; margin-top: 4px;">*Single skipped test requires multi-GB raw SkyScenes archive not bundled in repository.</p>

      <div class="tech-box" style="margin-top: 8px;">
        <h4 style="margin: 0 0 6px 0; font-size: 11px; color: #0F291E; font-weight: 700;">Repaired Core Platform Components</h4>
        <ul style="font-size: 11px; line-height: 1.5; color: #44403C; padding-left: 16px; margin: 0;">
          <li><strong>Database Schema &amp; Alembic:</strong> Migrations 000–007 repaired, index deduplication resolved, relations unified across all models.</li>
          <li><strong>FastAPI Authentication:</strong> Genuine cryptographic JWT enforcement with signature verification; zero silent demo-session fallbacks.</li>
          <li><strong>Three.js PLY Viewer:</strong> WebGL viewer supports elevation heatmaps, particle point size sliders, and OrbitControls.</li>
        </ul>
      </div>
    </div>

    <div>
      <div class="tech-box">
        <h4 style="margin: 0 0 8px 0; font-size: 12px; color: #78350F; font-weight: 700;">Scientific Integrity &amp; Honest Scope</h4>
        <ul style="font-size: 11px; line-height: 1.6; color: #44403C; padding-left: 16px; margin: 0;">
          <li><strong>Software Tests ≠ Real-World Validation:</strong> 169 passing unit/integration tests prove software correctness, data integrity, and error rejection. Real-world field accuracy requires physical survey ground-truthing with RTK-GPS.</li>
          <li><strong>Relative Depth Scope:</strong> Depth Anything V2 Small produces fine relative relief. It is not metric depth until an external scale calibration factor is fitted.</li>
          <li><strong>Photogrammetric Boundary:</strong> Videos with extreme motion blur, low visual texture (open ocean), or degenerate straight-line forward camera motion without parallax may fail SfM mapping—this is an inherent constraint of epipolar geometry.</li>
          <li><strong>Unmeasured Performance:</strong> Processing speeds and field metric accuracies are presented honestly as future validation targets rather than unmeasured claims.</li>
          <li><strong>Audited Documentation:</strong> All findings documented in <code>docs/JATAYUV_MASTER_AUDIT.md</code> and <code>docs/JATAYUV_FINAL_IMPLEMENTATION_REPORT.md</code>.</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 9 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Mission Control Web Dashboard &amp; 3D Viewer</h2>
    <span class="slide-num">SLIDE 09 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">Interactive Web Interface (Next.js 14 + Three.js)</h3>
      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Single-Pass Drone Video Ingestion Hub:</strong> Drag-and-drop video upload supporting 4K MP4/MOV footage with telemetry log pairing (.csv/.srt/.gpx).</li>
        <li><strong>Probed Telemetry HUD:</strong> Real-time display of video codec, duration, frame rate, resolution, and SHA-256 verification status.</li>
        <li><strong>Automated Pipeline Dispatch:</strong> One-click trigger executing stream demuxing, quality filtering, perception inference, and COLMAP dense 3D reconstruction.</li>
        <li><strong>Three.js PLY Viewer:</strong> Interactive WebGL viewer rendering verified PLY point clouds with hypsometric elevation heatmaps, particle point size sliders, orbit controls, and camera reset.</li>
        <li><strong>Strict Empty State:</strong> If no verified 3D model exists, cleanly displays mission alert rather than synthetic procedural geometry.</li>
      </ul>
    </div>

    <div>
      <div class="tech-box" style="text-align: center;">
        <div style="font-size: 11px; font-weight: 700; color: #0F291E; margin-bottom: 8px;">DASHBOARD MISSION CONTROL &amp; 3D VIEWER</div>
        <div style="background: #0A0F1D; color: #34D399; font-family: monospace; font-size: 10px; padding: 16px; border-radius: 8px; text-align: left; border: 1px solid #059669;">
          [HUD] MISSION: BORDER_SECTOR_07_UAV<br>
          [STATUS] VIDEO DEMUX: COMPLETE (240 FRAMES)<br>
          [STATUS] QUALITY FILTER: 212 SHARP / 28 BLURRED<br>
          [STATUS] AI DEPTH: DEPTH ANYTHING V2 SMALL (OK)<br>
          [STATUS] COLMAP SfM: 198 CAMERAS REGISTERED<br>
          [STATUS] DENSE CLOUD: 148,290 VERTICES (.PLY)<br>
          [VIEWER] THREE.JS WEBGL RENDER: ACTIVE (HYPSOMETRIC)
        </div>
        <p style="font-size: 11px; color: #78716C; margin-top: 8px;">
          Live dashboard interface running on Next.js 14 / Tailwind CSS.
        </p>
      </div>
    </div>
  </div>
</div>

<!-- ======================================================================= -->
<!-- SLIDE 10 -->
<!-- ======================================================================= -->
<div class="slide-card">
  <div class="slide-header">
    <h2 class="slide-title">Operational Impact, Limitations &amp; Future Roadmap</h2>
    <span class="slide-num">SLIDE 10 / 10</span>
  </div>

  <div class="grid-2col">
    <div>
      <h3 style="color: #0F291E; font-size: 14px; font-weight: 700; margin-top: 0;">Strategic Operational Impact</h3>
      <p style="font-size: 12px; line-height: 1.6; color: #44403C;">
        JATAYUV delivers an end-to-end aerial intelligence capability engineered specifically for defense and disaster response scenarios where multi-pass surveys are impossible.
      </p>

      <ul style="font-size: 12px; line-height: 1.6; color: #292524; padding-left: 18px;">
        <li><strong>Single-Pass Feasibility:</strong> Extracts dense 3D terrain and structural models from solitary drone flight sweeps.</li>
        <li><strong>Dynamic Filtration:</strong> Eliminates vehicle motion artifacts from urban mapping.</li>
        <li><strong>Reproducible Engineering:</strong> Full Alembic database migrations, verified pretrained weights, and standardized REST API endpoints.</li>
      </ul>
    </div>

    <div>
      <div class="tech-box">
        <h4 style="margin: 0 0 6px 0; font-size: 12px; color: #78350F; font-weight: 700;">Future Roadmap &amp; Field Validation Targets</h4>
        <ul style="font-size: 11px; line-height: 1.6; color: #44403C; padding-left: 16px; margin: 0;">
          <li><strong>Phase 1 (Future Work):</strong> Field trial validation against high-precision survey RTK ground control targets to measure absolute physical centimeter accuracy.</li>
          <li><strong>Phase 2 (Future Work):</strong> Real-time edge deployment on NVIDIA Jetson Orin with TensorRT quantization for in-flight pose estimation.</li>
          <li><strong>Phase 3 (Future Work):</strong> Gaussian Splatting (3DGS) integration for real-time photorealistic novel-view synthesis from drone trajectories.</li>
        </ul>
      </div>

      <div style="margin-top: 12px; text-align: center; font-size: 12px; font-weight: 700; color: #0F291E; background: #FAF6F0; padding: 8px; border-radius: 6px; border: 1px solid #E7DAC7;">
        JATAYUV — National Technical Research Organisation (NTRO) | SIH26158
      </div>
    </div>
  </div>
</div>

</div>
