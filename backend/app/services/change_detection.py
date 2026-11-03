import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any

class ChangeDetectionService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def detect_changes(
        self,
        before_image_path: str,
        after_image_path: str,
        output_diff_mask_path: str,
        output_heatmap_path: str,
        sensitivity_threshold: float = 35.0,
    ) -> Dict[str, Any]:
        """
        Computes spatial and pixel-level changes between bi-temporal flight surveys.
        """
        img_t0 = cv2.imread(before_image_path)
        img_t1 = cv2.imread(after_image_path)

        if img_t0 is None or img_t1 is None:
            raise ValueError("Before or After image could not be loaded")

        orig_h, orig_w = img_t1.shape[:2]

        # Ensure identical spatial dimensions
        if img_t0.shape[:2] != (orig_h, orig_w):
            img_t0 = cv2.resize(img_t0, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

        # 1. Grayscale difference & Gaussian blur for environmental illumination invariance
        gray_t0 = cv2.cvtColor(img_t0, cv2.COLOR_BGR2GRAY)
        gray_t1 = cv2.cvtColor(img_t1, cv2.COLOR_BGR2GRAY)

        blur_t0 = cv2.GaussianBlur(gray_t0, (5, 5), 0)
        blur_t1 = cv2.GaussianBlur(gray_t1, (5, 5), 0)

        diff = cv2.absdiff(blur_t0, blur_t1)

        # 2. Thresholding into binary change mask
        _, thresh = cv2.threshold(diff, sensitivity_threshold, 255, cv2.THRESH_BINARY)

        # 3. Morphological opening and closing to remove noise and bridge structural changes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        clean_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

        # 4. Generate Change Intensity Heatmap
        # Normalized diff normalized between 0-255
        norm_diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)

        # Alpha blend heatmap over post-survey image for spatial context
        overlay = cv2.addWeighted(img_t1, 0.6, heatmap, 0.4, 0)

        # 5. Calculate statistics
        total_pixels = orig_w * orig_h
        changed_pixels = int(np.sum(clean_mask > 0))
        changed_area_pct = round((changed_pixels / total_pixels) * 100.0, 2)
        mean_intensity = float(np.mean(diff[clean_mask > 0])) if changed_pixels > 0 else 0.0
        significance_score = round(min(1.0, (changed_area_pct / 100.0) * (mean_intensity / 128.0) * 2.0), 3)

        # Save results
        os.makedirs(os.path.dirname(output_diff_mask_path), exist_ok=True)
        cv2.imwrite(output_diff_mask_path, clean_mask)

        os.makedirs(os.path.dirname(output_heatmap_path), exist_ok=True)
        cv2.imwrite(output_heatmap_path, overlay)

        return {
            "diff_mask_path": output_diff_mask_path,
            "heatmap_path": output_heatmap_path,
            "changed_area_pct": changed_area_pct,
            "changed_pixels": changed_pixels,
            "significance_score": significance_score,
        }

change_service = ChangeDetectionService()

