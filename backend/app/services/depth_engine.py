"""JATAYUV depth inference engine (official Depth Anything V2 Small).

This module is the *only* place the backend touches a depth network. It loads the
vendored official implementation (``training/models/depth_anything_v2``) with strictly
verified checkpoints and runs inference on CPU or CUDA.

Two selectable checkpoints:

``pretrained``
    The official Depth Anything V2 Small release (SHA256 verified).
``jatayuv_drone_v1``
    The JATAYUV fine-tuned checkpoint (path from ``JATAYUV_DEPTH_CHECKPOINT`` or the
    default experiment output). If it is missing the engine raises
    :class:`DepthModelError` -- it never falls back to a toy network or fabricated
    weights.

Output semantics (unchanged from the official model): a non-negative **inverse relative
depth** field, higher = nearer, normalised for storage. The engine never converts this
to metres unless the checkpoint carries an explicitly fitted calibration model.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:  # allows ``python -m backend...`` and pytest from repo root
    sys.path.insert(0, _REPO_ROOT)

from training.models.dav2_factory import (  # noqa: E402
    OFFICIAL_SMALL_SHA256,
    SMALL_PARAM_COUNT,
    build_dav2_small,
    load_checkpoint_strict,
)


class DepthModelError(RuntimeError):
    """Raised when a requested checkpoint cannot be loaded or validated."""


DEFAULT_PRETRAINED = os.path.join(
    _REPO_ROOT, "training", "checkpoints", "pretrained", "depth_anything_v2_vits.pth"
)
DEFAULT_FINETUNED = os.environ.get(
    "JATAYUV_DEPTH_CHECKPOINT",
    os.path.join(
        _REPO_ROOT,
        "training", "checkpoints", "finetuned",
        "exp_b_skyscenes_relative", "best_model.pth",
    ),
)


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    label: str
    version: str
    checkpoint: str
    is_finetuned: bool
    description: str


MODEL_CATALOG: Dict[str, ModelSpec] = {
    "pretrained": ModelSpec(
        model_id="pretrained",
        label="Pretrained Depth Anything V2 Small",
        version="official-dav2-vits",
        checkpoint=DEFAULT_PRETRAINED,
        is_finetuned=False,
        description=(
            "Official Depth Anything V2 Small (24.79M parameters) as released by the "
            "Depth Anything team. Zero-shot relative inverse depth."
        ),
    ),
    "jatayuv_drone_v1": ModelSpec(
        model_id="jatayuv_drone_v1",
        label="JATAYUV fine-tuned Depth Anything V2 Small",
        version=os.environ.get("JATAYUV_DEPTH_VERSION", "jatayuv-drone-v1"),
        checkpoint=DEFAULT_FINETUNED,
        is_finetuned=True,
        description=(
            "Depth Anything V2 Small fine-tuned by JATAYUV on aerial depth supervision. "
            "Output remains relative inverse depth (no metric claim) unless a "
            "calibration was fitted and stored in the checkpoint."
        ),
    ),
}

MODEL_ALIASES = {
    "pretrained": "pretrained",
    "official": "pretrained",
    "depth_anything_v2_small_pretrained": "pretrained",
    "depth_anything_v2": "pretrained",
    "finetuned": "jatayuv_drone_v1",
    "fine-tuned": "jatayuv_drone_v1",
    "jatayuv": "jatayuv_drone_v1",
    "jatayuv_v1": "jatayuv_drone_v1",
    "jatayuv_drone_v1": "jatayuv_drone_v1",
}

DEFAULT_MODEL_ID = MODEL_ALIASES.get(
    os.environ.get("JATAYUV_DEPTH_MODEL", "pretrained").lower(), "pretrained"
)


def resolve_model_id(model_id: Optional[str]) -> str:
    if not model_id:
        return DEFAULT_MODEL_ID
    key = model_id.strip().lower()
    if key not in MODEL_ALIASES:
        raise DepthModelError(
            f"Unknown depth model '{model_id}'. Available: {sorted(set(MODEL_ALIASES))}"
        )
    return MODEL_ALIASES[key]


def list_models() -> Dict[str, Dict[str, Any]]:
    """Catalogue with live availability (does not load weights)."""
    out: Dict[str, Dict[str, Any]] = {}
    for model_id, spec in MODEL_CATALOG.items():
        out[model_id] = {
            "model_id": model_id,
            "label": spec.label,
            "version": spec.version,
            "description": spec.description,
            "is_finetuned": spec.is_finetuned,
            "checkpoint_path": spec.checkpoint,
            "checkpoint_available": os.path.isfile(spec.checkpoint),
            "depth_type": "relative",
            "depth_unit": "relative_inverse_depth",
        }
    return out


@dataclass
class LoadedDepthModel:
    spec: ModelSpec
    model: torch.nn.Module
    device: torch.device
    input_size: int
    sha256: str
    total_params: int
    checkpoint_epoch: Optional[int] = None
    calibration: Optional[Dict[str, float]] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class DepthEngine:
    """Thread-safe, lazily-loaded depth inference engine with a small model cache."""

    _cache: Dict[Tuple[str, int, str], LoadedDepthModel] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        model_id: Optional[str] = None,
        input_size: Optional[int] = None,
        device: Optional[str] = None,
    ):
        self.model_id = resolve_model_id(model_id)
        self.spec = MODEL_CATALOG[self.model_id]
        self.input_size = int(
            input_size
            or os.environ.get("JATAYUV_DEPTH_INPUT_SIZE", 518)
        )
        self.input_size = max(14, int(round(self.input_size / 14)) * 14)
        self.device = torch.device(
            device
            or ("cuda" if torch.cuda.is_available() else "cpu")
        )

    # ------------------------------------------------------------------ loading
    def _load(self) -> LoadedDepthModel:
        key = (self.model_id, self.input_size, str(self.device))
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached

            checkpoint = self.spec.checkpoint
            if not os.path.isfile(checkpoint):
                raise DepthModelError(
                    f"Depth checkpoint for '{self.model_id}' not found at {checkpoint}. "
                    + (
                        "Run the fine-tuning pipeline (docs/DEPTH_MODEL_TRAINING_PLAN.md) "
                        "or set JATAYUV_DEPTH_CHECKPOINT to an existing fine-tuned model."
                        if self.spec.is_finetuned
                        else "Run `python -m training.models.dav2_factory --download`."
                    )
                )

            model = build_dav2_small()
            try:
                report = load_checkpoint_strict(
                    model,
                    checkpoint,
                    verify_official_hash=not self.spec.is_finetuned,
                )
            except Exception as exc:  # invalid / foreign checkpoint
                raise DepthModelError(
                    f"Checkpoint validation failed for '{self.model_id}': {exc}"
                ) from exc

            if report.total_params != SMALL_PARAM_COUNT:
                raise DepthModelError(
                    f"Checkpoint has {report.total_params} parameters; Depth Anything V2 "
                    f"Small requires {SMALL_PARAM_COUNT}."
                )
            if self.spec.is_finetuned and report.sha256 == OFFICIAL_SMALL_SHA256:
                raise DepthModelError(
                    "The 'jatayuv_drone_v1' checkpoint is byte-identical to the official "
                    "pretrained weights: it is not a fine-tuned model."
                )

            payload: Dict[str, Any] = {}
            try:
                payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
            except Exception:
                payload = {}
            calibration = None
            if isinstance(payload, dict):
                arch = payload.get("architecture")
                if arch and arch != "DepthAnythingV2Small":
                    raise DepthModelError(
                        f"Checkpoint architecture '{arch}' is not DepthAnythingV2Small."
                    )
                calibration = payload.get("calibration")

            model.to(self.device).eval()
            loaded = LoadedDepthModel(
                spec=self.spec,
                model=model,
                device=self.device,
                input_size=self.input_size,
                sha256=report.sha256,
                total_params=report.total_params,
                checkpoint_epoch=payload.get("epoch") if isinstance(payload, dict) else None,
                calibration=calibration if isinstance(calibration, dict) else None,
                extra={
                    "checkpoint_bytes": report.bytes,
                    "dataset": payload.get("dataset") if isinstance(payload, dict) else None,
                    "experiment": payload.get("experiment") if isinstance(payload, dict) else None,
                },
            )
            self._cache[key] = loaded
            return loaded

    # ------------------------------------------------------------------ inference
    def _preprocess(self, image_bgr: np.ndarray) -> Tuple[torch.Tensor, Tuple[int, int]]:
        from torchvision.transforms import Compose

        from training.models.depth_anything_v2.util.transform import (
            NormalizeImage,
            PrepareForNet,
            Resize,
        )

        h, w = image_bgr.shape[:2]
        transform = Compose(
            [
                Resize(
                    width=self.input_size,
                    height=self.input_size,
                    resize_target=False,
                    keep_aspect_ratio=True,
                    ensure_multiple_of=14,
                    resize_method="lower_bound",
                    image_interpolation_method=cv2.INTER_CUBIC,
                ),
                NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                PrepareForNet(),
            ]
        )
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) / 255.0
        tensor = transform({"image": rgb})["image"]
        return torch.from_numpy(tensor).unsqueeze(0).to(self.device), (h, w)

    @torch.no_grad()
    def predict(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """Run inference on a BGR uint8 image; returns relative inverse depth."""
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Empty image passed to the depth engine")
        loaded = self._load()
        tensor, (h, w) = self._preprocess(image_bgr)

        if loaded.device.type == "cuda":
            torch.cuda.synchronize()
        started = time.perf_counter()
        raw = loaded.model(tensor)
        if loaded.device.type == "cuda":
            torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        depth = F.interpolate(
            raw[:, None], (h, w), mode="bilinear", align_corners=True
        )[0, 0]
        depth_np = depth.detach().float().cpu().numpy()

        return {
            "inverse_depth": depth_np,
            "inference_ms": round(elapsed_ms, 2),
            "model": loaded,
        }

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def normalize_relative(inverse_depth: np.ndarray) -> np.ndarray:
        """Robust [0,1] normalisation of inverse depth (1 = nearest)."""
        valid = np.isfinite(inverse_depth)
        if not valid.any():
            return np.zeros_like(inverse_depth, dtype=np.float32)
        lo, hi = np.percentile(inverse_depth[valid], [1, 99])
        if hi - lo < 1e-9:
            hi = lo + 1e-9
        norm = np.clip((inverse_depth - lo) / (hi - lo), 0.0, 1.0)
        return norm.astype(np.float32)

    @staticmethod
    def calibrated_metric(
        inverse_depth: np.ndarray, calibration: Dict[str, float]
    ) -> Optional[np.ndarray]:
        """depth = 1 / (a * pred + b) using an explicitly fitted calibration.

        Calibration is only produced by ``training/evaluation/calibration.py`` against
        real metric ground truth; the pretrained/fine-tuned relative model alone can
        never yield metres.
        """
        try:
            a = float(calibration["a"])
            b = float(calibration["b"])
        except (KeyError, TypeError, ValueError):
            return None
        denom = a * inverse_depth + b
        denom = np.where(np.abs(denom) < 1e-6, np.nan, denom)
        return 1.0 / denom
