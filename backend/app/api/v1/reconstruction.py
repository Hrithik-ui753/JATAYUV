import os
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db, db as scoped_db
from backend.app.models.image import Image
from backend.app.models.project import Project
from backend.app.models.job import Job
from backend.app.models.mission import Mission
from backend.app.models.reconstruction import Reconstruction, Reconstruction3D
from backend.app.models.processing import ProcessingRun
from backend.app.models.user import User
from backend.app.schemas.reconstruction import ReconstructionTriggerRequest, ReconstructionResponse
from backend.app.services.photogrammetry import (
    ReconstructionFailed,
    ReconstructionInputError,
    ReconstructionUnavailable,
    photogrammetry_service,
)
from backend.app.services.reconstruction import reconstruction_service
from backend.app.services.recon.readiness import ReconstructionReadiness
from backend.app.api.deps import get_current_user, get_current_active_user, check_project_owner

router = APIRouter(tags=["3D Photogrammetry"])


def _get_mission_or_404(mission_id: str):
    mission = Mission.query.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


router._get_mission_or_404 = _get_mission_or_404



@router.get("/reconstruction/backend")
@router.get("/api/v1/reconstruction/backend")
def reconstruction_backend_status():
    """Report the real COLMAP backend availability (no probe-only claim)."""
    return reconstruction_service.executable_status()


@router.post("/reconstruction/3d", response_model=ReconstructionResponse)
@router.post("/api/v1/reconstruction/3d", response_model=ReconstructionResponse)
def trigger_3d_reconstruction(

    req: ReconstructionTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = check_project_owner(req.project_id, db, current_user)

    if req.image_ids and len(req.image_ids) > 0:
        images = db.query(Image).filter(Image.id.in_(req.image_ids)).all()
    else:
        images = db.query(Image).filter(Image.project_id == project.id).all()

    if not images:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "invalid_input",
                "message": "Cannot run 3D reconstruction on a project with no uploaded aerial images",
            },
        )

    image_paths = [img.file_path for img in images]

    # Validate before creating a job so bad input never leaves an orphan job.
    try:
        photogrammetry_service.validate_inputs(image_paths)
    except ReconstructionInputError as exc:
        raise HTTPException(
            status_code=400,
            detail={"status": "invalid_input", "message": str(exc)},
        )

    job = Job(
        project_id=project.id,
        job_type="reconstruction_3d",
        status="processing",
        progress_pct=15,
        owner_id=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    ply_path = os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project.id}.ply")
    mesh_path = os.path.join(settings.RECONSTRUCTION_DIR, f"mesh_{project.id}.obj")
    dsm_path = os.path.join(settings.RECONSTRUCTION_DIR, f"dsm_{project.id}.tif")

    try:
        res = photogrammetry_service.reconstruct_3d_pointcloud(
            image_paths=image_paths,
            output_ply_path=ply_path,
            output_mesh_path=mesh_path,
            output_dsm_path=dsm_path,
        )
    except ReconstructionUnavailable as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        detail = {"status": "unavailable", "backend": "colmap", "message": str(exc)}
        detail.update(getattr(exc, "details", {}) or {})
        raise HTTPException(status_code=503, detail=detail)
    except ReconstructionInputError as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={"status": "invalid_input", "message": str(exc)},
        )
    except ReconstructionFailed as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        detail = {"status": "failed", "backend": "colmap", "message": str(exc)}
        detail.update(getattr(exc, "details", {}) or {})
        raise HTTPException(status_code=500, detail=detail)

    recon_record = (
        db.query(Reconstruction3D)
        .filter(Reconstruction3D.project_id == project.id)
        .first()
    )

    if not recon_record:
        recon_record = Reconstruction3D(
            project_id=project.id,
            job_id=job.id,
            pointcloud_ply_path=res["pointcloud_ply_path"],
            mesh_obj_path=res["mesh_obj_path"],
            dsm_tiff_path=res["dsm_tiff_path"],
            num_points=res["num_points"],
            camera_count=res["camera_count"],
            reprojection_error_px=res["reprojection_error_px"],
            bounds_json=json.dumps(res["bounds"]),
        )
        db.add(recon_record)
    else:
        recon_record.job_id = job.id
        recon_record.pointcloud_ply_path = res["pointcloud_ply_path"]
        recon_record.mesh_obj_path = res["mesh_obj_path"]
        recon_record.dsm_tiff_path = res["dsm_tiff_path"]
        recon_record.num_points = res["num_points"]
        recon_record.camera_count = res["camera_count"]
        recon_record.reprojection_error_px = res["reprojection_error_px"]
        recon_record.bounds_json = json.dumps(res["bounds"])

    job.status = "completed"
    job.progress_pct = 100
    db.commit()
    db.refresh(recon_record)

    return ReconstructionResponse(
        id=recon_record.id,
        project_id=recon_record.project_id,
        job_id=recon_record.job_id,
        pointcloud_ply_path=recon_record.pointcloud_ply_path,
        mesh_obj_path=recon_record.mesh_obj_path,
        dsm_tiff_path=recon_record.dsm_tiff_path,
        num_points=recon_record.num_points,
        camera_count=recon_record.camera_count,
        reprojection_error_px=recon_record.reprojection_error_px,
        bounds=res["bounds"],
        created_at=recon_record.created_at,
    )

