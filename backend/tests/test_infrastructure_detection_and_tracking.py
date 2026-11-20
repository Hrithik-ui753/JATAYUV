"""Tests for Infrastructure Detector and Multi-Frame Tracker."""
from __future__ import annotations

import os
import cv2
import numpy as np
import pytest

from backend.app.services.perception.infrastructure_detector import (
    InfrastructureClass,
    InfrastructureDetection,
    InfrastructureDetector,
)
from backend.app.services.perception.infrastructure_tracker import (
    InfrastructureTrack,
    InfrastructureTracker,
)

REAL_FRAME_PATH = os.path.join(
    "storage",
    "missions",
    "439219c0-21c1-4940-9dd9-e6f65ae86503",
    "videos",
    "30c3d866-8c72-43c7-a1bd-9bff24a8cf27",
    "frames",
    "7b4afb3d029e4dd8899bf2fcf9a00644",
    "00000000.jpg",
)


def test_infrastructure_detector_initialization():
    detector = InfrastructureDetector(confidence_threshold=0.35)
    assert detector.confidence_threshold == 0.35
    assert hasattr(detector, "detect")


def test_detector_classes_supported():
    classes = [c.value for c in InfrastructureClass]
    assert "transmission_tower" in classes
    assert "transmission_line" in classes
    assert "insulator" in classes
    assert "crossarm" in classes
    assert "electrical_equipment" in classes
    assert "structural_damage" in classes


def test_detection_on_synthetic_frame():
    detector = InfrastructureDetector(confidence_threshold=0.20)
    # Synthetic frame with high-contrast lines
    img = np.ones((720, 1280, 3), dtype=np.uint8) * 180
    cv2.line(img, (100, 300), (1100, 350), (20, 20, 20), 4)
    cv2.line(img, (100, 380), (1100, 430), (20, 20, 20), 4)

    dets = detector.detect(img, frame_index=0, timestamp_s=0.0)
    assert isinstance(dets, list)
    for d in dets:
        assert isinstance(d, InfrastructureDetection)
        assert d.confidence >= 0.20
        assert len(d.bbox) == 4
        assert d.bbox[2] > d.bbox[0]
        assert d.bbox[3] > d.bbox[1]


@pytest.mark.skipif(not os.path.exists(REAL_FRAME_PATH), reason="Real drone frame not present")
def test_detection_on_actual_drone_frame():
    detector = InfrastructureDetector(confidence_threshold=0.30)
    img = cv2.imread(REAL_FRAME_PATH)
    assert img is not None, "Failed to load real drone frame"
    assert img.shape == (1080, 1920, 3)

    dets = detector.detect(img, frame_index=0, timestamp_s=0.0)
    assert len(dets) > 0, "Detector should identify infrastructure in real transmission corridor footage"

    line_or_tower = any(
        d.class_name in (InfrastructureClass.TRANSMISSION_LINE, InfrastructureClass.TRANSMISSION_TOWER)
        for d in dets
    )
    assert line_or_tower, "Detected objects must include transmission corridor elements"


def test_tracker_tracks_and_suppresses_duplicates():
    tracker = InfrastructureTracker(iou_thresh=0.25, max_lost_frames=3)

    # Frame 0: detection
    d0 = [
        InfrastructureDetection(
            class_name=InfrastructureClass.TRANSMISSION_TOWER,
            confidence=0.85,
            bbox=[400.0, 100.0, 600.0, 700.0],
            frame_index=0,
            timestamp_s=0.0,
        )
    ]
    active0 = tracker.update(d0, frame_index=0, timestamp_s=0.0)
    assert len(active0) == 1
    track_id = active0[0].track_id
    assert track_id.startswith("TOWER-")

    # Frame 1: slightly shifted detection (same tower)
    d1 = [
        InfrastructureDetection(
            class_name=InfrastructureClass.TRANSMISSION_TOWER,
            confidence=0.88,
            bbox=[405.0, 102.0, 605.0, 702.0],
            frame_index=1,
            timestamp_s=0.033,
        )
    ]
    active1 = tracker.update(d1, frame_index=1, timestamp_s=0.033)
    assert len(active1) == 1
    # Must preserve persistent track ID across frames
    assert active1[0].track_id == track_id
    assert active1[0].total_observations == 2
    assert active1[0].is_confirmed is True


def test_tracker_filters_transient_single_frame_noise():
    tracker = InfrastructureTracker()
    # Ephemeral false alarm in single frame
    d_fake = [
        InfrastructureDetection(
            class_name=InfrastructureClass.INSULATOR,
            confidence=0.55,
            bbox=[50.0, 50.0, 70.0, 80.0],
            frame_index=0,
            timestamp_s=0.0,
        )
    ]
    tracker.update(d_fake, frame_index=0, timestamp_s=0.0)
    # Not confirmed yet (requires >= 2 frames)
    confirmed = tracker.get_confirmed_tracks()
    assert len(confirmed) == 0

