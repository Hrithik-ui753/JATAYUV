from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from backend.app.models.mission import Mission
from backend.app.models.frame import Frame
from backend.app.models.processing import ProcessingRun, ProcessingStatus
from backend.app.models.job import Job
from backend.app.services.mission_processing.core import (
    MissionProcessingService as _Core,
)

log = logging.getLogger("jatayuv.mission_processing.perception")


class MissionPerceptionService:
    """Thin extension of the existing mission processing service with P3 helpers."""

    def __init__(self, core: Optional[_Core] = None):
        self._core = core or _Core()

    # ------------------------------------------------------------------
    # Perception-run lifecycle
    # ------------------------------------------------------------------

    def create_perception_run(self, mission_id: str) -> Optional[ProcessingRun]:
        mission = Mission.get_by_id(mission_id)
        if mission is None:
            return None

        existing = self.get_latest_perception_run(mission_id)
        if existing is not None and existing.status not in (
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
        ):
            return existing

        run = ProcessingRun(
            mission_id=mission_id,
            run_type="perception",
            status=ProcessingStatus.PENDING,
        )
        run.save()

        # Determine the selected-frame count from P2 metadata when available.
        selected = self._selected_frame_count(mission_id)
        run.total_selected_frames = selected
        run.save()

        run.status = ProcessingStatus.PROCESSING
        run.started_at = datetime.now(timezone.utc)
        run.save()

        return run

    def get_latest_perception_run(self, mission_id: str) -> Optional[ProcessingRun]:
        runs = ProcessingRun.query(
            mission_id=mission_id,
            run_type="perception",
            order_by="started_at",
            desc=True,
        )
        return runs[0] if runs else None

    def cancel_perception_run(self, run_id: str) -> bool:
        run = ProcessingRun.get_by_id(run_id)
        if not run:
            return False
        if run.status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED):
            return False
        run.status = ProcessingStatus.CANCELLED
        run.cancelled_at = datetime.now(timezone.utc)
        run.save()
        return True

    def increment_processed(self, run_id: str, *, success: bool = True) -> None:
        run = ProcessingRun.get_by_id(run_id)
        if not run:
            return
        run.processed_frames = (run.processed_frames or 0) + 1
        if not success:
            run.failed_frames = (run.failed_frames or 0) + 1
        run.save()

    def finish_run(
        self,
        run_id: str,
        *,
        success: bool = True,
        device: Optional[str] = None,
        depth_model_id: Optional[str] = None,
        depth_model_version: Optional[str] = None,
        depth_checkpoint_sha256: Optional[str] = None,
        segmentation_model_id: Optional[str] = None,
        segmentation_model_version: Optional[str] = None,
        segmentation_checkpoint_sha256: Optional[str] = None,
        dynamic_model_id: Optional[str] = None,
        dynamic_model_version: Optional[str] = None,
        dynamic_checkpoint_sha256: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        run = ProcessingRun.get_by_id(run_id)
        if not run:
            return
        run.status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
        run.completed_at = datetime.now(timezone.utc)
        if device:
            run.device = device
        if depth_model_id:
            run.depth_model_id = depth_model_id
        if depth_model_version:
            run.depth_model_version = depth_model_version
        if depth_checkpoint_sha256:
            run.depth_checkpoint_sha256 = depth_checkpoint_sha256
        if segmentation_model_id:
            run.segmentation_model_id = segmentation_model_id
        if segmentation_model_version:
            run.segmentation_model_version = segmentation_model_version
        if segmentation_checkpoint_sha256:
            run.segmentation_checkpoint_sha256 = segmentation_checkpoint_sha256
        if dynamic_model_id:
            run.dynamic_model_id = dynamic_model_id
        if dynamic_model_version:
            run.dynamic_model_version = dynamic_model_version
        if dynamic_checkpoint_sha256:
            run.dynamic_checkpoint_sha256 = dynamic_checkpoint_sha256
        if error_message:
            run.error_message = error_message
        run.save()

    def build_perception_report(self, mission_id: str) -> Optional[Dict[str, Any]]:
        run = self.get_latest_perception_run(mission_id)
        if not run:
            return None

        artifacts = self._artifact_counts_for_run(run.id)
        notes: List[str] = []
        warnings: List[str] = []

        if not run.depth_model_id:
            notes.append("No depth model id recorded for this run")
        if not run.segmentation_model_id:
            notes.append("No segmentation model id recorded for this run")
        if not run.dynamic_model_id:
            notes.append("No dynamic detection model id recorded; dynamic masks unavailable")

        return {
            "perception_run_id": run.id,
            "mission_id": mission_id,
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "device": run.device,
            "total_selected_frames": run.total_selected_frames,
            "processed_frames": run.processed_frames,
            "failed_frames": run.failed_frames,
            "depth_model_id": run.depth_model_id,
            "depth_model_version": run.depth_model_version,
            "depth_checkpoint_sha256": run.depth_checkpoint_sha256,
            "segmentation_model_id": run.segmentation_model_id,
            "segmentation_model_version": run.segmentation_model_version,
            "segmentation_checkpoint_sha256": run.segmentation_checkpoint_sha256,
            "dynamic_model_id": run.dynamic_model_id,
            "dynamic_model_version": run.dynamic_model_version,
            "dynamic_checkpoint_sha256": run.dynamic_checkpoint_sha256,
            "batch_size": run.batch_size,
            "total_runtime_seconds": (
                (run.completed_at - run.started_at).total_seconds()
                if run.started_at and run.completed_at
                else None
            ),
            "artifact_counts": artifacts,
            "error_message": run.error_message,
            "warnings": warnings,
            "notes": notes,
        }

    # ------------------------------------------------------------------
    # Per-frame perception reading helpers (used by API)
    # ------------------------------------------------------------------

    def get_frame_perception(self, frame_id: str) -> Optional[Dict[str, Any]]:
        from backend.app.services.perception import (
            FrameDepthResult,
            FrameSegmentationResult,
            FrameDynamicObjectResult,
        )

        frame = Frame.get_by_id(frame_id)
        if not frame:
            return None

        run = self.get_latest_perception_run(frame.mission_id)
        if not run:
            return None

        # look for a FramePerception row for this frame inside the latest run
        frame_perceptions = run.frames
        match = next((fp for fp in frame_perceptions if fp.frame_id == frame_id), None)
        if not match:
            return None

        depth = match.depth_result
        segmentation = match.segmentation_result
        dynamic = match.dynamic_result

        return {
            "frame_id": frame_id,
            "mission_id": frame.mission_id,
            "video_id": frame.video_id,
            "frame_index": frame.frame_index if hasattr(frame, "frame_index") else None,
            "presentation_timestamp": getattr(frame, "presentation_timestamp", None),
            "timestamp_seconds": getattr(frame, "timestamp_seconds", None),
            "gps_latitude": frame.gps_latitude if hasattr(frame, "gps_latitude") else None,
            "gps_longitude": frame.gps_longitude if hasattr(frame, "gps_longitude") else None,
            "altitude": frame.altitude if hasattr(frame, "altitude") else None,
            "altitude_datum": frame.altitude_datum if hasattr(frame, "altitude_datum") else None,
            "gps_source": frame.gps_source if hasattr(frame, "gps_source") else None,
            "gps_association_gap_seconds": (
                frame.gps_association_gap_seconds
                if hasattr(frame, "gps_association_gap_seconds")
                else None
            ),
            "status": match.status,
            "processing_duration_seconds": match.processing_duration_seconds,
            "error_message": match.error_message,
            "warnings": match.warnings_json or {},
            "depth": _depth_record_to_api(depth) if depth else None,
            "segmentation": _segmentation_record_to_api(segmentation) if segmentation else None,
            "dynamic": _dynamic_record_to_api(dynamic) if dynamic else None,
            "perception_run_id": run.id,
            "created_at": match.created_at,
        }

    def get_frame_depth(self, frame_id: str) -> Optional[Dict[str, Any]]:
        rec = self.get_frame_perception(frame_id)
        if not rec or not rec.get("depth"):
            return None
        return {
            "frame_id": frame_id,
            **rec["depth"],
            "status": rec["status"],
            "error_message": rec["error_message"],
        }

    def get_frame_segmentation(self, frame_id: str) -> Optional[Dict[str, Any]]:
        rec = self.get_frame_perception(frame_id)
        if not rec or not rec.get("segmentation"):
            return None
        return {
            "frame_id": frame_id,
            **rec["segmentation"],
            "status": rec["status"],
            "error_message": rec["error_message"],
        }

    def get_frame_dynamic_mask(self, frame_id: str) -> Optional[Dict[str, Any]]:
        rec = self.get_frame_perception(frame_id)
        if not rec or not rec.get("dynamic"):
            return None
        return {
            "frame_id": frame_id,
            **rec["dynamic"],
            "status": rec["status"],
            "error_message": rec["error_message"],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _selected_frame_count(self, mission_id: str) -> int:
        frames = Frame.query(mission_id=mission_id, selected=True, order_by="created_at")
        return len(frames)

    def _artifact_counts_for_run(self, run_id: str) -> Dict[str, int]:
        from backend.app.models.artifact import Artifact

        counts: Dict[str, int] = {}
        rows = Artifact.query(perception_run_id=run_id)
        for r in rows:
            t = r.kind or "unknown"
            counts[t] = counts.get(t, 0) + 1
        return counts


# ------------------------------------------------------------------
# Row -> API mapping helpers
# ------------------------------------------------------------------


def _depth_record_to_api(r) -> Dict[str, Any]:
    return {
        "depth_map_path": r.depth_map_path,
        "depth_visualization_path": r.depth_visualization_path,
        "raw_depth_path": r.raw_depth_path,
        "model_id": r.model_id,
        "model_version": r.model_version,
        "checkpoint_sha256": r.checkpoint_sha256,
        "depth_type": r.depth_type,
        "depth_unit": r.depth_unit,
        "is_metric": bool(r.is_metric) if r.is_metric is not None else None,
        "input_width": r.input_width,
        "input_height": r.input_height,
        "output_width": r.output_width,
        "output_height": r.output_height,
        "inference_device": r.inference_device,
        "inference_duration_ms": r.inference_duration_ms,
        "depth_min": r.depth_min,
        "depth_max": r.depth_max,
        "depth_mean": r.depth_mean,
        "relative_min": r.relative_min,
        "relative_max": r.relative_max,
        "relative_mean": r.relative_mean,
        "confidence": r.confidence_json or {},
    }


def _segmentation_record_to_api(r) -> Dict[str, Any]:
    return {
        "mask_path": r.mask_path,
        "visualization_path": r.visualization_path,
        "model_id": r.model_id,
        "model_version": r.model_version,
        "checkpoint_sha256": r.checkpoint_sha256,
        "input_width": r.input_width,
        "input_height": r.input_height,
        "output_width": r.output_width,
        "output_height": r.output_height,
        "inference_device": r.inference_device,
        "inference_duration_ms": r.inference_duration_ms,
        "class_distribution": r.class_distribution_json or {},
        "per_class_pixel_counts": r.per_class_pixel_counts_json or {},
        "unsupported_class_handling": r.unsupported_class_handling_json or {},
    }


def _dynamic_record_to_api(r) -> Dict[str, Any]:
    return {
        "dynamic_mask_path": r.dynamic_mask_path,
        "detections": r.detections_json or [],
        "model_id": r.model_id,
        "model_version": r.model_version,
        "checkpoint_sha256": r.checkpoint_sha256,
        "inference_device": r.inference_device,
        "inference_duration_ms": r.inference_duration_ms,
        "dynamic_label_policy": r.dynamic_label_policy,
    }
