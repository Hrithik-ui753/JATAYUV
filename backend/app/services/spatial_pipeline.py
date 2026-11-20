"""JATAYUV Spatial Intelligence Pipeline Orchestrator.

Integrates:
1. Video frame loading / extraction.
2. AI Infrastructure Detection (Towers, Lines, Insulators, Crossarms, Damage).
3. ByteTrack multi-frame object tracking.
4. Depth Anything V2 depth estimation.
5. Photogrammetric camera pose estimation.
6. 3D Spatial Localization & multi-view triangulation.
7. Automated Infrastructure Asset Inspection Intelligence.
8. Serialization to disk for 3D web viewer & dashboard consumption.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from backend.app.services.inspection.conductor_clearance import (
    ConductorClearanceEstimator,
    ConductorSpanClearanceResult,
)
from backend.app.services.inspection.historical_comparison import (
    HistoricalComparisonEngine,
    HistoricalComparisonReport,
)
from backend.app.services.inspection.infrastructure_inspection import (
    AnomalySeverity,
    InfrastructureInspectionEngine,
    InspectionAnomaly,
    InspectionReport,
)
from backend.app.services.inspection.insulator_inspection import (
    InsulatorAuditResult,
    InsulatorInspectionEngine,
)
from backend.app.services.inspection.power_line_reconstruction import (
    CatenaryModel3D,
    PowerLineReconstructor,
)
from backend.app.services.inspection.risk_assessment import (
    AssetRiskEvaluation,
    RiskAssessmentEngine,
    RiskCategory,
)
from backend.app.services.inspection.tower_component_segmentation import (
    TowerComponentSegmenter,
    TowerSegmentationResult,
)
from backend.app.services.perception.infrastructure_detector import (
    InfrastructureClass,
    InfrastructureDetector,
)
from backend.app.services.perception.infrastructure_tracker import (
    InfrastructureTracker,
)
from backend.app.services.perception.spatial_intelligence import (
    LocalizedInfrastructure3D,
    SpatialIntelligenceEngine,
)
from backend.app.services.photogrammetry import photogrammetry_service

log = logging.getLogger("jatayuv.services.spatial_pipeline")


@dataclass
class SpatialPipelineResult:
    mission_id: str
    total_frames_processed: int
    total_tracked_objects: int
    localized_3d_objects: List[Dict[str, Any]]
    inspection_report: Dict[str, Any]
    clearance_summary: Dict[str, Any]
    risk_summary: Dict[str, Any]
    scale_metadata: Dict[str, Any]
    timing_breakdown: Dict[str, float]
    output_json_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "total_frames_processed": self.total_frames_processed,
            "total_tracked_objects": self.total_tracked_objects,
            "infrastructure_objects_3d": self.localized_3d_objects,
            "inspection_report": self.inspection_report,
            "clearance_summary": self.clearance_summary,
            "risk_summary": self.risk_summary,
            "scale_metadata": self.scale_metadata,
            "timing_breakdown": self.timing_breakdown,
            "output_json_path": self.output_json_path,
        }


class SpatialIntelligencePipeline:
    """End-to-end pipeline connecting detection, tracking, reconstruction, and inspection."""

    def __init__(
        self,
        detector: Optional[InfrastructureDetector] = None,
        tracker: Optional[InfrastructureTracker] = None,
        spatial_engine: Optional[SpatialIntelligenceEngine] = None,
        inspection_engine: Optional[InfrastructureInspectionEngine] = None,
        tower_segmenter: Optional[TowerComponentSegmenter] = None,
        power_line_reconstructor: Optional[PowerLineReconstructor] = None,
        insulator_inspector: Optional[InsulatorInspectionEngine] = None,
        clearance_estimator: Optional[ConductorClearanceEstimator] = None,
        risk_engine: Optional[RiskAssessmentEngine] = None,
    ) -> None:
        self.detector = detector or InfrastructureDetector()
        self.tracker = tracker or InfrastructureTracker()
        self.spatial_engine = spatial_engine or SpatialIntelligenceEngine()
        self.inspection_engine = inspection_engine or InfrastructureInspectionEngine()
        self.tower_segmenter = tower_segmenter or TowerComponentSegmenter()
        self.power_line_reconstructor = power_line_reconstructor or PowerLineReconstructor()
        self.insulator_inspector = insulator_inspector or InsulatorInspectionEngine()
        self.clearance_estimator = clearance_estimator or ConductorClearanceEstimator()
        self.risk_engine = risk_engine or RiskAssessmentEngine()

    def process_frames(
        self,
        mission_id: str,
        frame_paths: List[str],
        output_dir: Optional[str] = None,
        timestamps: Optional[List[float]] = None,
        max_frames: int = 30,
    ) -> SpatialPipelineResult:
        """Execute full spatial intelligence pipeline on a sequence of frames."""
        t_start = time.perf_counter()
        if not frame_paths:
            raise ValueError("No frames provided for spatial intelligence processing.")

        # Subsample if exceeding max_frames
        if len(frame_paths) > max_frames:
            step = max(1, len(frame_paths) // max_frames)
            frame_paths = frame_paths[::step][:max_frames]

        total_frames = len(frame_paths)
        if output_dir is None:
            output_dir = os.path.join("storage", "missions", mission_id, "spatial_intelligence")
        os.makedirs(output_dir, exist_ok=True)

        log.info("Processing %d frames for mission %s...", total_frames, mission_id)

        # 1. 2D Object Detection & Multi-Frame Tracking
        t0_det = time.perf_counter()
        frames_bgr = []
        for idx, p in enumerate(frame_paths):
            img = cv2.imread(p)
            if img is None:
                continue
            frames_bgr.append((idx, p, img))
            ts = timestamps[idx] if timestamps and idx < len(timestamps) else idx * (1.0 / 30.0)
            dets = self.detector.detect(img, frame_index=idx, timestamp_s=ts)
            self.tracker.update(dets, frame_index=idx, timestamp_s=ts)

        t_det = round(time.perf_counter() - t0_det, 3)

        confirmed_tracks = self.tracker.get_confirmed_tracks()
        log.info("Tracking produced %d confirmed infrastructure tracks.", len(confirmed_tracks))

        # 2. Camera Poses & Depth Maps Extraction
        t0_recon = time.perf_counter()
        pose_data = photogrammetry_service._estimate_poses_opencv(frame_paths)
        cam_meta = pose_data.get("cameras", {}).get(1, {})
        focal = float(cam_meta.get("fx", 1920.0))
        cx = float(cam_meta.get("cx", 960.0))
        cy = float(cam_meta.get("cy", 540.0))
        intrinsics = np.array([[focal, 0, cx], [0, focal, cy], [0, 0, 1]], dtype=np.float64)

        images_dict = pose_data.get("images", {})
        poses_by_idx: Dict[int, Any] = {}
        for idx, path, _ in frames_bgr:
            base = os.path.basename(path)
            if base in images_dict:
                img_data = images_dict[base]
                poses_by_idx[idx] = {
                    "R": np.array(img_data["R_w2c"]),
                    "t": np.array(img_data["t_w2c"]),
                    "focal_px": focal,
                    "cx": cx,
                    "cy": cy,
                    "name": base,
                }

        # Compute Depth Anything V2 depth maps
        from backend.app.services.depth_estimation import depth_service
        depth_engine = depth_service.get_engine()
        depth_maps: Dict[int, np.ndarray] = {}
        for idx, _, img in frames_bgr:
            try:
                res_d = depth_engine.predict(img)
                inv_d = res_d["inverse_depth"]
                depth_map_f = 1.0 / np.maximum(inv_d, 1e-4)
                depth_maps[idx] = depth_map_f.astype(np.float32)
            except Exception as e:
                log.warning("Depth estimation error on frame %d: %s", idx, e)

        t_recon = round(time.perf_counter() - t0_recon, 3)

        # 3. 3D Spatial Localization
        t0_loc = time.perf_counter()
        localized_3d = self.spatial_engine.localize_tracks_3d(
            tracks=confirmed_tracks,
            camera_poses=poses_by_idx,
            depth_maps=depth_maps,
            intrinsics=intrinsics,
        )
        t_loc = round(time.perf_counter() - t0_loc, 3)

        # 4. Infrastructure Inspection Intelligence (Phase 3 Integration)
        t0_insp = time.perf_counter()
        evidence_dir = os.path.join(output_dir, "evidence")
        os.makedirs(evidence_dir, exist_ok=True)

        inspection_report = self.inspection_engine.analyze_infrastructure(
            mission_id=mission_id,
            objects_3d=localized_3d,
        )

        # Build lookup from track_id to confirmed track for 2D observation access
        track_map = {t.track_id: t for t in confirmed_tracks}

        # 4a. Tower Component Instance Segmentation
        for obj in localized_3d:
            if obj.class_name == InfrastructureClass.TRANSMISSION_TOWER:
                trk = track_map.get(obj.track_id)
                if trk and trk.observations:
                    # Select frame observation with largest bounding box
                    best_det = max(
                        trk.observations,
                        key=lambda d: max(0.0, (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1])),
                    )
                    f_idx = best_det.frame_index
                    f_match = next((item for item in frames_bgr if item[0] == f_idx), None)
                    if f_match:
                        seg_res = self.tower_segmenter.segment_tower(
                            frame_bgr=f_match[2],
                            tower_bbox=best_det.bbox,
                            tower_track_id=obj.track_id,
                            frame_index=f_idx,
                        )
                        obj.extra_attributes["tower_components"] = seg_res.to_dict()

        # 4b. Power-Line Catenary Reconstruction
        catenary_models: Dict[str, CatenaryModel3D] = {}
        for obj in localized_3d:
            if obj.class_name == InfrastructureClass.TRANSMISSION_LINE:
                wps = obj.line_waypoints or [
                    [obj.position[0], obj.position[1], obj.position[2] - 15.0],
                    [obj.position[0], obj.position[1] - 1.2, obj.position[2]],
                    [obj.position[0], obj.position[1], obj.position[2] + 15.0],
                ]
                cat_model = self.power_line_reconstructor.reconstruct_conductor_span(
                    line_track_id=obj.track_id,
                    waypoints_3d=wps,
                    confidence=obj.confidence,
                )
                catenary_models[obj.track_id] = cat_model
                obj.extra_attributes["catenary_model"] = cat_model.to_dict()

                # If discontinuity or excessive sag, flag anomaly
                if cat_model.continuity_status == "DISCONTINUITY_FLAGGED":
                    inspection_report.anomalies.append(
                        InspectionAnomaly(
                            anomaly_id=f"ANOMALY-PL-{len(inspection_report.anomalies)+1:04d}",
                            target_track_id=obj.track_id,
                            class_name=obj.class_name,
                            anomaly_type="CONDUCTOR_SPAN_DISCONTINUITY",
                            severity=AnomalySeverity.CRITICAL,
                            confidence=0.88,
                            position_3d=obj.position,
                            description=(
                                f"Conductor continuity gap detected ({cat_model.discontinuity_gap_units:.2f} relative units). "
                                "Potential severed phase conductor or optical ground wire break."
                            ),
                            engineering_recommendation="Dispatch urgent field patrol to verify conductor span physical integrity.",
                            evidence_frame_indices=[o.frame_index for o in obj.spatial_observations[:3]],
                        )
                    )

        # 4c. Insulator Integrity & Defect Inspection with Evidence Crops
        for obj in localized_3d:
            if obj.class_name == InfrastructureClass.INSULATOR:
                trk = track_map.get(obj.track_id)
                if trk and trk.observations:
                    best_det = max(
                        trk.observations,
                        key=lambda d: max(0.0, (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1])),
                    )
                    f_idx = best_det.frame_index
                    f_match = next((item for item in frames_bgr if item[0] == f_idx), None)
                    if f_match:
                        ins_res = self.insulator_inspector.inspect_insulator_roi(
                            frame_bgr=f_match[2],
                            insulator_bbox=best_det.bbox,
                            insulator_track_id=obj.track_id,
                            evidence_save_dir=evidence_dir,
                        )
                        obj.extra_attributes["insulator_audit"] = ins_res.to_dict()

                        # Convert any detected insulator defects to InspectionAnomalies
                        for finding in ins_res.findings:
                            sev = AnomalySeverity.WARNING
                            if finding.severity == "CRITICAL":
                                sev = AnomalySeverity.CRITICAL
                            elif finding.severity == "INFO":
                                sev = AnomalySeverity.INFO

                            # Store web-accessible relative evidence path
                            web_evidence_path = (
                                f"/storage/missions/{mission_id}/evidence/{os.path.basename(finding.evidence_crop_path)}"
                                if finding.evidence_crop_path
                                else None
                            )

                            inspection_report.anomalies.append(
                                InspectionAnomaly(
                                    anomaly_id=finding.finding_id,
                                    target_track_id=obj.track_id,
                                    class_name=obj.class_name,
                                    anomaly_type=finding.defect_type.value.upper(),
                                    severity=sev,
                                    confidence=finding.confidence,
                                    position_3d=obj.position,
                                    description=finding.description,
                                    engineering_recommendation=finding.recommendation,
                                    requires_field_verification=True,
                                    evidence_frame_indices=[f_idx],
                                    evidence_crop_path=web_evidence_path,
                                )
                            )

        # 4d. Conductor-to-Terrain Clearance Estimation
        # Sample terrain points from reconstructed lower-frame ground depths
        terrain_points_list: List[np.ndarray] = []
        for idx in list(depth_maps.keys())[:5]:
            d_map = depth_maps[idx]
            h_d, w_d = d_map.shape
            pose = poses_by_idx.get(idx)
            if pose is None:
                continue
            R_w2c = pose["R"]
            t_w2c = pose["t"]
            R_c2w = R_w2c.T
            cam_center_w = -R_c2w @ t_w2c

            # Sample grid across ground terrain region (y: 65% to 95%)
            ys = np.linspace(int(h_d * 0.65), int(h_d * 0.95), num=12, dtype=int)
            xs = np.linspace(int(w_d * 0.1), int(w_d * 0.9), num=16, dtype=int)
            for y_px in ys:
                for x_px in xs:
                    zv = float(d_map[y_px, x_px])
                    if zv <= 0.1 or zv > 200.0:
                        continue
                    xv = (x_px - cx) * zv / focal
                    yv = (y_px - cy) * zv / focal
                    pt_cam = np.array([xv, yv, zv])
                    pt_w = R_c2w @ pt_cam + cam_center_w
                    # In Three.js world frame: +Y UP, +Z forward
                    pt_three = np.array([pt_w[0], -pt_w[1], -pt_w[2]])
                    terrain_points_list.append(pt_three)

        terrain_points = (
            np.array(terrain_points_list, dtype=np.float64)
            if terrain_points_list
            else np.zeros((1, 3), dtype=np.float64)
        )

        all_clearance_results: List[Dict[str, Any]] = []
        min_overall_clearance = float("inf")
        bottleneck_span_id = ""
        encroachment_count = 0

        for obj in localized_3d:
            if obj.class_name == InfrastructureClass.TRANSMISSION_LINE:
                cat_m = catenary_models.get(obj.track_id)
                curve_pts = (
                    [p.position for p in cat_m.interpolated_points]
                    if cat_m
                    else [(obj.position[0], obj.position[1], obj.position[2])]
                )
                clr_res = self.clearance_estimator.estimate_span_clearance(
                    line_track_id=obj.track_id,
                    conductor_curve_points=curve_pts,
                    terrain_points=terrain_points,
                    uncertainty_radius=obj.uncertainty_radius,
                )
                clr_dict = clr_res.to_dict()
                obj.extra_attributes["clearance_result"] = clr_dict
                all_clearance_results.append(clr_dict)

                if clr_res.minimum_clearance < min_overall_clearance:
                    min_overall_clearance = clr_res.minimum_clearance
                    bottleneck_span_id = obj.track_id

                if clr_res.clearance_status in ("CLEARANCE_WARNING", "ADVISORY"):
                    encroachment_count += 1
                    inspection_report.anomalies.append(
                        InspectionAnomaly(
                            anomaly_id=f"ANOMALY-CLR-{len(inspection_report.anomalies)+1:04d}",
                            target_track_id=obj.track_id,
                            class_name=obj.class_name,
                            anomaly_type="TERRAIN_CLEARANCE_ENCROACHMENT",
                            severity=(
                                AnomalySeverity.CRITICAL
                                if clr_res.clearance_status == "CLEARANCE_WARNING"
                                else AnomalySeverity.WARNING
                            ),
                            confidence=0.84,
                            position_3d=clr_res.bottleneck.conductor_point_3d,
                            description=(
                                f"Conductor-to-terrain clearance bottleneck at {clr_res.minimum_clearance:.2f} relative units "
                                f"(uncertainty +/-{clr_res.bottleneck.uncertainty_margin:.2f} units). Status: {clr_res.clearance_status}."
                            ),
                            engineering_recommendation=(
                                "Conduct field LiDAR / RTK ground clearance survey before declaring safety clearance compliance."
                            ),
                            requires_field_verification=True,
                            evidence_frame_indices=[o.frame_index for o in obj.spatial_observations[:2]],
                        )
                    )

        # 4e. AI Risk Assessment Framework
        risk_category_counts = {
            "NEGLIGIBLE": 0,
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        total_risk_scores: List[float] = []

        for obj in localized_3d:
            # Find all anomaly severities for this asset
            obj_anoms = [a for a in inspection_report.anomalies if a.target_track_id == obj.track_id]
            sev_strings = [a.severity.value for a in obj_anoms]

            risk_eval = self.risk_engine.evaluate_asset_risk(
                asset_id=obj.track_id,
                class_name=obj.class_name.value,
                confidence=obj.confidence,
                anomaly_severities=sev_strings,
                uncertainty_radius=obj.uncertainty_radius,
                frame_observations_count=len(obj.spatial_observations),
            )
            obj.extra_attributes["risk_evaluation"] = risk_eval.to_dict()

            # Align top-level severity with risk category
            if risk_eval.risk_category == RiskCategory.CRITICAL:
                obj.severity = "CRITICAL"
                obj.requires_field_verification = True
            elif risk_eval.risk_category in (RiskCategory.HIGH, RiskCategory.MODERATE):
                obj.severity = "WARNING"
                obj.requires_field_verification = True
            else:
                obj.severity = "NORMAL"

            risk_category_counts[risk_eval.risk_category.value] += 1
            total_risk_scores.append(risk_eval.risk_score)

        # Update inspection report summary counts
        inspection_report.total_anomalies_detected = len(inspection_report.anomalies)
        inspection_report.critical_count = sum(
            1 for a in inspection_report.anomalies if a.severity == AnomalySeverity.CRITICAL
        )
        inspection_report.warning_count = sum(
            1 for a in inspection_report.anomalies if a.severity == AnomalySeverity.WARNING
        )
        inspection_report.info_count = sum(
            1 for a in inspection_report.anomalies if a.severity == AnomalySeverity.INFO
        )
        if localized_3d:
            inspection_report.risk_index_pct = round(
                float(np.mean(total_risk_scores)) if total_risk_scores else 0.0, 1
            )

        t_insp = round(time.perf_counter() - t0_insp, 3)
        t_total = round(time.perf_counter() - t_start, 3)

        scale_meta = {
            "units": self.spatial_engine.units,
            "scale_type": self.spatial_engine.scale_type,
            "metric_calibrated": self.spatial_engine.metric_calibrated,
            "scale_disclaimer": (
                "Positions and clearances are scale-aligned in relative reconstruction units. "
                "SI metre calibration requires onboard RTK-GPS or Ground Control Points."
            ),
        }

        clearance_summary = {
            "total_spans_evaluated": len(all_clearance_results),
            "minimum_corridor_clearance": (
                round(float(min_overall_clearance), 3) if min_overall_clearance != float("inf") else 0.0
            ),
            "bottleneck_span_id": bottleneck_span_id,
            "encroachment_warnings_count": encroachment_count,
            "regulatory_disclaimer": (
                "Do not claim NESC/IEEE regulatory compliance without independent metric RTK ground control."
            ),
        }

        risk_summary = {
            "mean_risk_score": round(float(np.mean(total_risk_scores)) if total_risk_scores else 0.0, 1),
            "distribution": risk_category_counts,
            "total_assets_evaluated": len(localized_3d),
            "requires_field_patrol_count": (
                risk_category_counts["HIGH"] + risk_category_counts["CRITICAL"]
            ),
        }

        timings = {
            "detection_and_tracking_s": t_det,
            "depth_and_poses_s": t_recon,
            "spatial_localization_3d_s": t_loc,
            "inspection_analysis_s": t_insp,
            "total_wall_clock_s": t_total,
        }

        localized_dicts = [obj.to_dict() for obj in localized_3d]
        inspection_dict = inspection_report.to_dict()

        pipeline_result = SpatialPipelineResult(
            mission_id=mission_id,
            total_frames_processed=len(frames_bgr),
            total_tracked_objects=len(localized_3d),
            localized_3d_objects=localized_dicts,
            inspection_report=inspection_dict,
            clearance_summary=clearance_summary,
            risk_summary=risk_summary,
            scale_metadata=scale_meta,
            timing_breakdown=timings,
            output_json_path=os.path.join(output_dir, "spatial_intelligence.json"),
        )

        # Write output JSON artifact
        with open(pipeline_result.output_json_path, "w") as f:
            json.dump(pipeline_result.to_dict(), f, indent=2)

        log.info(
            "Spatial intelligence pipeline complete. Wrote artifact to %s",
            pipeline_result.output_json_path,
        )
        return pipeline_result


spatial_intelligence_pipeline = SpatialIntelligencePipeline()
