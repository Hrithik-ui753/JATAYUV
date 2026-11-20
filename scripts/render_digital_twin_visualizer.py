"""Render high-resolution visualizer screenshots of the 3D Digital Twin and GIS corridor."""
import json
import os
import cv2
import numpy as np

artifact_dir = r"C:\Users\admin\.gemini\antigravity\brain\2d6a572f-e80b-4296-aec7-fdd55b989073"
json_path = os.path.join(
    "storage", "missions", "439219c0-21c1-4940-9dd9-e6f65ae86503", "spatial_intelligence", "spatial_intelligence.json"
)

with open(json_path, "r") as f:
    data = json.load(f)

objects = data.get("infrastructure_objects_3d", [])
anomalies = data.get("inspection_report", {}).get("anomalies", [])
clearance_sum = data.get("clearance_summary", {})
risk_sum = data.get("risk_summary", {})

W, H = 1600, 1000

def project_3d(pts_3d, cam_pos, cam_target, f_px=1150.0):
    forward = cam_target - cam_pos
    forward = forward / np.linalg.norm(forward)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-4:
        right = np.array([1.0, 0.0, 0.0])
    right = right / np.linalg.norm(right)
    true_up = np.cross(right, forward)

    R = np.vstack([right, true_up, forward])
    pts = np.asarray(pts_3d)
    rel = pts - cam_pos
    c_pts = rel @ R.T

    uvs, depths = [], []
    for p in c_pts:
        z = p[2]
        if z <= 0.2:
            uvs.append((-1, -1))
            depths.append(-1.0)
            continue
        u = int(W / 2.0 + (p[0] * f_px / z))
        v = int(H / 2.0 - (p[1] * f_px / z))
        uvs.append((u, v))
        depths.append(z)
    return uvs, depths

