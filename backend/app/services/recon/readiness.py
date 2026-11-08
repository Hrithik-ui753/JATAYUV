from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List

from backend.app.models.mission import Mission
from backend.app.models.frame import Frame
from backend.app.models.camera_pose import CameraPose


class ReconstructionReadiness:
    """Assess whether a mission is ready for dense reconstruction."""

    def __init__(self, mission: Mission):
        self.mission = mission

    def check(self) -> Dict[str, Any]:
        frames = Frame.query(mission_id=self.mission.id, selected=True).all()
        frame_ids = [f.id for f in frames]

        poses = CameraPose.query(mission_id=self.mission.id).all()
        pose_map = {p.frame_id: p for p in poses}
        valid_pose_ids = [fid for fid in frame_ids if fid in pose_map]

        return {
            "mission_id": self.mission.id,
            "selected_frame_count": len(frames),
            "frame_files_readable": self._all_frames_readable(frames),
            "camera_intrinsics_available": bool(self.mission.camera_intrinsics_json),
            "valid_camera_pose_count": len(valid_pose_ids),
            "has_poses": len(valid_pose_ids) > 1,
            "requires_dense_inputs": not (len(frames) > 0 and len(valid_pose_ids) > 1),
            "ready": len(frames) > 0 and len(valid_pose_ids) > 1 and bool(self.mission.camera_intrinsics_json),
            "warnings": self._warnings(frames, pose_map),
        }

    def _all_frames_readable(self, frames: List[Frame]) -> bool:
        for f in frames:
            try:
                if not f.storage_path or not os.path.isfile(f.storage_path):
                    return False
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
