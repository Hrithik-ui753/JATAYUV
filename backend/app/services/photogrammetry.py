"""Photogrammetry / structure-from-motion facade.

P0 integrity contract
---------------------
* Reconstruction is performed by the COLMAP backend only. There is no procedural
  terrain, no sinusoidal relief, no brightness-as-elevation, no camera pose derived
  from a frame index and no hardcoded reprojection error.
* If COLMAP is unavailable the service raises :class:`ReconstructionUnavailable`;
  if it fails, :class:`ReconstructionFailed`; if the request is invalid,
  :class:`ReconstructionInputError`. No PLY, mesh or DSM artifact is written in any
  of those cases.
* ``num_points``, ``camera_count``, ``bounds`` and ``reprojection_error_px`` all
  come from the executed reconstruction (PLY contents and COLMAP's own
  ``model_analyzer`` output). Nothing is defaulted or invented.
* COLMAP output is in arbitrary reconstruction units and is not georeferenced, so
  no DSM is produced. ``dsm_tiff_path`` stays ``None`` with an explicit reason.
"""
from __future__ import annotations

import os
import shutil
import struct
from typing import Any, Dict, List, Optional

import cv2

from .reconstruction import (
    MIN_IMAGES,
    ColmapError,
    ColmapUnavailable,
    reconstruction_service,
)


class ReconstructionError(RuntimeError):
    """Base error for a reconstruction that did not produce verified geometry."""

    status = "failed"
    reason = "reconstruction_failed"

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}


class ReconstructionInputError(ReconstructionError):
    """Invalid or insufficient input imagery."""

    status = "invalid_input"
    reason = "invalid_input"


class ReconstructionUnavailable(ReconstructionError):
    """No reconstruction backend is installed/available."""

    status = "unavailable"
    reason = "backend_unavailable"


class ReconstructionFailed(ReconstructionError):
    """The reconstruction backend ran but did not produce verified geometry."""

    status = "failed"
    reason = "reconstruction_failed"


# --------------------------------------------------------------------------- PLY
_PLY_TYPES = {
    "char": "b", "int8": "b",
    "uchar": "B", "uint8": "B",
    "short": "h", "int16": "h",
    "ushort": "H", "uint16": "H",
    "int": "i", "int32": "i",
    "uint": "I", "uint32": "I",
    "float": "f", "float32": "f",
    "double": "d", "float64": "d",
}


def inspect_ply(path: str) -> Dict[str, Any]:
    """Validate a PLY file and return its real vertex count and bounds.

    Supports ``ascii`` and ``binary_little_endian`` / ``binary_big_endian`` vertex
    elements. Raises ``ValueError`` for anything that is not a usable point cloud.
    """
    if not path or not os.path.isfile(path):
        raise ValueError(f"PLY file not found: {path}")
    if os.path.getsize(path) == 0:
        raise ValueError(f"PLY file is empty: {path}")

    with open(path, "rb") as fh:
        header_lines: List[str] = []
        while True:
            raw = fh.readline()
            if not raw:
                raise ValueError("PLY header is truncated (missing end_header)")
            line = raw.decode("ascii", errors="replace").strip()
            header_lines.append(line)
            if len(header_lines) > 1000:
                raise ValueError("PLY header is unreasonably long")
            if line == "end_header":
                break
        body_offset = fh.tell()

    if not header_lines or header_lines[0] != "ply":
        raise ValueError("File is not a PLY (missing 'ply' magic header)")

    fmt = ""
    elements: List[Dict[str, Any]] = []
    for line in header_lines[1:]:
        if line.startswith("format "):
            fmt = line.split()[1]
        elif line.startswith("element "):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Malformed PLY element line: {line!r}")
            elements.append({"name": parts[1], "count": int(parts[2]), "properties": []})
        elif line.startswith("property "):
            if not elements:
                raise ValueError("PLY property declared before any element")
            parts = line.split()
            if parts[1] == "list":
                elements[-1]["properties"].append(
                    {"name": parts[-1], "type": "list", "count_type": parts[2], "item_type": parts[3]}
                )
            else:
                elements[-1]["properties"].append({"name": parts[-1], "type": parts[1]})

    if fmt not in ("ascii", "binary_little_endian", "binary_big_endian"):
        raise ValueError(f"Unsupported PLY format: {fmt!r}")

    vertex_el: Optional[Dict[str, Any]] = None
    vertex_index = None
    for idx, element in enumerate(elements):
        if element["name"] == "vertex":
            vertex_el = element
            vertex_index = idx
            break
    if vertex_el is None:
        raise ValueError("PLY has no vertex element")
    num_vertices = int(vertex_el["count"])
    if num_vertices <= 0:
        raise ValueError("PLY contains zero vertices")

    prop_names = [p["name"] for p in vertex_el["properties"] if p["type"] != "list"]
    if not all(axis in prop_names for axis in ("x", "y", "z")):
        raise ValueError("PLY vertex element does not declare x/y/z properties")

    bounds: Optional[Dict[str, float]] = None
    if vertex_index == 0:
        try:
            if fmt == "ascii":
                bounds = _ascii_ply_bounds(path, body_offset, num_vertices, prop_names)
            else:
                bounds = _binary_ply_bounds(
                    path, body_offset, num_vertices, vertex_el["properties"], fmt
                )
        except (ValueError, struct.error, OSError):
            bounds = None

    return {
        "format": fmt,
        "num_vertices": num_vertices,
        "bounds": bounds,
        "properties": prop_names,
    }


