from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from backend.app.models.mission import Mission
from backend.app.models.frame import Frame
from backend.app.models.camera_pose import CameraPose
from backend.app.services.recon.readiness import ReconstructionReadiness


class TestReconstructionReadiness:
    def test_ready_when_frames_poses_and_intrinsics_present(self, monkeypatch):
        mission = MagicMock(spec=Mission)
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.project_id = "project-1"
        mission.camera_intrinsics_json = '{"fx": 1000}'
        mission.flight_metadata = MagicMock()

        frame = MagicMock(spec=Frame)
        frame.id = "frame-1"
        frame.mission_id = mission.id
        frame.selected = True
        frame.storage_path = "/tmp/frame.jpg"

        pose = MagicMock(spec=CameraPose)
        pose.frame_id = "frame-1"

        def fake_query(*args, **kwargs):
            class Query:
                def filter_by(self, **kw):
                    return self
                def filter(self, *a, **kw):
                    return self
                def all(self):
<<<<<<< HEAD
                    if "selected" in str(kwargs):
=======
                    if "selected" in str(kw):
>>>>>>> origin/main
                        return [frame]
                    return [pose]
                def offset(self, *a, **kw):
                    return self
                def limit(self, *a, **kw):
                    return self
                def count(self):
                    return 1
            return Query()

        monkeypatch.setattr(Frame, "query", fake_query)
        monkeypatch.setattr(CameraPose, "query", fake_query)

        readiness = ReconstructionReadiness(mission)
        result = readiness.check()
        assert result["ready"] is True
        assert result["selected_frame_count"] == 1
        assert result["valid_camera_pose_count"] == 1
        assert result["camera_intrinsics_available"] is True
        assert result["has_poses"] is True

    def test_not_ready_without_intrinsics(self, monkeypatch):
        mission = MagicMock(spec=Mission)
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.project_id = "project-1"
        mission.camera_intrinsics_json = None

        frame = MagicMock(spec=Frame)
        frame.id = "frame-1"
        frame.mission_id = mission.id
        frame.selected = True
        frame.storage_path = "/tmp/frame.jpg"

        pose = MagicMock(spec=CameraPose)
        pose.frame_id = "frame-1"

        def fake_query(*args, **kwargs):
            class Query:
                def filter_by(self, **kw):
                    return self
                def filter(self, *a, **kw):
                    return self
                def all(self):
<<<<<<< HEAD
                    if "selected" in str(kwargs):
=======
                    if "selected" in str(kw):
>>>>>>> origin/main
                        return [frame]
                    return [pose]
                def offset(self, *a, **kw):
                    return self
                def limit(self, *a, **kw):
                    return self
                def count(self):
                    return 1
            return Query()

        monkeypatch.setattr(Frame, "query", fake_query)
        monkeypatch.setattr(CameraPose, "query", fake_query)

        readiness = ReconstructionReadiness(mission)
        result = readiness.check()
        assert result["ready"] is False
        assert result["camera_intrinsics_available"] is False
        assert any("intrinsics" in w.lower() for w in result["warnings"])

    def test_frame_files_readable_check(self, monkeypatch, tmp_path):
        mission = MagicMock(spec=Mission)
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.project_id = "project-1"
        mission.camera_intrinsics_json = '{"fx": 1000}'

        readable_file = tmp_path / "frame.jpg"
        readable_file.write_bytes(b"image")

        unreadable_file = tmp_path / "missing.jpg"

        frames = [
            MagicMock(spec=Frame, id="f1", mission_id=mission.id, selected=True, storage_path=str(readable_file)),
            MagicMock(spec=Frame, id="f2", mission_id=mission.id, selected=True, storage_path=str(unreadable_file)),
        ]

        pose = MagicMock(spec=CameraPose)
        pose.frame_id = "f1"

        def fake_query(*args, **kwargs):
            class Query:
                def filter_by(self, **kw):
                    return self
                def filter(self, *a, **kw):
                    return self
                def all(self):
<<<<<<< HEAD
                    if "selected" in str(kwargs):
=======
                    if "selected" in str(kw):
>>>>>>> origin/main
                        return frames
                    return [pose]
                def offset(self, *a, **kw):
                    return self
                def limit(self, *a, **kw):
                    return self
                def count(self):
                    return 1
            return Query()

        monkeypatch.setattr(Frame, "query", fake_query)
        monkeypatch.setattr(CameraPose, "query", fake_query)

        readiness = ReconstructionReadiness(mission)
        withpatch = patch.object(os.path, "isfile", side_effect=lambda p: os.path.exists(p))
        monkeypatch.setattr(os.path, "isfile", withpatch.start)
        result = readiness.check()
        withpatch.stop()
        assert result["frame_files_readable"] is False
