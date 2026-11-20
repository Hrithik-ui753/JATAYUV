"""JATAYUV Spatial Intelligence & Inspection API Endpoints.

REST API routes for:
- Triggering AI infrastructure detection, tracking, 3D localization, and inspection analysis.
- Querying 3D localized infrastructure assets and spatial coordinates.
- Querying asset inspection anomaly reports and engineering recommendations.
"""
from __future__ import annotations

import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.mission import Mission
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.services.spatial_pipeline import spatial_intelligence_pipeline

log = logging.getLogger("jatayuv.api.spatial_intelligence")

router = APIRouter(tags=["Spatial Intelligence & Inspection"])


class SpatialProcessRequest(BaseModel):
    video_id: Optional[str] = None
    max_frames: int = Field(default=25, ge=2, le=100)
    confidence_threshold: float = Field(default=0.30, ge=0.05, le=0.99)


def _find_mission_frames(mission_id: str) -> List[str]:
    """Find extracted frames for a mission across standard storage paths."""
    patterns = [
        os.path.join("storage", "missions", mission_id, "videos", "*", "frames", "*", "*.jpg"),
        os.path.join("storage", "missions", mission_id, "videos", "*", "frames", "*", "*.png"),
        os.path.join("storage", "missions", mission_id, "frames", "*.jpg"),
        os.path.join("storage", "missions", mission_id, "frames", "*.png"),
        os.path.join("storage", "uploads", "videos", "*.jpg"),
    ]
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches
    return []


