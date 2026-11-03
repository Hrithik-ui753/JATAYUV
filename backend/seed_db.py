import os
import sys
sys.path.insert(0, os.path.abspath("."))
import uuid
import json
import sqlite3
from datetime import datetime, timezone

db_path = os.path.abspath("storage/jatayuv.db")
con = sqlite3.connect(db_path)
cur = con.cursor()

# Check if analyst user exists
user = cur.execute("SELECT id FROM users WHERE email='analyst@jatayuv.ai'").fetchone()
if not user:
    from backend.app.core.security import get_password_hash
    user_id = str(uuid.uuid4())
    pw_hash = get_password_hash("jatayuv2026")
    cur.execute(
        "INSERT INTO users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, "analyst@jatayuv.ai", pw_hash, "Commander V. Sharma", "admin", 1, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())
    )
    con.commit()
else:
    user_id = user[0]

# Check if projects exist
proj_count = cur.execute("SELECT count(*) FROM projects").fetchone()[0]
if proj_count == 0:
    projects = [
        (
            "proj-coastal-01",
            "Mission Garuda: Coastal Cyclone Sector 4",
            "Emergency reconnaissance and humanitarian infrastructure damage triage following tropical cyclone surge.",
            "Paradip Port Coastal Corridor, Odisha",
            20.3160,
            86.6110,
            user_id,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "proj-urban-02",
            "Mission Trisul: Metropolitan Expansion Grid",
            "High-density urban survey, land use classification (LULC), and multi-temporal road network change mapping.",
            "Hyderabad Outer Ring Road & HITEC Hub",
            17.4435,
            78.3772,
            user_id,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "proj-valley-03",
            "Mission Himalaya: Glacial Terrain & Faultline Pass",
            "High-altitude UAV photogrammetric survey and monocular depth relief modeling for seismic slope stability.",
            "Joshimath Valley Faultline, Uttarakhand",
            30.5564,
            79.5661,
            user_id,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    ]

    cur.executemany(
        "INSERT INTO projects (id, name, description, location_name, center_lat, center_lon, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        projects
    )

    # Seed Images for proj-coastal-01
    images = [
        (
            "img-pre-01",
            "proj-coastal-01",
            "survey_nadir_pre_cyclone_001.jpg",
            "/storage/uploads/survey_nadir_pre_cyclone_001.jpg",
            "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80",
            4892400,
            3840,
            2160,
            "JPEG",
            1,
            "/storage/processed/pre_cyclone_001.jpg",
            json.dumps({
                "camera_make": "DJI Zenmuse P1",
                "camera_model": "Matrice 300 RTK",
                "focal_length_mm": 35.0,
                "iso": 100,
                "exposure_time": "1/1000",
                "altitude_m": 120.4,
                "latitude": 20.3162,
                "longitude": 86.6114,
                "heading_deg": 142.5,
                "capture_time": "2026-10-28T09:14:22Z"
            }),
            datetime.now(timezone.utc).isoformat()
        ),
        (
            "img-post-01",
            "proj-coastal-01",
            "survey_nadir_post_cyclone_001.jpg",
            "/storage/uploads/survey_nadir_post_cyclone_001.jpg",
            "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
            5120800,
            3840,
            2160,
            "JPEG",
            1,
            "/storage/processed/post_cyclone_001.jpg",
            json.dumps({
                "camera_make": "DJI Zenmuse P1",
                "camera_model": "Matrice 300 RTK",
                "focal_length_mm": 35.0,
                "iso": 125,
                "exposure_time": "1/800",
                "altitude_m": 118.8,
                "latitude": 20.3161,
                "longitude": 86.6112,
                "heading_deg": 142.1,
                "capture_time": "2026-11-01T14:30:10Z"
            }),
            datetime.now(timezone.utc).isoformat()
        ),
    ]

    cur.executemany(
        "INSERT INTO images (id, project_id, filename, file_path, thumbnail_path, file_size_bytes, width, height, format, is_preprocessed, preprocessed_path, telemetry_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        images
    )

    # Seed Jobs
    jobs = [
        (
            "job-depth-01",
            "proj-coastal-01",
            "depth_estimation",
            "completed",
            100,
            None,
            "celery-task-84912",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "job-seg-01",
            "proj-coastal-01",
            "semantic_segmentation",
            "completed",
            100,
            None,
            "celery-task-84913",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "job-damage-01",
            "proj-coastal-01",
            "damage_assessment",
            "completed",
            100,
            None,
            "celery-task-84914",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
        (
            "job-recon-01",
            "proj-coastal-01",
            "reconstruction_3d",
            "completed",
            100,
            None,
            "celery-task-84915",
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    ]

    cur.executemany(
        "INSERT INTO jobs (id, project_id, job_type, status, progress_pct, error_message, celery_task_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        jobs
    )

    # Seed Depth Result
    cur.execute(
        "INSERT INTO depth_results (id, job_id, image_id, depth_map_path, colormap_path, min_depth_m, max_depth_m, mean_depth_m, mesh_obj_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "depth-res-01",
            "job-depth-01",
            "img-pre-01",
            "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80",
            3.4,
            118.6,
            47.2,
            "/storage/reconstructions/mesh_proj-coastal-01.obj",
            datetime.now(timezone.utc).isoformat()
        )
    )

    # Seed Segmentation Result
    cur.execute(
        "INSERT INTO segmentation_results (id, job_id, image_id, mask_path, overlay_path, class_distribution_json, geojson_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "seg-res-01",
            "job-seg-01",
            "img-pre-01",
            "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80",
            json.dumps({
                "Buildings": 34.2,
                "Vegetation": 28.5,
                "Water": 14.1,
                "Roads": 12.8,
                "Bare Soil": 6.4,
                "Vehicles": 4.0
            }),
            "/storage/processed/buildings_img-pre-01.geojson",
            datetime.now(timezone.utc).isoformat()
        )
    )

    # Seed Damage Result
    cur.execute(
        "INSERT INTO damage_assessment_results (id, job_id, pre_image_id, post_image_id, damage_overlay_path, total_buildings, counts_by_level_json, damage_percentage, severity_index, geojson_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "dmg-res-01",
            "job-damage-01",
            "img-pre-01",
            "img-post-01",
            "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
            248,
            json.dumps({
                "no_damage": 52,
                "minor_damage": 64,
                "major_damage": 86,
                "destroyed": 46
            }),
            79.03,
            0.642,
            "/storage/processed/damage_img-post-01.geojson",
            datetime.now(timezone.utc).isoformat()
        )
    )

    # Seed Change Detection Result
    cur.execute(
        "INSERT INTO change_detection_results (id, job_id, before_image_id, after_image_id, diff_mask_path, heatmap_path, changed_area_pct, changed_pixels, significance_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "chg-res-01",
            "job-damage-01",
            "img-pre-01",
            "img-post-01",
            "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80",
            38.7,
            320480,
            0.874,
            datetime.now(timezone.utc).isoformat()
        )
    )

    # Seed 3D Reconstruction Result
    cur.execute(
        "INSERT INTO reconstructions_3d (id, project_id, job_id, pointcloud_ply_path, mesh_obj_path, dsm_tiff_path, num_points, camera_count, reprojection_error_px, bounds_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "recon-res-01",
            "proj-coastal-01",
            "job-recon-01",
            "/storage/reconstructions/pointcloud_proj-coastal-01.ply",
            "/storage/reconstructions/mesh_proj-coastal-01.obj",
            "/storage/reconstructions/dsm_proj-coastal-01.tif",
            124800,
            42,
            0.78,
            json.dumps({
                "min_x": -150.0,
                "max_x": 150.0,
                "min_y": -150.0,
                "max_y": 150.0,
                "min_z": 0.0,
                "max_z": 85.5
            }),
            datetime.now(timezone.utc).isoformat()
        )
    )

    con.commit()
    print("Seeded database successfully with realistic demo missions, imagery, telemetry, AI inference results, and 3D reconstruction!")
else:
    print(f"Database already contains {proj_count} projects.")

con.close()
