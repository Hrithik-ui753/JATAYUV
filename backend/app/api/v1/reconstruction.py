from __future__ import annotations



import os

from datetime import datetime

from typing import Any, Dict, List, Optional



from fastapi import APIRouter, Depends, HTTPException, Path, Query



from backend.app.api.deps import CurrentUser, get_current_active_user

from backend.app.models.mission import Mission

from backend.app.models.reconstruction import Reconstruction

from backend.app.models.processing import ProcessingRun

from backend.app.api.v1.schemas.reconstruction import (

    ReconstructionStartResponse,

    ReconstructionStatusResponse,

    ReconstructionListResponse,

    ReconstructionDetailResponse,

    ReconstructionArtifactResponse,

    ReconstructionReportResponse,

    ReconstructionCancelResponse,

)

from backend.app.services.recon.pipeline import ReconstructionPipeline

from backend.app.services.recon.readiness import ReconstructionReadiness

from backend.app.core.database import db

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.image import Image
from backend.app.models.project import Project
from backend.app.models.job import Job
from backend.app.models.reconstruction import Reconstruction3D
from backend.app.models.user import User
from backend.app.schemas.reconstruction import ReconstructionResponse

# Legacy placeholder: the original trigger request class was removed during the
# mission-scoped reconstruction refactor. If this endpoint still needs a request
# body, define it here explicitly rather than reintroducing the missing import.
ReconstructionTriggerRequest = None  # type: ignore[assignment, misc]
from backend.app.services.photogrammetry import (
    ReconstructionFailed,
    ReconstructionInputError,
    ReconstructionUnavailable,
    photogrammetry_service,
)
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(prefix="/reconstruction", tags=["3D Photogrammetry"])


def _reconstruction_detail(status_value: str, exc: Exception) -> dict:
    return {
        "status": status_value,
        "service": "3d_reconstruction",
        "reason": getattr(exc, "reason", "reconstruction_failed"),
        "message": str(exc),
        "details": getattr(exc, "details", {}),
    }


@router.get("/backend")
def reconstruction_backend_status(current_user: User = Depends(get_current_user)):
    """Report whether a real reconstruction backend is installed.

    ``available: false`` means reconstruction is unavailable by design (no
    synthetic geometry is substituted).
    """
    from backend.app.services.reconstruction import reconstruction_service

    info = reconstruction_service.executable_status()
    info["status"] = "available" if info["available"] else "unavailable"
    info["note"] = (
        "Reconstruction requires COLMAP. Unavailability is reported explicitly; no "
        "synthetic point cloud is generated."
        if not info["available"]
        else "COLMAP detected. Reconstruction is only reported as completed after it "
        "runs successfully on the supplied images."
    )
    return info


@router.post("/3d", response_model=ReconstructionResponse)
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

    if not check["ready"]:

        raise HTTPException(status_code=409, detail="Reconstruction inputs not ready")



    run = ProcessingRun(

        mission_id=mission_id,

        job_type="3d_reconstruction",

        status="pending",

        started_at=None,

        completed_at=None,

        cancelled_at=None,

        error_message=None,

    )

    db.add(run)

    db.commit()
    db.refresh(job)

    ply_path = os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project.id}.ply")
    mesh_path = os.path.join(settings.RECONSTRUCTION_DIR, f"mesh_{project.id}.ply")
    dsm_path = os.path.join(settings.RECONSTRUCTION_DIR, f"dsm_{project.id}.tif")

    image_paths = [img.file_path for img in images]

    try:
        res = photogrammetry_service.reconstruct_3d_pointcloud(
            image_paths=image_paths,
            output_ply_path=ply_path,
            output_mesh_path=mesh_path,
            output_dsm_path=dsm_path,
        )
    except ReconstructionInputError as exc:
        # Insufficient/invalid input. No artifacts and no Reconstruction3D row.
        job.status = "failed"
        job.progress_pct = 0
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_reconstruction_detail("invalid_input", exc),
        ) from exc
    except ReconstructionUnavailable as exc:
        job.status = "failed"
        job.progress_pct = 0
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_reconstruction_detail("unavailable", exc),
        ) from exc
    except ReconstructionFailed as exc:
        job.status = "failed"
        job.progress_pct = 0
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_reconstruction_detail("failed", exc),
        ) from exc
    except Exception as exc:
        job.status = "failed"
        job.progress_pct = 0
        job.error_message = f"3D reconstruction failed: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"3D reconstruction failed: {exc}",
        ) from exc

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
            bounds_json=json.dumps(res["bounds"]) if res["bounds"] else None,
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
        recon_record.bounds_json = json.dumps(res["bounds"]) if res["bounds"] else None

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
        backend=res.get("backend"),
        status=res.get("status", "completed"),
        georeferenced=res.get("georeferenced"),
        mesh_unavailable_reason=res.get("mesh_unavailable_reason"),
        dsm_unavailable_reason=res.get("dsm_unavailable_reason"),
        created_at=recon_record.created_at,
    )


@router.get("/3d/{project_id}", response_model=ReconstructionResponse)
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
            parsed = json.loads(recon.bounds_json)
            if isinstance(parsed, dict) and "min_x" in parsed and "max_z" in parsed:
                bounds = parsed
        except Exception:
            bounds = None

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
        status="completed",
        created_at=recon.created_at,
    )