@router.post(
    "/missions/{mission_id}/spatial-intelligence/process",
    summary="Run AI infrastructure detection & 3D localization on mission footage",
)
def process_mission_spatial_intelligence(
    mission_id: str,
    req: SpatialProcessRequest = SpatialProcessRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process mission drone footage through the AI infrastructure detection and 3D spatial intelligence pipeline."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        # Check if dummy/demo mission ID is used
        log.info("Mission %s not found in DB, checking file system storage directly.", mission_id)

    frames = _find_mission_frames(mission_id)
    if not frames:
        # Check globally for any extracted drone frames
        fallback_frames = sorted(glob.glob(os.path.join("storage", "missions", "*", "videos", "*", "frames", "*", "*.jpg")))
        if fallback_frames:
            frames = fallback_frames
        else:
            raise HTTPException(
                status_code=400,
                detail=f"No extracted video frames found for mission {mission_id}. Extract frames first.",
            )

    try:
        result = spatial_intelligence_pipeline.process_frames(
            mission_id=mission_id,
            frame_paths=frames,
            max_frames=req.max_frames,
        )
        return {
            "status": "completed",
            "mission_id": mission_id,
            "processed_frames": result.total_frames_processed,
            "total_infrastructure_objects": result.total_tracked_objects,
            "total_anomalies_flagged": result.inspection_report.get("total_anomalies_detected", 0),
            "data": result.to_dict(),
        }
    except Exception as exc:
        log.exception("Spatial intelligence pipeline failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"status": "failed", "message": str(exc)},
        )


@router.get(
    "/missions/{mission_id}/spatial-intelligence",
    summary="Get 3D localized infrastructure assets and spatial coordinates",
)
def get_mission_spatial_intelligence(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve 3D localized infrastructure objects, spatial coordinates, bounding extents, and scale metadata."""
    artifact_path = os.path.join("storage", "missions", mission_id, "spatial_intelligence", "spatial_intelligence.json")
    if not os.path.isfile(artifact_path):
        # Look across all missions for a ready artifact if mission_id is default or generic
        all_artifacts = sorted(glob.glob(os.path.join("storage", "missions", "*", "spatial_intelligence", "spatial_intelligence.json")))
        if all_artifacts:
            artifact_path = all_artifacts[-1]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Spatial intelligence has not been generated for mission {mission_id}.",
            )

    try:
        with open(artifact_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read artifact: {exc}")


@router.get(
    "/missions/{mission_id}/spatial-intelligence/inspection-report",
    summary="Get infrastructure inspection intelligence audit report",
)
def get_mission_inspection_report(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve automated asset inspection anomaly report and engineer recommendations."""
    full_data = get_mission_spatial_intelligence(mission_id, db, current_user)
    return full_data.get("inspection_report", {})


@router.get(
    "/missions/{mission_id}/spatial-intelligence/tracks/{track_id}",
    summary="Get detailed multi-frame observations for a specific infrastructure track",
)
def get_mission_track_detail(
    mission_id: str,
    track_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve multi-frame 2D bounding boxes, depth values, and 3D rays for a single tracked asset."""
    full_data = get_mission_spatial_intelligence(mission_id, db, current_user)
    objects = full_data.get("infrastructure_objects_3d", [])
    for obj in objects:
        if obj.get("track_id") == track_id:
            return obj
    raise HTTPException(status_code=404, detail=f"Track ID {track_id} not found in mission {mission_id}.")


@router.get(
    "/missions/{mission_id}/spatial-intelligence/clearance",
    summary="Get conductor-to-terrain 3D spatial clearance bottleneck analysis",
)
def get_mission_conductor_clearance(
    mission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve 3D conductor clearance bottlenecks, terrain encroachment warnings, and NESC/IEEE disclaimers."""
    full_data = get_mission_spatial_intelligence(mission_id, db, current_user)
    clearance_sum = full_data.get("clearance_summary", {})
    objects = full_data.get("infrastructure_objects_3d", [])
    spans = [
        {
            "track_id": o.get("track_id"),
            "clearance_result": o.get("clearance_result"),
        }
        for o in objects
        if o.get("class_name") == "transmission_line" and o.get("clearance_result")
    ]
    return {
        "mission_id": mission_id,
        "clearance_summary": clearance_sum,
        "span_clearance_profiles": spans,
    }


@router.post(
    "/missions/{mission_id_a}/compare/{mission_id_b}",
    summary="Run multi-temporal historical inspection comparison across two drone flights",
)
def compare_historical_missions(
    mission_id_a: str,
    mission_id_b: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare baseline mission A with current survey mission B accounting for uncalibrated scale differences."""
    from backend.app.services.inspection.historical_comparison import historical_comparison_engine

    data_a = get_mission_spatial_intelligence(mission_id_a, db, current_user)
    data_b = get_mission_spatial_intelligence(mission_id_b, db, current_user)

    report = historical_comparison_engine.compare_missions(data_a, data_b)
    return report.to_dict()


@router.get(
    "/missions/{mission_id}/spatial-intelligence/export",
    summary="Export comprehensive infrastructure inspection audit report",
)
def export_mission_inspection_report(
    mission_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export complete asset inventory, 3D coordinates, risk scores, and anomaly findings."""
    from fastapi.responses import PlainTextResponse

    full_data = get_mission_spatial_intelligence(mission_id, db, current_user)
    if format == "json":
        return full_data

    # Generate CSV summary
    lines = ["Asset_ID,Class,Position_X,Position_Y,Position_Z,Confidence,Risk_Score,Risk_Category,Severity,Requires_Field_Patrol"]
    for obj in full_data.get("infrastructure_objects_3d", []):
        pos = obj.get("position", [0, 0, 0])
        risk = obj.get("risk_evaluation", {})
        score = risk.get("risk_score", 0.0)
        cat = risk.get("risk_category", "NEGLIGIBLE")
        lines.append(
            f"{obj.get('track_id')},{obj.get('class_name')},"
            f"{pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f},"
            f"{obj.get('confidence', 0.0):.2f},{score:.1f},{cat},"
            f"{obj.get('severity', 'NORMAL')},{obj.get('requires_field_verification', False)}"
        )
    return PlainTextResponse(content="\n".join(lines), media_type="text/csv")

