import os
import subprocess
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from ..core.config import settings
from ..core.celery_app import celery_app
from ..models.reconstruction import Reconstruction3D
from ..models.job import Job
from ..models.image import Image
from ..core.database import get_db

class ReconstructionService:
    """Service to execute a COLMAP 3D reconstruction pipeline.
    The heavy lifting is performed in a Celery background task to avoid
    blocking the FastAPI request/response cycle.
    """

    def __init__(self):
        self.colmap_exe = "colmap"  # Assumes COLMAP is on PATH.
        self.base_workspace = settings.RECONSTRUCTION_DIR
        os.makedirs(self.base_workspace, exist_ok=True)

    def _prepare_workspace(self, image_paths: List[str]) -> str:
        """Create a temporary COLMAP project directory and copy images.
        Returns the absolute path to the workspace.
        """
        workspace = os.path.join(self.base_workspace, f"colmap_{uuid.uuid4().hex}")
        os.makedirs(workspace, exist_ok=True)
        images_dir = os.path.join(workspace, "images")
        os.makedirs(images_dir, exist_ok=True)
        for src in image_paths:
            basename = os.path.basename(src)
            dst = os.path.join(images_dir, basename)
            # Use a hard link when possible to avoid extra disk usage.
            try:
                os.link(src, dst)
            except OSError:
                # Fallback to copy if hard link fails.
                import shutil
                shutil.copy2(src, dst)
        return workspace

    def _run_colmap(self, workspace: str, sparse: bool = True, dense: bool = True, dense_cfg: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute COLMAP commands sequentially.
        Returns a dictionary with paths to generated artifacts and logs.
        """
        log_lines = []
        def _run(cmd: List[str]):
            log_lines.append(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True)
            log_lines.append(result.stdout)
            log_lines.append(result.stderr)
            result.check_returncode()
            return result

        # 1. Feature extraction
        _run([self.colmap_exe, "feature_extractor", "--database_path", "database.db", "--image_path", "images"])
        # 2. Feature matching
        _run([self.colmap_exe, "exhaustive_matcher", "--database_path", "database.db"])
        # 3. Sparse reconstruction (SfM)
        if sparse:
            _run([self.colmap_exe, "mapper", "--database_path", "database.db", "--image_path", "images", "--output_path", "sparse"])
        # 4. Dense reconstruction (optional)
        if dense:
            # Undistort images
            _run([self.colmap_exe, "image_undistorter", "--image_path", "images", "--input_path", "sparse/0", "--output_path", "dense"])
            # Stereo
            stereo_cmd = [self.colmap_exe, "stereo_fusion", "--workspace_path", "dense", "--output_path", "dense/fused.ply"]
            if dense_cfg:
                for k, v in dense_cfg.items():
                    stereo_cmd.extend([f"--{k}", str(v)])
            _run(stereo_cmd)
        # Export mesh (optional)
        _run([self.colmap_exe, "model_converter", "--input_path", "sparse/0", "--output_path", "model", "--output_type", "PLY"])
        # Mesh from dense point cloud
        _run([self.colmap_exe, "poisson_mesher", "--input_path", "dense/fused.ply", "--output_path", "dense/mesh.ply"])

        return {
            "workspace": workspace,
            "log": "\n".join(log_lines),
        }

    def _store_results(self, db_session, job: Job, workspace: str, project_id: str) -> Reconstruction3D:
        """Persist paths of generated files into the DB and return the model instance."""
        pointcloud_path = os.path.join(workspace, "dense", "fused.ply")
        mesh_path = os.path.join(workspace, "dense", "mesh.ply")
        # Additional metadata could be collected here – for brevity we store a minimal JSON.
        metadata = {
            "workspace": workspace,
            "generated": datetime.now(timezone.utc).isoformat(),
        }
        rec = Reconstruction3D(
            id=str(uuid.uuid4()),
            project_id=project_id,
            job_id=job.id,
            pointcloud_ply_path=pointcloud_path,
            mesh_obj_path=mesh_path,
            dsm_tiff_path=None,
            num_points=0,
            camera_count=0,
            reprojection_error_px=0.0,
            bounds_json=json.dumps(metadata),
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)
        return rec

    def submit_reconstruction(self, image_ids: List[str], project_id: str, user_id: str) -> str:
        """Create a Celery job that runs COLMAP on the supplied images.
        Returns the created Job.id for tracking.
        """
        from ..models.job import Job  # Local import to avoid circular deps.
        from ..core.database import SessionLocal
        db = SessionLocal()
        job = Job(
            project_id=project_id,
            job_type="3d_reconstruction",
            status="queued",
            progress_pct=0,
            owner_id=user_id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        # Kick off Celery task.
        _run_reconstruction_task.delay(job.id, image_ids, project_id)
        db.close()
        return job.id

# Celery task definition.
@celery_app.task(bind=True, name="reconstruction.run")
def _run_reconstruction_task(self, job_id: str, image_ids: List[str], project_id: str):
    from ..models.job import Job
    from ..core.database import SessionLocal
    from ..models.image import Image
    db: SessionLocal = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = "processing"
        job.progress_pct = 10
        db.commit()
        # Resolve image file paths.
        images = db.query(Image).filter(Image.id.in_(image_ids)).all()
        image_paths = [img.file_path for img in images]
        service = ReconstructionService()
        workspace = service._prepare_workspace(image_paths)
        job.progress_pct = 30
        db.commit()
        # Run COLMAP (may raise subprocess.CalledProcessError).
        result = service._run_colmap(workspace)
        job.progress_pct = 80
        db.commit()
        # Store results.
        rec = service._store_results(db, job, workspace, project_id)
        job.status = "completed"
        job.progress_pct = 100
        db.commit()
    except Exception as exc:
        job.status = "failed"
        job.progress_pct = 0
        job.error_message = str(exc)
        db.commit()
        raise
    finally:
        db.close()

reconstruction_service = ReconstructionService()

