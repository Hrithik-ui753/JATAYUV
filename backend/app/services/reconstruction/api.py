from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.app.models.mission import Mission
from backend.app.models.frame import Frame
from backend.app.models.camera_pose import CameraPose
from backend.app.models.processing import ProcessingRun
from backend.app.services.recon Orbital recon Orbital  # noqa - placeholder for real import if present


class ReconstructionReadiness:
    """Assess whether a mission is ready for dense reconstruction."""

    def __init__(self, mission: Mission):
        self.mission = mission

    def check(self) -> Dict[str, Any]:
        frames = Frame.query(mission_id=self.mission.id, selected=True).all()
        frame_ids = [f.id for f in frames]
        has_frames = len(frames) > 0

        poses = CameraPose.query(mission_id=self.mission.id).all()
        pose_map = {p.frame_id: p for p in poses}
        valid_pose_ids = [fid for fid in frame_ids if fid in pose_map]
        has_poses = len(valid_pose_ids) > 1

        return {
            "mission_id": self.mission.id,
            "selected_frame_count": len(frames),
            "frame_files_readable": self._all_frames_readable(frames),
            "camera_intrinsics_available": bool(self.mission.camera_intrinsics_json),
            "valid_camera_pose_count": len(valid_pose_ids),
            "has_poses": has_poses,
            "requires_dense_inputs": not (has_frames and has_poses),
            "ready": has_frames and has_poses and bool(self.mission.camera_intrinsics_json),
            "warnings": self._warnings(frames, pose_map),
        }

    def _all_frames_readable(self, frames: List[Frame]) -> bool:
        for f in frames:
            try:
                # Quick existence check only; full readability is tested in tasks.
                f.storage_path and os.path.isfile(f.storage_path)
            except Exception:
                return False
        return True

    def _warnings(self, frames: List[Frame], pose_map: Dict[str, CameraPose]) -> List[str]:
        warnings: List[str] = []
        if not frames:
            warnings.append("No selected frames found.")
        else:
            warnings.append(f"{len(frames)} selected frames present.")
        if not pose_map:
            warnings.append("No camera poses found for this mission.")
        else:
            warnings.append(f"{len(pose_map)} camera pose(s) found.")
        if not self.mission.camera_intrinsics_json:
            warnings.append("Camera intrinsics unavailable.")
        return warnings
