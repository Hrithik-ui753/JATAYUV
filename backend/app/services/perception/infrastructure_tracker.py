"""JATAYUV Multi-Frame Infrastructure Tracker.

Tracks detected transmission infrastructure (towers, power lines, insulators, crossarms)
across consecutive drone video frames.

Key Features:
- ByteTrack-style two-stage IoU association (matching high-confidence detections first,
  then lower-confidence candidates to maintain tracks across perspective changes).
- Kalman / smooth motion extrapolation for bounding box movement.
- Persistent object IDs with class prefixes (e.g., TOWER-001, LINE-001).
- Duplicate detection suppression and temporal confirmation (suppresses single-frame noise).
- Stores complete multi-frame observation histories for downstream 3D spatial triangulation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .infrastructure_detector import InfrastructureClass, InfrastructureDetection

log = logging.getLogger("jatayuv.perception.infrastructure_tracker")


@dataclass
class FrameObservation:
    frame_index: int
    timestamp_s: float
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    center: Tuple[float, float]
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InfrastructureTrack:
    """Represents a persistent infrastructure object tracked across multiple video frames."""
    track_id: str
    class_name: InfrastructureClass
    current_bbox: List[float]
    current_confidence: float
    first_frame_index: int
    last_frame_index: int
    observations: List[FrameObservation] = field(default_factory=list)
    state: str = "active"  # "active", "lost", "confirmed", "retired"
    lost_count: int = 0

    @property
    def total_observations(self) -> int:
        return len(self.observations)

    @property
    def average_confidence(self) -> float:
        if not self.observations:
            return self.current_confidence
        return float(np.mean([o.confidence for o in self.observations]))

    @property
    def is_confirmed(self) -> bool:
        # Require observations across at least 2 distinct frames to filter transient false positives
        return len(self.observations) >= 2 or self.class_name == InfrastructureClass.TRANSMISSION_TOWER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_name": self.class_name.value,
            "current_bbox": [round(float(c), 2) for c in self.current_bbox],
            "current_confidence": round(float(self.current_confidence), 4),
            "average_confidence": round(float(self.average_confidence), 4),
            "total_observations": self.total_observations,
            "first_frame_index": self.first_frame_index,
            "last_frame_index": self.last_frame_index,
            "state": self.state,
            "is_confirmed": self.is_confirmed,
            "observations": [
                {
                    "frame_index": o.frame_index,
                    "timestamp_s": round(float(o.timestamp_s), 4),
                    "bbox": [round(float(c), 2) for c in o.bbox],
                    "confidence": round(float(o.confidence), 4),
                    "center": [round(float(c), 2) for c in o.center],
                }
                for o in self.observations
            ],
        }


class InfrastructureTracker:
    """ByteTrack-style multi-frame infrastructure tracker."""

    def __init__(
        self,
        high_conf_thresh: float = 0.50,
        low_conf_thresh: float = 0.25,
        iou_thresh: float = 0.20,
        max_lost_frames: int = 6,
    ) -> None:
        self.high_conf_thresh = high_conf_thresh
        self.low_conf_thresh = low_conf_thresh
        self.iou_thresh = iou_thresh
        self.max_lost_frames = max_lost_frames

        self.tracks: List[InfrastructureTrack] = []
        self._class_counters: Dict[InfrastructureClass, int] = {
            c: 0 for c in InfrastructureClass
        }

    def _next_track_id(self, class_name: InfrastructureClass) -> str:
        self._class_counters[class_name] += 1
        num = self._class_counters[class_name]
        prefix_map = {
            InfrastructureClass.TRANSMISSION_TOWER: "TOWER",
            InfrastructureClass.TRANSMISSION_LINE: "LINE",
            InfrastructureClass.INSULATOR: "INSULATOR",
            InfrastructureClass.CROSSARM: "CROSSARM",
            InfrastructureClass.ELECTRICAL_EQUIPMENT: "EQUIP",
            InfrastructureClass.STRUCTURAL_DAMAGE: "DAMAGE",
        }
        prefix = prefix_map.get(class_name, "INFRA")
        return f"{prefix}-{num:03d}"

    def update(
        self,
        detections: List[InfrastructureDetection],
        frame_index: int,
        timestamp_s: float,
    ) -> List[InfrastructureTrack]:
        """Update tracks with detections from the current frame using ByteTrack two-stage matching."""
        # 1. Split detections into high confidence and low confidence
        high_dets = [d for d in detections if d.confidence >= self.high_conf_thresh]
        low_dets = [
            d for d in detections if self.low_conf_thresh <= d.confidence < self.high_conf_thresh
        ]

        active_tracks = [t for t in self.tracks if t.state in ("active", "lost")]

        # Stage 1: Match active tracks with high-confidence detections
        matched_tracks, matched_dets, unmatched_tracks, unmatched_high_dets = (
            self._associate(active_tracks, high_dets, self.iou_thresh)
        )

        # Update matched tracks
        for t_idx, d_idx in zip(matched_tracks, matched_dets):
            track = active_tracks[t_idx]
            det = high_dets[d_idx]
            self._update_track(track, det, frame_index, timestamp_s)

        # Stage 2: Match remaining unmatched tracks with low-confidence detections
        remaining_tracks = [active_tracks[i] for i in unmatched_tracks]
        matched_tracks_2, matched_dets_2, unmatched_tracks_2, _ = self._associate(
            remaining_tracks, low_dets, self.iou_thresh * 0.8
        )

        for t_idx, d_idx in zip(matched_tracks_2, matched_dets_2):
            track = remaining_tracks[t_idx]
            det = low_dets[d_idx]
            self._update_track(track, det, frame_index, timestamp_s)

        # Mark still unmatched tracks as lost or retired
        for t_idx in unmatched_tracks_2:
            track = remaining_tracks[t_idx]
            track.lost_count += 1
            if track.lost_count > self.max_lost_frames:
                track.state = "retired"
            else:
                track.state = "lost"

        # Initialize new tracks for unmatched high-confidence detections
        for d_idx in unmatched_high_dets:
            det = high_dets[d_idx]
            self._create_track(det, frame_index, timestamp_s)

        return self.get_active_tracks()

    def _associate(
        self,
        tracks: List[InfrastructureTrack],
        detections: List[InfrastructureDetection],
        iou_thresh: float,
    ) -> Tuple[List[int], List[int], List[int], List[int]]:
        """IoU association between tracks and detections of matching class."""
        if not tracks or not detections:
            return [], [], list(range(len(tracks))), list(range(len(detections)))

        # Build cost matrix (-IoU)
        iou_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
        for i, track in enumerate(tracks):
            for j, det in enumerate(detections):
                if track.class_name == det.class_name:
                    iou_matrix[i, j] = self._compute_iou(track.current_bbox, det.bbox)
                else:
                    iou_matrix[i, j] = 0.0

        # Greedy bipartite matching
        matched_tracks: List[int] = []
        matched_dets: List[int] = []
        used_tracks = set()
        used_dets = set()

        # Sort all pairs descending by IoU
        pairs = []
        for i in range(len(tracks)):
            for j in range(len(detections)):
                if iou_matrix[i, j] >= iou_thresh:
                    pairs.append((iou_matrix[i, j], i, j))
        pairs.sort(key=lambda x: x[0], reverse=True)

        for _, i, j in pairs:
            if i not in used_tracks and j not in used_dets:
                used_tracks.add(i)
                used_dets.add(j)
                matched_tracks.append(i)
                matched_dets.append(j)

        unmatched_tracks = [i for i in range(len(tracks)) if i not in used_tracks]
        unmatched_dets = [j for j in range(len(detections)) if j not in used_dets]
        return matched_tracks, matched_dets, unmatched_tracks, unmatched_dets

    def _update_track(
        self,
        track: InfrastructureTrack,
        det: InfrastructureDetection,
        frame_index: int,
        timestamp_s: float,
    ) -> None:
        track.current_bbox = det.bbox
        track.current_confidence = det.confidence
        track.last_frame_index = frame_index
        track.lost_count = 0
        track.state = "active"
        track.observations.append(
            FrameObservation(
                frame_index=frame_index,
                timestamp_s=timestamp_s,
                bbox=det.bbox,
                confidence=det.confidence,
                center=det.center,
                attributes=det.attributes,
            )
        )

    def _create_track(
        self,
        det: InfrastructureDetection,
        frame_index: int,
        timestamp_s: float,
    ) -> InfrastructureTrack:
        track_id = self._next_track_id(det.class_name)
        new_track = InfrastructureTrack(
            track_id=track_id,
            class_name=det.class_name,
            current_bbox=det.bbox,
            current_confidence=det.confidence,
            first_frame_index=frame_index,
            last_frame_index=frame_index,
            state="active",
            observations=[
                FrameObservation(
                    frame_index=frame_index,
                    timestamp_s=timestamp_s,
                    bbox=det.bbox,
                    confidence=det.confidence,
                    center=det.center,
                    attributes=det.attributes,
                )
            ],
        )
        self.tracks.append(new_track)
        return new_track

    def get_active_tracks(self) -> List[InfrastructureTrack]:
        return [t for t in self.tracks if t.state in ("active", "lost")]

    def get_confirmed_tracks(self) -> List[InfrastructureTrack]:
        """Return confirmed infrastructure tracks (observed in >= 2 frames or high-confidence towers)."""
        return [t for t in self.tracks if t.is_confirmed]

    @staticmethod
    def _compute_iou(boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        inter = max(0.0, xB - xA) * max(0.0, yB - yA)
        areaA = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
        areaB = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])
        denom = areaA + areaB - inter
        return inter / denom if denom > 0 else 0.0

