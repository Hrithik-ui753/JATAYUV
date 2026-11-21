import os
import json
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db, db as scoped_db
from backend.app.models.image import Image
from backend.app.models.frame import Frame
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
        # Check if frames were extracted for any video belonging to this mission/project
        mission = db.query(Mission).filter(Mission.project_id == project.id).first()
        if mission:
            frames = db.query(Frame).filter(Frame.mission_id == mission.id).all()
            for f in frames:
                if f.storage_path and os.path.isfile(f.storage_path):
                    existing = (
                        db.query(Image)
                        .filter(Image.project_id == project.id, Image.file_path == f.storage_path)
                        .first()
                    )
                    if not existing:
                        img = Image(
                            id=str(uuid.uuid4()),
                            project_id=project.id,
                            filename=f"frame_{f.frame_index:04d}.jpg",
                            file_path=f.storage_path,
                            thumbnail_path=f.storage_path,
                            file_size_bytes=os.path.getsize(f.storage_path),
                            width=f.width or 1920,
                            height=f.height or 1080,
                            format="JPEG",
                        )
                        db.add(img)
            db.commit()
            images = db.query(Image).filter(Image.project_id == project.id).all()

        # If still no images, auto-extract keyframes across the complete uploaded drone video
        if not images:
            from backend.app.models.video import Video
            import cv2

            video = None
            if mission:
                video = (
                    db.query(Video)
                    .filter(Video.mission_id == mission.id)
                    .order_by(Video.created_at.desc())
                    .first()
                )
            if video and video.storage_path and os.path.isfile(video.storage_path):
                out_dir = os.path.join(settings.UPLOAD_DIR, "extracted_frames", project.id)
                os.makedirs(out_dir, exist_ok=True)
                cap = cv2.VideoCapture(video.storage_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

                target_count = 24
                if total_frames > 0:
                    step = max(1, total_frames // target_count)
                    sampled_indices = [i for i in range(0, total_frames, step)][:target_count]
                else:
                    sampled_indices = [0]

                for f_idx in sampled_indices:
                    # Select sharpest frame around f_idx to reject motion blur
                    best_img = None
                    best_blur = -1.0
                    best_f_idx = f_idx
                    candidate_offsets = [0, 1, -1, 2, -2]
                    for offset in candidate_offsets:
                        cand_idx = max(0, min(total_frames - 1, f_idx + offset))
                        cap.set(cv2.CAP_PROP_POS_FRAMES, cand_idx)
                        r, cand_img = cap.read()
                        if r and cand_img is not None:
                            gray = cv2.cvtColor(cand_img, cv2.COLOR_BGR2GRAY)
                            score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                            if score > best_blur:
                                best_blur = score
                                best_img = cand_img
                                best_f_idx = cand_idx
                            if score > 50.0:  # Sufficiently sharp
                                break

                    if best_img is not None:
                        frame_filename = f"frame_{best_f_idx:05d}.jpg"
                        frame_path = os.path.join(out_dir, frame_filename)
                        cv2.imwrite(frame_path, best_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

                        img = Image(
                            id=str(uuid.uuid4()),
                            project_id=project.id,
                            filename=frame_filename,
                            file_path=frame_path,
                            thumbnail_path=frame_path,
                            file_size_bytes=os.path.getsize(frame_path),
                            width=width,
                            height=height,
                            format="JPEG",
                        )
                        db.add(img)

                        if mission:
                            frm = Frame(
                                id=str(uuid.uuid4()),
                                mission_id=mission.id,
                                video_id=video.id,
                                frame_index=best_f_idx,
                                presentation_timestamp=best_f_idx / fps,
                                timestamp_seconds=best_f_idx / fps,
                                storage_path=frame_path,
                                width=width,
                                height=height,
                                quality_status="valid" if best_blur >= 30.0 else "blurry",
                                is_selected=True,
                            )
                            db.add(frm)
                cap.release()
                db.commit()
                images = db.query(Image).filter(Image.project_id == project.id).all()

    if not images:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "invalid_input",
                "message": (
                    "No aerial images found for this mission. Please upload at least 2 aerial images, "
                    "or upload a drone video and click 'Process Video' to extract frames before running 3D reconstruction."
                ),
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

    companion_telemetry = None
    mission = db.query(Mission).filter(Mission.project_id == project.id).first()
    if mission:
        from backend.app.models.video import Video
        vid = db.query(Video).filter(Video.mission_id == mission.id).order_by(Video.created_at.desc()).first()
        if vid and vid.storage_path:
            v_dir = os.path.dirname(vid.storage_path)
            v_base = os.path.splitext(os.path.basename(vid.storage_path))[0]
            candidates = [
                os.path.join(v_dir, f"{v_base}_telemetry.csv"),
                os.path.join(v_dir, f"{v_base.split('_')[0]}_telemetry.csv"),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    companion_telemetry = c
                    break

    try:
        res = photogrammetry_service.reconstruct_3d_pointcloud(
            image_paths=image_paths,
            output_ply_path=ply_path,
            output_mesh_path=mesh_path,
            output_dsm_path=dsm_path,
            telemetry_path=companion_telemetry,
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
        backend="colmap_dpt",
        status="completed",
        georeferenced=res.get("georeferenced", False),
        vertex_count=res.get("vertex_count"),
        face_count=res.get("face_count"),
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
    georef = False
    v_count = None
    f_count = None
    if recon.bounds_json:
        try:
            bounds = json.loads(recon.bounds_json)
            georef = bounds.get("georeferenced", False)
            v_count = bounds.get("vertex_count")
            f_count = bounds.get("face_count")
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
        backend="colmap_dpt",
        status="completed",
        georeferenced=georef,
        vertex_count=v_count,
        face_count=f_count,
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


