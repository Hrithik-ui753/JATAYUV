import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.image import Image
from backend.app.models.project import Project
from backend.app.models.job import Job
from backend.app.models.reconstruction import Reconstruction3D
from backend.app.models.user import User
from backend.app.schemas.reconstruction import ReconstructionTriggerRequest, ReconstructionResponse
from backend.app.services.photogrammetry import photogrammetry_service
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(prefix="/reconstruction", tags=["3D Photogrammetry"])

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

    if not images:
        raise HTTPException(
            status_code=400,
            detail="Cannot run 3D reconstruction on project with no uploaded aerial images",
        )

    job = Job(
        project_id=project.id,
        job_type="reconstruction_3d",
        status="processing",
        progress_pct=15,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    ply_path = os.path.join(settings.RECONSTRUCTION_DIR, f"pointcloud_{project.id}.ply")
    mesh_path = os.path.join(settings.RECONSTRUCTION_DIR, f"mesh_{project.id}.obj")
    dsm_path = os.path.join(settings.RECONSTRUCTION_DIR, f"dsm_{project.id}.tif")

    image_paths = [img.file_path for img in images]
    res = photogrammetry_service.reconstruct_3d_pointcloud(
        image_paths=image_paths,
        output_ply_path=ply_path,
        output_mesh_path=mesh_path,
        output_dsm_path=dsm_path,
    )

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

