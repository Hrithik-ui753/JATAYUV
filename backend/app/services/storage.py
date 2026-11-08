import os
import uuid
from datetime import datetime, timezone
from backend.app.core.config import settings


class MissionStorage:
    """Persistent storage helpers for mission artifacts.

    This layer keeps private storage paths out of API responses and enforces
    a consistent naming convention for mission artifacts.
    """

    ARTIFACT_SUBDIRS = {
        "video": "videos",
        "frames": "frames",
        "metadata": "metadata",
        "camera_poses": "camera_poses",
        "depth_maps": "depth_maps",
        "point_clouds": "point_clouds",
        "meshes": "meshes",
        "textures": "textures",
        "validation_reports": "validation_reports",
    }

    def __init__(self):
        for subdir in self.ARTIFACT_SUBDIRS.values():
            os.makedirs(os.path.join(settings.STORAGE_DIR, subdir), exist_ok=True)

    def mission_artifact_dir(self, mission_id: str, artifact_type: str) -> str:
        subdir = self.ARTIFACT_SUBDIRS.get(artifact_type, artifact_type)
        return os.path.join(settings.STORAGE_DIR, subdir, mission_id)

    def make_video_path(self, mission_id: str, filename: str) -> str:
        d = self.mission_artifact_dir(mission_id, "video")
        os.makedirs(d, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        return os.path.join(d, safe_name)

    def make_frame_path(self, mission_id: str, video_id: str, frame_index: int) -> str:
        d = self.mission_artifact_dir(mission_id, "frames")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{video_id}_frame_{frame_index:06d}.png")

    def make_metadata_path(self, mission_id: str) -> str:
        d = self.mission_artifact_dir(mission_id, "metadata")
        os.makedirs(d, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return os.path.join(d, f"flight_metadata_{ts}.json")

    def make_camera_pose_path(self, mission_id: str, frame_id: str) -> str:
        d = self.mission_artifact_dir(mission_id, "camera_poses")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"pose_{frame_id}.json")

    def make_point_cloud_path(self, mission_id: str, version: str) -> str:
        d = self.mission_artifact_dir(mission_id, "point_clouds")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"pointcloud_{version}.ply")

    def make_mesh_path(self, mission_id: str, version: str) -> str:
        d = self.mission_artifact_dir(mission_id, "meshes")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"mesh_{version}.obj")

    def make_texture_path(self, mission_id: str, version: str) -> str:
        d = self.mission_artifact_dir(mission_id, "textures")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"texture_{version}.jpg")

    def make_validation_report_path(self, mission_id: str, report_id: str) -> str:
        d = self.mission_artifact_dir(mission_id, "validation_reports")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"validation_{report_id}.json")

    def public_url_for(self, path: str) -> str:
        """Convert an internal storage path to a URL the server can serve."""
        normalised = path.replace("\\", "/")
        storage_root = settings.STORAGE_DIR.replace("\\", "/").rstrip("/")
        if normalised.lower().startswith(storage_root.lower()):
            suffix = normalised[len(storage_root):].lstrip("/")
            return f"/storage/{suffix}"
        return normalised


_mission_storage = None


def get_mission_storage() -> MissionStorage:
    global _mission_storage
    if _mission_storage is None:
        _mission_storage = MissionStorage()
    return _mission_storage
