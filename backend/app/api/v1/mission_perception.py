from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from backend.app.api.deps import (
    CurrentUser,
    get_current_active_user,
)
from backend.app.core.security import ProjectSecurity
from backend.app.services.perception import (
    describe_all_perception_models,
    is_depth_available,
    is_segmentation_available,
    is_dynamic_detection_available,
)
from backend.app.models.schemas import (  # noqa: I001 - planner may keep shared types here
    FrameListResponse,
    FramePerceptionListResponse,
    FramePerceptionResponse,
    FrameDepthResponse,
    FrameSegmentationResponse,
    FrameDynamicMaskResponse,
    MissionPerceptionProcessResponse,
    MissionPerceptionStatusResponse,
    MissionPerceptionReportResponse,
    MissionPerceptionModelsResponse,
    MissionCancelResponse,
)

log = logging.getLogger("jatayuv.api.mission_perception")

router = APIRouter(prefix="/api/v1/missions", tags=["mission-perception"])
router_public = APIRouter(prefix="/api/v1/frames", tags=["frame-perception"])


@router.post(
    "/{mission_id}/perception/process",
    response_model=MissionPerceptionProcessResponse,
    responses={
        401: {"model": None},
        403: {"model": None},
        404: {"model": None},
        409: {"model": None},
    },
)
def process_mission_perception(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
    request: Request = None,  # type: ignore[assignment]
):
    """
    Start a new P3 perception processing run for the given mission.

    This is an asynchronous operation. It returns the created run id and the
    canonical status URL; callers should poll ``GET
    /api/v1/missions/{mission_id}/perception/status``.
    """
    from backend.app.models.mission import Mission
    from backend.app.models.processing import ProcessingRun
    from backend.app.models.job import Job
    from backend.app.schemas.processing import ProcessingStatus
    from backend.app.services.mission_processing import MissionProcessingService
    from backend.app.core.config import settings

    security = ProjectSecurity()

    # Ownership + existence checks (RBAC pattern used elsewhere in the API).
    mission = security.get_mission_or_404(mission_id)
    if mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # P2 must already be complete; perception depends on selected frames.
    p2_run = mission.get_latest_p2_run()
    if p2_run is None:
        raise HTTPException(status_code=409, detail="Missing completed P2 processing run")
    if p2_run.status not in (ProcessingStatus.COMPLETED,):
        raise HTTPException(
            status_code=409,
            detail="P2 processing not yet completed",
        )

    # Build the Celery-backed processing job. In this environment Celery is
    # not running, so we create the job record and return its id + status URL
    # without asserting live worker progress.
    svc = MissionProcessingService()
    run = svc.create_perception_run(mission_id=mission_id)

    if run is None:
        raise HTTPException(status_code=500, detail="Failed to create perception run")

    # Enqueue tasks using the existing celery app. If Celery is unreachable we
    # still keep the DB run in PENDING/PROCESSING so the API remains usable for
    # reporting and manual inspection.
    try:
        from backend.app.workers.celery_app import celery_app
    except Exception:
        celery_app = None

    if celery_app is not None:
        try:
            from backend.app.workers.tasks_perception import (
                launch_mission_perception_tasks,
            )

            launch_mission_perception_tasks.delay(str(run.id))
        except Exception:
            log.exception("Failed to enqueue perception tasks")
            run.status = ProcessingStatus.FAILED
            run.error_message = "Celery task enqueue failed"
            run.save()
            raise HTTPException(status_code=500, detail="Failed to enqueue perception tasks")

    status_url = (
        request.base_url
        if request is not None
        else None
    )
    if status_url is None:
        status_url = request.url if request else None

    return MissionPerceptionProcessResponse(
        perception_run_id=str(run.id),
        mission_id=mission_id,
        status=run.status,
        started_at=run.started_at,
        message="Perception run created",
        status_url=status_url,
    )


