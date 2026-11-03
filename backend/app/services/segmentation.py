import os
import json
import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List

class AerialSegmentationModel(nn.Module):
    """
    High-Resolution Aerial Semantic Segmentation Network.
    Maps aerial multispectral features into discrete spatial land-use classes.
    """
    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.num_classes = num_classes
        self.backbone = nn.Sequential(
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
        self.classifier = nn.Sequential(
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, kernel_size=1),
        )

    def forward(self, x):
        feats = self.backbone(x)
        logits = self.classifier(feats)
        return logits

class SemanticSegmentationService:
    CLASSES = [
        {"id": 0, "name": "background", "label": "Other / Unclassified", "color": [0, 0, 0]},
        {"id": 1, "name": "building", "label": "Buildings & Roofs", "color": [246, 92, 139]},   # BGR for #8b5cf6
        {"id": 2, "name": "vegetation", "label": "Canopy & Trees", "color": [129, 185, 16]},   # BGR for #10b981
        {"id": 3, "name": "road", "label": "Roads & Asphalt", "color": [139, 116, 100]},       # BGR for #64748b
        {"id": 4, "name": "water", "label": "Water Surfaces", "color": [246, 130, 59]},        # BGR for #3b82f6
        {"id": 5, "name": "soil", "label": "Bare Ground / Sand", "color": [11, 158, 245]},     # BGR for #f59e0b
        {"id": 6, "name": "vehicle", "label": "Vehicles & Assets", "color": [68, 68, 239]},    # BGR for #ef4444
    ]

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AerialSegmentationModel(num_classes=len(self.CLASSES)).to(self.device)
        self.model.eval()

    def segment_aerial_image(
        self,
        input_image_path: str,
        output_mask_path: str,
        output_overlay_path: str,
        output_geojson_path: str = None,
    ) -> Dict[str, Any]:
        """
        Segments land-use and land-cover classes from high-resolution aerial imagery.
        """
        img = cv2.imread(input_image_path)
        if img is None:
            raise ValueError(f"Could not load image at {input_image_path}")

        orig_h, orig_w = img.shape[:2]
        target_w, target_h = 512, 512
        resized = cv2.resize(img, (target_w, target_h))

        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            preds = torch.argmax(logits, dim=1).squeeze().cpu().numpy().astype(np.uint8)

        # Scale predictions back to original resolution
        dense_mask = cv2.resize(preds, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

        # Calculate class coverage distribution
        total_pixels = orig_w * orig_h
        class_distribution = {}
        for c in self.CLASSES:
            if c["id"] == 0:
                continue
            count = int(np.sum(dense_mask == c["id"]))
            pct = round((count / total_pixels) * 100.0, 2)
            class_distribution[c["name"]] = pct

        # Generate colorized mask overlay
        color_mask = np.zeros_like(img)
        for c in self.CLASSES:
            color_mask[dense_mask == c["id"]] = c["color"]

        # Blend with original image (40% original + 60% color mask)
        overlay = cv2.addWeighted(img, 0.45, color_mask, 0.55, 0)

        # Save mask & overlay
        os.makedirs(os.path.dirname(output_mask_path), exist_ok=True)
        cv2.imwrite(output_mask_path, dense_mask)

        os.makedirs(os.path.dirname(output_overlay_path), exist_ok=True)
        cv2.imwrite(output_overlay_path, overlay)

        # Optional GeoJSON polygon export of building footprints
        if output_geojson_path:
            self._export_building_geojson(dense_mask, output_geojson_path)

        return {
            "mask_path": output_mask_path,
            "overlay_path": output_overlay_path,
            "class_distribution": class_distribution,
            "geojson_path": output_geojson_path,
        }

    def _export_building_geojson(self, mask: np.ndarray, geojson_path: str):
        building_mask = (mask == 1).astype(np.uint8) * 255
        contours, _ = cv2.findContours(building_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        features = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < 50:  # Filter noise
                continue
            approx = cv2.approxPolyDP(cnt, 2.0, True)
            poly_coords = [[float(pt[0][0]), float(pt[0][1])] for pt in approx]
            if len(poly_coords) < 3:
                continue
            # Close polygon
            poly_coords.append(poly_coords[0])

            features.append({
                "type": "Feature",
                "properties": {
                    "id": i + 1,
                    "class": "building",
                    "pixel_area": round(float(area), 1),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [poly_coords],
                },
            })

        fc = {"type": "FeatureCollection", "features": features}
        os.makedirs(os.path.dirname(geojson_path), exist_ok=True)
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)

segmentation_service = SemanticSegmentationService()

