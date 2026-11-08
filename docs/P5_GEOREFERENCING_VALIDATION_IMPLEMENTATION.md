# P5: Metric Scale Recovery, Georeferencing and Spatial Validation

## Objective
Convert valid P4 reconstruction coordinates and camera poses into a metrically scaled,
geographically referenced coordinate system, and produce an honest spatial validation
report.

## Scope
- P5 only.
- No dense point clouds, meshes, or texture exports.
- No fabrication of metric scale or accuracy.
- Independent checkpoints must not be used to fit the transformation.

## Dependencies
- pyproj for CRS handling.
- numpy/scipy for estimation and validation.
- Valid P4 pose and sparse geometry outputs when available.
- Valid GPS/IMU telemetry and optional GCP/checkpoint data for scale recovery.

## Validated outputs
- Coordinate transformation parameters with provenance.
- Metric scale factor only when supported.
- Transformed camera poses and sparse geometry versioned separately from P4.
- Independent spatial validation metrics when independent checkpoints exist.
- Honest uncertainty reporting.

## Key limitations
- Monocular scale ambiguity unless externally resolved.
- Unknown altitude datum prevents validated absolute elevation.
- No independent validation when no independent checkpoints exist.
