"""Multi-temporal building damage assessment service (xBD 4-tier).

P0 integrity contract
---------------------
* Inference only runs with a verified trained checkpoint loaded strictly.
* Randomly initialised weights are never built at import time and never used as a
  fallback.
* A missing/incompatible checkpoint raises :class:`DamageModelUnavailable`
  (``status="unavailable"``) before any artifact is written.
* Damage classes, counts and severity are derived only from real network output.
  No accuracy metric is computed or claimed at inference time.

Checkpoint format mirrors the segmentation service: a ``torch.save`` dict holding a
raw state dict or one of ``model_state`` / ``state_dict`` / ``model_state_dict`` /
``weights``, optionally with ``architecture``, ``num_classes`` and provenance.
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn

from .segmentation import file_sha256, _extract_state_dict

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

ARCHITECTURE = "SiameseDamageAssessmentModel"

DEFAULT_DAMAGE_CHECKPOINT = os.environ.get(
    "JATAYUV_DAMAGE_CHECKPOINT",
    os.path.join(_REPO_ROOT, "storage", "models", "checkpoints", "damage_xbd_siamese.pth"),
)


class DamageModelUnavailable(RuntimeError):
    """Raised when no verified damage-assessment checkpoint can be loaded."""

    status = "unavailable"

    def __init__(
        self,
        message: str,
        *,
        checkpoint_path: Optional[str] = None,
        reason: str = "checkpoint_missing",
    ) -> None:
        super().__init__(message)
        self.checkpoint_path = checkpoint_path
        self.reason = reason


class SiameseDamageAssessmentModel(nn.Module):
    """Dual-stream Siamese network for aligned pre/post disaster aerial imagery.

    Architecture definition only; see :func:`load_verified_model`.
    """

    def __init__(self, num_damage_classes: int = 4):
        super().__init__()
        self.num_damage_classes = num_damage_classes
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


def load_verified_model(
    checkpoint_path: str,
    *,
    num_damage_classes: int,
    device: torch.device,
) -> tuple[SiameseDamageAssessmentModel, Dict[str, Any]]:
    """Build the architecture and load every weight from a verified checkpoint."""
    if not checkpoint_path or not os.path.isfile(checkpoint_path):
        raise DamageModelUnavailable(
            "No verified damage-assessment checkpoint found at "
            f"{checkpoint_path!r}. Train or install a checkpoint and point "
            "JATAYUV_DAMAGE_CHECKPOINT at it; random weights are never used.",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_missing",
        )

    try:
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    except Exception as exc:
        raise DamageModelUnavailable(
            f"Damage checkpoint at {checkpoint_path!r} could not be read: {exc}",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_unreadable",
        ) from exc

    metadata: Dict[str, Any] = payload if isinstance(payload, dict) else {}
    architecture = metadata.get("architecture")
    if architecture is not None and architecture != ARCHITECTURE:
        raise DamageModelUnavailable(
            f"Damage checkpoint architecture {architecture!r} does not match {ARCHITECTURE!r}.",
            checkpoint_path=checkpoint_path,
            reason="architecture_mismatch",
        )
    declared_classes = metadata.get("num_classes")
    if declared_classes is not None and int(declared_classes) != num_damage_classes:
        raise DamageModelUnavailable(
            f"Damage checkpoint declares {declared_classes} classes but the service "
            f"expects {num_damage_classes}.",
            checkpoint_path=checkpoint_path,
            reason="class_count_mismatch",
        )

    try:
        state_dict, _ = _extract_state_dict(payload)
    except Exception as exc:
        raise DamageModelUnavailable(
            f"Damage checkpoint does not contain a recognisable model state dict: {exc}",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_unreadable",
        ) from exc

    model = SiameseDamageAssessmentModel(num_damage_classes=num_damage_classes)
    try:
        model.load_state_dict(state_dict, strict=True)
    except Exception as exc:
        raise DamageModelUnavailable(
            f"Damage checkpoint is incompatible with {ARCHITECTURE}: {exc}",
            checkpoint_path=checkpoint_path,
            reason="state_dict_incompatible",
        ) from exc

    model.to(device).eval()
    info = {
        "architecture": ARCHITECTURE,
        "num_classes": num_damage_classes,
        "checkpoint_path": checkpoint_path,
        "checkpoint_sha256": file_sha256(checkpoint_path),
        "dataset": metadata.get("dataset"),
        "training_run": metadata.get("training_run"),
        "created_at": metadata.get("created_at"),
        "reported_metrics": metadata.get("metrics"),
    }
    return model, info


@dataclass
class _LoadedDamageModel:
    model: SiameseDamageAssessmentModel
    device: torch.device
    info: Dict[str, Any]


class DamageAssessmentService:
    DAMAGE_LEVELS: List[Dict[str, Any]] = [
        {"id": 0, "key": "no_damage", "label": "No Damage", "color": [46, 204, 113]},       # Emerald
        {"id": 1, "key": "minor_damage", "label": "Minor Damage", "color": [241, 196, 15]}, # Yellow
        {"id": 2, "key": "major_damage", "label": "Major Damage", "color": [230, 126, 34]}, # Orange
        {"id": 3, "key": "destroyed", "label": "Destroyed", "color": [231, 76, 60]},        # Red
    ]

    def __init__(self, checkpoint_path: Optional[str] = None):
        self._checkpoint_path = checkpoint_path or DEFAULT_DAMAGE_CHECKPOINT
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded: Optional[_LoadedDamageModel] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------- availability
    @property
    def checkpoint_path(self) -> str:
        return self._checkpoint_path

    def checkpoint_info(self) -> Dict[str, Any]:
        path = self._checkpoint_path
        exists = bool(path) and os.path.isfile(path)
        info: Dict[str, Any] = {
            "architecture": ARCHITECTURE,
            "num_classes": len(self.DAMAGE_LEVELS),
            "checkpoint_path": path,
            "checkpoint_available": exists,
            "status": "available" if exists else "unavailable",
        }
        if exists:
            try:
                info["checkpoint_sha256"] = file_sha256(path)
            except OSError:
                info["checkpoint_sha256"] = None
        return info

    def is_available(self) -> bool:
        return bool(self._checkpoint_path) and os.path.isfile(self._checkpoint_path)

    def get_model(self) -> _LoadedDamageModel:
        with self._lock:
            if self._loaded is not None:
                return self._loaded
            model, info = load_verified_model(
                self._checkpoint_path,
                num_damage_classes=len(self.DAMAGE_LEVELS),
                device=self._device,
            )
            self._loaded = _LoadedDamageModel(model=model, device=self._device, info=info)
            return self._loaded

    # --------------------------------------------------------------- inference
    def assess_damage(
        self,
        pre_image_path: str,
        post_image_path: str,
        output_overlay_path: str,
        output_geojson_path: str = None,
    ) -> Dict[str, Any]:
        """Evaluate building damage with a verified checkpoint only."""
        loaded = self.get_model()

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
        ).permute(2, 0, 1).unsqueeze(0).to(loaded.device)

        post_tensor = torch.from_numpy(
            cv2.cvtColor(post_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        ).permute(2, 0, 1).unsqueeze(0).to(loaded.device)

        with torch.no_grad():
            logits = loaded.model(pre_tensor, post_tensor)
            preds = torch.argmax(logits, dim=1).squeeze().cpu().numpy().astype(np.uint8)

        # Scale predictions back to original resolution
        dense_damage = cv2.resize(preds, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)

        # Footprint derivation: threshold on the pre-disaster image. These are heuristic
        # candidate footprints, not model-predicted building instances; the report says so.
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
        os.makedirs(os.path.dirname(os.path.abspath(output_overlay_path)), exist_ok=True)
        cv2.imwrite(output_overlay_path, damage_overlay, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Save GeoJSON export
        if output_geojson_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_geojson_path)), exist_ok=True)
            fc = {"type": "FeatureCollection", "features": geojson_features}
            with open(output_geojson_path, "w", encoding="utf-8") as f:
                json.dump(fc, f, indent=2)

        return {
            "status": "completed",
            "damage_overlay_path": output_overlay_path,
            "total_buildings": total_buildings,
            "counts_by_level": counts_by_level,
            "damage_percentage": damage_percentage,
            "severity_index": severity_index,
            "geojson_path": output_geojson_path,
            "checkpoint_path": loaded.info["checkpoint_path"],
            "checkpoint_sha256": loaded.info["checkpoint_sha256"],
            "architecture": loaded.info["architecture"],
            "dataset": loaded.info["dataset"],
            "reported_metrics": loaded.info["reported_metrics"],
            "footprint_source": "pre_image_threshold_heuristic",
            "metrics_note": (
                "Severity index and damage percentages are computed from this run's "
                "predictions. No accuracy metric is claimed at inference time."
            ),
        }


damage_service = DamageAssessmentService()
