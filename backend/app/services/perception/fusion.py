from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import numpy.typing as npt

from backend.app.models.frame import Frame
from backend.app.services.storage import StorageService
from backend.app.services.perception.depth import (
    DepthInferenceResult,
    infer_depth,
)
from backend.app.services.perception.dynamic import (
    DynamicDetectionResult,
    build_dynamic_exclusion_mask,
    describe_dynamic_model as _describe_dynamic_model,
    infer_dynamic_objects,
)
from backend.app.services.perception.segmentation import (
    SegmentationInferenceResult,
    describe_segmentation_model as _describe_segmentation_model,
    infer_segmentation,
)

try:
    from backend.app.services.perception.models import (
        FramePerception,
        FrameDepthResult,
        FrameSegmentationResult,
        FrameDynamicObjectResult,
    )
except ImportError:
    FramePerception = None  # type: ignore[assignment]
    FrameDepthResult = None  # type: ignore[assignment]
    FrameSegmentationResult = None  # type: ignore[assignment]
    FrameDynamicObjectResult = None  # type: ignore[assignment]

log = logging.getLogger("jatayuv.perception.fusion")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_perception_artifact_dir(
    mission_id: str, subdir: str
) -> str:
    base = os.path.abspath("storage/missions/{mission_id}/perception/{subdir}")
    return base.format(mission_id=mission_id, subdir=subdir)


