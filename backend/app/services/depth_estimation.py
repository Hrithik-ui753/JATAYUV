"""Monocular depth estimation service (Depth Anything V2 Small, official).

Replaces the previous placeholder CNN that was registered under the name
"Depth Anything V2". The service now:

* loads the official Depth Anything V2 **Small** model through
  :mod:`backend.app.services.depth_engine` (strict checkpoint validation),
* supports model selection between the pretrained checkpoint and the JATAYUV
  fine-tuned checkpoint,
* keeps the historic ``estimate_depth(...)`` signature used by the API and Celery
  workers, so the existing API contract keeps working,
* never converts relative depth to metres. ``altitude_m`` is accepted for backwards
  compatibility but deliberately ignored: the network's output has no metric scale.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch

from backend.app.services.depth_engine import (
    MODEL_CATALOG,
    DepthEngine,
    DepthModelError,
    list_models,
    resolve_model_id,
)


class DepthEstimationService:
    """Service wrapper around the verified Depth Anything V2 Small engine."""

    def __init__(self, model_id: Optional[str] = None, input_size: Optional[int] = None):
        self.default_model_id = resolve_model_id(model_id)
        self.default_input_size = input_size
        self._engines: Dict[tuple, DepthEngine] = {}

    # ------------------------------------------------------------------ engine
    def get_engine(
        self, model_id: Optional[str] = None, input_size: Optional[int] = None
    ) -> DepthEngine:
        key = (resolve_model_id(model_id), input_size or self.default_input_size)
        if key not in self._engines:
            self._engines[key] = DepthEngine(
                model_id=key[0], input_size=key[1]
            )
        return self._engines[key]

    def available_models(self) -> Dict[str, Dict[str, Any]]:
        return list_models()

    # ------------------------------------------------------------------ inference
    def estimate_depth(
        self,
        input_image_path: str,
        output_depth_path: str,
        output_colormap_path: str,
        altitude_m: Optional[float] = None,
        output_mesh_path: Optional[str] = None,
        model_id: Optional[str] = None,
        input_size: Optional[int] = None,
        output_raw_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run monocular depth inference and persist the depth artefacts.

        Returns metadata including ``depth_type`` ("relative" or "metric_calibrated")
        so callers can never mistake relative depth for metres.
        """
        engine = self.get_engine(model_id, input_size)
        image = cv2.imread(input_image_path, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Image not found or unreadable: {input_image_path}")

        result = engine.predict(image)
        inverse = result["inverse_depth"]
        loaded = result["model"]

        norm_inverse = engine.normalize_relative(inverse)
        relative_min = float(np.min(norm_inverse))
        relative_max = float(np.max(norm_inverse))
        relative_mean = float(np.mean(norm_inverse))

        os.makedirs(os.path.dirname(os.path.abspath(output_depth_path)), exist_ok=True)
        depth_16bit = (norm_inverse * 65535.0).astype(np.uint16)
        cv2.imwrite(output_depth_path, depth_16bit)

        depth_8bit = (norm_inverse * 255.0).astype(np.uint8)
        colormap = cv2.applyColorMap(depth_8bit, cv2.COLORMAP_TURBO)
        os.makedirs(os.path.dirname(os.path.abspath(output_colormap_path)), exist_ok=True)
        cv2.imwrite(output_colormap_path, colormap)

        if output_raw_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_raw_path)), exist_ok=True)
            np.save(output_raw_path, inverse.astype(np.float32))

        mesh_path = None
        if output_mesh_path:
            self._export_obj_mesh(norm_inverse, output_mesh_path)
            mesh_path = output_mesh_path

        depth_type = "relative"
        depth_unit = "relative_inverse_depth"
        metric_min = metric_max = metric_mean = None
        if loaded.calibration:
            metric = engine.calibrated_metric(inverse, loaded.calibration)
            if metric is not None and np.isfinite(metric).sum() > 0:
                depth_type = "metric_calibrated"
                depth_unit = "metre"
                metric_min = float(np.nanpercentile(metric, 1))
                metric_max = float(np.nanpercentile(metric, 99))
                metric_mean = float(np.nanmean(metric))

        metadata = {
            "depth_map_path": output_depth_path,
            "colormap_path": output_colormap_path,
            "raw_depth_path": output_raw_path,
            "mesh_obj_path": mesh_path,
            "depth_type": depth_type,
            "depth_unit": depth_unit,
            "depth_encoding": "normalized_inverse_relative (0=far, 1=near)",
            "is_metric": depth_type == "metric_calibrated",
            "min_depth_m": metric_min,
            "max_depth_m": metric_max,
            "mean_depth_m": metric_mean,
            "relative_min": relative_min,
            "relative_max": relative_max,
            "relative_mean": relative_mean,
            "model_id": loaded.spec.model_id,
            "model_label": loaded.spec.label,
            "model_version": loaded.spec.version,
            "checkpoint_path": loaded.spec.checkpoint,
            "checkpoint_sha256": loaded.sha256,
            "checkpoint_epoch": loaded.checkpoint_epoch,
            "input_size": loaded.input_size,
            "inference_ms": result["inference_ms"],
            "device": str(loaded.device),
            "altitude_m_used": False,
            "notes": (
                "Relative inverse depth from Depth Anything V2 Small. Pixel values are "
                "normalised per image and have no metric scale."
            ),
        }
        if altitude_m is not None:
            metadata["altitude_m_ignored"] = float(altitude_m)
        self._write_sidecar_metadata(output_depth_path, metadata)
        return metadata

    # ------------------------------------------------------------------ artefacts
    @staticmethod
    def _write_sidecar_metadata(depth_path: str, metadata: Dict[str, Any]) -> None:
        sidecar = os.path.splitext(depth_path)[0] + ".json"
        try:
            payload = {
                k: v
                for k, v in metadata.items()
                if k not in ("depth_map_path", "colormap_path")
            }
            with open(sidecar, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, default=str)
        except OSError:
            pass

    @staticmethod
    def _export_obj_mesh(depth_grid: np.ndarray, obj_path: str, downsample: int = 16) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(obj_path)), exist_ok=True)
        sub_grid = depth_grid[::downsample, ::downsample]
        rows, cols = sub_grid.shape
        with open(obj_path, "w", encoding="utf-8") as fh:
            fh.write("# JATAYUV-AI Depth Anything V2 Small surface mesh (relative height)\n")
            fh.write("# y is normalised relative depth (1=near); units are NOT metres\n")
            for r in range(rows):
                for c in range(cols):
                    x = (c / max(cols - 1, 1)) * 20.0 - 10.0
                    z = (r / max(rows - 1, 1)) * 20.0 - 10.0
                    y = float(sub_grid[r, c]) * 5.0
                    fh.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            for r in range(rows - 1):
                for c in range(cols - 1):
                    v1 = r * cols + c + 1
                    v2 = v1 + 1
                    v3 = (r + 1) * cols + c + 1
                    v4 = v3 + 1
                    fh.write(f"f {v1} {v3} {v2}\n")
                    fh.write(f"f {v2} {v3} {v4}\n")


depth_service = DepthEstimationService()