def _ply_axis_indices(prop_names: List[str]) -> tuple[int, int, int]:
    return prop_names.index("x"), prop_names.index("y"), prop_names.index("z")


def _ascii_ply_bounds(
    path: str, body_offset: int, num_vertices: int, prop_names: List[str]
) -> Dict[str, float]:
    ix, iy, iz = _ply_axis_indices(prop_names)
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    with open(path, "r", encoding="ascii", errors="replace") as fh:
        fh.seek(body_offset)
        read = 0
        for line in fh:
            parts = line.split()
            if len(parts) <= max(ix, iy, iz):
                continue
            try:
                values = (float(parts[ix]), float(parts[iy]), float(parts[iz]))
            except ValueError:
                continue
            for axis, value in enumerate(values):
                mins[axis] = min(mins[axis], value)
                maxs[axis] = max(maxs[axis], value)
            read += 1
            if read >= num_vertices:
                break
    if read == 0:
        raise ValueError("PLY contains no readable vertices")
    return {
        "min_x": round(mins[0], 4), "max_x": round(maxs[0], 4),
        "min_y": round(mins[1], 4), "max_y": round(maxs[1], 4),
        "min_z": round(mins[2], 4), "max_z": round(maxs[2], 4),
    }


def _binary_ply_bounds(
    path: str,
    body_offset: int,
    num_vertices: int,
    properties: List[Dict[str, Any]],
    fmt: str,
) -> Dict[str, float]:
    if any(p["type"] == "list" for p in properties):
        raise ValueError("List properties in the vertex element are not supported")
    endian = "<" if fmt == "binary_little_endian" else ">"
    try:
        struct_fmt = endian + "".join(_PLY_TYPES[p["type"]] for p in properties)
    except KeyError as exc:
        raise ValueError(f"Unsupported PLY property type: {exc}") from exc
    names = [p["name"] for p in properties]
    ix, iy, iz = names.index("x"), names.index("y"), names.index("z")
    stride = struct.calcsize(struct_fmt)

    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    read = 0
    with open(path, "rb") as fh:
        fh.seek(body_offset)
        for _ in range(num_vertices):
            record = fh.read(stride)
            if len(record) < stride:
                break
            values = struct.unpack(struct_fmt, record)
            for axis, index in enumerate((ix, iy, iz)):
                value = float(values[index])
                mins[axis] = min(mins[axis], value)
                maxs[axis] = max(maxs[axis], value)
            read += 1
    if read == 0:
        raise ValueError("PLY binary body is empty or truncated")
    return {
        "min_x": round(mins[0], 4), "max_x": round(maxs[0], 4),
        "min_y": round(mins[1], 4), "max_y": round(maxs[1], 4),
        "min_z": round(mins[2], 4), "max_z": round(maxs[2], 4),
    }


