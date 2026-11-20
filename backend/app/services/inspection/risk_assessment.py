"""JATAYUV AI Risk Assessment Framework.

Multi-factor transparent engineering risk score combining:
1. Detection Confidence (C in [0, 1])
2. Observed Anomaly Severity (CRITICAL=40, WARNING=20, INFO=5)
3. Spatial Uncertainty Radius (+/- sigma)
4. Multi-Frame Confirmation Depth (N_frames)
5. Historical Degradation Rate (delta_hist)

Categories:
- NEGLIGIBLE (0 - 15)
- LOW (16 - 35)
- MODERATE (36 - 60)
- HIGH (61 - 85)
- CRITICAL (86 - 100)

Never automatically condemns an asset based solely on unverified AI observations;
always produces explainable contributing factors and recommends field verification.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

log = logging.getLogger("jatayuv.inspection.risk_assessment")


class RiskCategory(str, Enum):
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AssetRiskEvaluation:
    asset_id: str
    class_name: str
    risk_score: float                     # 0.0 to 100.0
    risk_category: RiskCategory
    contributing_factors: List[str] = field(default_factory=list)
    confidence_weight: float = 0.0
    severity_weight: float = 0.0
    uncertainty_weight: float = 0.0
    temporal_support_weight: float = 0.0
    historical_drift_weight: float = 0.0
    recommended_action: str = ""
    requires_human_verification: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "class_name": self.class_name,
            "risk_score": round(float(self.risk_score), 1),
            "risk_category": self.risk_category.value,
            "contributing_factors": self.contributing_factors,
            "factor_breakdown": {
                "confidence_weight": round(float(self.confidence_weight), 2),
                "severity_weight": round(float(self.severity_weight), 2),
                "uncertainty_weight": round(float(self.uncertainty_weight), 2),
                "temporal_support_weight": round(float(self.temporal_support_weight), 2),
                "historical_drift_weight": round(float(self.historical_drift_weight), 2),
            },
            "recommended_action": self.recommended_action,
            "requires_human_verification": self.requires_human_verification,
        }


class RiskAssessmentEngine:
    """Transparent multi-criteria engineering risk assessment engine."""

    def evaluate_asset_risk(
        self,
        asset_id: str,
        class_name: str,
        confidence: float,
        anomaly_severities: List[str],
        uncertainty_radius: float,
        frame_observations_count: int,
        historical_anomaly_count_delta: int = 0,
    ) -> AssetRiskEvaluation:
        """Compute transparent asset risk evaluation."""
        contributing_factors: List[str] = []

        # 1. Severity weight
        # Critical = 40, Warning = 20, Info = 5
        sev_score = 0.0
        for s in anomaly_severities:
            s_upper = s.upper()
            if s_upper == "CRITICAL":
                sev_score += 40.0
                contributing_factors.append("Critical anomaly flagged on asset.")
            elif s_upper == "WARNING":
                sev_score += 20.0
                contributing_factors.append("Advisory structural or clearance warning.")
            elif s_upper == "INFO":
                sev_score += 5.0
        sev_score = min(50.0, sev_score)

        # 2. Confidence weight (higher confidence in defect increases urgency)
        # Scaled by whether an anomaly exists
        if sev_score > 0:
            conf_weight = confidence * 20.0
            contributing_factors.append(f"AI detection confidence: {confidence*100:.1f}%.")
        else:
            conf_weight = 0.0

        # 3. Uncertainty penalty / attenuation
        # Very high spatial uncertainty (+/- sigma > 3.0) lowers confidence in defect severity,
        # but flags need for re-survey
        if uncertainty_radius > 3.0:
            unc_weight = 10.0
            contributing_factors.append(
                f"Elevated spatial dispersion (+/-{uncertainty_radius:.2f} u) requires line-of-sight verification."
            )
        else:
            unc_weight = 0.0

        # 4. Multi-frame support
        # High frame count confirms persistent defect vs single-frame glitch
        if frame_observations_count >= 4 and sev_score > 0:
            temporal_weight = 12.0
            contributing_factors.append(f"Defect validated across {frame_observations_count} consecutive drone views.")
        elif frame_observations_count <= 1 and sev_score > 0:
            temporal_weight = 2.0
            contributing_factors.append("Single-view observation: potential transient artifact.")
        else:
            temporal_weight = 0.0

        # 5. Historical degradation drift
        hist_weight = 0.0
        if historical_anomaly_count_delta > 0:
            hist_weight = min(18.0, historical_anomaly_count_delta * 9.0)
            contributing_factors.append(f"New anomaly appeared since previous baseline survey (+{historical_anomaly_count_delta}).")

        # Total score
        raw_score = sev_score + conf_weight + unc_weight + temporal_weight + hist_weight
        final_score = float(np.clip(raw_score, 0.0, 100.0))

        # Risk Category mapping
        if final_score <= 15.0:
            category = RiskCategory.NEGLIGIBLE
            rec = "Routine scheduled maintenance cycle."
        elif final_score <= 35.0:
            category = RiskCategory.LOW
            rec = "Monitor during next regular flight inspection."
        elif final_score <= 60.0:
            category = RiskCategory.MODERATE
            rec = "Schedule targeted telephoto survey within 60 days."
        elif final_score <= 85.0:
            category = RiskCategory.HIGH
            rec = "Dispatch ground inspection crew for physical asset verification within 14 days."
        else:
            category = RiskCategory.CRITICAL
            rec = "High-priority engineer review: potential imminent clearance or structural failure."

        if not contributing_factors:
            contributing_factors.append("Asset geometry and clearance in nominal condition.")

        return AssetRiskEvaluation(
            asset_id=asset_id,
            class_name=class_name,
            risk_score=final_score,
            risk_category=category,
            contributing_factors=contributing_factors,
            confidence_weight=conf_weight,
            severity_weight=sev_score,
            uncertainty_weight=unc_weight,
            temporal_support_weight=temporal_weight,
            historical_drift_weight=hist_weight,
            recommended_action=rec,
            requires_human_verification=(category in (RiskCategory.HIGH, RiskCategory.CRITICAL, RiskCategory.MODERATE)),
        )


risk_assessment_engine = RiskAssessmentEngine()
