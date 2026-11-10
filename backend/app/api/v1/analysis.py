import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.image import Image
from backend.app.models.job import Job
from backend.app.models.inference_result import (
    DepthResult,
    SegmentationResult,
    DamageAssessmentResult,
    ChangeDetectionResult,
)
from backend.app.models.user import User
from backend.app.schemas.analysis import (
    DepthTriggerRequest,
    DepthResponse,
    DepthModelInfo,
    SegmentationTriggerRequest,
    SegmentationResponse,
    DamageTriggerRequest,
    DamageResponse,
    ChangeTriggerRequest,
    ChangeResponse,
)
from backend.app.services.depth_estimation import depth_service
from backend.app.services.depth_engine import DepthModelError
<<<<<<< HEAD
=======
<<<<<<< HEAD
from backend.app.services.segmentation import segmentation_service
from backend.app.services.damage_assessment import damage_service
=======
>>>>>>> origin/main
from backend.app.services.segmentation import (
    SegmentationModelUnavailable,
    segmentation_service,
)
from backend.app.services.damage_assessment import (
    DamageModelUnavailable,
    damage_service,
)
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
from backend.app.services.change_detection import change_service
from backend.app.api.deps import get_current_user, check_project_owner

router = APIRouter(prefix="/analysis", tags=["AI Inference Services"])

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main

def _unavailable_detail(service: str, exc: Exception) -> dict:
    """Structured 503 payload: the model is unavailable, not failed."""
    return {
        "status": "unavailable",
        "service": service,
        "reason": getattr(exc, "reason", "not_available"),
        "checkpoint_path": getattr(exc, "checkpoint_path", None),
        "message": str(exc),
    }


<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
# --- 1. Monocular Depth Estimation ---
def _depth_response(record: DepthResult) -> DepthResponse:
    """Map an ORM row to the API model without faking metric depth.

    The legacy ``*_depth_m`` columns are only meaningful for calibrated metric output.
    For relative results they are reported as ``None`` so clients cannot read a
    normalised relative field as metres.
    """
    is_metric = (record.depth_type or "relative") == "metric_calibrated"
    return DepthResponse(
        id=record.id,
        job_id=record.job_id,
        image_id=record.image_id,
        depth_map_path=record.depth_map_path,
        colormap_path=record.colormap_path,
        min_depth_m=record.min_depth_m if is_metric else None,
        max_depth_m=record.max_depth_m if is_metric else None,
        mean_depth_m=record.mean_depth_m if is_metric else None,
        mesh_obj_path=record.mesh_obj_path,
        depth_type=record.depth_type or "relative",
        depth_unit=record.depth_unit or "relative_inverse_depth",
        is_metric=is_metric,
        relative_min=record.relative_min,
        relative_max=record.relative_max,
        relative_mean=record.relative_mean,
        model_id=record.model_id,
        model_label=record.model_label,
        model_version=record.model_version,
        checkpoint_path=record.checkpoint_path,
        checkpoint_sha256=record.checkpoint_sha256,
        input_size=record.input_size,
        inference_ms=record.inference_ms,
        raw_depth_path=record.raw_depth_path,
        created_at=record.created_at,
    )


@router.get("/depth/models", response_model=list[DepthModelInfo])
def list_depth_models(current_user: User = Depends(get_current_user)):
    """List the selectable depth checkpoints (pretrained vs JATAYUV fine-tuned)."""
    return [DepthModelInfo(**info) for info in depth_service.available_models().values()]