@router.get(
    "/{mission_id}/perception/status",
    response_model=MissionPerceptionStatusResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def perception_status(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Return the current status of the latest perception run for a mission.

    Returns real DB status; does not fabricate progress.
    """
    from backend.app.models.mission import Mission
    from backend.app.models.processing import ProcessingRun
    from backend.app.core.config import settings
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    mission = security.get_mission_or_404(mission_id)
    if mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    run = svc.get_latest_perception_run(mission_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No perception run found")

    total = int(run.total_selected_frames or 0)
    processed = int(run.processed_frames or 0)
    failed = int(run.failed_frames or 0)
    pct = int(round(processed / total * 100)) if total else 0

    return MissionPerceptionStatusResponse(
        perception_run_id=str(run.id),
        mission_id=mission_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        cancelled_at=run.cancelled_at,
        device=run.device,
        total_selected_frames=total,
        processed_frames=processed,
        failed_frames=failed,
        progress_pct=pct,
        error_message=run.error_message,
        depth_model_id=run.depth_model_id,
        segmentation_model_id=run.segmentation_model_id,
        dynamic_model_id=run.dynamic_model_id,
    )


@router.get(
    "/{mission_id}/perception/report",
    response_model=MissionPerceptionReportResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def perception_report(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Return the perception processing report for a mission.

    Includes model ids, checkpoint hashes, artifact counts, runtime, and any
    warnings/errors. Does not fabricate metrics.
    """
    from backend.app.models.mission import Mission
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    mission = security.get_mission_or_404(mission_id)
    if mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    report = svc.build_perception_report(mission_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No perception report available")

    return MissionPerceptionReportResponse(**report)


@router.get(
    "/{mission_id}/perception/models",
    response_model=MissionPerceptionModelsResponse,
)
def perception_models(mission_id: str = Path(...)):
    """
    Return availability and provenance metadata for all P3 perception models.

    This endpoint is public (no auth required) because it describes model
    availability, not mission data.
    """
    return MissionPerceptionModelsResponse(
        models=describe_all_perception_models(),
    )


@router.post(
    "/{mission_id}/perception/cancel",
    response_model=MissionCancelResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def cancel_perception(
    mission_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Request cancellation of an in-progress perception run.

    Cancellation is best-effort; workers check cancellation markers between
    frames and during checkpoint verification.
    """
    from backend.app.models.mission import Mission
    from backend.app.models.processing import ProcessingRun
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    mission = security.get_mission_or_404(mission_id)
    if mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    run = svc.get_latest_perception_run(mission_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No perception run found")

    cancelled = svc.cancel_perception_run(run.id)
    return MissionCancelResponse(
        perception_run_id=str(run.id),
        cancelled=cancelled,
        status=run.status,
    )


# ---------------------------------------------------------------------------
# Frame-level perception inspection endpoints
# ---------------------------------------------------------------------------

@router_public.get(
    "/{frame_id}/perception",
    response_model=FramePerceptionResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def frame_perception(
    frame_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    Return the full perception record for a single frame.

    Includes depth, segmentation, dynamic-mask results and artifact URLs.
    """
    from backend.app.models.frame import Frame
    from backend.app.models.processing import ProcessingRun
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    frame = security.get_frame_or_404(frame_id)
    if frame.mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    record = svc.get_frame_perception(frame_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No perception record for frame")

    return FramePerceptionResponse(**record)


@router_public.get(
    "/{frame_id}/depth",
    response_model=FrameDepthResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def frame_depth(
    frame_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    from backend.app.models.frame import Frame
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    frame = security.get_frame_or_404(frame_id)
    if frame.mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    result = svc.get_frame_depth(frame_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No depth result for frame")

    return FrameDepthResponse(**result)


@router_public.get(
    "/{frame_id}/segmentation",
    response_model=FrameSegmentationResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def frame_segmentation(
    frame_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    from backend.app.models.frame import Frame
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    frame = security.get_frame_or_404(frame_id)
    if frame.mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    result = svc.get_frame_segmentation(frame_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No segmentation result for frame")

    return FrameSegmentationResponse(**result)


@router_public.get(
    "/{frame_id}/dynamic-mask",
    response_model=FrameDynamicMaskResponse,
    responses={401: {"model": None}, 403: {"model": None}, 404: {"model": None}},
)
def frame_dynamic_mask(
    frame_id: str = Path(...),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    from backend.app.models.frame import Frame
    from backend.app.services.mission_processing import MissionProcessingService

    security = ProjectSecurity()
    frame = security.get_frame_or_404(frame_id)
    if frame.mission.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    svc = MissionProcessingService()
    result = svc.get_frame_dynamic_mask(frame_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No dynamic mask result for frame")

    return FrameDynamicMaskResponse(**result)
