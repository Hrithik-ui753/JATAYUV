"""AI Models API — list registered model versions and their metadata."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.ai_model_version import AIModelVersion
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.schemas.ai_model import AIModelVersionResponse

router = APIRouter(prefix="/models", tags=["AI Models"])


@router.get("", response_model=List[AIModelVersionResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all registered AI model versions."""
    models = db.query(AIModelVersion).order_by(AIModelVersion.task_type, AIModelVersion.model_name).all()

    # If the table is empty, seed with default entries so the UI always shows something useful
    if not models:
        _seed_default_models(db)
        models = db.query(AIModelVersion).order_by(AIModelVersion.task_type, AIModelVersion.model_name).all()

    return [
        AIModelVersionResponse(
            id=m.id,
            model_name=m.model_name,
            display_name=m.display_name,
            version=m.version,
            task_type=m.task_type,
            description=m.description,
            accuracy_metrics=m.accuracy_metrics or {},
            is_active=m.is_active == "1",
            loaded_at=m.loaded_at,
            created_at=m.created_at,
        )
        for m in models
    ]


@router.get("/{model_id}", response_model=AIModelVersionResponse)
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(AIModelVersion).filter(AIModelVersion.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return AIModelVersionResponse(
        id=m.id,
        model_name=m.model_name,
        display_name=m.display_name,
        version=m.version,
        task_type=m.task_type,
        description=m.description,
        accuracy_metrics=m.accuracy_metrics or {},
        is_active=m.is_active == "1",
        loaded_at=m.loaded_at,
        created_at=m.created_at,
    )


def _seed_default_models(db: Session) -> None:
    """Insert default AI model catalog entries if table is empty."""
    default_models = [
        AIModelVersion(
            model_name="depth_anything_v2",
            display_name="Depth Anything V2 — Large",
            version="2.0.0",
            task_type="depth_estimation",
            description="Monocular depth estimation from single RGB aerial images using a vision transformer backbone. Trained on a combination of labeled and unlabeled data for robust generalisation.",
            accuracy_metrics={"AbsRel": 0.043, "delta1": 0.981, "SILog": 0.058},
            is_active="1",
        ),
        AIModelVersion(
            model_name="segformer_b5_aerial",
            display_name="SegFormer B5 — Aerial Semantic",
            version="1.2.0",
            task_type="segmentation",
            description="Hierarchical transformer encoder for semantic segmentation of aerial imagery into 8 land-cover classes: building, road, vegetation, water, bare soil, vehicle, background, sky.",
            accuracy_metrics={"mIoU": 0.817, "pixel_accuracy": 0.924},
            is_active="1",
        ),
        AIModelVersion(
            model_name="xbd_damage_cnn",
            display_name="xBD Building Damage Classifier",
            version="1.0.0",
            task_type="damage_assessment",
            description="Siamese CNN trained on the xBD disaster dataset. Classifies each building polygon into four damage levels: no damage, minor damage, major damage, destroyed.",
            accuracy_metrics={"F1_weighted": 0.891, "accuracy": 0.902},
            is_active="1",
        ),
        AIModelVersion(
            model_name="siamese_change_detector",
            display_name="Siamese Change Detection Network",
            version="1.1.0",
            task_type="change_detection",
            description="Pixel-level change detection for bi-temporal aerial image pairs. Outputs a binary change mask and a continuous significance heatmap.",
            accuracy_metrics={"F1": 0.874, "IoU": 0.795, "precision": 0.891},
            is_active="1",
        ),
        AIModelVersion(
            model_name="colmap_photogrammetry",
            display_name="COLMAP Structure-from-Motion + Dense MVS",
            version="3.8.0",
            task_type="reconstruction_3d",
            description="Feature extraction and matching (SIFT), incremental SfM, and patch-match MVS for dense 3D point cloud and mesh reconstruction from overlapping aerial image sets.",
            accuracy_metrics={"coverage": 0.94, "point_density": "high"},
            is_active="1",
        ),
    ]
    db.add_all(default_models)
    db.commit()