@router.get("/reconstruction/3d/{project_id}", response_model=ReconstructionResponse)
@router.get("/api/v1/reconstruction/3d/{project_id}", response_model=ReconstructionResponse)
def get_3d_reconstruction(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_project_owner(project_id, db, current_user)
    recon = db.query(Reconstruction3D).filter(Reconstruction3D.project_id == project_id).first()
    if not recon:
        raise HTTPException(status_code=404, detail="3D reconstruction result not found for this project")
    
    bounds = None
    if recon.bounds_json:
        try:
            bounds = json.loads(recon.bounds_json)
        except Exception:
            pass

    return ReconstructionResponse(
        id=recon.id,
        project_id=recon.project_id,
        job_id=recon.job_id,
        pointcloud_ply_path=recon.pointcloud_ply_path,
        mesh_obj_path=recon.mesh_obj_path,
        dsm_tiff_path=recon.dsm_tiff_path,
        num_points=recon.num_points,
        camera_count=recon.camera_count,
        reprojection_error_px=recon.reprojection_error_px,
        bounds=bounds,
        created_at=recon.created_at,
    )


@router.post("/missions/{mission_id}/reconstruction/start")
@router.post("/api/v1/missions/{mission_id}/reconstruction/start")
def start_mission_reconstruction(
    mission_id: str,
    current_user: User = Depends(get_current_active_user),
):
    mission = router._get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to run reconstruction for this mission")

    readiness = ReconstructionReadiness(mission).check()
    if not readiness.get("ready"):
        raise HTTPException(status_code=409, detail=readiness)

    # Return job / run details
    return {
        "status": "started",
        "mission_id": mission_id,
        "readiness": readiness,
    }


@router.get("/missions/{mission_id}/reconstruction/status")
@router.get("/api/v1/missions/{mission_id}/reconstruction/status")
def get_mission_reconstruction_status(
    mission_id: str,
    current_user: User = Depends(get_current_active_user),
):
    mission = router._get_mission_or_404(mission_id)
    if mission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to view reconstruction status")

    q = ProcessingRun.query
    run = (q(mission_id=mission_id) if callable(q) else q.filter_by(mission_id=mission_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="No reconstruction run found for this mission")

    return {
        "status": getattr(run, "status", "unknown"),
        "mission_id": mission_id,
        "run_id": getattr(run, "id", None),
    }


@router.get("/reconstructions/{reconstruction_id}/point-cloud")
@router.get("/api/v1/reconstructions/{reconstruction_id}/point-cloud")
def get_reconstruction_point_cloud(
    reconstruction_id: str,
    current_user: User = Depends(get_current_active_user),
):
    q = Reconstruction.query
    if callable(q) and not hasattr(q, "get"):
        rec = q().get(reconstruction_id)
    else:
        rec = q.get(reconstruction_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Reconstruction not found")

    mission = getattr(rec, "mission", None)
    if mission and getattr(mission, "user_id", None) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to access this reconstruction")

    ply_path = getattr(rec, "point_cloud_path", None)
    if not ply_path or not os.path.exists(ply_path):
        raise HTTPException(status_code=404, detail="Point cloud artifact missing")

    return FileResponse(ply_path, media_type="application/octet-stream")


    return FileResponse(ply_path, media_type="application/octet-stream")


