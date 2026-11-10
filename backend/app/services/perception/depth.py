from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import numpy.typing as npt

from backend.app.services.depth_estimation import DepthEstimationService
from backend.app.services.depth_engine import DepthModelError

log = logging.getLogger("jatayuv.perception.depth")

DepthArray = npt.NDArray[np.float32]


@dataclass
class DepthInferenceResult:
    depth_map_path: str
    depth_visualization_path: str
    raw_depth_path: Optional[str]
    model_id: str
    model_version: str
    checkpoint_sha256: str
    depth_type: str
    depth_unit: str
    is_metric: bool
    input_width: int
    input_height: int
    output_width: int
    output_height: int
    inference_device: str
    inference_duration_ms: float
    preprocessing_json: Dict[str, Any]
    depth_min: Optional[float]
    depth_max: Optional[float]
    depth_mean: Optional[float]
    relative_min: Optional[float]
    relative_max: Optional[float]
    relative_mean: Optional[float]
    confidence_json: Dict[str, Any]
    inverse_depth: DepthArray
    normalized_visualization: np.ndarray


def _normalize_visualization(inverse_depth: DepthArray) -> np.ndarray:
    valid = np.isfinite(inverse_depth)
    vis = np.zeros_like(inverse_depth, dtype=np.float32)
    if valid.any():
        lo, hi = np.percentile(inverse_depth[valid], [1, 99])
        if hi - lo < 1e-9:
            hi = lo + 1e-9
        vis = np.clip((inverse_depth - lo) / (hi - lo), 0.0, 1.0)
    return vis


def _make_visualization_image(normalized: np.ndarray) -> np.ndarray:
    img = (np.clip(normalized, 0.0, 1.0) * 255.0).astype(np.uint8)
    return cv2.applyColorMap(img, cv2.COLORMAP_TURBO)


def infer_depth(
    frame_bgr: np.ndarray,
    *,
    model_id: Optional[str] = None,
    input_size: Optional[int] = None,
) -> DepthInferenceResult:
    """Run Depth Anything V2 Small inference on a single BGR frame.

    Returns measured depth outputs. This is relative inverse depth, not metric.
    """
    service = DepthEstimationService(model_id=model_id, input_size=input_size)
    h, w = frame_bgr.shape[:2]

    # Write the frame to a temp path because the existing service expects a file.
    tmp_frame = os.path.abspath("__.tmp_depth_frame.jpg")
    try:
        ok = cv2.imwrite(tmp_frame, frame_bgr)
        if not ok or not os.path.isfile(tmp_frame):
            raise ValueError("Failed to write temporary frame for depth inference")

        depth_path = tmp_frame + ".depth.png"
        colormap_path = tmp_frame + ".depth_colormap.png"
        raw_path = tmp_frame + ".depth.npy"

        metadata = service.estimate_depth(
            input_image_path=tmp_frame,
            output_depth_path=depth_path,
            output_colormap_path=colormap_path,
            output_raw_path=raw_path,
            model_id=model_id,
            input_size=input_size,
        )

        raw = np.load(raw_path)
        normalized_vis = _normalize_visualization(raw)
        vis_image = _make_visualization_image(normalized_vis)

<<<<<<< HEAD
        h, w = frame_bgr.shape[:2]
=======
>>>>>>> origin/main
        return DepthInferenceResult(
            depth_map_path=depth_path,
            depth_visualization_path=colormap_path,
            raw_depth_path=raw_path,
            model_id=metadata["model_id"],
            model_version=metadata["model_version"],
            checkpoint_sha256=metadata["checkpoint_sha256"],
<<<<<<< HEAD
            depth_type=metadata.get("depth_type", "relative"),
            depth_unit="relative_inverse_depth",
            is_metric=False,
            input_width=input_size or 518,
            input_height=input_size or 518,
            output_width=w,
            output_height=h,
=======
            depth_type=metadata["depth_type"],
            depth_unit=metadata["depth_unit"],
            is_metric=metadata["is_metric"],
            input_width=input_size or 518,
            input_height=input_size or 518,
            output_width=int(raw.shape[1]),
            output_height=int(raw.shape[0]),
>>>>>>> origin/main
            inference_device=metadata["device"],
            inference_duration_ms=float(metadata["inference_ms"]),
            preprocessing_json={
                "model_id": model_id,
                "input_size": input_size,
                "normalization": "percentile_1_99_per_image",
            },
            depth_min=None,
            depth_max=None,
            depth_mean=None,
            relative_min=float(metadata["relative_min"]),
            relative_max=float(metadata["relative_max"]),
            relative_mean=float(metadata["relative_mean"]),
            confidence_json={},
            inverse_depth=raw.astype(np.float32),
            normalized_visualization=normalized_vis.astype(np.float32),
        )
    finally:
        for p in (tmp_frame, depth_path, colormap_path, raw_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass


def is_depth_available(model_id: Optional[str] = None) -> bool:
<<<<<<< HEAD
    try:
        service = DepthEstimationService(model_id=model_id)
        spec = service.get_engine(model_id=model_id).spec
        return bool(spec.checkpoint) and os.path.isfile(spec.checkpoint)
    except Exception:
        return False


def describe_depth_model() -> Dict[str, Any]:
    try:
        service = DepthEstimationService()
        spec = service.get_engine().spec
        available = bool(spec.checkpoint) and os.path.isfile(spec.checkpoint)
        model_id = spec.model_id
        label = spec.label
        version = spec.version
        ckpt = spec.checkpoint
    except Exception:
        available = False
        ckpt = None
        model_id = "depth_anything_v2_small"
        label = "Depth Anything V2 Small"
        version = "2.0.0"

    return {
        "model_id": model_id,
        "model_name": label,
        "version": version,
        "depth_type": "relative",
        "is_metric": False,
        "depth_unit": "relative_inverse_depth",
        "checkpoint_available": available,
        "checkpoint_path": ckpt,
        "status": "available" if available else "unavailable",
    }

=======
    service = DepthEstimationService(model_id=model_id)
    models = service.available_models()
    spec = service.get_engine(model_id=model_id).spec
    return bool(spec.checkpoint) and os.path.isfile(spec.checkpoint)


def describe_depth_model() -> Dict[str, Any]:
    from backend.app.services.perception import describe_depth_model as _describe

    return _describe()
>>>>>>> origin/main
