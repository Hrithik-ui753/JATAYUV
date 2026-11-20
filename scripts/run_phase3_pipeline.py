"""Execute Phase 3 Spatial Intelligence & Advanced Inspection Pipeline on real drone frames."""
import glob
import json
import os
import sys
import time

from backend.app.services.spatial_pipeline import spatial_intelligence_pipeline

mission_id = "439219c0-21c1-4940-9dd9-e6f65ae86503"
frames_dir = os.path.join(
    "storage",
    "missions",
    mission_id,
    "videos",
    "30c3d866-8c72-43c7-a1bd-9bff24a8cf27",
    "frames",
    "7b4afb3d029e4dd8899bf2fcf9a00644",
)
frame_paths = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))

print(f"Found {len(frame_paths)} frames for mission {mission_id}.")
if not frame_paths:
    print("No frames found!")
    sys.exit(1)

out_dir = os.path.join("storage", "missions", mission_id, "spatial_intelligence")
os.makedirs(out_dir, exist_ok=True)

t0 = time.time()
result = spatial_intelligence_pipeline.process_frames(
    mission_id=mission_id,
    frame_paths=frame_paths,
    output_dir=out_dir,
    max_frames=30,
)
t_elapsed = round(time.time() - t0, 2)

print(f"Pipeline finished in {t_elapsed}s.")
print(f"Total localized objects: {result.total_tracked_objects}")
print(f"Total anomalies flagged: {result.inspection_report.get('total_anomalies_detected')}")
print(f"Clearance summary: {result.clearance_summary}")
print(f"Risk summary: {result.risk_summary}")
print(f"Output saved to {result.output_json_path}")

