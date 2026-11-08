from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from backend.app.workers.celery_app import celery_app
from backend.app.services.perception.depth import (
    infer_depth,
    is_depth_available,
)
from backend.app.services.perception.segmentation import (
    infer_segmentation,
    is_segmentation_available,
)
from backend.app.services.perception.dynamic import (
    infer_dynamic_objects,
    is_dynamic_detection_available,
    build_dynamic_exclusion_mask,
)
from backend.app.services.mission_processing.perception_extension import (
    MissionPerceptionService,
)
from backend.app.services.storage import StorageService

log = logging.getLogger("jatayuv.celery_perception")

_DUMMY_ROW = object()

_MISSION_ID_UNKNOWN = "__unknown__"


def _mission_perception_service():
    return MissionPerceptionService()


def _storage_service():
    return StorageService()


def sha256_file(path: str) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


def _list_selected_frame_image_paths(mission_id: str):
    svc = MissionPerceptionService()
    frames = svc._core.get_selected_frames_for_mission(mission_id)
    image_paths = []
    for f in frames:
        path = getattr(f, "image_path", None)
        if path and os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS:
            image_paths.append(path)
    return image_paths


@celery_app.task(bind=True, name="jatayuv.perception.depth_inference")
def depth_inference_task(
    self: Any,
    mission_id: str,
    frame_image_path: str,
    run_id: str,
    frame_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run depth inference for a single frame."""
    if not is_depth_available():
        raise RuntimeError("Depth model unavailable")

    start = time.perf_counter()
    try:
        result = infer_depth(
            frame_image_path,
            model_id=kwargs.get("model_id"),
            input_size=kwargs.get("depth_input_size"),
        )
    except Exception:
        log.exception("depth inference failed for frame %s", frame_id)
        svc = _mission_perception_service()
        svc.increment_processed(run_id, success=False)
        svc.finish_run(
            run_id,
            success=False,
            error_message="Depth inference failed for frame %s" % frame_id,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000.0

    svc = _mission_perception_service()
    svc.increment_processed(run_id)

    return {
        "frame_id": frame_id,
        "mission_id": mission_id,
        "run_id": run_id,
        "depth_result": {
            "depth_map_path": result.depth_map_path,
            "depth_visualization_path": result.depth_visualization_path,
            "raw_depth_path": result.raw_depth_path,
            "model_id": result.model_id,
            "model_version": result.model_version,
            "checkpoint_sha256": result.checkpoint_sha256,
            "depth_type": result.depth_type,
            "depth_unit": result.depth_unit,
            "is_metric": result.is_metric,
            "input_width": result.input_width,
            "input_height": result.input_height,
            "output_width": result.output_width,
            "output_height": result.output_height,
            "inference_device": result.inference_device,
            "inference_duration_ms": duration_ms,
            "preprocessing_json": result.preprocessing_json,
            "depth_min": float(result.depth_min) if result.depth_min is not None else None,
            "depth_max": float(result.depth_max) if result.depth_max is not None else None,
            "depth_mean": float(result.depth_mean) if result.depth_mean is not None else None,
            "relative_min": float(result.relative_min),
            "relative_max": float(result.relative_max),
            "relative_mean": float(result.relative_mean),
            "confidence_json": result.confidence_json,
        },
    }


@celery_app.task(bind=True, name="jatayuv.perception.segmentation_inference")
def segmentation_inference_task(
    self: Any,
    mission_id: str,
    frame_image_path: str,
    run_id: str,
    frame_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    if not is_segmentation_available():
        raise RuntimeError("Segmentation model unavailable")

    start = time.perf_counter()
    try:
        result = infer_segmentation(
            frame_image_path,
            model_id=kwargs.get("model_id"),
        )
    except Exception:
        log.exception("segmentation inference failed for frame %s", frame_id)
        svc = _mission_perception_service()
        svc.increment_processed(run_id, success=False)
        raise

    duration_ms = (time.perf_counter() - start) * 1000.0
    svc = _mission_perception_service()
    svc.increment_processed(run_id)

    return {
        "frame_id": frame_id,
        "mission_id": mission_id,
        "run_id": run_id,
        "segmentation_result": {
            "mask_path": result.mask_path,
            "visualization_path": result.visualization_path,
            "model_id": result.model_id,
            "model_version": result.model_version,
            "checkpoint_sha256": result.checkpoint_sha256,
            "input_width": result.input_width,
            "input_height": result.input_height,
            "output_width": result.output_width,
            "output_height": result.output_height,
            "inference_device": result.inference_device,
            "inference_duration_ms": duration_ms,
            "preprocessing_json": result.preprocessing_json,
            "class_distribution": result.class_distribution,
            "per_class_pixel_counts": result.per_class_pixel_counts,
            "unsupported_class_handling": result.unsupported_class_handling,
        },
    }


@celery_app.task(bind=True, name="jatayuv.perception.dynamic_detection")
def dynamic_detection_task(
    self: Any,
    mission_id: str,
    frame_image_path: str,
    run_id: str,
    frame_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    available = is_dynamic_detection_available()
    frame = None
    try:
        import cv2

        frame = cv2.imread(frame_image_path)
        if frame is None:
            raise ValueError("Could not load frame %s" % frame_image_path)

        result = infer_dynamic_objects(
            frame,
            model_id=kwargs.get("model_id"),
        )
    except Exception:
        log.exception("dynamic detection failed for frame %s", frame_id)
        svc = _mission_perception_service()
        svc.increment_processed(run_id, success=False)
        raise

    svc = _mission_perception_service()
    svc.increment_processed(run_id)

    detections = [
        {
            "category": d.get("category"),
            "label": d.get("label"),
            "score": d.get("score"),
            "box": d.get("box"),
            "mask_path": d.get("mask_path"),
            "dynamic_label": d.get("dynamic_label", "POTENTIALLY_DYNAMIC"),
        }
        for d in result.detections
    ]

    return {
        "frame_id": frame_id,
        "mission_id": mission_id,
        "run_id": run_id,
        "dynamic_result": {
            "dynamic_mask_path": None,
            "detections": detections,
            "model_id": result.model_id,
            "model_version": result.model_version,
            "checkpoint_sha256": result.checkpoint_sha256,
            "inference_device": result.inference_device,
            "inference_duration_ms": result.inference_duration_ms,
            "preprocessing_json": result.preprocessing_json,
            "dynamic_label_policy": result.dynamic_label_policy,
        },
    }


@celery_app.task(bind=True, name="jatayuv.perception.per_frame_fuse")
def per_frame_perception_fuse_task(
    self: Any,
    mission_id: str,
    run_id: str,
    frame_id: str,
    frame_image_path: str,
    depth_result: Optional[Dict[str, Any]] = None,
    segmentation_result: Optional[Dict[str, Any]] = None,
    dynamic_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist perception artifacts and DB records for one frame."""
    from backend.app.services.perception.fusion import (
        store_artifact,
        persist_perception_record_to_db,
    )

    svc = _mission_perception_service()
    storage = _storage_service()

    depth_art = None
    if depth_result:
        depth_art = store_artifact(
            mission_id=mission_id,
            artifact_type="depth",
            frame_id=frame_id,
            source_path=depth_result["depth_map_path"],
            model_id=depth_result.get("model_id"),
            model_version=depth_result.get("model_version"),
            checkpoint_sha256=depth_result.get("checkpoint_sha256"),
            description="Depth map (relative inverse depth)",
        )
        if depth_result.get("raw_depth_path"):
            store_artifact(
                mission_id=mission_id,
                artifact_type="depth_raw_npy",
                frame_id=frame_id,
                source_path=depth_result["raw_depth_path"],
                model_id=depth_result.get("model_id"),
                model_version=depth_result.get("model_version"),
                checkpoint_sha256=depth_result.get("checkpoint_sha256"),
                description="Raw relative depth NPY",
            )
        store_artifact(
            mission_id=mission_id,
            artifact_type="depth_visualizations",
            frame_id=frame_id,
            source_path=depth_result["depth_visualization_path"],
            model_id=depth_result.get("model_id"),
            model_version=depth_result.get("model_version"),
            checkpoint_sha256=depth_result.get("checkpoint_sha256"),
            description="Depth visualization (colormap)",
        )

    segmentation_art = None
    if segmentation_result:
        segmentation_art = store_artifact(
            mission_id=mission_id,
            artifact_type="segmentation",
            frame_id=frame_id,
            source_path=segmentation_result["mask_path"],
            model_id=segmentation_result.get("model_id"),
            model_version=segmentation_result.get("model_version"),
            checkpoint_sha256=segmentation_result.get("checkpoint_sha256"),
            description="Segmentation class-ID mask",
        )
        store_artifact(
            mission_id=mission_id,
            artifact_type="segmentation_visualizations",
            frame_id=frame_id,
            source_path=segmentation_result["visualization_path"],
            model_id=segmentation_result.get("model_id"),
            model_version=segmentation_result.get("model_version"),
            checkpoint_sha256=segmentation_result.get("checkpoint_sha256"),
            description="Segmentation visualization overlay",
        )

    dynamic_art = None
    dynamic_mask_storage_path = None
    if dynamic_result and dynamic_result.get("detections"):
        import cv2
        import numpy as np
        import numpy.typing as npt

        frame_img = cv2.imread(frame_image_path)
        if frame_img is not None:
            mask = build_dynamic_exclusion_mask(frame_img, dynamic_result["detections"])
            tmp = os.path.abspath("__.tmp_dynamic_mask.png")
            try:
                cv2.imwrite(tmp, mask)
                dynamic_mask_storage_path = tmp
            finally:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
        if dynamic_mask_storage_path:
            dynamic_art = store_artifact(
                mission_id=mission_id,
                artifact_type="dynamic_masks",
                frame_id=frame_id,
                source_path=dynamic_mask_storage_path,
                model_id=dynamic_result.get("model_id"),
                model_version=dynamic_result.get("model_version"),
                checkpoint_sha256=dynamic_result.get("checkpoint_sha256"),
                description="Dynamic object exclusion mask",
            )

    record = {
        "frame_id": frame_id,
        "mission_id": mission_id,
        "status": "COMPLETED",
        "processing_duration_seconds": 0.0,
        "error_message": None,
        "warnings": {},
        "depth": depth_result,
        "segmentation": segmentation_result,
        "dynamic": dynamic_result,
        "perception_run_id": run_id,
        "created_at": None,
        "depth_artifact": depth_art,
        "segmentation_artifact": segmentation_art,
        "dynamic_artifact": dynamic_art,
    }

    try:
        persist_perception_record_to_db(svc._core.db_session, mission_id=mission_id, perception_run_id=run_id, record=record)
    except Exception:
        log.exception("persist failed for frame %s", frame_id)
        raise

    return {"frame_id": frame_id, "run_id": run_id, "persisted": True}


@celery_app.task(bind=True, name="jatayuv.perception.mission_report")
def mission_perception_report_task(
    self: Any,
    mission_id: str,
) -> Dict[str, Any]:
    svc = MissionPerceptionService()
    return svc.build_perception_report(mission_id)


def launch_mission_perception_tasks(run_id: str):
    """
    Enqueue the full perception pipeline for a mission run.

    In the live environment this is called by the API's process endpoint.
    """
    svc = MissionPerceptionService()
    mission_id = svc._core.get_run_mission_id(run_id)
    if not mission_id:
        raise RuntimeError("Unknown perception run: %s" % run_id)

    image_paths = _list_selected_frame_image_paths(mission_id)
    from backend.app.models.frame import Frame

    frames = Frame.query(mission_id=mission_id, selected=True, order_by="created_at")
    frame_by_path = {getattr(f, "image_path", ""): f for f in frames}

    for idx, path in enumerate(image_paths):
        frame_id = None
        for f in frames:
            if getattr(f, "image_path", "") == path:
                frame_id = f.id
                break
        if not frame_id:
            continue

        if not is_depth_available():
            log.warning("depth unavailable for frame %s", frame_id)
            continue
        if not is_segmentation_available():
            log.warning("segmentation unavailable for frame %s", frame_id)
            continue

        depth_res = depth_inference_task.delay(
            mission_id,
            path,
            run_id,
            frame_id,
        )
        segmentation_res = segmentation_inference_task.delay(
            mission_id,
            path,
            run_id,
            frame_id,
        )
        dynamic_res = dynamic_detection_task.delay(
            mission_id,
            path,
            run_id,
            frame_id,
        )

        per_frame_perception_fuse_task.delay(
            mission_id,
            run_id,
            frame_id,
            path,
            depth_res,
            segmentation_res,
            dynamic_res,
        )