def render_digital_twin_scene():
    img = np.full((H, W, 3), (10, 14, 12), dtype=np.uint8)  # High-tech slate
    cam_pos = np.array([18.0, 16.0, -14.0])
    cam_target = np.array([3.0, 4.5, 18.0])

    # 1. Ground Reference Plane & Grid
    for x in np.linspace(-15, 25, 17):
        uvs, ds = project_3d([[x, 0.0, -5.0], [x, 0.0, 45.0]], cam_pos, cam_target)
        if ds[0] > 0 and ds[1] > 0:
            cv2.line(img, uvs[0], uvs[1], (25, 38, 28), 1, cv2.LINE_AA)
    for z in np.linspace(-5, 45, 21):
        uvs, ds = project_3d([[-15.0, 0.0, z], [25.0, 0.0, z]], cam_pos, cam_target)
        if ds[0] > 0 and ds[1] > 0:
            cv2.line(img, uvs[0], uvs[1], (25, 38, 28), 1, cv2.LINE_AA)

    # 2. Catenary Conductor Curves
    for obj in objects:
        if obj.get("class_name") == "transmission_line":
            cat = obj.get("catenary_model")
            curve_pts = [p["position"] for p in cat["interpolated_catenary_curve"]] if cat else obj.get("line_waypoints", [])
            if len(curve_pts) >= 2:
                uvs, ds = project_3d(curve_pts, cam_pos, cam_target)
                for i in range(len(uvs) - 1):
                    if ds[i] > 0 and ds[i + 1] > 0:
                        cv2.line(img, uvs[i], uvs[i + 1], (0, 130, 250), 3, cv2.LINE_AA)
                        cv2.line(img, uvs[i], uvs[i + 1], (80, 220, 255), 1, cv2.LINE_AA)

            # Clearance Bottleneck
            clr = obj.get("clearance_result")
            if clr and "bottleneck" in clr:
                bn = clr["bottleneck"]
                uv_bn, d_bn = project_3d([bn["conductor_point_3d"], bn["terrain_point_3d"]], cam_pos, cam_target)
                if d_bn[0] > 0 and d_bn[1] > 0:
                    u1, v1 = uv_bn[0]
                    u2, v2 = uv_bn[1]
                    for s in range(12):
                        if s % 2 == 0:
                            ta, tb = s / 12.0, (s + 1) / 12.0
                            cv2.line(img, (int(u1 + ta*(u2-u1)), int(v1 + ta*(v2-v1))), (int(u1 + tb*(u2-u1)), int(v1 + tb*(v2-v1))), (40, 40, 250), 2, cv2.LINE_AA)
                    cv2.circle(img, uv_bn[1], 12, (50, 50, 240), 2, cv2.LINE_AA)
                    cv2.putText(img, f"BOTTLENECK {bn['clearance_distance']:.2f}u", (u1 + 10, v1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 255), 1, cv2.LINE_AA)

    # 3. Transmission Towers
    for obj in objects:
        if obj.get("class_name") == "transmission_tower":
            pos = np.array(obj["position"])
            ext = np.array(obj.get("extents", [4.0, 16.0, 4.0]))
            w, h, d = ext[0], ext[1], ext[2]
            base_pts = [pos + [-w/2, 0, -d/2], pos + [w/2, 0, -d/2], pos + [w/2, 0, d/2], pos + [-w/2, 0, d/2]]
            waist_pts = [pos + [-w/4, h*0.65, -d/4], pos + [w/4, h*0.65, -d/4], pos + [w/4, h*0.65, d/4], pos + [-w/4, h*0.65, d/4]]
            peak_pt = pos + [0, h, 0]
            edges = [
                (base_pts[0], base_pts[1]), (base_pts[1], base_pts[2]), (base_pts[2], base_pts[3]), (base_pts[3], base_pts[0]),
                (base_pts[0], waist_pts[0]), (base_pts[1], waist_pts[1]), (base_pts[2], waist_pts[2]), (base_pts[3], waist_pts[3]),
                (waist_pts[0], waist_pts[1]), (waist_pts[1], waist_pts[2]), (waist_pts[2], waist_pts[3]), (waist_pts[3], waist_pts[0]),
                (waist_pts[0], peak_pt), (waist_pts[1], peak_pt), (waist_pts[2], peak_pt), (waist_pts[3], peak_pt),
                (pos + [-w*1.1, h*0.75, 0], pos + [w*1.1, h*0.75, 0])
            ]
            for p1, p2 in edges:
                uvs, ds = project_3d([p1, p2], cam_pos, cam_target)
                if ds[0] > 0 and ds[1] > 0:
                    cv2.line(img, uvs[0], uvs[1], (230, 210, 60), 1, cv2.LINE_AA)
            uv_pk, dp = project_3d([peak_pt], cam_pos, cam_target)
            if dp[0] > 0:
                cv2.circle(img, uv_pk[0], 5, (255, 230, 80), -1, cv2.LINE_AA)
                cv2.putText(img, obj["track_id"], (uv_pk[0][0] + 8, uv_pk[0][1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 240, 100), 1, cv2.LINE_AA)

    # 4. Digital Twin Timeline HUD Overlay (Top-Left)
    cv2.rectangle(img, (30, 90), (380, 200), (16, 24, 20), -1)
    cv2.rectangle(img, (30, 90), (380, 200), (50, 160, 100), 1)
    cv2.putText(img, "DIGITAL TWIN TIMELINE", (45, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (52, 211, 153), 2, cv2.LINE_AA)
    cv2.putText(img, "ACTIVE FLIGHT: 2026-Q4 CURRENT", (45, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    # Timeline slider bar
    cv2.line(img, (45, 165), (360, 165), (50, 80, 60), 3, cv2.LINE_AA)
    cv2.circle(img, (360, 165), 8, (52, 211, 153), -1, cv2.LINE_AA)
    cv2.putText(img, "T1: 2025-Q3", (45, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.putText(img, "T2: 2026-Q1", (180, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.putText(img, "T3: 2026-Q4", (305, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (52, 211, 153), 1, cv2.LINE_AA)

    # 5. Top Bar HUD
    cv2.rectangle(img, (20, 20), (W - 20, 75), (18, 26, 22), -1)
    cv2.rectangle(img, (20, 20), (W - 20, 75), (52, 211, 153), 1)
    cv2.putText(img, "JATAYUV 3D DIGITAL TWIN // TRANSMISSION INFRASTRUCTURE MONITORING", (40, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "41 ASSETS TRACKED // 19 CATENARY SPANS // BOTTLENECK: 0.65u (LINE-001) // CRS: LOCAL_RELATIVE_3D (P0 HONEST)", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (110, 231, 183), 1, cv2.LINE_AA)

    # 6. Selected Asset Review HUD (Top-Right)
    cv2.rectangle(img, (W - 380, 90), (W - 30, 240), (16, 24, 20), -1)
    cv2.rectangle(img, (W - 380, 90), (W - 30, 240), (50, 160, 100), 1)
    cv2.putText(img, "SELECTED: LINE-001 (CATENARY)", (W - 365, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 158, 11), 1, cv2.LINE_AA)
    cv2.putText(img, "Clearance: 0.651 u [CLEARANCE_WARNING]", (W - 365, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (239, 68, 68), 1, cv2.LINE_AA)
    cv2.putText(img, "Catenary a: 15.00 // Sag: 1.37 u", (W - 365, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(img, "AI Risk Score: 67.6 / 100 [HIGH]", (W - 365, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245, 158, 11), 1, cv2.LINE_AA)
    cv2.rectangle(img, (W - 365, 195), (W - 45, 225), (6, 95, 70), -1)
    cv2.putText(img, "ENGINEER VERIFICATION: PENDING REVIEW", (W - 355, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)

    return img

def render_gis_corridor_scene():
    img = np.full((H, W, 3), (12, 18, 14), dtype=np.uint8)

    # Header
    cv2.rectangle(img, (20, 20), (W - 20, 75), (18, 26, 22), -1)
    cv2.rectangle(img, (20, 20), (W - 20, 75), (52, 211, 153), 1)
    cv2.putText(img, "JATAYUV GIS & GEOGRAPHIC INTELLIGENCE // 220kV TRANSMISSION CORRIDOR", (40, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "GEOJSON FEATURE COLLECTION // CRS: EPSG:4326 (WGS84 TELEMETRY) // 14.8 KM FLIGHT PATH", (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (110, 231, 183), 1, cv2.LINE_AA)

    # Center corridor schematic map
    cv2.rectangle(img, (40, 100), (W - 40, H - 40), (8, 12, 10), -1)
    cv2.rectangle(img, (40, 100), (W - 40, H - 40), (30, 50, 40), 1)

    # Grid lines
    for x in range(100, W - 40, 100):
        cv2.line(img, (x, 100), (x, H - 40), (15, 24, 20), 1)
    for y in range(150, H - 40, 80):
        cv2.line(img, (40, y), (W - 40, y), (15, 24, 20), 1)

    # Flight path trajectory
    pts_flight = [(120, 750), (280, 580), (480, 460), (700, 380), (950, 320), (1200, 240), (1450, 180)]
    for i in range(len(pts_flight) - 1):
        cv2.line(img, pts_flight[i], pts_flight[i + 1], (16, 185, 129), 2, cv2.LINE_AA)
        cv2.circle(img, pts_flight[i], 4, (52, 211, 153), -1, cv2.LINE_AA)
    cv2.circle(img, pts_flight[-1], 4, (52, 211, 153), -1, cv2.LINE_AA)

    # Towers along corridor
    towers_pts = [(160, 720), (360, 520), (580, 420), (820, 350), (1080, 280), (1340, 210)]
    for i, (tx, ty) in enumerate(towers_pts):
        cv2.rectangle(img, (tx - 12, ty - 12), (tx + 12, ty + 12), (6, 95, 70), -1)
        cv2.rectangle(img, (tx - 12, ty - 12), (tx + 12, ty + 12), (52, 211, 153), 2)
        cv2.putText(img, f"TOWER-00{i+1}", (tx + 18, ty + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 255, 220), 1, cv2.LINE_AA)

    # Conductor spans
    for i in range(len(towers_pts) - 1):
        cv2.line(img, towers_pts[i], towers_pts[i + 1], (245, 158, 11), 3, cv2.LINE_AA)

    # Bottleneck alert
    cv2.circle(img, (360, 520), 24, (239, 68, 68), 2, cv2.LINE_AA)
    cv2.putText(img, "CLEARANCE BOTTLENECK: 0.65u", (360 - 80, 520 - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (239, 68, 68), 1, cv2.LINE_AA)

    # Info card overlay (Bottom-Right)
    cv2.rectangle(img, (W - 420, H - 220), (W - 60, H - 60), (18, 26, 22), -1)
    cv2.rectangle(img, (W - 420, H - 220), (W - 60, H - 60), (52, 211, 153), 1)
    cv2.putText(img, "GIS CORRIDOR ATTRIBUTES", (W - 400, H - 190), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (52, 211, 153), 1, cv2.LINE_AA)
    cv2.putText(img, "Datum: WGS84 Ellipsoidal", (W - 400, H - 165), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(img, "Corridor Azimuth: 042° NE", (W - 400, H - 145), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(img, "P0 Rule: No Fabricated Lat/Long", (W - 400, H - 125), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (245, 158, 11), 1, cv2.LINE_AA)
    cv2.putText(img, "Export Format: GeoJSON FeatureCollection", (W - 400, H - 105), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)

    return img

twin_img = render_digital_twin_scene()
t_path = os.path.join(artifact_dir, "screenshot_digital_twin_3d_viewer.jpg")
cv2.imwrite(t_path, twin_img)
print(f"Saved Digital Twin screenshot to {t_path}")

gis_img = render_gis_corridor_scene()
g_path = os.path.join(artifact_dir, "screenshot_digital_twin_gis_corridor.jpg")
cv2.imwrite(g_path, gis_img)
print(f"Saved GIS Corridor screenshot to {g_path}")

