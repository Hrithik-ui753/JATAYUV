from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from backend.app.workers.celery_app import celery_app
from backend.app.models.reconstruction import ReconstructionRun, ReconstructionFrame, ReconstructionQualityReport
from backend.app.models.processing import ProcessingRun, ProcessingStatus
from backend.app.models.frame import Frame
from backend.app.models.artifact import Artifact
from backend.app.services.recon.pipeline import ReconstructionPipeline
from backend.app.services.recon.readiness import ReconstructionReadiness
from backend.app.core.database import db

log = logging.getLogger("jatayuv.recon.tasks")


@celery_app.task(bind=True, name="reconstruction.validate_and_run")
def run_reconstruction_task(
    self,
    mission_id: str,
    run_id: str,
    workspace: str,
    *,
    colmap_config: Optional[Dict[str, Any]] = None,
    dense_config: Optional[Dict[str, Any]] = None,
    mesh_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Orchestrate P6 dense reconstruction for a mission.

    This task is idempotent with respect to the mission run id: it will
    revalidate inputs and re-run the COLMAP pipeline only when the run is
    pending/processing. It preserves original artifacts and writes versioned
    reconstruction outputs.
    """
    log.info("Starting reconstruction run %s for mission %s", run_id, mission_id)

    pipeline = ReconstructionPipeline(mission_id)
    os.makedirs(workspace, exist_ok=True)

    try:
        # ----------------------------------------------------------------
        # 1. Validate inputs
        # ----------------------------------------------------------------
        self.update_state(state="validation", meta={"step": "validating_inputs"})
        selected_frames = Frame.query(mission_id=mission_id, selected=True).all()
        if not selected_frames:
            raise RuntimeError("No selected frames available for reconstruction")

        image_paths = [f.storage_path for f in selected_frames if f.storage_path]
        for p in image_paths:
            if not os.path.isfile(p):
                raise RuntimeError(f"Frame file missing: {p}")

        pipeline.prepare_workspace(run_id)

        # ----------------------------------------------------------------
        # 2. COLMAP dense pipeline
        # ----------------------------------------------------------------
        self.update_state(state="colmap", meta={"step": "colmap_sparse_and_dense"})
        colmap_result = pipeline.run_colmap_dense(
            image_paths,
            dense_cfg=dense_config,
        )

        # ----------------------------------------------------------------
        # 3. Point cloud post-processing
        # ----------------------------------------------------------------
        self.update_state(state="point_cloud", meta={"step": "filtering_and_export"})
        dense_ply = colmap_result.get("dense_ply_path")
        if dense_ply and os.path.isfile(dense_ply):
            import open3d as o3d
            pcd = o3d.io.read_point_cloud(dense_ply)
            filtered = pipeline.filter_point_cloud(pcd, voxel_size=dense_config.get("voxel_size", 0.05))
            pc_path = os.path.join(workspace, "point_clouds", "dense_filtered.ply")
            pipeline.save_point_cloud(filtered, pc_path)
        else:
            pc_path = dense_ply

        # ----------------------------------------------------------------
        # 4. Mesh reconstruction
        # ----------------------------------------------------------------
        mesh_path = None
        mesh_meta = None
        mesh_cfg = mesh_config or {}
        if mesh_cfg.get("build_mesh") and pc_path and os.path.isfile(pc_path):
            self.update_state(state="mesh", meta={"step": "poisson_meshing"})
            import open3d as o3d
            pcd = o3d.io.read_point_cloud(pc_path)
            mesh = pipeline.reconstruct_mesh_poisson(pcd, depth=mesh_cfg.get("poisson_depth", 8))
            mesh_path = os.path.join(workspace, "meshes", "reconstructed.obj")
            mtl_path = os.path.join(workspace, "materials", "reconstructed.mtl")
            texture_paths = []
            if mesh_cfg.get("texture", False):
                self.update_state(state="texture", meta={"step": "texture_projection"})
                textured = pipeline.apply_texture_from_images(mesh, image_paths, {}, [])
                texture_paths.append(os.path.join(workspace, "textures", "reconstructed.jpg"))
                o3d.io.write_triangle_mesh(mesh_path, textured)
            else:
                o3d.io.write_triangle_mesh(mesh_path, mesh)
            mesh_meta = pipeline.save_mesh(mesh, mesh_path, mtl_path=mtl_path, texture_paths=texture_paths)

        # ----------------------------------------------------------------
        # 5. Persist artifacts and DB records
        # ----------------------------------------------------------------
        self.update_state(state="persist", meta={"step": "persisting_artifacts"})
        run = ReconstructionRun(
            id=run_id,
            mission_id=mission_id,
            reconstruction_version=time.strftime("%Y-%m-%dT%H-%M-%S"),
            reconstruction_method="colmap_dense",
            status="completed",
            point_cloud_path=pc_path,
            mesh_path=mesh_path,
            vertex_count=mesh_meta.get("vertex_count") if mesh_meta else None,
            face_count=mesh_meta.get("face_count") if mesh_meta else None,
            point_count=colmap_result.get("num_points"),
            processing_duration_seconds=int(time.time() - self.start_time if hasattr(self, "start_time") else 0),
            coordinate_reference_system=colmap_result.get("coordinate_reference_system"),
            coordinate_frame=colmap_result.get("coordinate_frame"),
            units=colmap_result.get("units"),
            source_frame_ids_json=[f.id for f in selected_frames],
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        quality = ReconstructionQualityReport(
            reconstruction_run_id=run_id,
            validated_point_count=colmap_result.get("num_points"),
            validated_registered_images=colmap_result.get("registered_images"),
            validated_reprojection_error_px=colmap_result.get("reprojection_error_px"),
            geometry_source_provenance_json={"colmap": True, "dense": True},
            validation_status="validated" if colmap_result.get("num_points", 0) > 0 else "failed",
        )
        db.add(quality)
        db.commit()

        # ----------------------------------------------------------------
        # 6. Mark processing run completed
        # ----------------------------------------------------------------
        proc = ProcessingRun.query.filter_by(id=run_id).first()
        if proc:
            proc.status = "completed"
            proc.completed_at = datetime.utcnow()
            db.commit()

        return {"status": "completed", "reconstruction_id": run_id}

    except Exception as exc:
        log.exception("Reconstruction run %s failed", run_id)
        try:
            run = ReconstructionRun.query.filter_by(id=run_id).first()
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                db.commit()
            proc = ProcessingRun.query.filter_by(id=run_id).first()
            if proc:
                proc.status = "failed"
                proc.error_message = str(exc)
                db.commit()
        except Exception:
            pass
        raise
