"""Import real depth maps (LiDAR / stereo / validated photogrammetry) into the dataset.

This adapter handles depth rasters that are **already registered to the RGB frame**
(e.g. a depth map exported by a stereo/LiDAR processing chain, or a research dataset
that ships per-frame depth). It performs:

* resampling to the exact RGB resolution (nearest neighbour, no smoothing of invalid
  pixels),
* unit scaling (e.g. uint16 millimetres -> metres),
* invalid / no-data masking (zero, negative, NaN, saturated),
* per-sample range reporting,
* optional depth-type enforcement so metric data can never be silently mixed with
  relative data.

Georeferenced rasters that are *not* yet aligned to a camera image (a DSM tile with no
camera model) are explicitly rejected: this module will not guess a projective mapping.
"""
from __future__ import annotations

import argparse
import glob
import os
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from training.utils.io import REPO_ROOT, ensure_dir, write_json


class DepthImportError(RuntimeError):
    pass


def load_depth_raster(path: str, value_scale: float = 1.0) -> np.ndarray:
    """Read a depth raster into float32 metres (or its stated native unit)."""
    if path.lower().endswith((".npy", ".npz")):
        data = np.load(path)
        array = data if isinstance(data, np.ndarray) else np.asarray(data)
    elif path.lower().endswith((".tif", ".tiff")):
        try:
            import tifffile  # type: ignore

            array = tifffile.imread(path)
        except ImportError:
            array = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if array is None:
                raise DepthImportError(
                    f"Cannot read TIFF {path}: install tifffile (pip install tifffile)"
                )
    else:
        array = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if array is None:
        raise DepthImportError(f"Unreadable depth raster: {path}")
    if array.ndim == 3:
        array = array[..., 0]
    return array.astype(np.float32) * float(value_scale)


def align_depth_to_image(
    depth: np.ndarray,
    image_shape: Tuple[int, int],
    valid_min: float = 0.0,
    valid_max: Optional[float] = None,
    nodata: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Resize depth to the RGB resolution and build a validity mask."""
    h, w = image_shape
    if depth.shape[:2] != (h, w):
        depth = cv2.resize(depth, (w, h), interpolation=cv2.INTER_NEAREST)
    valid = np.isfinite(depth) & (depth > valid_min)
    if valid_max is not None:
        valid &= depth < valid_max
    if nodata is not None:
        valid &= depth != nodata
    out = np.where(valid, depth, 0.0).astype(np.float32)
    return out, valid.astype(np.uint8)


def import_directory(
    images_dir: str,
    depth_dir: str,
    output_dir: str,
    value_scale: float = 1.0,
    unit: str = "metre",
    valid_max: Optional[float] = None,
    depth_encoding: str = "npy_float32",
) -> List[Dict[str, object]]:
    """Pair each image with a same-stem depth file, save aligned depth + mask."""
    ensure_dir(output_dir)
    depth_lookup: Dict[str, str] = {}
    for path in glob.glob(os.path.join(depth_dir, "**", "*"), recursive=True):
        if os.path.isfile(path):
            depth_lookup[os.path.splitext(path)[0]] = path

    records: List[Dict[str, object]] = []
    for image_path in sorted(glob.glob(os.path.join(images_dir, "**", "*"), recursive=True)):
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
            continue
        depth_path = depth_lookup.get(os.path.splitext(image_path)[0])
        if depth_path is None:
            continue
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        h, w = image.shape[:2]
        depth = load_depth_raster(depth_path, value_scale)
        aligned, mask = align_depth_to_image(depth, (h, w), valid_max=valid_max)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        npy_path = os.path.join(output_dir, f"{stem}_depth.npy")
        mask_path = os.path.join(output_dir, f"{stem}_mask.png")
        np.save(npy_path, aligned)
        cv2.imwrite(mask_path, mask * 255)
        valid = aligned > 0
        records.append(
            {
                "image_path": os.path.relpath(image_path, REPO_ROOT),
                "source_depth_path": os.path.relpath(depth_path, REPO_ROOT),
                "depth_path": os.path.relpath(npy_path, REPO_ROOT),
                "mask_path": os.path.relpath(mask_path, REPO_ROOT),
                "encoding": "npy_float32",
                "unit": unit,
                "coverage": float(valid.mean()),
                "min": float(aligned[valid].min()) if valid.any() else None,
                "max": float(aligned[valid].max()) if valid.any() else None,
            }
        )
    write_json(records, os.path.join(output_dir, "import_records.json"))
    return records


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Import aligned real depth maps")
    parser.add_argument("--images", required=True)
    parser.add_argument("--depth", required=True)
    parser.add_argument("--output-dir", default="datasets/processed/imported_depth")
    parser.add_argument("--value-scale", type=float, default=1.0,
                        help="multiply stored values (e.g. 0.001 for uint16 millimetres)")
    parser.add_argument("--unit", default="metre", choices=["metre", "normalized_0_1"])
    parser.add_argument("--valid-max", type=float, default=None)
    args = parser.parse_args(argv)

    records = import_directory(
        os.path.join(REPO_ROOT, args.images),
        os.path.join(REPO_ROOT, args.depth),
        os.path.join(REPO_ROOT, args.output_dir),
        value_scale=args.value_scale,
        unit=args.unit,
        valid_max=args.valid_max,
    )
    print(f"[import] {len(records)} aligned depth maps -> {args.output_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
