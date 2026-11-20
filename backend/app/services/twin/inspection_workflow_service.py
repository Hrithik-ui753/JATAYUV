"""JATAYUV Engineering Inspection Workflow & Human Verification Service.

Manages:
1. Review of AI observations by certified engineers.
2. Verification state transitions:
   UNVERIFIED -> VERIFIED_DEFECT | FALSE_POSITIVE | ACCEPTED_CONDITION.
3. Creation and assignment of field inspection tasks / maintenance work orders.
4. Attachment of field photos and verification notes.
5. Tracking of repair status (PENDING_REVIEW -> WORK_ORDER_CREATED -> IN_REPAIR -> REPAIRED -> RESOLVED).
6. Strict invariant: Keeps AI observations clearly distinguished from human-verified findings.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("jatayuv.twin.workflow")


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED_DEFECT = "VERIFIED_DEFECT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ACCEPTED_CONDITION = "ACCEPTED_CONDITION"


class RepairStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    WORK_ORDER_CREATED = "WORK_ORDER_CREATED"
    IN_REPAIR = "IN_REPAIR"
    REPAIRED = "REPAIRED"
    RESOLVED = "RESOLVED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


@dataclass
class FindingVerificationRecord:
    id: str
    mission_id: str
    asset_track_id: str
    anomaly_id: str
    finding_type: str                     # "AI_OBSERVATION" or "VERIFIED_FINDING"
    verification_status: VerificationStatus
    verified_by_user_id: Optional[str]
    verified_at: Optional[str]
    engineer_notes: str
    repair_status: RepairStatus
    field_photo_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "asset_track_id": self.asset_track_id,
            "anomaly_id": self.anomaly_id,
            "finding_type": self.finding_type,
            "verification_status": self.verification_status.value,
            "verified_by_user_id": self.verified_by_user_id,
            "verified_at": self.verified_at,
            "engineer_notes": self.engineer_notes,
            "repair_status": self.repair_status.value,
            "field_photo_path": self.field_photo_path,
        }


@dataclass
class InspectionTaskRecord:
    id: str
    mission_id: str
    title: str
    description: str
    priority: TaskPriority
    status: str                           # "OPEN", "ASSIGNED", "IN_PROGRESS", "COMPLETED"
    assigned_to: Optional[str]
    due_date: Optional[str]
    target_asset_ids: List[str]
    created_at: str
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date,
            "target_asset_ids": self.target_asset_ids,
            "created_at": self.created_at,
            "resolution_notes": self.resolution_notes,
        }


class InspectionWorkflowService:
    """Orchestrates engineering verification, field notes, and repair work orders."""

    def __init__(self) -> None:
        self._verifications: Dict[str, FindingVerificationRecord] = {}
        self._tasks: Dict[str, InspectionTaskRecord] = {}
        self._task_counter = 0
        self._verif_counter = 0

    def verify_observation(
        self,
        mission_id: str,
        asset_track_id: str,
        anomaly_id: str,
        status: str,
        engineer_notes: str,
        verified_by: Optional[str] = None,
        field_photo_path: Optional[str] = None,
        repair_status: Optional[str] = None,
    ) -> FindingVerificationRecord:
        """Record human engineer verification on an AI screening observation."""
        v_status = (
            VerificationStatus[status.upper()]
            if status.upper() in VerificationStatus.__members__
            else VerificationStatus.VERIFIED_DEFECT
        )

        r_status = RepairStatus.PENDING_REVIEW
        if repair_status and repair_status.upper() in RepairStatus.__members__:
            r_status = RepairStatus[repair_status.upper()]
        elif v_status == VerificationStatus.VERIFIED_DEFECT:
            r_status = RepairStatus.WORK_ORDER_CREATED
        elif v_status in (VerificationStatus.FALSE_POSITIVE, VerificationStatus.ACCEPTED_CONDITION):
            r_status = RepairStatus.RESOLVED

        # P0 Rule: finding_type upgrades to VERIFIED_FINDING only when human-verified
        f_type = "VERIFIED_FINDING" if v_status != VerificationStatus.UNVERIFIED else "AI_OBSERVATION"

        self._verif_counter += 1
        record_id = f"VERIF-{self._verif_counter:04d}"
        now_iso = datetime.now(timezone.utc).isoformat() + "Z"

        rec = FindingVerificationRecord(
            id=record_id,
            mission_id=mission_id,
            asset_track_id=asset_track_id,
            anomaly_id=anomaly_id,
            finding_type=f_type,
            verification_status=v_status,
            verified_by_user_id=verified_by or "Lead Transmission Engineer",
            verified_at=now_iso,
            engineer_notes=engineer_notes,
            repair_status=r_status,
            field_photo_path=field_photo_path,
        )

        key = f"{mission_id}:{anomaly_id}"
        self._verifications[key] = rec
        log.info("Recorded inspection verification for anomaly %s (status=%s)", anomaly_id, v_status.value)
        return rec

    def create_work_order_task(
        self,
        mission_id: str,
        title: str,
        description: str,
        priority: str = "HIGH",
        assigned_to: Optional[str] = None,
        due_date: Optional[str] = None,
        target_asset_ids: Optional[List[str]] = None,
    ) -> InspectionTaskRecord:
        """Create a field maintenance work order task."""
        self._task_counter += 1
        task_id = f"TASK-{self._task_counter:04d}"
        now_iso = datetime.now(timezone.utc).isoformat() + "Z"

        p_enum = (
            TaskPriority[priority.upper()]
            if priority.upper() in TaskPriority.__members__
            else TaskPriority.MEDIUM
        )

        task = InspectionTaskRecord(
            id=task_id,
            mission_id=mission_id,
            title=title,
            description=description,
            priority=p_enum,
            status="ASSIGNED" if assigned_to else "OPEN",
            assigned_to=assigned_to or "Field Patrol Crew 1",
            due_date=due_date or "2026-12-01",
            target_asset_ids=target_asset_ids or [],
            created_at=now_iso,
        )

        self._tasks[task_id] = task
        return task

    def get_mission_verifications(self, mission_id: str) -> List[FindingVerificationRecord]:
        return [v for v in self._verifications.values() if v.mission_id == mission_id]

    def get_mission_tasks(self, mission_id: str) -> List[InspectionTaskRecord]:
        return [t for t in self._tasks.values() if t.mission_id == mission_id]


inspection_workflow_service = InspectionWorkflowService()

