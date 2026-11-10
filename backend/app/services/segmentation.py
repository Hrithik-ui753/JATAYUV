<<<<<<< HEAD
"""Aerial semantic segmentation service.

P0 integrity contract
---------------------
* The network is **only** ever run with a verified trained checkpoint loaded
  strictly (``load_state_dict(strict=True)``).
* No randomly initialised network is built at import time, and random weights are
  never used as a silent fallback.
* If the checkpoint is missing, unreadable or architecturally incompatible the
  service raises :class:`SegmentationModelUnavailable` (``status="unavailable"``).
  Callers must surface that as an explicit error, never as a prediction.
* No accuracy metric is reported here. Metrics belong to the training/evaluation
  pipeline and must be produced by real evaluation runs.

The checkpoint format expected is a ``torch.save`` dict containing either a raw
state dict or one of the keys ``model_state`` / ``state_dict`` / ``model_state_dict``
/ ``weights``, optionally with ``architecture``, ``num_classes`` and provenance
metadata (``dataset``, ``training_run``, ``metrics``, ``created_at``).
"""
from __future__ import annotations

import hashlib
import json
=======
<<<<<<< HEAD
import os
import json
=======
"""Aerial semantic segmentation service.

P0 integrity contract
---------------------
* The network is **only** ever run with a verified trained checkpoint loaded
  strictly (``load_state_dict(strict=True)``).
* No randomly initialised network is built at import time, and random weights are
  never used as a silent fallback.
* If the checkpoint is missing, unreadable or architecturally incompatible the
  service raises :class:`SegmentationModelUnavailable` (``status="unavailable"``).
  Callers must surface that as an explicit error, never as a prediction.
* No accuracy metric is reported here. Metrics belong to the training/evaluation
  pipeline and must be produced by real evaluation runs.

The checkpoint format expected is a ``torch.save`` dict containing either a raw
state dict or one of the keys ``model_state`` / ``state_dict`` / ``model_state_dict``
/ ``weights``, optionally with ``architecture``, ``num_classes`` and provenance
metadata (``dataset``, ``training_run``, ``metrics``, ``created_at``).
"""
from __future__ import annotations

import hashlib
import json
>>>>>>> origin/main
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
import cv2
import numpy as np
import torch
import torch.nn as nn
<<<<<<< HEAD

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

ARCHITECTURE = "AerialSegmentationModel"
STATE_DICT_KEYS = ("model_state", "state_dict", "model_state_dict", "weights")

DEFAULT_SEGMENTATION_CHECKPOINT = os.environ.get(
    "JATAYUV_SEGMENTATION_CHECKPOINT",
    os.path.join(_REPO_ROOT, "storage", "models", "checkpoints", "segmentation_loveda.pth"),
)


class SegmentationModelUnavailable(RuntimeError):
    """Raised when no verified segmentation checkpoint can be loaded.

    ``status`` is always ``"unavailable"`` so API layers can distinguish an
    unavailable model from an inference failure.
    """

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

=======
<<<<<<< HEAD
from typing import Dict, Any, List
>>>>>>> origin/main

class AerialSegmentationModel(nn.Module):
    """Aerial semantic segmentation network (7 land-cover classes).

    This is an architecture definition only. Instantiating it produces random
    weights; therefore instances are never created outside :func:`load_verified_model`,
    which always overwrites every parameter from a verified checkpoint.
    """
<<<<<<< HEAD

=======
    High-Resolution Aerial Semantic Segmentation Network.
    Maps aerial multispectral features into discrete spatial land-use classes.
    """
=======

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

ARCHITECTURE = "AerialSegmentationModel"
STATE_DICT_KEYS = ("model_state", "state_dict", "model_state_dict", "weights")

DEFAULT_SEGMENTATION_CHECKPOINT = os.environ.get(
    "JATAYUV_SEGMENTATION_CHECKPOINT",
    os.path.join(_REPO_ROOT, "storage", "models", "checkpoints", "segmentation_loveda.pth"),
)


class SegmentationModelUnavailable(RuntimeError):
    """Raised when no verified segmentation checkpoint can be loaded.

    ``status`` is always ``"unavailable"`` so API layers can distinguish an
    unavailable model from an inference failure.
    """

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


class AerialSegmentationModel(nn.Module):
    """Aerial semantic segmentation network (7 land-cover classes).

    This is an architecture definition only. Instantiating it produces random
    weights; therefore instances are never created outside :func:`load_verified_model`,
    which always overwrites every parameter from a verified checkpoint.
    """

>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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

<<<<<<< HEAD

def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_state_dict(payload: Any) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Return ``(state_dict, metadata)`` from a checkpoint payload."""
    if isinstance(payload, dict):
        for key in STATE_DICT_KEYS:
            candidate = payload.get(key)
            if isinstance(candidate, dict) and candidate:
                return candidate, payload
        tensors_only = {
            k: v
            for k, v in payload.items()
            if isinstance(v, torch.Tensor) or hasattr(v, "detach")
        }
        if tensors_only and len(tensors_only) == len(payload):
            return tensors_only, {}
    raise SegmentationModelUnavailable(
        "Checkpoint does not contain a recognisable model state dict.",
        checkpoint_path=None,
        reason="checkpoint_unreadable",
    )


