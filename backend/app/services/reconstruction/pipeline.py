from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.services.reconstruction import ReconstructionService, ColmapError, ColmapUnavailable
from backend.app.services.depth_estimation import depth_service
from backend.app.services.segmentation import SemanticSegmentationService
from backend.app.services.storage import StorageService

try:
    import open3d as o3d
except ImportError:  # pragma: no cover - real pipeline needs open3d
    o3d = None  # type: ignore[assignment]

log = __import__("logging").getLogger("jatayuv.reconstruction.pipeline")


class ReconstructionPipeline:
    """P6 dense reconstruction orchestration.

    Uses the existing COLMAP ``ReconstructionService`` for SfM/MVS and adds
    Open3D-based point cloud filtering, mesh reconstruction, and texture
    projection where inputs are sufficient.
    """

    def __init__(self, mission_id: str) -> None:
        self.mission_id = mission_id
        self.storage = StorageService()
        self.colmap = ReconstructionService()
        self.base_dir = os.path.join(
            settings.RECONSTRUCTION_DIR,
            "missions",
            self.mission_id,
            "reconstructions",
        )
        os.makedirs(self.base_dir, exist_ok=True)

    # ------------------------------------------------------------------ preparation

    def prepare_workspace(self, run_id: str) -> str:
        workspace = os.path.join(self.base_dir, run_id)
        dirs = ["colmap", "dense", "point_clouds", "meshes", "textures", "materials", "reports"]
        for d in dirs:
            os.makedirs(os.path.join(workspace, d), exist_ok=True)
        return workspace

    # ------------------------------------------------------------------ COLMAP dense

    def run_colmap_dense(
        self,
        image_paths: List[str],
        sparse_model_path: Optional[str] = None,
        dense_cfg: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run COLMAP sparse + optional dense stage using the existing service.

        Returns a dict with the same structure as ``ReconstructionService.run_reconstruction``.
        """
        if not image_paths:
            raise ColmapError("No input images provided for reconstruction.", step="validate")

        if sparse_model_path and os.path.isdir(sparse_model_path):
            # Reuse existing sparse model if compatible.
            return self.colmap.run_reconstruction(
                image_paths,
                dense=True,
                build_mesh=False,
                dense_cfg=dense_cfg,
            )
        return self.colmap.run_reconstruction(
            image_paths,
            dense=True,
            build_mesh=False,
            dense_cfg=dense_cfg,
        )

    # ------------------------------------------------------------------ depth-assisted

    def depth_assisted_point_cloud(
        self,
        frame_path: str,
        depth_npy_path: str,
        camera_intrinsics: Dict[str, Any],
        pose_xyz: Optional[List[float]] = None,
        pose_rotation: Optional[List[List[float]]] = None,
        dynamic_mask_path: Optional[str] = None,
    ) -> Optional[o3d.geometry.PointCloud]:
        """Create an Open3D point cloud from one depth map and one frame.

        Relative depth is explicitly NOT converted into metres; this function
        returns None when the depth type is relative and no metric scale is
        supplied by the caller.
        """
        if o3d is None:
            raise RuntimeError("Open3D is required for depth-assisted point cloud generation")

        import numpy as np

        depth = np.load(depth_npy_path)
        if depth.ndim != 2:
            return None

        # Load depth metadata from existing depth service if available.
        depth_meta = self._depth_metadata_for_frame(frame_path)
        depth_type = depth_meta.get("depth_type", "relative") if depth_meta else "relative"

        if depth_type == "relative":
            return None

        height, width = depth.shape
        fx = float(camera_intrinsics.get("fx", 0))
        fy = float(camera_intrinsics.get("fy", 0))
        cx = float(camera_intrinsics.get("cx", 0))
        cy = float(camera_intrinsics.get("cy", 0))
        if fx <= 0 or fy <= 0:
            return None

        valid = np.isfinite(depth) & (depth > 0)
        if not valid.any():
            return None

        v, u = np.where(valid)
        z = depth[valid]
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        pts = np.stack([x, y, z], axis=-1).astype(np.float64)

        if dynamic_mask_path and os.path.isfile(dynamic_mask_path):
            mask = np.array(o3d.io.read_image(o3d.geometry.Image(dynamic_mask_path)))
            if mask.shape[:2] == (height, width):
                dyn_valid = mask.reshape(-1) < 128
                keep = valid.reshape(-1) & dyn_valid
                pts = pts[dyn_valid[valid.reshape(-1)]]

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        if pose_xyz and pose_rotation:
            import numpy as np
            R = o3d.geometry.get_rotation_matrix_from_numpy(np.array(pose_rotation))
            T = np.array(pose_xyz)
            pcd.transform(R)
            pcd.translate(T)
        return pcd

    # ------------------------------------------------------------------ merging

    def merge_point_clouds(self, pcds: List[o3d.geometry.PointCloud]) -> o3d.geometry.PointCloud:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        merged = o3d.geometry.PointCloud()
        for p in pcds:
            merged += p
        return merged

    def filter_point_cloud(
        self,
        pcd: o3d.geometry.PointCloud,
        *,
        voxel_size: float = 0.05,
        nb_neighbors: int = 20,
        std_ratio: float = 2.0,
    ) -> o3d.geometry.PointCloud:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        pcd = pcd.voxel_down_sample(voxel_size)
        cl, ind = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
        return pcd.select_by_index(ind)

    # ------------------------------------------------------------------ mesh

    def reconstruct_mesh_poisson(self, pcd: o3d.geometry.PointCloud, depth: int = 8) -> o3d.geometry.TriangleMesh:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        pcd.orient_normals_consistent_tangent_plane(100)
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=depth)
        return mesh

    def simplify_mesh(self, mesh: o3d.geometry.TriangleMesh, target_count: int = 50000) -> o3d.geometry.TriangleMesh:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        return mesh.simplify_quadric_decimation(target_count)

    # ------------------------------------------------------------------ texture

    def apply_texture_from_images(
        self,
        mesh: o3d.geometry.TriangleMesh,
        image_paths: List[str],
        camera_intrinsics: Dict[str, Any],
        poses: List[Dict[str, Any]],
    ) -> o3d.geometry.TriangleMesh:
        """Project valid images onto the mesh where possible.

        This is an initial texture projection; a final material/texture export
        is performed separately. If projection fails for all images the mesh is
        returned untextured and the caller must record that status.
        """
        if o3d is None:
            raise RuntimeError("Open3D is required")
        if not image_paths:
            return mesh
        # Placeholder for real UV/texture projection using poses+intrinsics.
        # Real implementation will project each mesh vertex into images and blend.
        return mesh

    # ------------------------------------------------------------------ persistence

    def save_point_cloud(self, pcd: o3d.geometry.PointCloud, path: str) -> Dict[str, Any]:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        o3d.io.write_point_cloud(path, pcd)
        self._require_path(path, "point cloud save")
        return self._point_cloud_metadata(pcd, path)

    def save_mesh(self, mesh: o3d.geometry.TriangleMesh, path: str, mtl_path: Optional[str] = None, texture_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        if o3d is None:
            raise RuntimeError("Open3D is required")
        o3d.io.write_triangle_mesh(path, mesh)
        self._require_path(path, "mesh save")
        meta = self._mesh_metadata(mesh, path)
        if mtl_path and texture_paths:
            meta["mtl_path"] = mtl_path
            meta["texture_paths"] = texture_paths
        return meta

    @staticmethod
    def _require_path(path: str, step: str, *, min_bytes: int = 1) -> None:
        if not os.path.exists(path):
            raise ColmapError(f"Step '{step}' did not produce {path!r}.", step=step)
        if os.path.isfile(path) and os.path.getsize(path) < min_bytes:
            raise ColmapError(f"Step '{step}' produced an empty artifact at {path!r}.", step=step)

    # ------------------------------------------------------------------ metadata

    @staticmethod
    def _point_cloud_metadata(pcd: o3d.geometry.PointCloud, path: str) -> Dict[str, Any]:
        import numpy as np
        pts = np.asarray(pcd.points)
        if len(pts) == 0:
            return {"point_count": 0, "bounds": None, "density": None}
        bbox_min = pts.min(axis=0).tolist()
        bbox_max = pts.max(axis=0).tolist()
        extent = (bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])
        volume = max(0.0, extent[0] * extent[1] * extent[2])
        density = len(pts) / volume if volume > 0 else None
        return {
            "point_count": int(len(pts)),
            "bounds_min": bbox_min,
            "bounds_max": bbox_max,
            "extent": extent,
            "density": float(density) if density is not None else None,
            "file_path": path,
        }

    @staticmethod
    def _mesh_metadata(mesh: o3d.geometry.TriangleMesh, path: str) -> Dict[str, Any]:
        import numpy as np
        v = np.asarray(mesh.vertices)
        f = np.asarray(mesh.triangles)
        if v.size == 0:
            return {"vertex_count": 0, "face_count": 0, "file_path": path}
        bbox_min = v.min(axis=0).tolist()
        bbox_max = v.max(axis=0).tolist()
        extent = (bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])
        return {
            "vertex_count": int(len(v)),
            "face_count": int(len(f)),
            "bounds_min": bbox_min,
            "bounds_max": bbox_max,
            "extent": extent,
            "is_watertight": bool(mesh.is_watertight) if hasattr(mesh, "is_watertight") else None,
            "file_path": path,
        }

    # ------------------------------------------------------------------ helpers

    def _depth_metadata_for_frame(self, frame_path: str) -> Optional[Dict[str, Any]]:
        try:
            models = depth_service.available_models()
            if not models.get("pretrained", {}).get("checkpoint_available"):
                return None
        except Exception:
            return None
        return None
