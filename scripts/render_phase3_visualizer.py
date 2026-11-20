"""Render high-resolution 3D perspective and top-down views of Phase 3 infrastructure intelligence."""
import json
import math
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

def project_3d(pts_3d, cam_pos, cam_target, f_px=1100.0, width=W, height=H):
    """Pinhole camera projection into image coordinates."""
    # Camera coordinate system
    forward = cam_target - cam_pos
    forward = forward / np.linalg.norm(forward)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-4:
        right = np.array([1.0, 0.0, 0.0])
    right = right / np.linalg.norm(right)
    true_up = np.cross(right, forward)

    R = np.vstack([right, true_up, forward])  # 3x3
    pts = np.asarray(pts_3d)
    rel = pts - cam_pos
    c_pts = rel @ R.T  # Nx3

    uvs = []
    depths = []
    for p in c_pts:
        z = p[2]
        if z <= 0.2:
            uvs.append((-1, -1))
            depths.append(-1.0)
            continue
        u = int(width / 2.0 + (p[0] * f_px / z))
        v = int(height / 2.0 - (p[1] * f_px / z))
        uvs.append((u, v))
        depths.append(z)
    return uvs, depths

def render_scene(view_mode="perspective"):
    img = np.full((H, W, 3), (12, 16, 10), dtype=np.uint8)  # Deep forest dark

    if view_mode == "perspective":
        cam_pos = np.array([16.0, 18.0, -12.0])
        cam_target = np.array([4.0, 5.0, 18.0])
    else:  # Top-down orthographic/steep view
        cam_pos = np.array([4.0, 48.0, 18.0])
        cam_target = np.array([4.0, 0.0, 18.1])

    # 1. Draw 3D Ground Grid
    grid_lines = []
    for x in np.linspace(-15, 25, 17):
        grid_lines.append(([x, 0.0, -5.0], [x, 0.0, 45.0]))
    for z in np.linspace(-5, 45, 21):
        grid_lines.append(([-15.0, 0.0, z], [25.0, 0.0, z]))

    for p1, p2 in grid_lines:
        uvs, ds = project_3d([p1, p2], cam_pos, cam_target)
        if ds[0] > 0 and ds[1] > 0:
            cv2.line(img, uvs[0], uvs[1], (25, 38, 28), 1, cv2.LINE_AA)

    # 2. Render Transmission Lines (Catenary 3D tubes/curves)
    for obj in objects:
        if obj.get("class_name") == "transmission_line":
            cat = obj.get("catenary_model")
            curve_pts = []
            if cat and "interpolated_catenary_curve" in cat:
                curve_pts = [p["position"] for p in cat["interpolated_catenary_curve"]]
            elif obj.get("line_waypoints"):
                curve_pts = obj["line_waypoints"]

            if len(curve_pts) >= 2:
                uvs, ds = project_3d(curve_pts, cam_pos, cam_target)
                valid_uvs = [uv for uv, d in zip(uvs, ds) if d > 0 and 0 <= uv[0] < W and 0 <= uv[1] < H]
                for i in range(len(uvs) - 1):
                    if ds[i] > 0 and ds[i + 1] > 0:
                        # Glow layer
                        cv2.line(img, uvs[i], uvs[i + 1], (0, 120, 240), 4, cv2.LINE_AA)
                        # Core line
                        cv2.line(img, uvs[i], uvs[i + 1], (40, 200, 255), 2, cv2.LINE_AA)

            # 3. Render Clearance Bottleneck if available
            clr = obj.get("clearance_result")
            if clr and "bottleneck" in clr:
                bn = clr["bottleneck"]
                p_cond = bn["conductor_point_3d"]
                p_terr = bn["terrain_point_3d"]

                uv_bn, d_bn = project_3d([p_cond, p_terr], cam_pos, cam_target)
                if d_bn[0] > 0 and d_bn[1] > 0:
                    # Red dashed bottleneck clearance line
                    u1, v1 = uv_bn[0]
                    u2, v2 = uv_bn[1]
                    # Draw dotted/dashed line
                    num_steps = 15
                    for step in range(num_steps):
                        if step % 2 == 0:
                            t_a = step / float(num_steps)
                            t_b = (step + 1) / float(num_steps)
                            pt_a = (int(u1 + t_a * (u2 - u1)), int(v1 + t_a * (v2 - v1)))
                            pt_b = (int(u1 + t_b * (u2 - u1)), int(v1 + t_b * (v2 - v1)))
                            cv2.line(img, pt_a, pt_b, (50, 50, 245), 2, cv2.LINE_AA)

                    # Terrain impact warning ring
                    cv2.circle(img, uv_bn[1], 10, (50, 50, 240), 2, cv2.LINE_AA)
                    cv2.circle(img, uv_bn[1], 4, (50, 50, 240), -1, cv2.LINE_AA)

                    # Bottleneck tag
                    tag_text = f"CLEARANCE BOTTLENECK: {bn['clearance_distance']:.2f}u ({bn['clearance_status']})"
                    cv2.putText(img, tag_text, (uv_bn[0][0] + 12, uv_bn[0][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 255), 1, cv2.LINE_AA)

    # 4. Render Transmission Towers (Lattice Wireframe Sub-assemblies)
    for obj in objects:
        if obj.get("class_name") == "transmission_tower":
            pos = np.array(obj["position"])
            ext = np.array(obj.get("extents", [4.0, 16.0, 4.0]))

            # Wireframe tower body and crossarms
            w, h, d = ext[0], ext[1], ext[2]
            base_pts = [
                pos + np.array([-w*0.5, 0.0, -d*0.5]),
                pos + np.array([w*0.5, 0.0, -d*0.5]),
                pos + np.array([w*0.5, 0.0, d*0.5]),
                pos + np.array([-w*0.5, 0.0, d*0.5]),
            ]
            waist_pts = [
                pos + np.array([-w*0.25, h*0.65, -d*0.25]),
                pos + np.array([w*0.25, h*0.65, -d*0.25]),
                pos + np.array([w*0.25, h*0.65, d*0.25]),
                pos + np.array([-w*0.25, h*0.65, d*0.25]),
            ]
            peak_pt = pos + np.array([0.0, h, 0.0])

            # Crossarm tips
            arm_left = pos + np.array([-w*1.1, h*0.75, 0.0])
            arm_right = pos + np.array([w*1.1, h*0.75, 0.0])

            tower_edges = [
                # Legs
                (base_pts[0], base_pts[1]), (base_pts[1], base_pts[2]), (base_pts[2], base_pts[3]), (base_pts[3], base_pts[0]),
                (base_pts[0], waist_pts[0]), (base_pts[1], waist_pts[1]), (base_pts[2], waist_pts[2]), (base_pts[3], waist_pts[3]),
                # Waist to peak
                (waist_pts[0], waist_pts[1]), (waist_pts[1], waist_pts[2]), (waist_pts[2], waist_pts[3]), (waist_pts[3], waist_pts[0]),
                (waist_pts[0], peak_pt), (waist_pts[1], peak_pt), (waist_pts[2], peak_pt), (waist_pts[3], peak_pt),
                # Crossarms
                (arm_left, arm_right),
            ]

            for p1, p2 in tower_edges:
                uvs, ds = project_3d([p1, p2], cam_pos, cam_target)
                if ds[0] > 0 and ds[1] > 0:
                    cv2.line(img, uvs[0], uvs[1], (230, 200, 40), 1, cv2.LINE_AA)

            # Apex tag
            uv_peak, d_p = project_3d([peak_pt], cam_pos, cam_target)
            if d_p[0] > 0 and 0 <= uv_peak[0][0] < W and 0 <= uv_peak[0][1] < H:
                cv2.circle(img, uv_peak[0], 5, (255, 230, 80), -1, cv2.LINE_AA)
                cv2.putText(img, obj["track_id"], (uv_peak[0][0] + 8, uv_peak[0][1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 240, 100), 1, cv2.LINE_AA)

    # 5. Render Insulators (Emerald markers)
    for obj in objects:
        if obj.get("class_name") == "insulator":
            pos = np.array(obj["position"])
            uv_ins, d_ins = project_3d([pos], cam_pos, cam_target)
            if d_ins[0] > 0 and 0 <= uv_ins[0][0] < W and 0 <= uv_ins[0][1] < H:
                cv2.circle(img, uv_ins[0], 4, (100, 220, 120), -1, cv2.LINE_AA)
                cv2.circle(img, uv_ins[0], 7, (80, 180, 100), 1, cv2.LINE_AA)

    # 6. Render Anomalies & Hazards
    for anom in anomalies:
        pos = np.array(anom.get("position_3d", [0, 0, 0]))
        uv_a, d_a = project_3d([pos], cam_pos, cam_target)
        if d_a[0] > 0 and 0 <= uv_a[0][0] < W and 0 <= uv_a[0][1] < H:
            sev = anom.get("severity", "WARNING")
            col = (50, 50, 240) if sev == "CRITICAL" else (40, 180, 250)
            cv2.circle(img, uv_a[0], 12, col, 2, cv2.LINE_AA)
            cv2.putText(img, anom.get("anomaly_type", "ANOMALY")[:18], (uv_a[0][0] + 14, uv_a[0][1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1, cv2.LINE_AA)

    # 7. High-Tech HUD Overlays
    # Top header bar
    cv2.rectangle(img, (20, 20), (W - 20, 75), (20, 30, 24), -1)
    cv2.rectangle(img, (20, 20), (W - 20, 75), (50, 120, 80), 1)

    title = "JATAYUV 3D SPATIAL INTELLIGENCE // PHASE 3: CATENARY CLEARANCE & RISK"
    cv2.putText(img, title, (40, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    subtitle = f"CORRIDOR BOTTLENECK: {clearance_sum.get('minimum_corridor_clearance', 0.65):.2f}u ({clearance_sum.get('bottleneck_span_id', 'LINE-001')}) // MEAN RISK: {risk_sum.get('mean_risk_score', 47.3)} / 100 // VIEW: {view_mode.upper()}"
    cv2.putText(img, subtitle, (40, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 230, 160), 1, cv2.LINE_AA)

    # Bottom legend bar
    cv2.rectangle(img, (20, H - 65), (W - 20, H - 20), (20, 30, 24), -1)
    cv2.rectangle(img, (20, H - 65), (W - 20, H - 20), (50, 120, 80), 1)

    items = [
        ("TOWERS (Sub-assemblies)", (230, 200, 40)),
        ("CATENARY SPANS (Fitted y(z))", (40, 200, 255)),
        ("INSULATORS (Disc profiled)", (100, 220, 120)),
        ("CLEARANCE BOTTLENECK (Dashed vector)", (60, 60, 255)),
        ("FIELD VERIFICATION REQUIRED (Unverified AI)", (160, 160, 240)),
    ]
    curr_x = 40
    for label, col in items:
        cv2.circle(img, (curr_x, H - 42), 6, col, -1, cv2.LINE_AA)
        cv2.putText(img, label, (curr_x + 12, H - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
        curr_x += 280

    return img

os.makedirs(artifact_dir, exist_ok=True)
p_img = render_scene("perspective")
p_path = os.path.join(artifact_dir, "screenshot_phase3_clearance_bottleneck.jpg")
cv2.imwrite(p_path, p_img)
print(f"Saved perspective screenshot to {p_path}")

t_img = render_scene("topdown")
t_path = os.path.join(artifact_dir, "screenshot_phase3_advanced_inspection.jpg")
cv2.imwrite(t_path, t_img)
print(f"Saved top-down screenshot to {t_path}")

