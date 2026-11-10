<<<<<<< HEAD
"""COLMAP photogrammetry runner.

P0 integrity contract
---------------------
* Every external command is validated (executable found, arguments present, exit
  status checked) before its output is trusted.
* The dense stage follows the documented COLMAP order:
  ``image_undistorter`` -> ``patch_match_stereo`` -> ``stereo_fusion``.
* Reconstruction statistics (point count, camera count, mean reprojection error)
  are parsed from COLMAP's own ``model_analyzer`` output. If they cannot be
  determined the run fails; no placeholder accuracy value is ever written.
* If COLMAP is not installed the service raises :class:`ColmapUnavailable`.
* This module has not been executed against a real COLMAP install in this
  environment; it makes no claim that reconstruction works until it is run with
  real overlapping imagery.
"""
from __future__ import annotations

=======
<<<<<<< HEAD
import os
import subprocess
>>>>>>> origin/main
import json
import os
import re
import shutil
import subprocess
import uuid
from typing import Any, Dict, List, Optional

from ..core.config import settings
from ..workers.celery_app import celery_app


class ColmapError(RuntimeError):
    """Raised when a COLMAP step fails or produces an invalid/absent artifact."""

    status = "failed"

    def __init__(self, message: str, *, step: Optional[str] = None, log_tail: str = "") -> None:
        super().__init__(message)
        self.step = step
        self.log_tail = log_tail


class ColmapUnavailable(ColmapError):
    """Raised when no COLMAP executable can be located."""

    status = "unavailable"


# COLMAP needs at least two registered images to triangulate anything.
MIN_IMAGES = 2


def _tail(text: str, limit: int = 1500) -> str:
    text = (text or "").strip()
    return text[-limit:] if len(text) > limit else text


def _parse_model_analyzer(output: str) -> Dict[str, Any]:
    """Extract real reconstruction statistics from ``colmap model_analyzer`` output."""
    def _int(pattern: str) -> Optional[int]:
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            return None
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return None

    points = _int(r"^\s*Points:\s*(\d+)\s*$")
    cameras = _int(r"^\s*Cameras:\s*(\d+)\s*$")
    registered = _int(r"^\s*Registered images:\s*(\d+)\s*$")

    error_match = re.search(
        r"Mean reprojection error:\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s*px",
        output,
        re.MULTILINE,
    )
    reprojection_error = float(error_match.group(1)) if error_match else None

    return {
        "num_points": points,
        "camera_count": cameras,
        "registered_images": registered,
        "reprojection_error_px": reprojection_error,
    }


class ReconstructionService:
    """Executes the COLMAP structure-from-motion / multi-view-stereo pipeline."""

    def __init__(self) -> None:
        self.colmap_exe = self._detect_colmap()
        self.base_workspace = settings.RECONSTRUCTION_DIR
        os.makedirs(self.base_workspace, exist_ok=True)

    # ------------------------------------------------------------- environment
    @staticmethod
    def _detect_colmap() -> Optional[str]:
        """Locate the COLMAP binary (``COLMAP_EXE`` env var, settings, .tools, then ``PATH``)."""
        configured = os.environ.get("COLMAP_EXE", "").strip()
        if configured:
            if os.path.isfile(configured):
                return configured
            found = shutil.which(configured)
            if found:
                return found
        if hasattr(settings, "COLMAP_EXE") and settings.COLMAP_EXE and os.path.isfile(settings.COLMAP_EXE):
            return settings.COLMAP_EXE
        found_path = shutil.which("colmap")
        if found_path:
            return found_path
        repo_tools = os.path.join(settings.BASE_DIR, ".tools", "colmap", "bin", "colmap.exe")
        if os.path.isfile(repo_tools):
            return repo_tools
        return None

    def executable_status(self) -> Dict[str, Any]:
        available = bool(self.colmap_exe)
        return {
            "backend": "colmap",
            "status": "available" if available else "unavailable",
            "executable": self.colmap_exe,
            "available": available,
            "min_images": MIN_IMAGES,
        }

    def _require_colmap(self) -> str:
        if not self.colmap_exe:
            raise ColmapUnavailable(
                "COLMAP executable not found. Install COLMAP and put it on PATH (or set "
                "COLMAP_EXE) to enable real 3D reconstruction. No synthetic geometry is "
                "produced in its absence.",
                step="detect",
            )
        if not (os.path.isfile(self.colmap_exe) or shutil.which(self.colmap_exe)):
            raise ColmapUnavailable(
                f"Configured COLMAP executable {self.colmap_exe!r} does not exist.",
                step="detect",
            )
        return self.colmap_exe

    # --------------------------------------------------------------- workspace
    def _prepare_workspace(self, image_paths: List[str]) -> str:
<<<<<<< HEAD
=======
        """Create a temporary COLMAP project directory and copy images.
        Returns the absolute path to the workspace.
        """
=======
"""COLMAP photogrammetry runner.

P0 integrity contract
---------------------
* Every external command is validated (executable found, arguments present, exit
  status checked) before its output is trusted.
* The dense stage follows the documented COLMAP order:
  ``image_undistorter`` -> ``patch_match_stereo`` -> ``stereo_fusion``.
* Reconstruction statistics (point count, camera count, mean reprojection error)
  are parsed from COLMAP's own ``model_analyzer`` output. If they cannot be
  determined the run fails; no placeholder accuracy value is ever written.
* If COLMAP is not installed the service raises :class:`ColmapUnavailable`.
* This module has not been executed against a real COLMAP install in this
  environment; it makes no claim that reconstruction works until it is run with
  real overlapping imagery.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from typing import Any, Dict, List, Optional

from ..core.config import settings
from ..workers.celery_app import celery_app


class ColmapError(RuntimeError):
    """Raised when a COLMAP step fails or produces an invalid/absent artifact."""

    status = "failed"

    def __init__(self, message: str, *, step: Optional[str] = None, log_tail: str = "") -> None:
        super().__init__(message)
        self.step = step
        self.log_tail = log_tail


class ColmapUnavailable(ColmapError):
    """Raised when no COLMAP executable can be located."""

    status = "unavailable"


# COLMAP needs at least two registered images to triangulate anything.
MIN_IMAGES = 2


def _tail(text: str, limit: int = 1500) -> str:
    text = (text or "").strip()
    return text[-limit:] if len(text) > limit else text


def _parse_model_analyzer(output: str) -> Dict[str, Any]:
    """Extract real reconstruction statistics from ``colmap model_analyzer`` output."""
    def _int(pattern: str) -> Optional[int]:
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            return None
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return None

    points = _int(r"^\s*Points:\s*(\d+)\s*$")
    cameras = _int(r"^\s*Cameras:\s*(\d+)\s*$")
    registered = _int(r"^\s*Registered images:\s*(\d+)\s*$")

    error_match = re.search(
        r"Mean reprojection error:\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s*px",
        output,
        re.MULTILINE,
    )
    reprojection_error = float(error_match.group(1)) if error_match else None

    return {
        "num_points": points,
        "camera_count": cameras,
        "registered_images": registered,
        "reprojection_error_px": reprojection_error,
    }


class ReconstructionService:
    """Executes the COLMAP structure-from-motion / multi-view-stereo pipeline."""

    def __init__(self) -> None:
        self.colmap_exe = self._detect_colmap()
        self.base_workspace = settings.RECONSTRUCTION_DIR
        os.makedirs(self.base_workspace, exist_ok=True)

    # ------------------------------------------------------------- environment
    @staticmethod
    def _detect_colmap() -> Optional[str]:
        """Locate the COLMAP binary (``COLMAP_EXE`` env var, then ``PATH``)."""
        configured = os.environ.get("COLMAP_EXE", "").strip()
        if configured:
            if os.path.isfile(configured):
                return configured
            found = shutil.which(configured)
            if found:
                return found
        return shutil.which("colmap")

    def executable_status(self) -> Dict[str, Any]:
        return {
            "backend": "colmap",
            "executable": self.colmap_exe,
            "available": bool(self.colmap_exe),
            "min_images": MIN_IMAGES,
        }

    def _require_colmap(self) -> str:
        if not self.colmap_exe:
            raise ColmapUnavailable(
                "COLMAP executable not found. Install COLMAP and put it on PATH (or set "
                "COLMAP_EXE) to enable real 3D reconstruction. No synthetic geometry is "
                "produced in its absence.",
                step="detect",
            )
        if not (os.path.isfile(self.colmap_exe) or shutil.which(self.colmap_exe)):
            raise ColmapUnavailable(
                f"Configured COLMAP executable {self.colmap_exe!r} does not exist.",
                step="detect",
            )
        return self.colmap_exe

    # --------------------------------------------------------------- workspace
    def _prepare_workspace(self, image_paths: List[str]) -> str:
>>>>>>> origin/main
        """Create an isolated COLMAP project directory and stage the images."""
        if len(image_paths) < MIN_IMAGES:
            raise ColmapError(
                f"COLMAP reconstruction requires at least {MIN_IMAGES} overlapping images "
                f"(received {len(image_paths)}).",
                step="validate",
            )
        for src in image_paths:
            if not os.path.isfile(src):
                raise ColmapError(
                    f"Input image not found: {src}", step="validate"
                )

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        workspace = os.path.join(self.base_workspace, f"colmap_{uuid.uuid4().hex}")
        os.makedirs(workspace, exist_ok=True)
        images_dir = os.path.join(workspace, "images")
        os.makedirs(images_dir, exist_ok=True)
        for src in image_paths:
            basename = os.path.basename(src)
            dst = os.path.join(images_dir, basename)
<<<<<<< HEAD
=======
<<<<<<< HEAD
            # Use a hard link when possible to avoid extra disk usage.
>>>>>>> origin/main
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
        return workspace

    # --------------------------------------------------------------- execution
    def _run(self, cmd: List[str], workspace: str, log_lines: List[str], step: str) -> subprocess.CompletedProcess:
        """Validate and execute one COLMAP command, failing loudly on error."""
        if not cmd or not all(isinstance(part, str) for part in cmd):
            raise ColmapError("Refusing to run an empty/invalid COLMAP command.", step=step)
        executable = cmd[0]
        if not (os.path.isfile(executable) or shutil.which(executable)):
            raise ColmapUnavailable(
                f"COLMAP executable {executable!r} is not available.", step=step
            )

        log_lines.append(f"[{step}] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, cwd=workspace, capture_output=True, text=True, check=False
            )
        except OSError as exc:
            raise ColmapError(
                f"Could not start COLMAP step '{step}': {exc}", step=step
            ) from exc

        log_lines.append(result.stdout or "")
        if result.stderr:
            log_lines.append(result.stderr)

        if result.returncode != 0:
            raise ColmapError(
                f"COLMAP step '{step}' failed with exit code {result.returncode}: "
                f"{_tail(result.stderr or result.stdout)}",
                step=step,
                log_tail=_tail(result.stderr or result.stdout),
            )
        return result

    @staticmethod
    def _require_path(path: str, step: str, *, min_bytes: int = 1) -> None:
        if not os.path.exists(path):
            raise ColmapError(
                f"COLMAP step '{step}' reported success but did not produce {path!r}.",
                step=step,
            )
        if os.path.isfile(path) and os.path.getsize(path) < min_bytes:
            raise ColmapError(
                f"COLMAP step '{step}' produced an empty artifact at {path!r}.", step=step
            )

    # -------------------------------------------------------------- full run
    def run_reconstruction(
        self,
        image_paths: List[str],
        *,
        dense: bool = True,
        build_mesh: bool = True,
        dense_cfg: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run COLMAP synchronously and return real artifacts and real statistics.

        Raises :class:`ColmapUnavailable` when COLMAP is missing and
        :class:`ColmapError` when any step fails or its output cannot be verified.
        """
        exe = self._require_colmap()
        workspace = self._prepare_workspace(image_paths)
        images_dir = os.path.join(workspace, "images")
        database = os.path.join(workspace, "database.db")
        sparse_dir = os.path.join(workspace, "sparse")
        sparse_model = os.path.join(sparse_dir, "0")
        dense_dir = os.path.join(workspace, "dense")
        log_lines: List[str] = []

        # 1. Feature extraction
        self._run(
            [exe, "feature_extractor", "--database_path", database, "--image_path", images_dir],
            workspace, log_lines, "feature_extractor",
        )
        self._require_path(database, "feature_extractor", min_bytes=1024)

        # 2. Feature matching
        self._run(
            [exe, "exhaustive_matcher", "--database_path", database],
            workspace, log_lines, "exhaustive_matcher",
        )

        # 3. Sparse reconstruction (incremental SfM)
        os.makedirs(sparse_dir, exist_ok=True)
        self._run(
            [
                exe, "mapper",
                "--database_path", database,
                "--image_path", images_dir,
                "--output_path", sparse_dir,
            ],
            workspace, log_lines, "mapper",
        )
        model_files = [
            name for name in ("cameras.bin", "images.bin", "points3D.bin")
            if os.path.isfile(os.path.join(sparse_model, name))
        ]
        if len(model_files) != 3:
            raise ColmapError(
                "COLMAP mapper did not produce a complete sparse model "
                f"(found {model_files or 'nothing'} in {sparse_model}). The images probably "
                "lack sufficient overlap or texture.",
                step="mapper",
            )

        # 4. Real statistics straight from COLMAP
        analyzer = self._run(
            [exe, "model_analyzer", "--path", sparse_model],
            workspace, log_lines, "model_analyzer",
        )
        stats = _parse_model_analyzer(analyzer.stdout or "")
        if stats["num_points"] is None or stats["camera_count"] is None:
            raise ColmapError(
                "Could not read point/camera counts from COLMAP model_analyzer output; "
                "refusing to report reconstruction statistics.",
                step="model_analyzer",
                log_tail=_tail(analyzer.stdout),
            )
        if stats["reprojection_error_px"] is None:
            raise ColmapError(
                "COLMAP did not report a mean reprojection error; no accuracy value will "
                "be invented.",
                step="model_analyzer",
                log_tail=_tail(analyzer.stdout),
            )
        if stats["num_points"] == 0:
            raise ColmapError(
                "COLMAP reconstructed zero 3D points; there is no point cloud to export.",
                step="mapper",
            )
        registered = stats["registered_images"]
        if registered is not None and registered < MIN_IMAGES:
            raise ColmapError(
                f"COLMAP registered only {registered} image(s); at least {MIN_IMAGES} are "
                "required for a triangulated reconstruction.",
                step="mapper",
            )

        # 5. Sparse cloud export (PLY, real COLMAP coordinates)
        sparse_ply = os.path.join(workspace, "sparse.ply")
        self._run(
            [
                exe, "model_converter",
                "--input_path", sparse_model,
                "--output_path", sparse_ply,
                "--output_type", "PLY",
            ],
            workspace, log_lines, "model_converter",
        )
        self._require_path(sparse_ply, "model_converter")

        result: Dict[str, Any] = {
            "status": "completed",
            "backend": "colmap",
            "backend_path": exe,
            "workspace": workspace,
            "sparse_model_path": sparse_model,
            "sparse_ply_path": sparse_ply,
            "pointcloud_ply_path": sparse_ply,
            "mesh_ply_path": None,
            "num_points": int(stats["num_points"]),
            "camera_count": int(stats["camera_count"]),
            "registered_images": registered,
            "reprojection_error_px": float(stats["reprojection_error_px"]),
            "georeferenced": False,
            "log": "\n".join(log_lines),
        }