def store_artifact(
    *,
    mission_id: str,
    artifact_type: str,
    frame_id: Optional[str],
    source_path: str,
    mime_type: Optional[str] = None,
    description: Optional[str] = None,
    model_id: Optional[str] = None,
    model_version: Optional[str] = None,
    checkpoint_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    storage = StorageService()
    rel = build_perception_artifact_dir(mission_id, artifact_type)
    os.makedirs(rel, exist_ok=True)

    base = os.path.basename(source_path)
    stem, ext = os.path.splitext(base)
    unique_id = str(uuid.uuid4())[:8]
    out_name = f"{stem}__{unique_id}{ext}"
    out_path = os.path.join(rel, out_name)

    # Atomic-ish write: write to temp then move into place.
    tmp = out_path + ".tmp"
    try:
        _copy_or_move(source_path, tmp, copy=False)
        computed_sha = sha256_file(tmp)
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        _copy_or_move(source_path, out_path, copy=False) if False else None

    # If source was a temp path we no longer need, leave it; otherwise copy.
    file_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0

    storage.register_artifact(
        kind=artifact_type,
        source_path=out_path,
        relative_path=os.path.relpath(out_path, os.path.abspath("storage")),
    )

    return {
        "storage_path": out_path,
        "relative_path": os.path.relpath(out_path, os.path.abspath("storage")),
        "artifact_type": artifact_type,
        "frame_id": frame_id,
        "file_size_bytes": file_size,
        "checksum_sha256": computed_sha,
        "mime_type": mime_type,
        "description": description,
        "model_id": model_id,
        "model_version": model_version,
        "checkpoint_sha256": checkpoint_sha256,
        "source_path": source_path,
    }


def _copy_or_move(src: str, dst: str, copy: bool) -> None:
    import shutil

    if os.path.exists(src):
        if copy:
            shutil.copy2(src, dst)
        else:
            shutil.move(src, dst)


def build_perception_record_from_frame(
    *,
    mission_id: str,
    frame_id: str,
    frame: Frame,
    frame_index: int,
    perception_run_id: str,
    depth_result: Optional[DepthInferenceResult],
    segmentation_result: Optional[SegmentationInferenceResult],
    dynamic_result: Optional[DynamicDetectionResult],
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    # --- depth artifacts ---
    depth_artifact: Optional[Dict[str, Any]] = None
    depth_result_record: Optional[Dict[str, Any]] = None
    if depth_result is not None:
        depth_artifact = store_artifact(
            mission_id=mission_id,
            artifact_type="depth",
            frame_id=frame_id,
            source_path=depth_result.depth_map_path,
            mime_type="image/png",
            description="Depth map (relative inverse depth)",
            model_id=depth_result.model_id,
            model_version=depth_result.model_version,
            checkpoint_sha256=depth_result.checkpoint_sha256,
        )
        depth_raw_artifact: Optional[Dict[str, Any]] = None
        if depth_result.raw_depth_path:
            depth_raw_artifact = store_artifact(
                mission_id=mission_id,
                artifact_type="depth_raw_npy",
                frame_id=frame_id,
                source_path=depth_result.raw_depth_path,
                mime_type="application/x-numpy",
                description="Raw relative depth NPY",
                model_id=depth_result.model_id,
                model_version=depth_result.model_version,
                checkpoint_sha256=depth_result.checkpoint_sha256,
            )
        depth_viz_artifact = store_artifact(
            mission_id=mission_id,
            artifact_type="depth_visualizations",
            frame_id=frame_id,
            source_path=depth_result.depth_visualization_path,
            mime_type="image/png",
            description="Depth visualization (colormap)",
            model_id=depth_result.model_id,
            model_version=depth_result.model_version,
            checkpoint_sha256=depth_result.checkpoint_sha256,
        )

        depth_result_record = {
            "depth_map_path": depth_artifact["storage_path"],
            "depth_visualization_path": depth_viz_artifact["storage_path"],
            "raw_depth_path": depth_raw_artifact["storage_path"] if depth_raw_artifact else None,
            "model_id": depth_result.model_id,
            "model_version": depth_result.model_version,
            "checkpoint_sha256": depth_result.checkpoint_sha256,
            "input_width": depth_result.input_width,
            "input_height": depth_result.input_height,
            "output_width": depth_result.output_width,
            "output_height": depth_result.output_height,
            "inference_device": depth_result.inference_device,
            "inference_duration_ms": depth_result.inference_duration_ms,
            "preprocessing_json": depth_result.preprocessing_json,
            "depth_type": depth_result.depth_type,
            "depth_unit": depth_result.depth_unit,
            "is_metric": depth_result.is_metric,
            "depth_min": depth_result.depth_min,
            "depth_max": depth_result.depth_max,
            "depth_mean": depth_result.depth_mean,
            "relative_min": depth_result.relative_min,
            "relative_max": depth_result.relative_max,
            "relative_mean": depth_result.relative_mean,
            "confidence_json": depth_result.confidence_json,
        }

    # --- segmentation artifacts ---
    segmentation_artifact: Optional[Dict[str, Any]] = None
    segmentation_result_record: Optional[Dict[str, Any]] = None
    if segmentation_result is not None:
        seg_artifact = store_artifact(
            mission_id=mission_id,
            artifact_type="segmentation",
            frame_id=frame_id,
            source_path=segmentation_result.mask_path,
            mime_type="image/png",
            description="Segmentation class-ID mask",
            model_id=segmentation_result.model_id,
            model_version=segmentation_result.model_version,
            checkpoint_sha256=segmentation_result.checkpoint_sha256,
        )
        seg_viz_artifact = store_artifact(
            mission_id=mission_id,
            artifact_type="segmentation_visualizations",
            frame_id=frame_id,
            source_path=segmentation_result.visualization_path,
            mime_type="image/png",
            description="Segmentation visualization overlay",
            model_id=segmentation_result.model_id,
            model_version=segmentation_result.model_version,
            checkpoint_sha256=segmentation_result.checkpoint_sha256,
        )

        segmentation_result_record = {
            "mask_path": seg_artifact["storage_path"],
            "visualization_path": seg_viz_artifact["storage_path"],
            "model_id": segmentation_result.model_id,
            "model_version": segmentation_result.model_version,
            "checkpoint_sha256": segmentation_result.checkpoint_sha256,
            "input_width": segmentation_result.input_width,
            "input_height": segmentation_result.input_height,
            "output_width": segmentation_result.output_width,
            "output_height": segmentation_result.output_height,
            "inference_device": segmentation_result.inference_device,
            "inference_duration_ms": segmentation_result.inference_duration_ms,
            "preprocessing_json": segmentation_result.preprocessing_json,
            "class_distribution_json": segmentation_result.class_distribution,
            "per_class_pixel_counts_json": segmentation_result.per_class_pixel_counts,
            "unsupported_class_handling_json": segmentation_result.unsupported_class_handling,
        }

    # --- dynamic artifacts ---
    dynamic_artifact: Optional[Dict[str, Any]] = None
    dynamic_exclusion_mask: Optional[np.ndarray] = None
    dynamic_result_record: Optional[Dict[str, Any]] = None
    if dynamic_result is not None and dynamic_result.detections:
        dynamic_exclusion_mask = build_dynamic_exclusion_mask(
            frame_bgr=frame.frame_bgr(), detections=dynamic_result.detections
        )
        dynamic_mask_path = None
        if dynamic_exclusion_mask is not None:
            tmp = os.path.abspath("__.tmp_dynamic_mask.png")
            try:
                cv2.imwrite(tmp, dynamic_exclusion_mask)
                dynamic_mask_path = tmp
            finally:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
        if dynamic_mask_path:
            dyn_mask_artifact = store_artifact(
                mission_id=mission_id,
                artifact_type="dynamic_masks",
                frame_id=frame_id,
                source_path=dynamic_mask_path,
                mime_type="image/png",
                description="Dynamic object exclusion mask",
                model_id=dynamic_result.model_id,
                model_version=dynamic_result.model_version,
                checkpoint_sha256=dynamic_result.checkpoint_sha256,
            )
            dynamic_artifact = dyn_mask_artifact
            dynamic_mask_path = None

    # gather GPS info if available
    gps_latitude = frame.gps_latitude
    gps_longitude = frame.gps_longitude
    altitude = frame.altitude
    altitude_datum = frame.altitude_datum
    gps_source = frame.gps_source
    gps_association_gap_seconds = frame.gps_association_gap_seconds

    return {
        "frame_id": frame_id,
        "mission_id": mission_id,
        "video_id": frame.video_id,
        "frame_index": frame_index,
        "presentation_timestamp": frame.presentation_timestamp,
        "timestamp_seconds": frame.timestamp_seconds,
        "gps_latitude": gps_latitude,
        "gps_longitude": gps_longitude,
        "altitude": altitude,
        "altitude_datum": altitude_datum,
        "gps_source": gps_source,
        "gps_association_gap_seconds": gps_association_gap_seconds,
        "status": "COMPLETED",
        "processing_duration_seconds": 0.0,
        "error_message": None,
        "warnings": {},
        "depth": depth_result_record,
        "segmentation": segmentation_result_record,
        "dynamic": dynamic_result_record,
        "perception_run_id": perception_run_id,
        "created_at": now,
        "depth_artifact": depth_artifact,
        "segmentation_artifact": segmentation_artifact,
        "dynamic_artifact": dynamic_artifact,
        "dynamic_exclusion_mask": dynamic_exclusion_mask,
    }


def persist_perception_record_to_db(
    db: Any,
    *,
    mission_id: str,
    perception_run_id: str,
    record: Dict[str, Any],
) -> Optional[str]:
    """Persist a single frame perception record into DB + artifact rows.

    Returns the created FramePerception.id.
    """
    if FramePerception is None:
        raise RuntimeError("Perception models not importable in this process")

    session = db() if callable(db) else db
    try:
        fp = FramePerception(
            perception_run_id=perception_run_id,
            frame_id=record["frame_id"],
            status=record["status"],
            processing_duration_seconds=record["processing_duration_seconds"],
            error_message=record["error_message"],
            warnings_json=record["warnings"],
        )
        session.add(fp)
        session.flush()

        if record["depth"] is not None:
            d = FrameDepthResult(
                frame_perception_id=fp.id,
                **record["depth"],
            )
            session.add(d)

        if record["segmentation"] is not None:
            s = FrameSegmentationResult(
                frame_perception_id=fp.id,
                **record["segmentation"],
            )
            session.add(s)

        if record["dynamic"] is not None:
            dyn = FrameDynamicObjectResult(
                frame_perception_id=fp.id,
                **record["dynamic"],
            )
            session.add(dyn)

        session.flush()

        # persistence of artifacts at the storage level
        storage = StorageService()
        for art in _iter_artifacts(record):
            storage.register_artifact(
                kind=art["artifact_type"],
                source_path=art["storage_path"],
                relative_path=art["relative_path"],
            )

        session.commit()
        return fp.id
    except Exception:
        session.rollback()
        raise


def _iter_artifacts(record: Dict[str, Any]):
    for key in ("depth_artifact", "segmentation_artifact", "dynamic_artifact"):
        val = record.get(key)
        if isinstance(val, dict):
            yield val