# ---------------------------------------------------------------------- service
class PhotogrammetryService:
    """Validated entry point for 3D reconstruction."""

    def validate_inputs(self, image_paths: List[str]) -> List[str]:
        """Validate supplied imagery; returns the usable absolute paths."""
        if not image_paths:
            raise ReconstructionInputError(
                "3D reconstruction requires at least "
                f"{MIN_IMAGES} overlapping aerial images; none were supplied."
            )
        paths = [os.path.abspath(p) for p in image_paths if p]
        if len(paths) < MIN_IMAGES:
            raise ReconstructionInputError(
                f"3D reconstruction requires at least {MIN_IMAGES} overlapping aerial "
                f"images; only {len(paths)} were supplied. No synthetic geometry is "
                "generated for insufficient input."
            )
        missing = [p for p in paths if not os.path.isfile(p)]
        if missing:
            raise ReconstructionInputError(
                f"{len(missing)} input image(s) are missing on disk: {missing[:3]}"
            )
        unreadable = []
        for path in paths:
            # Cheap decode check so COLMAP is never handed non-images.
            if cv2.imread(path, cv2.IMREAD_REDUCED_COLOR_8) is None:
                unreadable.append(path)
        if unreadable:
            raise ReconstructionInputError(
                f"{len(unreadable)} input file(s) are not readable images: {unreadable[:3]}"
            )
        return paths

    def reconstruct_3d_pointcloud(
        self,
        image_paths: List[str],
        output_ply_path: str,
        output_mesh_path: str = None,
        output_dsm_path: str = None,
    ) -> Dict[str, Any]:
        """Run a real COLMAP reconstruction and materialise verified artifacts.

        Raises a :class:`ReconstructionError` subclass instead of ever returning
        synthetic geometry.
        """
        paths = self.validate_inputs(image_paths)

        try:
            result = reconstruction_service.run_reconstruction(paths, dense=True, build_mesh=True)
        except ColmapUnavailable as exc:
            raise ReconstructionUnavailable(
                str(exc), details={"backend": "colmap", "step": exc.step}
            ) from exc
        except ColmapError as exc:
            raise ReconstructionFailed(
                str(exc), details={"backend": "colmap", "step": exc.step, "log_tail": exc.log_tail}
            ) from exc

        source_ply = result.get("pointcloud_ply_path")
        if not source_ply or not os.path.isfile(source_ply):
            raise ReconstructionFailed(
                "Reconstruction completed without a point cloud artifact.",
                details={"backend": "colmap"},
            )

        os.makedirs(os.path.dirname(os.path.abspath(output_ply_path)), exist_ok=True)
        shutil.copy2(source_ply, output_ply_path)

        try:
            cloud = inspect_ply(output_ply_path)
        except ValueError as exc:
            # Never leave an unreadable artifact behind for clients to render.
            try:
                os.remove(output_ply_path)
            except OSError:
                pass
            raise ReconstructionFailed(
                f"Reconstructed point cloud could not be validated: {exc}",
                details={"backend": "colmap"},
            ) from exc

        mesh_path: Optional[str] = None
        mesh_reason: Optional[str] = None
        mesh_source = result.get("mesh_ply_path")
        if output_mesh_path and mesh_source and os.path.isfile(mesh_source):
            if os.path.splitext(output_mesh_path)[1].lower() == ".ply":
                os.makedirs(os.path.dirname(os.path.abspath(output_mesh_path)), exist_ok=True)
                shutil.copy2(mesh_source, output_mesh_path)
                mesh_path = output_mesh_path
            else:
                mesh_reason = (
                    "COLMAP produced a PLY mesh; no OBJ conversion is attempted, so the "
                    "requested OBJ path was not written."
                )
        elif output_mesh_path:
            mesh_reason = "The reconstruction did not produce a mesh."

        dsm_reason = None
        if output_dsm_path:
            dsm_reason = (
                "A DSM requires georeferenced elevation. COLMAP output is in arbitrary "
                "reconstruction units, so no DSM was generated."
            )

        log = result.get("log") or ""
        return {
            "status": "completed",
            "backend": result.get("backend", "colmap"),
            "georeferenced": False,
            "units": "colmap_arbitrary_units",
            "pointcloud_ply_path": output_ply_path,
            "mesh_obj_path": mesh_path,
            "mesh_unavailable_reason": mesh_reason,
            "dsm_tiff_path": None,
            "dsm_unavailable_reason": dsm_reason,
            "num_points": int(cloud["num_vertices"]),
            "sparse_point_count": int(result["num_points"]),
            "camera_count": int(result["camera_count"]),
            "registered_images": result.get("registered_images"),
            "reprojection_error_px": float(result["reprojection_error_px"]),
            "bounds": cloud["bounds"],
            "workspace": result.get("workspace"),
            "log_tail": log[-2000:],
        }


photogrammetry_service = PhotogrammetryService()
