import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.app.services.recon.pipeline import ReconstructionPipeline
from backend.app.services.recon.readiness import ReconstructionReadiness
<<<<<<< HEAD
from backend.app.models.frame import Frame
from backend.app.models.camera_pose import CameraPose

=======
>>>>>>> origin/main


class TestReconstructionPipelineWorkspace:
    def test_prepare_workspace_creates_expected_dirs(self, tmp_path):
        pipeline = ReconstructionPipeline.__new__(ReconstructionPipeline)
        pipeline.mission_id = "mission-1"
        pipeline.base_dir = str(tmp_path)
        pipeline.colmap = MagicMock()
        workspace = pipeline.prepare_workspace("run-1")
        for d in ["colmap", "dense", "point_clouds", "meshes", "textures", "materials", "reports"]:
            assert os.path.isdir(os.path.join(workspace, d))


class TestReconstructionPipelineDepthAssistedRejectsRelativeDepth:
    def test_depth_assisted_point_cloud_returns_none_for_relative_depth(self, monkeypatch):
        pipeline = ReconstructionPipeline.__new__(ReconstructionPipeline)
        pipeline.mission_id = "mission-1"
        pipeline.colmap = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            depth_path = os.path.join(td, "depth.npy")
            np.save(depth_path, np.random.rand(10, 10).astype(np.float32))

            frame_path = os.path.join(td, "frame.jpg")
            with open(frame_path, "wb") as f:
                f.write(b"fake")

            def fake_depth_metadata(path):
                return {"depth_type": "relative"}

            monkeypatch.setattr(pipeline, "_depth_metadata_for_frame", fake_depth_metadata)

            result = pipeline.depth_assisted_point_cloud(
                frame_path,
                depth_path,
                {"fx": 1000, "fy": 1000, "cx": 5, "cy": 5},
            )
            assert result is None

    def test_depth_assisted_point_cloud_requires_open3d(self, monkeypatch):
        pipeline = ReconstructionPipeline.__new__(ReconstructionPipeline)
        pipeline.mission_id = "mission-1"
        pipeline.colmap = MagicMock()
        monkeypatch.setattr("backend.app.services.recon.pipeline.o3d", None)

        with pytest.raises(RuntimeError, match="Open3D is required"):
            pipeline.depth_assisted_point_cloud(
                "unused",
                "unused",
                {"fx": 1000, "fy": 1000, "cx": 5, "cy": 5},
            )


class TestReconstructionReadinessWarnings:
    def test_warnings_list_populated(self, monkeypatch):
        mission = MagicMock()
        mission.id = "mission-1"
        mission.user_id = "user-1"
        mission.project_id = "project-1"
        mission.camera_intrinsics_json = None

        frame = MagicMock()
        frame.id = "frame-1"
        frame.mission_id = mission.id
        frame.selected = True
        frame.storage_path = "/tmp/frame.jpg"

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
                    return []
                def offset(self, *a, **kw):
                    return self
                def limit(self, *a, **kw):
                    return self
                def count(self):
                    return 0
            return Query()

        monkeypatch.setattr(Frame, "query", fake_query)
        monkeypatch.setattr(CameraPose, "query", fake_query)

        readiness = ReconstructionReadiness(mission)
        result = readiness.check()
        assert isinstance(result["warnings"], list)
        assert len(result["warnings"]) >= 1
        assert result["ready"] is False
