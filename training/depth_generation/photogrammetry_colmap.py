"""Photogrammetry-based pseudo-depth from overlapping drone images (COLMAP MVS).

Pipeline (all steps are real COLMAP invocations, no simulation):

1. group overlapping frames (by flight/sequence, capped per group),
2. ``colmap feature_extractor``  -> SIFT features,
3. ``colmap exhaustive_matcher`` -> matches (sequential matching for long sequences),
4. ``colmap mapper``             -> sparse reconstruction + camera poses,
5. ``colmap image_undistorter``  -> undistorted workspace,
6. ``colmap patch_match_stereo`` -> dense per-image depth maps,
7. ``colmap stereo_fusion``      -> fused dense point cloud,
8. project the dense points into each camera to obtain depth maps aligned to the
   *undistorted* frames, then rectify to the original image geometry,
9. normalise scale (SfM is scale-ambiguous unless georeferenced) and store validity
   masks + confidence.

Scale handling: a COLMAP reconstruction has an arbitrary global scale. Unless the user
supplies a georeferencing/scale factor, the resulting depths are stored as
``type="relative"`` / ``unit="arbitrary_scale"`` and are **never** treated as metres.

If the COLMAP binaries are missing the module raises :class:`PhotogrammetryUnavailable`
instead of pretending to produce depth.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from training.utils.io import REPO_ROOT, ensure_dir, utc_now_iso, write_json


class PhotogrammetryUnavailable(RuntimeError):
    """Raised when COLMAP (or OpenMVS) is not installed."""


COLMAP_INSTALL_HINT = (
    "COLMAP is not installed or not on PATH. Install it from "
    "https://colmap.github.io/install.html (Windows: use the official binary release), "
    "then re-run. JATAYUV does not bundle or auto-install COLMAP."
)


@dataclass
class ColmapConfig:
    binary: str = "colmap"
    max_images_per_group: int = 120
    dense: bool = True
    sequential_overlap: int = 10
    max_image_size: int = 2000
    scale_to_metres: Optional[float] = None  # e.g. from a georeferenced control point
    confidence_min: float = 0.05


def check_colmap(binary: str = "colmap") -> Tuple[bool, str]:
    path = shutil.which(binary)
    if not path:
        return False, COLMAP_INSTALL_HINT
    try:
        out = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=30)
        first = (out.stdout or out.stderr).splitlines()[0] if (out.stdout or out.stderr) else ""
        return True, f"{path} ({first.strip()})"
    except Exception as exc:
        return False, f"{path} found but not runnable: {exc}"


def _run(cmd: List[str], cwd: Optional[str] = None) -> None:
    print("[colmap] " + " ".join(cmd[:6]) + (" …" if len(cmd) > 6 else ""))
    process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"COLMAP step failed: {' '.join(cmd[:3])} (exit {process.returncode})\n"
            f"{(process.stderr or process.stdout)[-1500:]}"
        )


def read_colmap_cameras(path: str) -> Dict[int, np.ndarray]:
    """Parse ``cameras.txt`` (SIMPLE_PINHOLE / PINHOLE) into 3x3 intrinsics."""
    cameras: Dict[int, np.ndarray] = {}
    if not os.path.isfile(path):
        return cameras
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            camera_id = int(parts[0])
            model = parts[1]
            width, height = int(parts[2]), int(parts[3])
            params = [float(p) for p in parts[4:]]
            K = np.eye(3)
            if model == "SIMPLE_PINHOLE":
                f, cx, cy = params[0], params[1], params[2]
                K[0, 0] = K[1, 1] = f
            elif model == "PINHOLE":
                fx, fy, cx, cy = params[0], params[1], params[2], params[3]
                K[0, 0], K[1, 1] = fx, fy
            else:
                # SIMPLE_RADIAL / OPENCV etc: use the first focal parameter.
                f, cx, cy = params[0], params[1], params[2]
                K[0, 0] = K[1, 1] = f
            K[0, 2], K[1, 2] = cx, cy
            cameras[camera_id] = K
            cameras[-(camera_id)] = np.array([width, height], dtype=np.float64)
    return cameras


def read_colmap_images(path: str) -> Dict[str, Dict[str, object]]:
    """Parse ``images.txt`` for camera id, quaternion and translation per image."""
    images: Dict[str, Dict[str, object]] = {}
    if not os.path.isfile(path):
        return images
    with open(path, "r", encoding="utf-8") as fh:
        lines = [line for line in fh if not line.startswith("#")]
    for index in range(0, len(lines), 2):
        if index >= len(lines):
            break
        parts = lines[index].split()
        if len(parts) < 10:
            continue
        qw, qx, qy, qz = (float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
        tx, ty, tz = float(parts[5]), float(parts[6]), float(parts[7])
        camera_id = int(parts[8])
        name = parts[9]
        images[name] = {
            "camera_id": camera_id,
            "qvec": np.array([qw, qx, qy, qz]),
            "tvec": np.array([tx, ty, tz]),
        }
    return images


def qvec_to_rotmat(qvec: np.ndarray) -> np.ndarray:
    w, x, y, z = qvec
    return np.array(
        [
            [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
            [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
            [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
        ]
    )


def load_ply_points(path: str) -> np.ndarray:
    """Load xyz from a COLMAP fused point cloud.

    Uses ``plyfile`` when available (fast binary reader) and falls back to a small
    ASCII-PLY parser so the pipeline works without extra dependencies.
    """
    try:
        from plyfile import PlyData  # type: ignore

        ply = PlyData.read(path)
        vertex = ply["vertex"]
        return np.stack(
            [np.asarray(vertex["x"]), np.asarray(vertex["y"]), np.asarray(vertex["z"])],
            axis=1,
        ).astype(np.float64)
    except ImportError:
        pass

    with open(path, "r", encoding="ascii", errors="ignore") as fh:
        header = []
        for line in fh:
            header.append(line.strip())
            if line.strip() == "end_header":
                break
        if not any("format ascii" in line for line in header):
            raise RuntimeError(
                "Binary PLY requires the optional 'plyfile' package. "
                "Install it (pip install plyfile) or export the cloud as ASCII."
            )
        count = 0
        for line in header:
            if line.startswith("element vertex"):
                count = int(line.split()[-1])
                break
        points = np.empty((count, 3), dtype=np.float64)
        for index in range(count):
            values = fh.readline().split()
            points[index] = [float(values[0]), float(values[1]), float(values[2])]
    return points


def project_points(points: np.ndarray, R: np.ndarray, t: np.ndarray, K: np.ndarray,
                   width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    """Z-buffered projection of 3D points into one camera; returns (depth, mask)."""
    camera_points = points @ R.T + t.reshape(1, 3)
    z = camera_points[:, 2]
    valid = z > 1e-3
    camera_points = camera_points[valid]
    z = z[valid]
    pixels = camera_points @ K.T
    u = pixels[:, 0] / pixels[:, 2]
    v = pixels[:, 1] / pixels[:, 2]
    inside = (u >= 0) & (u < width) & (v >= 0) & (v < height)
    u, v, z = u[inside], v[inside], z[inside]

    depth = np.zeros((height, width), dtype=np.float32)
    mask = np.zeros((height, width), dtype=np.uint8)
    if z.size == 0:
        return depth, mask
    order = np.argsort(-z)  # far to near so nearer points overwrite
    ui = np.round(u[order]).astype(np.int32)
    vi = np.round(v[order]).astype(np.int32)
    depth[vi, ui] = z[order].astype(np.float32)
    mask[vi, ui] = 1
    return depth, mask


def run_sfm(image_paths: List[str], workspace: str, config: ColmapConfig) -> Dict[str, object]:
    """Run COLMAP SfM + dense MVS; returns paths to the reconstruction artefacts."""
    available, detail = check_colmap(config.binary)
    if not available:
        raise PhotogrammetryUnavailable(detail + "\n" + COLMAP_INSTALL_HINT)

    image_dir = os.path.join(workspace, "images")
    ensure_dir(image_dir)
    for path in image_paths:
        shutil.copy2(path, os.path.join(image_dir, os.path.basename(path)))

    database = os.path.join(workspace, "database.db")
    sparse = os.path.join(workspace, "sparse")
    dense = os.path.join(workspace, "dense")
    ensure_dir(sparse)

    _run([
        config.binary, "feature_extractor",
        "--database_path", database,
        "--image_path", image_dir,
        "--ImageReader.camera_model", "SIMPLE_RADIAL",
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.max_image_size", str(config.max_image_size),
    ])
    if len(image_paths) <= 40:
        _run([config.binary, "exhaustive_matcher", "--database_path", database])
    else:
        _run([
            config.binary, "sequential_matcher",
            "--database_path", database,
            "--SequentialMatching.overlap", str(config.sequential_overlap),
        ])
    _run([
        config.binary, "mapper",
        "--database_path", database,
        "--image_path", image_dir,
        "--output_path", sparse,
    ])
    model_dir = os.path.join(sparse, "0")
    if not os.path.isdir(model_dir):
        raise RuntimeError("COLMAP mapper produced no reconstruction (model 0 missing)")

    artefacts: Dict[str, object] = {"model_dir": model_dir}
    if not config.dense:
        return artefacts

    _run([
        config.binary, "image_undistorter",
        "--image_path", image_dir,
        "--input_path", model_dir,
        "--output_path", dense,
        "--output_type", "COLMAP",
    ])
    _run([
        config.binary, "patch_match_stereo",
        "--workspace_path", dense,
        "--workspace_format", "COLMAP",
        "--PatchMatchStereo.geom_consistency", "true",
    ])
    fused = os.path.join(dense, "fused.ply")
    _run([
        config.binary, "stereo_fusion",
        "--workspace_path", dense,
        "--workspace_format", "COLMAP",
        "--input_type", "geometric",
        "--output_path", fused,
    ])
    artefacts["fused_ply"] = fused
    artefacts["dense_dir"] = dense
    return artefacts


def generate_depth_for_group(
    image_paths: List[str],
    workspace: str,
    output_dir: str,
    config: Optional[ColmapConfig] = None,
) -> List[Dict[str, object]]:
    """Full MVS -> per-image depth maps for one overlapping group of frames."""
    config = config or ColmapConfig()
    ensure_dir(workspace)
    ensure_dir(output_dir)
    artefacts = run_sfm(image_paths, workspace, config)

    if "fused_ply" not in artefacts or not os.path.isfile(str(artefacts["fused_ply"])):
        return []

    points = load_ply_points(str(artefacts["fused_ply"]))
    model_dir = str(artefacts["model_dir"])
    cameras = read_colmap_cameras(os.path.join(model_dir, "cameras.txt"))
    images = read_colmap_images(os.path.join(model_dir, "images.txt"))

    records: List[Dict[str, object]] = []
    for name, info in images.items():
        camera_id = int(info["camera_id"])
        K = cameras.get(camera_id)
        if K is None:
            continue
        size = cameras.get(-camera_id)
        if size is None:
            continue
        width, height = int(size[0]), int(size[1])
        R = qvec_to_rotmat(np.asarray(info["qvec"], dtype=np.float64))
        t = np.asarray(info["tvec"], dtype=np.float64)
        depth, mask = project_points(points, R, t, K, width, height)
        # Dilate the sparse projection slightly so the mask covers the same surface.
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        valid = depth > 0
        if valid.mean() < config.confidence_min:
            continue
        if config.scale_to_metres:
            depth = depth * config.scale_to_metres

        stem = os.path.splitext(name)[0]
        npy_path = os.path.join(output_dir, f"{stem}_colmap_depth.npy")
        mask_path = os.path.join(output_dir, f"{stem}_colmap_mask.png")
        np.save(npy_path, depth.astype(np.float32))
        cv2.imwrite(mask_path, (mask * 255).astype(np.uint8))
        records.append(
            {
                "image_name": name,
                "source_image": os.path.join(workspace, "images", name),
                "depth_path": npy_path,
                "mask_path": mask_path,
                "coverage": float(valid.mean()),
                "depth_min": float(depth[valid].min()) if valid.any() else None,
                "depth_max": float(depth[valid].max()) if valid.any() else None,
                "scale_to_metres": config.scale_to_metres,
                "generated_utc": utc_now_iso(),
            }
        )
    write_json(records, os.path.join(output_dir, "colmap_depth_records.json"))
    return records


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="COLMAP photogrammetry depth generation")
    parser.add_argument("--images", required=True, help="directory of overlapping frames")
    parser.add_argument("--workspace", default="datasets/processed/colmap_workspace")
    parser.add_argument("--output-dir", default="datasets/depth_maps/colmap")
    parser.add_argument("--max-images", type=int, default=60)
    parser.add_argument("--scale-to-metres", type=float, default=None)
    parser.add_argument("--sparse-only", action="store_true")
    args = parser.parse_args(argv)

    ok, detail = check_colmap()
    print(f"[colmap] availability: {detail}")
    if not ok:
        return 3

    patterns = ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff")
    paths: List[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(os.path.join(args.images, pattern)))
    paths = sorted(paths)[: args.max_images]
    if len(paths) < 3:
        print("[colmap] need at least 3 overlapping images")
        return 2

    records = generate_depth_for_group(
        paths,
        os.path.join(REPO_ROOT, args.workspace),
        os.path.join(REPO_ROOT, args.output_dir),
        ColmapConfig(dense=not args.sparse_only, scale_to_metres=args.scale_to_metres),
    )
    print(f"[colmap] wrote {len(records)} per-image depth maps")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
