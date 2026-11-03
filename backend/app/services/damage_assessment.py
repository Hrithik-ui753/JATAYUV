import os
import json
import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List

class SiameseDamageAssessmentModel(nn.Module):
    """
    Dual-stream Siamese Neural Network for multi-temporal aerial damage classification.
    Processes aligned Pre- and Post-disaster aerial imagery to quantify building damage levels.
    """
    def __init__(self, num_damage_classes: int = 4):
        super().__init__()
        # Shared feature encoder
        self.branch = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )

        # Cross-temporal difference fusion head
        self.classifier = nn.Sequential(
            nn.ConvTranspose2d(256, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_damage_classes, kernel_size=1),
        )

    def forward(self, pre_x, post_x):
        pre_f = self.branch(pre_x)
        post_f = self.branch(post_x)
        diff = torch.abs(post_f - pre_f)
        fused = torch.cat([post_f, diff], dim=1)
        logits = self.classifier(fused)
        return logits

class DamageAssessmentService:
    DAMAGE_LEVELS = [
        {"id": 0, "key": "no_damage", "label": "No Damage", "color": [46, 204, 113]},       # Emerald
        {"id": 1, "key": "minor_damage", "label": "Minor Damage", "color": [241, 196, 15]}, # Yellow
        {"id": 2, "key": "major_damage", "label": "Major Damage", "color": [230, 126, 34]}, # Orange
        {"id": 3, "key": "destroyed", "label": "Destroyed", "color": [231, 76, 60]},        # Red
    ]

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SiameseDamageAssessmentModel(num_damage_classes=4).to(self.device)
        self.model.eval()

    def assess_damage(
        self,
        pre_image_path: str,
        post_image_path: str,
        output_overlay_path: str,
        output_geojson_path: str = None,
    ) -> Dict[str, Any]:
        """
        Executes xBD-standard building damage evaluation between Pre and Post aerial captures.
        """
        pre_img = cv2.imread(pre_image_path)
        post_img = cv2.imread(post_image_path)

        if pre_img is None or post_img is None:
            raise ValueError("Pre- or Post-disaster image could not be loaded")

        orig_h, orig_w = post_img.shape[:2]
        target_w, target_h = 512, 512

        pre_resized = cv2.resize(pre_img, (target_w, target_h))
        post_resized = cv2.resize(post_img, (target_w, target_h))

        pre_tensor = torch.from_numpy(
            cv2.cvtColor(pre_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        ).permute(2, 0, 1).unsqueeze(0).to(self.device)

        post_tensor = torch.from_numpy(
            cv2.cvtColor(post_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        ).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(pre_tensor, post_tensor)
            preds = torch.argmax(logits, dim=1).squeeze().cpu().numpy().astype(np.uint8)

        # Scale predictions back to original resolution
        dense_damage = cv2.resize(preds, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

        # Extract simulated discrete building contours
        # In production, building polygons are mapped from pre-disaster footprint mask
        gray_pre = cv2.cvtColor(pre_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_pre, 140, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        total_buildings = 0
        counts_by_level = {"no_damage": 0, "minor_damage": 0, "major_damage": 0, "destroyed": 0}
        geojson_features = []

        # Color overlay on post-disaster image
        damage_overlay = post_img.copy()

        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < 300 or area > 50000:
                continue

            total_buildings += 1
            # Sample damage within this structure footprint
            mask_b = np.zeros((orig_h, orig_w), dtype=np.uint8)
            cv2.drawContours(mask_b, [cnt], -1, 255, -1)
            mean_damage_val = np.mean(dense_damage[mask_b == 255]) if np.any(mask_b == 255) else 0

            # Map mean damage to tier
            if mean_damage_val < 0.6:
                tier = "no_damage"
                color = [46, 204, 113]  # Green (BGR)
            elif mean_damage_val < 1.4:
                tier = "minor_damage"
                color = [15, 196, 241]  # Yellow (BGR)
            elif mean_damage_val < 2.2:
                tier = "major_damage"
                color = [34, 126, 230]  # Orange (BGR)
            else:
                tier = "destroyed"
                color = [60, 76, 231]   # Red (BGR)

            counts_by_level[tier] += 1

            # Draw highlighted polygon and label on overlay
            cv2.drawContours(damage_overlay, [cnt], -1, color, 3)

            approx = cv2.approxPolyDP(cnt, 2.0, True)
            poly_coords = [[float(pt[0][0]), float(pt[0][1])] for pt in approx]
            poly_coords.append(poly_coords[0])

            geojson_features.append({
                "type": "Feature",
                "properties": {
                    "building_id": total_buildings,
                    "damage_level": tier,
                    "severity_score": round(float(mean_damage_val) / 3.0, 3),
                    "footprint_area_px": round(float(area), 1),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [poly_coords],
                },
            })

        # Calculate statistics
        affected_count = counts_by_level["minor_damage"] + counts_by_level["major_damage"] + counts_by_level["destroyed"]
        damage_percentage = round((affected_count / max(1, total_buildings)) * 100.0, 1)

        # Severity index weighted calculation: (minor*0.33 + major*0.66 + destroyed*1.0) / total
        weighted_sum = (
            counts_by_level["minor_damage"] * 0.33 +
            counts_by_level["major_damage"] * 0.66 +
            counts_by_level["destroyed"] * 1.0
        )
        severity_index = round(weighted_sum / max(1, total_buildings), 3)

        # Save damage overlay image
        os.makedirs(os.path.dirname(output_overlay_path), exist_ok=True)
        cv2.imwrite(output_overlay_path, damage_overlay, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Save GeoJSON export
        if output_geojson_path:
            os.makedirs(os.path.dirname(output_geojson_path), exist_ok=True)
            fc = {"type": "FeatureCollection", "features": geojson_features}
            with open(output_geojson_path, "w", encoding="utf-8") as f:
                json.dump(fc, f, indent=2)

        return {
            "damage_overlay_path": output_overlay_path,
            "total_buildings": total_buildings,
            "counts_by_level": counts_by_level,
            "damage_percentage": damage_percentage,
            "severity_index": severity_index,
            "geojson_path": output_geojson_path,
        }

damage_service = DamageAssessmentService()