def load_verified_model(
    checkpoint_path: str,
    *,
    num_classes: int,
    device: torch.device,
) -> tuple[AerialSegmentationModel, Dict[str, Any]]:
    """Build the architecture and fill every weight from a verified checkpoint.

    Raises :class:`SegmentationModelUnavailable` on any problem; never returns a
    partially initialised (random) model.
    """
    if not checkpoint_path or not os.path.isfile(checkpoint_path):
        raise SegmentationModelUnavailable(
            "No verified segmentation checkpoint found at "
            f"{checkpoint_path!r}. Train or install a checkpoint and point "
            "JATAYUV_SEGMENTATION_CHECKPOINT at it; random weights are never used.",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_missing",
        )

    try:
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    except Exception as exc:  # corrupt file / unsupported format
        raise SegmentationModelUnavailable(
            f"Segmentation checkpoint at {checkpoint_path!r} could not be read: {exc}",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_unreadable",
        ) from exc

    metadata: Dict[str, Any] = payload if isinstance(payload, dict) else {}
    architecture = metadata.get("architecture")
    if architecture is not None and architecture != ARCHITECTURE:
        raise SegmentationModelUnavailable(
            "Segmentation checkpoint architecture "
            f"{architecture!r} does not match {ARCHITECTURE!r}.",
            checkpoint_path=checkpoint_path,
            reason="architecture_mismatch",
        )
    declared_classes = metadata.get("num_classes")
    if declared_classes is not None and int(declared_classes) != num_classes:
        raise SegmentationModelUnavailable(
            f"Segmentation checkpoint declares {declared_classes} classes but the "
            f"service expects {num_classes}.",
            checkpoint_path=checkpoint_path,
            reason="class_count_mismatch",
        )

    try:
        state_dict, _ = _extract_state_dict(payload)
    except SegmentationModelUnavailable as exc:
        exc.checkpoint_path = checkpoint_path
        raise

    model = AerialSegmentationModel(num_classes=num_classes)
    try:
        model.load_state_dict(state_dict, strict=True)
    except Exception as exc:
        raise SegmentationModelUnavailable(
            "Segmentation checkpoint is incompatible with "
            f"{ARCHITECTURE}: {exc}",
            checkpoint_path=checkpoint_path,
            reason="state_dict_incompatible",
        ) from exc

    model.to(device).eval()
    info = {
        "architecture": ARCHITECTURE,
        "num_classes": num_classes,
        "checkpoint_path": checkpoint_path,
        "checkpoint_sha256": file_sha256(checkpoint_path),
        "dataset": metadata.get("dataset"),
        "training_run": metadata.get("training_run"),
        "created_at": metadata.get("created_at"),
        # Whatever the checkpoint records; never invented here.
        "reported_metrics": metadata.get("metrics"),
    }
    return model, info


@dataclass
class _LoadedSegmentation:
    model: AerialSegmentationModel
    device: torch.device
    info: Dict[str, Any]


