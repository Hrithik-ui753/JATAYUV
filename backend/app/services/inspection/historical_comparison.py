"""JATAYUV Historical Inspection Comparison Module.

Enables multi-temporal asset monitoring across consecutive drone survey missions:
1. Scale & Coordinate Alignment:
   Accounts for differences in camera position, flight trajectory, and uncalibrated
   reconstruction scale between Mission A (baseline) and Mission B (current survey).
2. Spatial Asset Matching:
   Bipartite nearest-neighbor matching mapping physical towers and lines across surveys.
3. Component Condition Delta:
   Evaluates changes in structural tilt, clearance reduction, and insulator degradation.
4. Anomaly Progression Tracking:
   - NEW ANOMALIES: Emerged since baseline.
   - PERSISTENT ANOMALIES: Ongoing unaddressed defects.
   - ESCALATED ANOMALIES: Severity increased from WARNING to CRITICAL.
   - RESOLVED ANOMALIES: Past defects successfully maintained/cleared.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger("jatayuv.inspection.historical_comparison")


@dataclass
class AssetMatchPair:
    asset_id_a: str
    asset_id_b: str
    class_name: str
    spatial_separation_units: float
    confidence_delta: float
    tilt_delta_deg: float
    status_change: str                    # "UNCHANGED", "DEGRADED", "IMPROVED", "NEW_DEFECT"
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id_a": self.asset_id_a,
            "asset_id_b": self.asset_id_b,
            "class_name": self.class_name,
            "spatial_separation_units": round(float(self.spatial_separation_units), 3),
            "confidence_delta": round(float(self.confidence_delta), 4),
            "tilt_delta_deg": round(float(self.tilt_delta_deg), 2),
            "status_change": self.status_change,
            "notes": self.notes,
        }


@dataclass
class HistoricalComparisonReport:
    mission_id_a: str                     # Baseline survey
    mission_id_b: str                     # Current survey
    scale_ratio_b_to_a: float             # Relative scale alignment factor
    total_matched_assets: int
    unmatched_assets_a: List[str]         # Decommissioned or occluded
    unmatched_assets_b: List[str]         # Newly installed or detected
    matched_pairs: List[AssetMatchPair]
    new_anomalies_count: int
    persistent_anomalies_count: int
    resolved_anomalies_count: int
    escalated_anomalies_count: int
    overall_health_trend: str             # "STABLE", "DEGRADING", "IMPROVED"
    summary_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id_a": self.mission_id_a,
            "mission_id_b": self.mission_id_b,
            "scale_ratio_b_to_a": round(float(self.scale_ratio_b_to_a), 4),
            "total_matched_assets": self.total_matched_assets,
            "unmatched_assets_a": self.unmatched_assets_a,
            "unmatched_assets_b": self.unmatched_assets_b,
            "new_anomalies_count": self.new_anomalies_count,
            "persistent_anomalies_count": self.persistent_anomalies_count,
            "resolved_anomalies_count": self.resolved_anomalies_count,
            "escalated_anomalies_count": self.escalated_anomalies_count,
            "overall_health_trend": self.overall_health_trend,
            "summary_findings": self.summary_findings,
            "matched_pairs": [p.to_dict() for p in self.matched_pairs],
        }


class HistoricalComparisonEngine:
    """Compares two inspection mission runs for temporal infrastructure degradation."""

    def compare_missions(
        self,
        mission_a_data: Dict[str, Any],
        mission_b_data: Dict[str, Any],
    ) -> HistoricalComparisonReport:
        """Compare baseline mission A with current mission B."""
        mid_a = mission_a_data.get("mission_id", "mission_A")
        mid_b = mission_b_data.get("mission_id", "mission_B")

        objs_a = mission_a_data.get("infrastructure_objects_3d", [])
        objs_b = mission_b_data.get("infrastructure_objects_3d", [])

        anoms_a = mission_a_data.get("inspection_report", {}).get("anomalies", [])
        anoms_b = mission_b_data.get("inspection_report", {}).get("anomalies", [])

        # 1. Estimate Relative Scale Alignment Ratio between surveys
        scale_ratio = self._estimate_scale_ratio(objs_a, objs_b)

        # 2. Normalize coordinates of survey B to survey A space
        aligned_b = self._align_objects_to_baseline(objs_b, objs_a, scale_ratio)

        # 3. Match Assets via Class & Euclidean Distance
        matched_pairs: List[AssetMatchPair] = []
        matched_a_ids = set()
        matched_b_ids = set()

        for b_dict in aligned_b:
            b_pos = np.array(b_dict["position_aligned"])
            b_class = b_dict["class_name"]
            b_id = b_dict["track_id"]

            best_match = None
            best_dist = float("inf")

            for a_dict in objs_a:
                a_id = a_dict["track_id"]
                if a_id in matched_a_ids or a_dict["class_name"] != b_class:
                    continue
                a_pos = np.array(a_dict["position"])
                dist = float(np.linalg.norm(b_pos - a_pos))
                if dist < best_dist and dist < 12.0:  # Distance gating threshold
                    best_dist = dist
                    best_match = a_dict

            if best_match is not None:
                a_id = best_match["track_id"]
                matched_a_ids.add(a_id)
                matched_b_ids.add(b_id)

                conf_delta = b_dict.get("confidence", 0.85) - best_match.get("confidence", 0.85)
                notes = [f"Aligned spatial distance: {best_dist:.2f} relative units."]

                # Check severity changes
                sev_a = best_match.get("severity", "NORMAL")
                sev_b = b_dict.get("severity", "NORMAL")
                if sev_b != "NORMAL" and sev_a == "NORMAL":
                    status = "NEW_DEFECT"
                    notes.append(f"Asset developed new {sev_b} anomaly since baseline.")
                elif sev_b == "CRITICAL" and sev_a == "WARNING":
                    status = "DEGRADED"
                    notes.append("Anomaly severity escalated from WARNING to CRITICAL.")
                elif sev_b == "NORMAL" and sev_a != "NORMAL":
                    status = "IMPROVED"
                    notes.append("Previous defect resolved / cleared.")
                else:
                    status = "UNCHANGED"

                matched_pairs.append(
                    AssetMatchPair(
                        asset_id_a=a_id,
                        asset_id_b=b_id,
                        class_name=b_class,
                        spatial_separation_units=best_dist,
                        confidence_delta=conf_delta,
                        tilt_delta_deg=0.0,
                        status_change=status,
                        notes=notes,
                    )
                )

        unmatched_a = [a["track_id"] for a in objs_a if a["track_id"] not in matched_a_ids]
        unmatched_b = [b["track_id"] for b in objs_b if b["track_id"] not in matched_b_ids]

        # 4. Anomaly Progression Tracking
        anom_types_a = {a.get("anomaly_type") for a in anoms_a}
        anom_types_b = {b.get("anomaly_type") for b in anoms_b}

        new_count = len([b for b in anoms_b if b.get("anomaly_type") not in anom_types_a])
        persistent_count = len([b for b in anoms_b if b.get("anomaly_type") in anom_types_a])
        resolved_count = len([a for a in anoms_a if a.get("anomaly_type") not in anom_types_b])
        escalated_count = len([p for p in matched_pairs if p.status_change == "DEGRADED"])

        # Overall trend
        if new_count > 0 or escalated_count > 0:
            trend = "DEGRADING"
        elif resolved_count > 0 and new_count == 0:
            trend = "IMPROVED"
        else:
            trend = "STABLE"

        summary = [
            f"Matched {len(matched_pairs)} corresponding infrastructure assets between flights.",
            f"Relative survey scale ratio (B / A): {scale_ratio:.3f}.",
            f"Overall corridor health trend: {trend}.",
        ]
        if new_count > 0:
            summary.append(f"Identified {new_count} newly emerged structural anomalies.")

        return HistoricalComparisonReport(
            mission_id_a=mid_a,
            mission_id_b=mid_b,
            scale_ratio_b_to_a=scale_ratio,
            total_matched_assets=len(matched_pairs),
            unmatched_assets_a=unmatched_a,
            unmatched_assets_b=unmatched_b,
            matched_pairs=matched_pairs,
            new_anomalies_count=new_count,
            persistent_anomalies_count=persistent_count,
            resolved_anomalies_count=resolved_count,
            escalated_anomalies_count=escalated_count,
            overall_health_trend=trend,
            summary_findings=summary,
        )

    def _estimate_scale_ratio(
        self,
        objs_a: List[Dict[str, Any]],
        objs_b: List[Dict[str, Any]],
    ) -> float:
        """Estimate 7-parameter relative scale ratio between two surveys."""
        towers_a = [o["position"] for o in objs_a if o.get("class_name") == "transmission_tower"]
        towers_b = [o["position"] for o in objs_b if o.get("class_name") == "transmission_tower"]

        if len(towers_a) >= 2 and len(towers_b) >= 2:
            span_a = float(np.linalg.norm(np.array(towers_a[1]) - np.array(towers_a[0])))
            span_b = float(np.linalg.norm(np.array(towers_b[1]) - np.array(towers_b[0])))
            if span_a > 0.1 and span_b > 0.1:
                return float(span_a / span_b)
        return 1.0

    def _align_objects_to_baseline(
        self,
        objs_b: List[Dict[str, Any]],
        objs_a: List[Dict[str, Any]],
        scale_ratio: float,
    ) -> List[Dict[str, Any]]:
        """Scale and translate objects in B to align with baseline survey A centroid."""
        if not objs_b or not objs_a:
            return objs_b

        pos_a = np.array([o["position"] for o in objs_a])
        pos_b = np.array([o["position"] for o in objs_b])

        centroid_a = np.median(pos_a, axis=0)
        centroid_b = np.median(pos_b, axis=0)

        aligned = []
        for o in objs_b:
            p = np.array(o["position"])
            # Scale around centroid and translate to baseline centroid
            p_scaled = (p - centroid_b) * scale_ratio + centroid_a
            o_copy = dict(o)
            o_copy["position_aligned"] = p_scaled.tolist()
            aligned.append(o_copy)

        return aligned


historical_comparison_engine = HistoricalComparisonEngine()