<<<<<<< HEAD
=======
    def _store_results(self, db_session, job: Job, workspace: str, project_id: str) -> Reconstruction3D:
        """Persist paths of generated files into the DB and return the model instance."""
        pointcloud_path = os.path.join(workspace, "dense", "fused.ply")
        mesh_path = os.path.join(workspace, "dense", "mesh.ply")
        # Additional metadata could be collected here – for brevity we store a minimal JSON.
        metadata = {
            "workspace": workspace,
            "generated": datetime.now(timezone.utc).isoformat(),
        }
=======
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
        return workspace

    # --------------------------------------------------------------- execution
    def _run(self, cmd: List[str], workspace: str, log_lines: List[str], step: str) -> subprocess.CompletedProcess:
        """Validate and execute one COLMAP command, failing loudly on error."""
        if not cmd or not all(isinstance(part, str) for part in cmd):
            raise ColmapError("Refusing to run an empty/invalid COLMAP command.", step=step)
        executable = cmd[0]
        if not (os.path.isfile(executable) or shutil.which(executable)):
            raise ColmapUnavailable(
                f"COLMAP executable {executable!r} is not available.", step=step
            )

        log_lines.append(f"[{step}] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, cwd=workspace, capture_output=True, text=True, check=False
            )
        except OSError as exc:
            raise ColmapError(
                f"Could not start COLMAP step '{step}': {exc}", step=step
            ) from exc

        log_lines.append(result.stdout or "")
        if result.stderr:
            log_lines.append(result.stderr)

        if result.returncode != 0:
            raise ColmapError(
                f"COLMAP step '{step}' failed with exit code {result.returncode}: "
                f"{_tail(result.stderr or result.stdout)}",
                step=step,
                log_tail=_tail(result.stderr or result.stdout),
            )
        return result

    @staticmethod
    def _require_path(path: str, step: str, *, min_bytes: int = 1) -> None:
        if not os.path.exists(path):
            raise ColmapError(
                f"COLMAP step '{step}' reported success but did not produce {path!r}.",
                step=step,
            )
        if os.path.isfile(path) and os.path.getsize(path) < min_bytes:
            raise ColmapError(
                f"COLMAP step '{step}' produced an empty artifact at {path!r}.", step=step
            )

    # -------------------------------------------------------------- full run
    def run_reconstruction(
        self,
        image_paths: List[str],
        *,
        dense: bool = True,
        build_mesh: bool = True,
        dense_cfg: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run COLMAP synchronously and return real artifacts and real statistics.

        Raises :class:`ColmapUnavailable` when COLMAP is missing and
        :class:`ColmapError` when any step fails or its output cannot be verified.
        """
        exe = self._require_colmap()
        workspace = self._prepare_workspace(image_paths)
        images_dir = os.path.join(workspace, "images")
        database = os.path.join(workspace, "database.db")
        sparse_dir = os.path.join(workspace, "sparse")
        sparse_model = os.path.join(sparse_dir, "0")
        dense_dir = os.path.join(workspace, "dense")
        log_lines: List[str] = []

        # 1. Feature extraction
        self._run(
            [exe, "feature_extractor", "--database_path", database, "--image_path", images_dir],
            workspace, log_lines, "feature_extractor",
        )
        self._require_path(database, "feature_extractor", min_bytes=1024)

        # 2. Feature matching
        self._run(
            [exe, "exhaustive_matcher", "--database_path", database],
            workspace, log_lines, "exhaustive_matcher",
        )

        # 3. Sparse reconstruction (incremental SfM)
        os.makedirs(sparse_dir, exist_ok=True)
        self._run(
            [
                exe, "mapper",
                "--database_path", database,
                "--image_path", images_dir,
                "--output_path", sparse_dir,
            ],
            workspace, log_lines, "mapper",
        )
        model_files = [
            name for name in ("cameras.bin", "images.bin", "points3D.bin")
            if os.path.isfile(os.path.join(sparse_model, name))
        ]
        if len(model_files) != 3:
            raise ColmapError(
                "COLMAP mapper did not produce a complete sparse model "
                f"(found {model_files or 'nothing'} in {sparse_model}). The images probably "
                "lack sufficient overlap or texture.",
                step="mapper",
            )

        # 4. Real statistics straight from COLMAP
        analyzer = self._run(
            [exe, "model_analyzer", "--path", sparse_model],
            workspace, log_lines, "model_analyzer",
        )
        stats = _parse_model_analyzer(analyzer.stdout or "")
        if stats["num_points"] is None or stats["camera_count"] is None:
            raise ColmapError(
                "Could not read point/camera counts from COLMAP model_analyzer output; "
                "refusing to report reconstruction statistics.",
                step="model_analyzer",
                log_tail=_tail(analyzer.stdout),
            )
        if stats["reprojection_error_px"] is None:
            raise ColmapError(
                "COLMAP did not report a mean reprojection error; no accuracy value will "
                "be invented.",
                step="model_analyzer",
                log_tail=_tail(analyzer.stdout),
            )
        if stats["num_points"] == 0:
            raise ColmapError(
                "COLMAP reconstructed zero 3D points; there is no point cloud to export.",
                step="mapper",
            )
        registered = stats["registered_images"]
        if registered is not None and registered < MIN_IMAGES:
            raise ColmapError(
                f"COLMAP registered only {registered} image(s); at least {MIN_IMAGES} are "
                "required for a triangulated reconstruction.",
                step="mapper",
            )

        # 5. Sparse cloud export (PLY, real COLMAP coordinates)
        sparse_ply = os.path.join(workspace, "sparse.ply")
        self._run(
            [
                exe, "model_converter",
                "--input_path", sparse_model,
                "--output_path", sparse_ply,
                "--output_type", "PLY",
            ],
            workspace, log_lines, "model_converter",
        )
        self._require_path(sparse_ply, "model_converter")

        result: Dict[str, Any] = {
            "status": "completed",
            "backend": "colmap",
            "backend_path": exe,
            "workspace": workspace,
            "sparse_model_path": sparse_model,
            "sparse_ply_path": sparse_ply,
            "pointcloud_ply_path": sparse_ply,
            "mesh_ply_path": None,
            "num_points": int(stats["num_points"]),
            "camera_count": int(stats["camera_count"]),
            "registered_images": registered,
            "reprojection_error_px": float(stats["reprojection_error_px"]),
            "georeferenced": False,
            "log": "\n".join(log_lines),
        }

>>>>>>> origin/main
        # 6. Optional dense stage: undistort -> patch-match stereo -> fusion
        if dense:
            self._run(
                [
                    exe, "image_undistorter",
                    "--image_path", images_dir,
                    "--input_path", sparse_model,
                    "--output_path", dense_dir,
                    "--output_type", "COLMAP",
                ],
                workspace, log_lines, "image_undistorter",
            )
            self._require_path(os.path.join(dense_dir, "images"), "image_undistorter")

            stereo_cmd = [
                exe, "patch_match_stereo",
                "--workspace_path", dense_dir,
                "--workspace_format", "COLMAP",
                "--PatchMatchStereo.geom_consistency", "true",
            ]
            if dense_cfg:
                for key, value in dense_cfg.items():
                    stereo_cmd.extend([f"--{key}", str(value)])
            self._run(stereo_cmd, workspace, log_lines, "patch_match_stereo")

            fused_ply = os.path.join(dense_dir, "fused.ply")
            self._run(
                [
                    exe, "stereo_fusion",
                    "--workspace_path", dense_dir,
                    "--workspace_format", "COLMAP",
                    "--input_type", "geometric",
                    "--output_path", fused_ply,
                ],
                workspace, log_lines, "stereo_fusion",
            )
            self._require_path(fused_ply, "stereo_fusion", min_bytes=1024)
            result["dense_ply_path"] = fused_ply
            result["pointcloud_ply_path"] = fused_ply

            # 7. Optional Poisson mesh from the verified dense cloud
            if build_mesh:
                mesh_ply = os.path.join(dense_dir, "mesh.ply")
                self._run(
                    [
                        exe, "poisson_mesher",
                        "--input_path", fused_ply,
                        "--output_path", mesh_ply,
                    ],
                    workspace, log_lines, "poisson_mesher",
                )
                self._require_path(mesh_ply, "poisson_mesher", min_bytes=128)
                result["mesh_ply_path"] = mesh_ply

        result["log"] = "\n".join(log_lines)
        return result

    # ------------------------------------------------------------------- DB
    def _store_results(self, db_session, job, workspace: str, project_id: str, result: Dict[str, Any]):
        """Persist verified COLMAP artifacts and real statistics."""
        from ..models.reconstruction import Reconstruction3D

        pointcloud = result.get("pointcloud_ply_path")
        if not pointcloud or not os.path.isfile(pointcloud):
            raise ColmapError(
                "Refusing to store a reconstruction without a verified point cloud artifact.",
                step="store",
            )

        # Only the real cloud bounds are stored; no placeholder metadata is written into
        # the bounds column (it is part of the public API response).
        bounds = result.get("bounds")
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        rec = Reconstruction3D(
            id=str(uuid.uuid4()),
            project_id=project_id,
            job_id=job.id,
<<<<<<< HEAD
            pointcloud_ply_path=pointcloud,
            mesh_obj_path=result.get("mesh_ply_path"),
            dsm_tiff_path=None,
=======
<<<<<<< HEAD
            pointcloud_ply_path=pointcloud_path,
            mesh_obj_path=mesh_path,
            dsm_tiff_path=None,
            num_points=0,
            camera_count=0,
            reprojection_error_px=0.0,
            bounds_json=json.dumps(metadata),
=======
            pointcloud_ply_path=pointcloud,
            mesh_obj_path=result.get("mesh_ply_path"),
            dsm_tiff_path=None,
>>>>>>> origin/main
            num_points=int(result["num_points"]),
            camera_count=int(result["camera_count"]),
            reprojection_error_px=float(result["reprojection_error_px"]),
            bounds_json=json.dumps(bounds) if bounds else None,
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
        )
        db_session.add(rec)
        db_session.commit()
        db_session.refresh(rec)
        return rec

<<<<<<< HEAD
    # --------------------------------------------------------------- submission
=======
<<<<<<< HEAD
>>>>>>> origin/main
    def submit_reconstruction(self, image_ids: List[str], project_id: str, user_id: str) -> str:
        """Queue a Celery job that runs COLMAP on the supplied images."""
        from ..models.job import Job
        from ..core.database import SessionLocal

        db = SessionLocal()
        try:
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
            job_id = job.id
        finally:
            db.close()

        _run_reconstruction_task.delay(job_id, image_ids, project_id)
        return job_id


reconstruction_service = ReconstructionService()

<<<<<<< HEAD
=======
=======
    # --------------------------------------------------------------- submission
    def submit_reconstruction(self, image_ids: List[str], project_id: str, user_id: str) -> str:
        """Queue a Celery job that runs COLMAP on the supplied images."""
        from ..models.job import Job
        from ..core.database import SessionLocal

        db = SessionLocal()
        try:
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
            job_id = job.id
        finally:
            db.close()

        _run_reconstruction_task.delay(job_id, image_ids, project_id)
        return job_id


reconstruction_service = ReconstructionService()

>>>>>>> origin/main

@celery_app.task(bind=True, name="reconstruction.run")
def _run_reconstruction_task(self, job_id: str, image_ids: List[str], project_id: str):
    """Celery entry point. Only marks a job completed after verified artifacts exist."""
    from ..models.job import Job
    from ..models.image import Image
    from ..core.database import SessionLocal

    db = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job is None:
            return {"status": "failed", "reason": f"Job {job_id} not found"}
        job.status = "processing"
        job.progress_pct = 10
        db.commit()

        images = db.query(Image).filter(Image.id.in_(image_ids)).all()
        image_paths = [img.file_path for img in images]
        service = ReconstructionService()
        service._require_colmap()

        job.progress_pct = 25
        db.commit()

        result = service.run_reconstruction(image_paths)

        job.progress_pct = 85
        db.commit()

        service._store_results(db, job, result["workspace"], project_id, result)
        job.status = "completed"
        job.progress_pct = 100
        job.error_message = None
        db.commit()
        return {"status": "completed", "num_points": result["num_points"]}
    except Exception as exc:
        if job is not None:
            job.status = "failed"
            job.progress_pct = 0
            job.error_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
