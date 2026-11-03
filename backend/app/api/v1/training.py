import os
import shutil
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from torch.utils.data import DataLoader

from backend.app.core.config import settings
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.training import (
    DatasetInfoResponse,
    TrainTriggerRequest,
    TrainResponse,
    EvaluateRequest,
    EvaluateResponse,
    ExportCheckpointRequest,
    ExportCheckpointResponse,
)
from backend.app.services.training.config import TrainingConfig
from backend.app.services.training.utils.licensing import DATASET_LICENSES, verify_file_integrity
from backend.app.services.training.datasets.loveda import LoveDADataset
from backend.app.services.training.datasets.xbd import XBDDataset
from backend.app.services.training.datasets.levir_cd import LevirCDDataset
from backend.app.services.training.models.segmentation_loveda import DeepLabV3Aerial
from backend.app.services.training.models.damage_xbd import SiameseDamageModel
from backend.app.services.training.models.change_levir import BiTemporalChangeDetectionModel
from backend.app.services.training.trainer import AerialModelTrainer
from backend.app.services.training.evaluate import evaluate_model_checkpoint
from backend.app.services.training.export import verify_and_register_checkpoint

router = APIRouter(prefix="/training", tags=["AI Training & Evaluation"])

@router.get("/datasets", response_model=List[DatasetInfoResponse])
def get_dataset_info(current_user: User = Depends(get_current_user)):
    """Lists supported datasets, their licenses, classes, and integrity."""
    results = []
    base_data_dir = os.path.join(settings.STORAGE_DIR, "datasets")

    for name, info in DATASET_LICENSES.items():
        ds_dir = os.path.join(base_data_dir, name)
        exists = os.path.isdir(ds_dir)
        classes = info.get("classes") or info.get("damage_classes") or []

        results.append(DatasetInfoResponse(
            dataset_name=name,
            full_name=info["full_name"],
            license=info["license"],
            license_url=info["license_url"],
            author=info["author"],
            citation=info["citation"],
            commercial_use_allowed=info["commercial_use_allowed"],
            classes=classes,
            acquisition_procedure=info["acquisition_procedure"],
            integrity_status={
                "directory": ds_dir,
                "exists": exists,
                "sample_count": len(os.listdir(ds_dir)) if exists else 0
            }
        ))
    return results


@router.post("/train", response_model=TrainResponse)
def trigger_training(
    req: TrainTriggerRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Executes a reproducible training run on LoveDA, xBD, or LEVIR-CD.
    """
    dataset_root = os.path.join(settings.STORAGE_DIR, "datasets", req.dataset_name)

    if req.dataset_name == "LoveDA":
        num_classes = 7
        if not os.path.isdir(dataset_root) or req.use_synthetic_data:
            os.makedirs(dataset_root, exist_ok=True)
            LoveDADataset.create_synthetic_fixture(dataset_root, num_samples=4)

        train_ds = LoveDADataset(dataset_root, split="train", target_size=(req.image_size, req.image_size))
        val_ds = LoveDADataset(dataset_root, split="val", target_size=(req.image_size, req.image_size))
        model = DeepLabV3Aerial(num_classes=num_classes)

    elif req.dataset_name == "xBD":
        num_classes = 4
        if not os.path.isdir(dataset_root) or req.use_synthetic_data:
            os.makedirs(dataset_root, exist_ok=True)
            XBDDataset.create_synthetic_fixture(dataset_root, num_scenes=2, pairs_per_scene=3)

        train_ds = XBDDataset(dataset_root, split="train", target_size=(req.image_size, req.image_size))
        val_ds = XBDDataset(dataset_root, split="val", target_size=(req.image_size, req.image_size))
        model = SiameseDamageModel(num_damage_classes=num_classes)

    elif req.dataset_name in ["LEVIR-CD", "ChangeDetection"]:
        num_classes = 2
        if not os.path.isdir(dataset_root) or req.use_synthetic_data:
            os.makedirs(dataset_root, exist_ok=True)
            LevirCDDataset.create_synthetic_fixture(dataset_root, num_samples=4)

        train_ds = LevirCDDataset(dataset_root, split="train", target_size=(req.image_size, req.image_size))
        val_ds = LevirCDDataset(dataset_root, split="val", target_size=(req.image_size, req.image_size))
        model = BiTemporalChangeDetectionModel(num_classes=num_classes)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported dataset '{req.dataset_name}'. Allowed: LoveDA, xBD, LEVIR-CD"
        )

    train_loader = DataLoader(train_ds, batch_size=req.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=req.batch_size, shuffle=False)

    cfg = TrainingConfig(
        experiment_name=req.experiment_name,
        model_name=req.model_name,
        model_version=req.model_version,
        dataset_name=req.dataset_name,
        num_classes=num_classes,
        epochs=req.epochs,
        batch_size=req.batch_size,
        image_size=req.image_size,
        learning_rate=req.learning_rate,
        seed=req.seed,
        save_dir=os.path.join(settings.STORAGE_DIR, "models", "checkpoints")
    )

    trainer = AerialModelTrainer(
        config=cfg,
        model=model,
        train_loader=train_loader,
        val_loader=val_loader
    )

    summary = trainer.run_training()

    return TrainResponse(
        experiment_name=req.experiment_name,
        model_version=req.model_version,
        best_epoch=summary["best_epoch"],
        best_metric=summary["best_metric"],
        best_checkpoint_path=summary["best_checkpoint_path"],
        test_metrics=summary.get("test_metrics"),
        history_file=summary["history_file"]
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_checkpoint(
    req: EvaluateRequest,
    current_user: User = Depends(get_current_user)
):
    """Evaluates a checkpoint on a specified dataset split and returns un-fabricated metrics."""
    if not os.path.isfile(req.checkpoint_path):
        raise HTTPException(status_code=404, detail=f"Checkpoint not found at: {req.checkpoint_path}")

    try:
        results = evaluate_model_checkpoint(
            checkpoint_path=req.checkpoint_path,
            dataset_name=req.dataset_name,
            dataset_dir=req.dataset_dir,
            split=req.split,
            batch_size=req.batch_size
        )
        return EvaluateResponse(
            dataset_name=results["dataset_name"],
            split=results["split"],
            num_evaluated_samples=results["num_evaluated_samples"],
            checkpoint_path=results["checkpoint_path"],
            metrics=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/export", response_model=ExportCheckpointResponse)
def export_checkpoint(
    req: ExportCheckpointRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validates model contract on synthetic tensor and registers checkpoint in ModelRegistry.
    """
    result = verify_and_register_checkpoint(
        checkpoint_path=req.checkpoint_path,
        task_type=req.task_type,
        model_name=req.model_name,
        version=req.version,
        dataset_name=req.dataset_name,
        input_size=req.input_size
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Checkpoint validation failed: {result.get('error')}"
        )

    return ExportCheckpointResponse(
        success=True,
        registered=True,
        model_name=result.get("model_name"),
        version=result.get("version"),
        architecture=result.get("architecture"),
        class_labels=result.get("class_labels"),
        metrics=result.get("metrics")
    )