@router.post("/depth", response_model=DepthResponse)
def trigger_depth_estimation(
    req: DepthTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image = db.query(Image).filter(Image.id == req.image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    check_project_owner(image.project_id, db, current_user)

    job = Job(
        project_id=image.project_id,
        job_type="depth_estimation",
        status="processing",
        progress_pct=25,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Output paths
    depth_path = os.path.join(settings.PROCESSED_DIR, f"depth_{image.id}.png")
    colormap_path = os.path.join(settings.PROCESSED_DIR, f"colormap_{image.id}.png")
    mesh_path = os.path.join(settings.PROCESSED_DIR, f"mesh_{image.id}.obj")
    raw_path = os.path.join(settings.PROCESSED_DIR, f"depth_{image.id}.npy")

    try:
        res = depth_service.estimate_depth(
            input_image_path=image.file_path,
            output_depth_path=depth_path,
            output_colormap_path=colormap_path,
            output_mesh_path=mesh_path,
            model_id=req.model_id,
            input_size=req.input_size,
            output_raw_path=raw_path,
        )
    except DepthModelError as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
<<<<<<< HEAD
=======
<<<<<<< HEAD
        raise HTTPException(status_code=503, detail=str(exc))
=======
>>>>>>> origin/main
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_unavailable_detail("depth_estimation", exc),
        )
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Depth inference failed: {exc}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Depth inference failed: {exc}")

    depth_record = DepthResult(
        job_id=job.id,
        image_id=image.id,
        depth_map_path=res["depth_map_path"],
        colormap_path=res["colormap_path"],
        # Legacy NOT NULL columns: 0.0 placeholder unless genuinely metric.
        min_depth_m=res["min_depth_m"] if res["min_depth_m"] is not None else 0.0,
        max_depth_m=res["max_depth_m"] if res["max_depth_m"] is not None else 0.0,
        mean_depth_m=res["mean_depth_m"] if res["mean_depth_m"] is not None else 0.0,
        mesh_obj_path=res["mesh_obj_path"],
        depth_type=res["depth_type"],
        depth_unit=res["depth_unit"],
        model_id=res["model_id"],
        model_label=res["model_label"],
        model_version=res["model_version"],
        checkpoint_path=res["checkpoint_path"],
        checkpoint_sha256=res["checkpoint_sha256"],
        input_size=res["input_size"],
        inference_ms=res["inference_ms"],
        relative_min=res["relative_min"],
        relative_max=res["relative_max"],
        relative_mean=res["relative_mean"],
        raw_depth_path=res["raw_depth_path"],
    )
    db.add(depth_record)
    job.status = "completed"
    job.progress_pct = 100
    db.commit()
    db.refresh(depth_record)
    return _depth_response(depth_record)


@router.get("/depth/{image_id}", response_model=DepthResponse)
def get_depth_result(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(DepthResult).filter(DepthResult.image_id == image_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Depth inference result not found")
    return _depth_response(record)


# --- 2. Semantic Segmentation ---
@router.post("/segmentation", response_model=SegmentationResponse)
def trigger_segmentation(
    req: SegmentationTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image = db.query(Image).filter(Image.id == req.image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    check_project_owner(image.project_id, db, current_user)

    job = Job(
        project_id=image.project_id,
        job_type="semantic_segmentation",
        status="processing",
        progress_pct=30,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    mask_path = os.path.join(settings.PROCESSED_DIR, f"segmask_{image.id}.png")
    overlay_path = os.path.join(settings.PROCESSED_DIR, f"segoverlay_{image.id}.png")
    geojson_path = os.path.join(settings.PROCESSED_DIR, f"buildings_{image.id}.geojson")

<<<<<<< HEAD
=======
<<<<<<< HEAD
    res = segmentation_service.segment_aerial_image(
        input_image_path=image.file_path,
        output_mask_path=mask_path,
        output_overlay_path=overlay_path,
        output_geojson_path=geojson_path,
    )
=======
>>>>>>> origin/main
    try:
        res = segmentation_service.segment_aerial_image(
            input_image_path=image.file_path,
            output_mask_path=mask_path,
            output_overlay_path=overlay_path,
            output_geojson_path=geojson_path,
        )
    except SegmentationModelUnavailable as exc:
        # No verified checkpoint: report unavailability. Nothing is persisted, so a
        # random-weight "prediction" can never surface later as a stored result.
        job.status = "failed"
        job.error_message = f"Segmentation model unavailable: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_unavailable_detail("semantic_segmentation", exc),
        ) from exc
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Segmentation inference failed: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation inference failed: {exc}",
        ) from exc
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

    seg_record = SegmentationResult(
        job_id=job.id,
        image_id=image.id,
        mask_path=res["mask_path"],
        overlay_path=res["overlay_path"],
        class_distribution_json=json.dumps(res["class_distribution"]),
        geojson_path=res["geojson_path"],
    )
    db.add(seg_record)
    job.status = "completed"
    job.progress_pct = 100
    db.commit()
    db.refresh(seg_record)

    return SegmentationResponse(
        id=seg_record.id,
        job_id=seg_record.job_id,
        image_id=seg_record.image_id,
        mask_path=seg_record.mask_path,
        overlay_path=seg_record.overlay_path,
        class_distribution=res["class_distribution"],
        geojson_path=seg_record.geojson_path,
        created_at=seg_record.created_at,
    )

@router.get("/segmentation/{image_id}", response_model=SegmentationResponse)
def get_segmentation_result(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(SegmentationResult).filter(SegmentationResult.image_id == image_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Segmentation result not found")
    return SegmentationResponse(
        id=record.id,
        job_id=record.job_id,
        image_id=record.image_id,
        mask_path=record.mask_path,
        overlay_path=record.overlay_path,
        class_distribution=json.loads(record.class_distribution_json),
        geojson_path=record.geojson_path,
        created_at=record.created_at,
    )


# --- 3. Building Damage Assessment (xBD) ---
@router.post("/damage", response_model=DamageResponse)
def trigger_damage_assessment(
    req: DamageTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pre_img = db.query(Image).filter(Image.id == req.pre_image_id).first()
    post_img = db.query(Image).filter(Image.id == req.post_image_id).first()
    if not pre_img or not post_img:
        raise HTTPException(status_code=404, detail="Pre or Post image not found")
    check_project_owner(post_img.project_id, db, current_user)

    job = Job(
        project_id=post_img.project_id,
        job_type="damage_assessment",
        status="processing",
        progress_pct=20,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    overlay_path = os.path.join(settings.PROCESSED_DIR, f"damage_{post_img.id}.png")
    geojson_path = os.path.join(settings.PROCESSED_DIR, f"damage_{post_img.id}.geojson")

<<<<<<< HEAD
=======
<<<<<<< HEAD
    res = damage_service.assess_damage(
        pre_image_path=pre_img.file_path,
        post_image_path=post_img.file_path,
        output_overlay_path=overlay_path,
        output_geojson_path=geojson_path,
    )
=======
>>>>>>> origin/main
    try:
        res = damage_service.assess_damage(
            pre_image_path=pre_img.file_path,
            post_image_path=post_img.file_path,
            output_overlay_path=overlay_path,
            output_geojson_path=geojson_path,
        )
    except DamageModelUnavailable as exc:
        job.status = "failed"
        job.error_message = f"Damage model unavailable: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_unavailable_detail("damage_assessment", exc),
        ) from exc
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Damage assessment failed: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Damage assessment failed: {exc}",
        ) from exc
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

    damage_record = DamageAssessmentResult(
        job_id=job.id,
        pre_image_id=pre_img.id,
        post_image_id=post_img.id,
        damage_overlay_path=res["damage_overlay_path"],
        total_buildings=res["total_buildings"],
        counts_by_level_json=json.dumps(res["counts_by_level"]),
        damage_percentage=res["damage_percentage"],
        severity_index=res["severity_index"],
        geojson_path=res["geojson_path"],
    )
    db.add(damage_record)
    job.status = "completed"
    job.progress_pct = 100
    db.commit()
    db.refresh(damage_record)

    return DamageResponse(
        id=damage_record.id,
        job_id=damage_record.job_id,
        pre_image_id=damage_record.pre_image_id,
        post_image_id=damage_record.post_image_id,
        damage_overlay_path=damage_record.damage_overlay_path,
        total_buildings=damage_record.total_buildings,
        counts_by_level=res["counts_by_level"],
        damage_percentage=damage_record.damage_percentage,
        severity_index=damage_record.severity_index,
        geojson_path=damage_record.geojson_path,
        created_at=damage_record.created_at,
    )

@router.get("/damage/{pre_id}/{post_id}", response_model=DamageResponse)
def get_damage_result(
    pre_id: str,
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(DamageAssessmentResult)
        .filter(
            DamageAssessmentResult.pre_image_id == pre_id,
            DamageAssessmentResult.post_image_id == post_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Damage assessment result not found")
    return DamageResponse(
        id=record.id,
        job_id=record.job_id,
        pre_image_id=record.pre_image_id,
        post_image_id=record.post_image_id,
        damage_overlay_path=record.damage_overlay_path,
        total_buildings=record.total_buildings,
        counts_by_level=json.loads(record.counts_by_level_json),
        damage_percentage=record.damage_percentage,
        severity_index=record.severity_index,
        geojson_path=record.geojson_path,
        created_at=record.created_at,
    )


# --- 4. Change Detection ---
@router.post("/change", response_model=ChangeResponse)
def trigger_change_detection(
    req: ChangeTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    before_img = db.query(Image).filter(Image.id == req.before_image_id).first()
    after_img = db.query(Image).filter(Image.id == req.after_image_id).first()
    if not before_img or not after_img:
        raise HTTPException(status_code=404, detail="Before or After image not found")
    check_project_owner(after_img.project_id, db, current_user)

    job = Job(
        project_id=after_img.project_id,
        job_type="change_detection",
        status="processing",
        progress_pct=20,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    mask_path = os.path.join(settings.PROCESSED_DIR, f"diffmask_{after_img.id}.png")
    heatmap_path = os.path.join(settings.PROCESSED_DIR, f"diffheat_{after_img.id}.png")

    res = change_service.detect_changes(
        before_image_path=before_img.file_path,
        after_image_path=after_img.file_path,
        output_diff_mask_path=mask_path,
        output_heatmap_path=heatmap_path,
    )

    change_record = ChangeDetectionResult(
        job_id=job.id,
        before_image_id=before_img.id,
        after_image_id=after_img.id,
        diff_mask_path=res["diff_mask_path"],
        heatmap_path=res["heatmap_path"],
        changed_area_pct=res["changed_area_pct"],
        changed_pixels=res["changed_pixels"],
        significance_score=res["significance_score"],
    )
    db.add(change_record)
    job.status = "completed"
    job.progress_pct = 100
    db.commit()
    db.refresh(change_record)
    return change_record

@router.get("/change/{before_id}/{after_id}", response_model=ChangeResponse)
def get_change_result(
    before_id: str,
    after_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(ChangeDetectionResult)
        .filter(
            ChangeDetectionResult.before_image_id == before_id,
            ChangeDetectionResult.after_image_id == after_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Change detection result not found")
    return record

