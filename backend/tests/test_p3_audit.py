import os
from typing import Dict

import cv2
import numpy as np
import pytest

from backend.app.services.perception import (
    describe_all_perception_models,
    describe_supported_segmentation_classes,
    describe_dynamic_model,
    describe_depth_model,
    is_depth_available,
    is_segmentation_available,
    is_dynamic_detection_available,
    map_segmentation_target_to_model_class,
    infer_depth,
    infer_segmentation,
    infer_dynamic_objects,
    build_dynamic_exclusion_mask,
)


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_AERIAL_IMAGE = os.path.join(FIXTURE_DIR, "aerial_01.jpg")


def _aerial_frame():
    assert _AERIAL_IMAGE, "Test fixture path missing"
    frame = cv2.imread(_AERIAL_IMAGE)
    assert frame is not None, "Test fixture missing"
    return frame


class TestPerceptionModelDescriptions:
    def test_all_models_summary_present(self):
        summary = describe_all_perception_models()
        assert isinstance(summary, dict)
        assert "depth" in summary
        assert "segmentation" in summary
        assert "dynamic_detection" in summary
        assert "availability" in summary

    def test_depth_description_is_relative(self):
        desc = describe_all_perception_models()["depth"]
        assert desc.get("depth_type") == "relative"
        assert desc.get("is_metric") is False
        assert desc.get("depth_unit") == "relative_inverse_depth"

    def test_dynamic_description_reports_unavailability(self):
        desc = describe_all_perception_models()["dynamic_detection"]
        assert desc.get("checkpoint_available") is False
        assert desc.get("model_id") is None

    def test_availability_summary_matches_individual_checks(self):
        summary = describe_all_perception_models()["availability"]
        assert summary["depth"] is is_depth_available()
        assert summary["segmentation"] is is_segmentation_available()
        assert summary["dynamic_detection"] is is_dynamic_detection_available()


class TestPerceptionAvailability:
    def test_depth_availability_returns_bool(self):
        value = is_depth_available()
        assert isinstance(value, bool)

    def test_segmentation_availability_returns_bool(self):
        value = is_segmentation_available()
        assert isinstance(value, bool)

    def test_dynamic_detection_availability_returns_bool(self):
        value = is_dynamic_detection_available()
        assert isinstance(value, bool)
        assert value is False


class TestUnsupportedClassMapping:
    def test_unsupported_classes_map_to_none(self):
        unsupported = {
            k: v
            for k, v in {
                "buildings_and_structures": map_segmentation_target_to_model_class("buildings_and_structures"),
                "roads_and_paved_surfaces": map_segmentation_target_to_model_class("roads_and_paved_surfaces"),
                "vegetation": map_segmentation_target_to_model_class("vegetation"),
                "ground_and_terrain": map_segmentation_target_to_model_class("ground_and_terrain"),
                "water": map_segmentation_target_to_model_class("water"),
                "vehicles": map_segmentation_target_to_model_class("vehicles"),
                "humans": map_segmentation_target_to_model_class("humans"),
                "obstacles": map_segmentation_target_to_model_class("obstacles"),
                "unknown_or_unsupported": map_segmentation_target_to_model_class("unknown_or_unsupported"),
            }.items()
            if v is None
        }
        assert "humans" in unsupported
        assert "obstacles" in unsupported

    def test_supported_classes_map_to_model_ids(self):
        buildings_id = map_segmentation_target_to_model_class("buildings_and_structures")
        assert isinstance(buildings_id, int)

    def test_describe_supported_segmentation_classes_present(self):
        info = describe_supported_segmentation_classes()
        assert isinstance(info, dict)
        assert info.get("supported_classes")
        assert info.get("target_mapping")


class TestDepthInferenceRelativeLabeling:
    def test_depth_inference_produces_relative_outputs(self):
        frame = _aerial_frame()

        result = infer_depth(frame)
        assert result.depth_type == "relative"
        assert result.is_metric is False
        assert result.depth_unit == "relative_inverse_depth"
        assert result.model_id is not None
        assert result.checkpoint_sha256 is not None
        assert result.inference_duration_ms >= 0

    def test_depth_inference_shape_matches_frame(self):
        frame = _aerial_frame()
        h, w = frame.shape[:2]

        result = infer_depth(frame)
        assert result.output_height == h
        assert result.output_width == w

    def test_depth_inference_confidence_is_empty_dict(self):
        frame = _aerial_frame()

        result = infer_depth(frame)
        assert result.confidence_json == {}


class TestSegmentationClassMapping:
    def test_segmentation_reports_unsupported_handling(self):
        frame = _aerial_frame()

        result = infer_segmentation(frame)
        handling = result.unsupported_class_handling
        assert handling.get("humans") == "mapped_to_unknown"
        assert handling.get("obstacles") == "mapped_to_unknown"

    def test_segmentation_class_distribution_measurable(self):
        frame = _aerial_frame()

        result = infer_segmentation(frame)
        assert isinstance(result.class_distribution, dict)
        assert len(result.class_distribution) > 0
        assert isinstance(result.per_class_pixel_counts, dict)


class TestDynamicDetectionHonesty:
    def test_dynamic_detection_reports_no_detections_when_unavailable(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = infer_dynamic_objects(frame)
        assert result.model_id is None
        assert result.detections == []
        assert result.inference_device == "unavailable"

    def test_dynamic_exclusion_mask_uses_boxes_only_for_known_categories(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        detections = [
            {"category": "car", "label": "car", "box": [10, 20, 50, 60]},
            {"category": "unknown_obj", "label": "something", "box": [0, 0, 200, 100]},
        ]
        mask = build_dynamic_exclusion_mask(frame, detections)
        assert mask.shape == (100, 200)
        assert mask[20:60, 10:50].max() == 255
        assert mask[:, :].max() == 255


class TestPerceptionFusionMetadata:
    def test_dynamic_model_description_includes_expected_fields(self):
        desc = describe_dynamic_model()
        assert isinstance(desc, dict)
        assert "model_id" in desc
        assert "supported_categories" in desc
        assert "notes" in desc
