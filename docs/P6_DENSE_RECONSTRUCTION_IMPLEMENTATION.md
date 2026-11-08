# P6: Dense 3D Reconstruction, Point Cloud, Mesh and Texture Generation

## Objective
Create a genuine dense reconstruction pipeline from valid P2 selected frames, P3 depth/segmentation/masks, P4 camera calibration/poses, and optional P5 georeferencing.

## Scope
P6 only. No final 3D viewer or export dashboard (that is P7). No fabricated geometry, textures, or metric scale.

## Inputs required
- Selected frames (P2)
- Camera intrinsics and distortion (P4 calibration)
- Camera poses (P4, with provenance and coordinate convention)
- Optional P3 depth artifacts (relative or metric with provenance)
- Optional P3 segmentation and dynamic masks
- Optional P5 georeferencing solution and CRS/units info

## Algorithms and tools
- COLMAP dense pipeline where the executable is available: image undistortion, patch-match stereo, stereo fusion.
- Open3D for point cloud processing, filtering, Poisson/ball-pivoting/TSDF mesh reconstruction, and texture projection.
- Depth-assisted point clouds only when metric depth is valid and calibrated; otherwise only relative/visualization use.
- Semantic class metadata associated to geometry only where segmentation supports it.

## Coordinate conventions
- Preserve reconstruction coordinate frame when georeferencing is unavailable; label UNGEOREFERENCED/LOCAL.
- Apply P5 transformations consistently when available.
- Never mix metric and relative-depth data in the same fused geometry.

## Outputs
- Versioned dense point cloud PLY
- Mesh OBJ with MTL and texture images where generated
- Reconstruction metadata and quality report
- Artifact registry entries with checksums and provenance

## Known limitations
- COLMAP must be installed and the version verified at runtime.
- Relative depth cannot be turned into metres.
- Texture depends on valid poses, intrinsics, and visible surface coverage.
- No dense reconstruction if inputs are insufficient; failure is reported honestly.

## Documentation created
- This file: docs/P6_DENSE_RECONSTRUCTION_IMPLEMENTATION.md
- Runtime environment summary: `backend/app/core/runtime_env.json`