class SemanticSegmentationService:
    CLASSES: List[Dict[str, Any]] = [
=======
<<<<<<< HEAD
class SemanticSegmentationService:
    CLASSES = [
=======

def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_state_dict(payload: Any) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Return ``(state_dict, metadata)`` from a checkpoint payload."""
    if isinstance(payload, dict):
        for key in STATE_DICT_KEYS:
            candidate = payload.get(key)
            if isinstance(candidate, dict) and candidate:
                return candidate, payload
        tensors_only = {
            k: v
            for k, v in payload.items()
            if isinstance(v, torch.Tensor) or hasattr(v, "detach")
        }
        if tensors_only and len(tensors_only) == len(payload):
            return tensors_only, {}
    raise SegmentationModelUnavailable(
        "Checkpoint does not contain a recognisable model state dict.",
        checkpoint_path=None,
        reason="checkpoint_unreadable",
    )


def load_verified_model(
    checkpoint_path: str,
    *,
    num_classes: int,
    device: torch.device,
) -> tuple[AerialSegmentationModel, Dict[str, Any]]:
    """Build the architecture and fill every weight from a verified checkpoint.

    Raises :class:`SegmentationModelUnavailable` on any problem; never returns a
    partially initialised (random) model.
    """
    if not checkpoint_path or not os.path.isfile(checkpoint_path):
        raise SegmentationModelUnavailable(
            "No verified segmentation checkpoint found at "
            f"{checkpoint_path!r}. Train or install a checkpoint and point "
            "JATAYUV_SEGMENTATION_CHECKPOINT at it; random weights are never used.",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_missing",
        )

    try:
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    except Exception as exc:  # corrupt file / unsupported format
        raise SegmentationModelUnavailable(
            f"Segmentation checkpoint at {checkpoint_path!r} could not be read: {exc}",
            checkpoint_path=checkpoint_path,
            reason="checkpoint_unreadable",
        ) from exc

    metadata: Dict[str, Any] = payload if isinstance(payload, dict) else {}
    architecture = metadata.get("architecture")
    if architecture is not None and architecture != ARCHITECTURE:
        raise SegmentationModelUnavailable(
            "Segmentation checkpoint architecture "
            f"{architecture!r} does not match {ARCHITECTURE!r}.",
            checkpoint_path=checkpoint_path,
            reason="architecture_mismatch",
        )
    declared_classes = metadata.get("num_classes")
    if declared_classes is not None and int(declared_classes) != num_classes:
        raise SegmentationModelUnavailable(
            f"Segmentation checkpoint declares {declared_classes} classes but the "
            f"service expects {num_classes}.",
            checkpoint_path=checkpoint_path,
            reason="class_count_mismatch",
        )

    try:
        state_dict, _ = _extract_state_dict(payload)
    except SegmentationModelUnavailable as exc:
        exc.checkpoint_path = checkpoint_path
        raise

    model = AerialSegmentationModel(num_classes=num_classes)
    try:
        model.load_state_dict(state_dict, strict=True)
    except Exception as exc:
        raise SegmentationModelUnavailable(
            "Segmentation checkpoint is incompatible with "
            f"{ARCHITECTURE}: {exc}",
            checkpoint_path=checkpoint_path,
            reason="state_dict_incompatible",
        ) from exc

    model.to(device).eval()
    info = {
        "architecture": ARCHITECTURE,
        "num_classes": num_classes,
        "checkpoint_path": checkpoint_path,
        "checkpoint_sha256": file_sha256(checkpoint_path),
        "dataset": metadata.get("dataset"),
        "training_run": metadata.get("training_run"),
        "created_at": metadata.get("created_at"),
        # Whatever the checkpoint records; never invented here.
        "reported_metrics": metadata.get("metrics"),
    }
    return model, info


@dataclass
class _LoadedSegmentation:
    model: AerialSegmentationModel
    device: torch.device
    info: Dict[str, Any]


class SemanticSegmentationService:
    CLASSES: List[Dict[str, Any]] = [
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        {"id": 0, "name": "background", "label": "Other / Unclassified", "color": [0, 0, 0]},
        {"id": 1, "name": "building", "label": "Buildings & Roofs", "color": [246, 92, 139]},   # BGR for #8b5cf6
        {"id": 2, "name": "vegetation", "label": "Canopy & Trees", "color": [129, 185, 16]},   # BGR for #10b981
        {"id": 3, "name": "road", "label": "Roads & Asphalt", "color": [139, 116, 100]},       # BGR for #64748b
        {"id": 4, "name": "water", "label": "Water Surfaces", "color": [246, 130, 59]},        # BGR for #3b82f6
        {"id": 5, "name": "soil", "label": "Bare Ground / Sand", "color": [11, 158, 245]},     # BGR for #f59e0b
        {"id": 6, "name": "vehicle", "label": "Vehicles & Assets", "color": [68, 68, 239]},    # BGR for #ef4444
    ]

<<<<<<< HEAD
    def __init__(self, checkpoint_path: Optional[str] = None):
        # Nothing is loaded and no network is constructed here: a service object
        # alone must never imply that usable weights exist.
        self._checkpoint_path = checkpoint_path or DEFAULT_SEGMENTATION_CHECKPOINT
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded: Optional[_LoadedSegmentation] = None
        self._lock = threading.Lock()

=======
<<<<<<< HEAD
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AerialSegmentationModel(num_classes=len(self.CLASSES)).to(self.device)
        self.model.eval()

=======
    def __init__(self, checkpoint_path: Optional[str] = None):
        # Nothing is loaded and no network is constructed here: a service object
        # alone must never imply that usable weights exist.
        self._checkpoint_path = checkpoint_path or DEFAULT_SEGMENTATION_CHECKPOINT
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded: Optional[_LoadedSegmentation] = None
        self._lock = threading.Lock()

>>>>>>> origin/main
    # ------------------------------------------------------------- availability
    @property
    def checkpoint_path(self) -> str:
        return self._checkpoint_path

    def checkpoint_info(self) -> Dict[str, Any]:
        """Describe the configured checkpoint without loading it."""
        path = self._checkpoint_path
        exists = bool(path) and os.path.isfile(path)
        info: Dict[str, Any] = {
            "architecture": ARCHITECTURE,
            "num_classes": len(self.CLASSES),
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

    def get_model(self) -> _LoadedSegmentation:
        """Load (once) the verified checkpoint or raise ``SegmentationModelUnavailable``."""
        with self._lock:
            if self._loaded is not None:
                return self._loaded
            model, info = load_verified_model(
                self._checkpoint_path,
                num_classes=len(self.CLASSES),
                device=self._device,
            )
            self._loaded = _LoadedSegmentation(model=model, device=self._device, info=info)
            return self._loaded

    # --------------------------------------------------------------- inference
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    def segment_aerial_image(
        self,
        input_image_path: str,
        output_mask_path: str,
        output_overlay_path: str,
        output_geojson_path: str = None,
    ) -> Dict[str, Any]:
<<<<<<< HEAD
=======
<<<<<<< HEAD
        """
        Segments land-use and land-cover classes from high-resolution aerial imagery.
        """
=======
>>>>>>> origin/main
        """Segment land-cover classes using a verified checkpoint only."""
        # Fail before touching the image or writing any artifact when weights are
        # unavailable, so callers never receive partial results.
        loaded = self.get_model()

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        img = cv2.imread(input_image_path)
        if img is None:
            raise ValueError(f"Could not load image at {input_image_path}")

        orig_h, orig_w = img.shape[:2]
        target_w, target_h = 512, 512
        resized = cv2.resize(img, (target_w, target_h))

        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
<<<<<<< HEAD
        tensor = (
            torch.from_numpy(rgb.astype(np.float32) / 255.0)
            .permute(2, 0, 1)
            .unsqueeze(0)
            .to(loaded.device)
        )

        with torch.no_grad():
            logits = loaded.model(tensor)
=======
<<<<<<< HEAD
        tensor = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
=======
        tensor = (
            torch.from_numpy(rgb.astype(np.float32) / 255.0)
            .permute(2, 0, 1)
            .unsqueeze(0)
            .to(loaded.device)
        )

        with torch.no_grad():
            logits = loaded.model(tensor)
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
        os.makedirs(os.path.dirname(os.path.abspath(output_mask_path)), exist_ok=True)
        cv2.imwrite(output_mask_path, dense_mask)

        os.makedirs(os.path.dirname(os.path.abspath(output_overlay_path)), exist_ok=True)
=======
<<<<<<< HEAD
        os.makedirs(os.path.dirname(output_mask_path), exist_ok=True)
        cv2.imwrite(output_mask_path, dense_mask)

        os.makedirs(os.path.dirname(output_overlay_path), exist_ok=True)
=======
        os.makedirs(os.path.dirname(os.path.abspath(output_mask_path)), exist_ok=True)
        cv2.imwrite(output_mask_path, dense_mask)

        os.makedirs(os.path.dirname(os.path.abspath(output_overlay_path)), exist_ok=True)
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        cv2.imwrite(output_overlay_path, overlay)

        # Optional GeoJSON polygon export of building footprints
        if output_geojson_path:
            self._export_building_geojson(dense_mask, output_geojson_path)

        return {
<<<<<<< HEAD
            "status": "completed",
=======
<<<<<<< HEAD
=======
            "status": "completed",
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
            "mask_path": output_mask_path,
            "overlay_path": output_overlay_path,
            "class_distribution": class_distribution,
            "geojson_path": output_geojson_path,
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main
            "checkpoint_path": loaded.info["checkpoint_path"],
            "checkpoint_sha256": loaded.info["checkpoint_sha256"],
            "architecture": loaded.info["architecture"],
            "dataset": loaded.info["dataset"],
            "reported_metrics": loaded.info["reported_metrics"],
            "metrics_note": (
                "No segmentation accuracy metric is computed or claimed at inference time."
            ),
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
        os.makedirs(os.path.dirname(os.path.abspath(geojson_path)), exist_ok=True)
=======
<<<<<<< HEAD
        os.makedirs(os.path.dirname(geojson_path), exist_ok=True)
>>>>>>> origin/main
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)


<<<<<<< HEAD
segmentation_service = SemanticSegmentationService()
=======
=======
        os.makedirs(os.path.dirname(os.path.abspath(geojson_path)), exist_ok=True)
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2)


segmentation_service = SemanticSegmentationService()
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
