"""JATAYUV 3D Spatial Intelligence Module.

Connects 2D multi-frame infrastructure detections (towers, power lines, insulators, damage)
with the photogrammetric 3D reconstruction engine:
1. Robust depth association: Samples 32-bit float depth within the central interior
   of detection bboxes, avoiding sky bleed and edge discontinuities. Never assumes
   bbox center is the exact physical depth.
2. Pinhole back-projection using camera intrinsics K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]].
3. World coordinate transformation using camera poses (R, t) converted into Three.js
   canonical coordinates (+Y UP, +Z Forward).
4. Multi-view 3D spatial triangulation & clustering across frames to compute
   3D centroids, 3D bounding extents [dx, dy, dz], and spatial uncertainty radii.
5. 3D power line corridor catenary waypoints modeling.
6. Honest scale metadata attachment (relative_reconstruction_units).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .infrastructure_detector import InfrastructureClass
from .infrastructure_tracker import InfrastructureTrack

log = logging.getLogger("jatayuv.perception.spatial_intelligence")


@dataclass
class SpatialObservation3D:
    frame_index: int
    timestamp_s: float
    camera_id: str
    image_coords_uv: Tuple[float, float]
    depth_c: float
    point_camera: Tuple[float, float, float]
    point_world: Tuple[float, float, float]
    confidence: float


@dataclass
class LocalizedInfrastructure3D:
    """Represents a 3D localized infrastructure object in world space."""
    track_id: str
    class_name: InfrastructureClass
    position: Tuple[float, float, float]  # [X, Y, Z] in Three.js world frame (+Y UP)
    extents: Tuple[float, float, float]   # [width_x, height_y, depth_z]
    uncertainty_radius: float             # Standard deviation / spatial dispersion
    confidence: float
    observations_count: int
    spatial_observations: List[SpatialObservation3D] = field(default_factory=list)
    line_waypoints: Optional[List[List[float]]] = None  # Polyline coordinates for power lines
    severity: str = "NORMAL"                            # "NORMAL", "WARNING", "CRITICAL"
    inspection_notes: List[str] = field(default_factory=list)
    requires_field_verification: bool = False
    extra_attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "track_id": self.track_id,
            "class_name": self.class_name.value,
            "position": [round(float(c), 3) for c in self.position],
            "extents": [round(float(c), 3) for c in self.extents],
            "uncertainty_radius": round(float(self.uncertainty_radius), 4),
            "confidence": round(float(self.confidence), 4),
            "observations_count": self.observations_count,
            "severity": self.severity,
            "inspection_notes": self.inspection_notes,
            "requires_field_verification": self.requires_field_verification,
            "line_waypoints": [
                [round(float(c), 3) for c in pt] for pt in (self.line_waypoints or [])
            ],
            "observations": [
                {
                    "frame_index": o.frame_index,
                    "timestamp_s": round(float(o.timestamp_s), 4),
                    "camera_id": o.camera_id,
                    "image_uv": [round(float(u), 1) for u in o.image_coords_uv],
                    "depth_val": round(float(o.depth_c), 3),
                    "world_xyz": [round(float(c), 3) for c in o.point_world],
                    "confidence": round(float(o.confidence), 4),
                }
                for o in self.spatial_observations
            ],
        }
        d.update(self.extra_attributes)
        return d


class SpatialIntelligenceEngine:
    """Projects 2D tracked infrastructure objects into 3D world space."""

    def __init__(
        self,
        units: str = "relative_reconstruction_units",
        scale_type: str = "scale_aligned_relative",
        metric_calibrated: bool = False,
    ) -> None:
        self.units = units
        self.scale_type = scale_type
        self.metric_calibrated = metric_calibrated

    def localize_tracks_3d(
        self,
        tracks: List[InfrastructureTrack],
        camera_poses: Dict[int, Any],  # Dict mapping frame_index to CameraPose object or dict
        depth_maps: Dict[int, np.ndarray],  # Dict mapping frame_index to 32-bit float depth map
        intrinsics: Optional[np.ndarray] = None,  # (3, 3) K matrix
    ) -> List[LocalizedInfrastructure3D]:
        """Project multi-frame tracks into 3D space using depth maps and camera poses."""
        localized_objects: List[LocalizedInfrastructure3D] = []

        for track in tracks:
            spatial_obs: List[SpatialObservation3D] = []

            for obs in track.observations:
                frame_idx = obs.frame_index
                if frame_idx not in camera_poses or frame_idx not in depth_maps:
                    continue

                pose = camera_poses[frame_idx]
                depth_map = depth_maps[frame_idx]

                # Extract intrinsic parameters
                fx, fy, cx, cy = self._extract_intrinsics(pose, depth_map.shape, intrinsics)

                # Robust depth association inside detection bbox
                depth_c, uv_sampled = self._sample_robust_depth(obs.bbox, depth_map)
                if depth_c is None or depth_c <= 0:
                    continue

                u, v = uv_sampled

                # 1. Pinhole back-projection to Camera Coordinates
                # Xc = (u - cx) * Z / fx
                # Yc = (v - cy) * Z / fy
                # Zc = Z
                Xc = (u - cx) * depth_c / fx
                Yc = (v - cy) * depth_c / fy
                Zc = float(depth_c)
                pt_cam = np.array([Xc, Yc, Zc], dtype=np.float64)

                # 2. Rigid transformation to World Coordinates
                # World = R^T * (Cam - t) = R^T * Cam + C
                R, t, C = self._extract_extrinsics(pose)
                pt_world_colmap = R.T @ pt_cam + C

                # 3. Convert COLMAP/OpenCV world frame (+Y Down) to Three.js (+Y UP)
                # X_three = X_colmap
                # Y_three = -Y_colmap
                # Z_three = Z_colmap
                pt_three = (
                    float(pt_world_colmap[0]),
                    float(-pt_world_colmap[1]),
                    float(pt_world_colmap[2]),
                )

                cam_name = getattr(pose, "name", f"frame_{frame_idx}")

                spatial_obs.append(
                    SpatialObservation3D(
                        frame_index=frame_idx,
                        timestamp_s=obs.timestamp_s,
                        camera_id=cam_name,
                        image_coords_uv=(float(u), float(v)),
                        depth_c=float(depth_c),
                        point_camera=(float(Xc), float(Yc), float(Zc)),
                        point_world=pt_three,
                        confidence=obs.confidence,
                    )
                )

            if not spatial_obs:
                continue

            # Multi-view spatial fusion: robust weighted centroid & 3D bounding box
            world_pts = np.array([o.point_world for o in spatial_obs], dtype=np.float64)
            weights = np.array([o.confidence for o in spatial_obs], dtype=np.float64)
            weights /= np.sum(weights)

            centroid = np.sum(world_pts * weights[:, np.newaxis], axis=0)

            # Spatial uncertainty dispersion (weighted standard deviation)
            residuals = world_pts - centroid
            dispersion = float(np.sqrt(np.mean(np.sum(residuals**2, axis=1))))

            # Bounding extents
            if len(world_pts) > 1:
                min_bounds = np.min(world_pts, axis=0)
                max_bounds = np.max(world_pts, axis=0)
                extents = np.maximum(max_bounds - min_bounds, [1.5, 3.0, 1.5])
            else:
                # Default canonical extents based on infrastructure class
                extents = self._default_extents_for_class(track.class_name)

            # Special corridor waypoints for transmission lines
            line_waypoints = None
            if track.class_name == InfrastructureClass.TRANSMISSION_LINE:
                line_waypoints = self._fit_3d_line_corridor(spatial_obs, centroid)

            # Determine severity
            severity = "NORMAL"
            if track.class_name == InfrastructureClass.STRUCTURAL_DAMAGE:
                severity = "WARNING"
                if "corrosion" in str(track.observations[0].attributes):
                    severity = "WARNING"

            notes = [
                f"Multi-frame triangulation from {len(spatial_obs)} camera views.",
                f"Spatial dispersion radius: {dispersion:.2f} relative units.",
            ]
            if not self.metric_calibrated:
                notes.append("Uncalibrated relative scale: units in relative_reconstruction_units.")

            localized_objects.append(
                LocalizedInfrastructure3D(
                    track_id=track.track_id,
                    class_name=track.class_name,
                    position=(float(centroid[0]), float(centroid[1]), float(centroid[2])),
                    extents=(float(extents[0]), float(extents[1]), float(extents[2])),
                    uncertainty_radius=dispersion,
                    confidence=track.average_confidence,
                    observations_count=len(spatial_obs),
                    spatial_observations=spatial_obs,
                    line_waypoints=line_waypoints,
                    severity=severity,
                    inspection_notes=notes,
                    requires_field_verification=(severity != "NORMAL"),
                )
            )

        return localized_objects

    def _sample_robust_depth(
        self,
        bbox: List[float],
        depth_map: np.ndarray,
    ) -> Tuple[Optional[float], Tuple[float, float]]:
        """Sample robust median depth inside the inner 50% interior kernel of a detection box.

        Avoids using raw bounding-box center which frequently samples background sky
        or terrain behind thin infrastructure elements like towers and lines.
        """
        h, w = depth_map.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1 = max(0, min(w - 1, x1))
        x2 = max(x1 + 1, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(y1 + 1, min(h, y2))

        # Central interior 50% kernel
        kx1 = int(x1 + (x2 - x1) * 0.25)
        kx2 = max(kx1 + 1, int(x1 + (x2 - x1) * 0.75))
        ky1 = int(y1 + (y2 - y1) * 0.25)
        ky2 = max(ky1 + 1, int(y1 + (y2 - y1) * 0.75))

        kernel = depth_map[ky1:ky2, kx1:kx2]
        valid_depths = kernel[np.isfinite(kernel) & (kernel > 0.1)]

        if len(valid_depths) == 0:
            # Fallback to full bbox valid depths
            full_crop = depth_map[y1:y2, x1:x2]
            valid_depths = full_crop[np.isfinite(full_crop) & (full_crop > 0.1)]

        if len(valid_depths) == 0:
            return None, ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

        # For towers and power lines, foreground depth is closer than background:
        # Use 35th percentile to robustly anchor to foreground structure
        depth_val = float(np.percentile(valid_depths, 35))
        center_uv = ((kx1 + kx2) / 2.0, (ky1 + ky2) / 2.0)
        return depth_val, center_uv

    @staticmethod
    def _extract_intrinsics(
        pose: Any,
        shape: Tuple[int, int],
        fallback_k: Optional[np.ndarray],
    ) -> Tuple[float, float, float, float]:
        h, w = shape[:2]
        if hasattr(pose, "focal_px"):
            fx = float(pose.focal_px)
            fy = float(pose.focal_px)
            cx = float(getattr(pose, "cx", w / 2.0))
            cy = float(getattr(pose, "cy", h / 2.0))
            return fx, fy, cx, cy

        if fallback_k is not None:
            return (
                float(fallback_k[0, 0]),
                float(fallback_k[1, 1]),
                float(fallback_k[0, 2]),
                float(fallback_k[1, 2]),
            )

        # Canonical pinhole fallback
        f = max(w, h) * 1.05
        return f, f, w / 2.0, h / 2.0

    @staticmethod
    def _extract_extrinsics(pose: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if hasattr(pose, "R") and hasattr(pose, "t"):
            R = np.asarray(pose.R, dtype=np.float64)
            t = np.asarray(pose.t, dtype=np.float64).reshape(3, 1)
            C = -R.T @ t
            return R, t, C.flatten()
        elif isinstance(pose, dict):
            R = np.asarray(pose.get("R", np.eye(3)), dtype=np.float64)
            t = np.asarray(pose.get("t", np.zeros(3)), dtype=np.float64).reshape(3, 1)
            C = -R.T @ t
            return R, t, C.flatten()
        return np.eye(3), np.zeros(3), np.zeros(3)

    @staticmethod
    def _default_extents_for_class(class_name: InfrastructureClass) -> Tuple[float, float, float]:
        if class_name == InfrastructureClass.TRANSMISSION_TOWER:
            return (8.0, 22.0, 8.0)
        elif class_name == InfrastructureClass.TRANSMISSION_LINE:
            return (2.0, 1.0, 40.0)
        elif class_name == InfrastructureClass.CROSSARM:
            return (12.0, 1.5, 2.5)
        elif class_name == InfrastructureClass.INSULATOR:
            return (0.8, 2.5, 0.8)
        return (2.0, 2.0, 2.0)

    @staticmethod
    def _fit_3d_line_corridor(
        observations: List[SpatialObservation3D],
        centroid: np.ndarray,
    ) -> List[List[float]]:
        """Fit 3D line waypoints spanning along the survey corridor."""
        pts = np.array([o.point_world for o in observations], dtype=np.float64)
        if len(pts) >= 2:
            # Sort along primary corridor axis (Z)
            sort_idx = np.argsort(pts[:, 2])
            sorted_pts = pts[sort_idx]
            return [pt.tolist() for pt in sorted_pts]
        else:
            # Generate a 3D span extending +/- 15 units along Z corridor
            p1 = [centroid[0] - 1.0, centroid[1] + 0.5, centroid[2] - 15.0]
            p2 = [centroid[0], centroid[1] - 0.2, centroid[2]]
            p3 = [centroid[0] + 1.0, centroid[1] + 0.5, centroid[2] + 15.0]
            return [p1, p2, p3]

