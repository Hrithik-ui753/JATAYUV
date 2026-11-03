import os
import shutil
import tempfile
import pytest
import numpy as np
import torch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.training.utils.seed import set_seed
from backend.app.services.training.utils.licensing import (
    DATASET_LICENSES,
    verify_file_integrity,
    get_dataset_license_info,
)
from backend.app.services.training.utils.metrics import (
    ConfusionMatrix,
    compute_segmentation_metrics,
    compute_damage_metrics,
    compute_change_detection_metrics,
)
from backend.app.services.training.utils.checkpoints import CheckpointManager
from backend.app.services.training.datasets.loveda import LoveDADataset
from backend.app.services.training.datasets.xbd import XBDDataset
from backend.app.services.training.datasets.levir_cd import LevirCDDataset
from backend.app.services.training.models.segmentation_loveda import DeepLabV3Aerial
from backend.app.services.training.models.damage_xbd import SiameseDamageModel
from backend.app.services.training.models.change_levir import BiTemporalChangeDetectionModel
from backend.app.services.training.config import TrainingConfig
from backend.app.services.training.trainer import AerialModelTrainer
from backend.app.services.training.evaluate import evaluate_model_checkpoint
from backend.app.services.training.export import verify_and_register_checkpoint
from backend.app.services.model_registry import ModelRegistry

client = TestClient(app)

@pytest.fixture
def temp_training_dir():
    d = tempfile.mkdtemp(prefix="jatayuv_m07_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)

def test_reproducible_random_seed():
    """Verify reproducible random seeds produce identical tensors."""
    set_seed(1337)
    t1 = torch.randn(5, 5)
    np1 = np.random.rand(5)

    set_seed(1337)
    t2 = torch.randn(5, 5)
    np2 = np.random.rand(5)

    assert torch.equal(t1, t2), "Seeding should produce identical PyTorch tensors"
    assert np.array_equal(np1, np2), "Seeding should produce identical NumPy arrays"

def test_dataset_licensing_and_integrity(temp_training_dir):
    """Verify dataset licenses and file integrity checks."""
    for ds_name in ["LoveDA", "xBD", "LEVIR-CD"]:
        info = get_dataset_license_info(ds_name)
        assert "license" in info
        assert "author" in info
        assert "acquisition_procedure" in info

    # Test file integrity
    dummy_file = os.path.join(temp_training_dir, "test.txt")
    with open(dummy_file, "w") as f:
        f.write("JATAYUV-AI aerial integrity check")

    res = verify_file_integrity(dummy_file)
    assert res["exists"] is True
    assert res["sha256"] is not None
    assert res["size_bytes"] > 0

    # Wrong checksum
    res_bad = verify_file_integrity(dummy_file, expected_sha256="badhash123")
    assert res_bad["verified"] is False

def test_loveda_dataset_pipeline(temp_training_dir):
    """Verify LoveDA dataset loading, pairing, label mapping, and augmentations."""
    LoveDADataset.create_synthetic_fixture(temp_training_dir, num_samples=3)

    integrity = LoveDADataset.verify_integrity(temp_training_dir)
    assert integrity["integrity_passed"] is True
    assert integrity["num_train_samples"] > 0
    assert integrity["num_val_samples"] > 0

    ds = LoveDADataset(temp_training_dir, split="train", target_size=(128, 128))
    assert len(ds) > 0
    sample = ds[0]

    assert sample["image"].shape == (3, 128, 128)
    assert sample["mask"].shape == (128, 128)
    # Class values must be within 0..6
    assert torch.all(sample["mask"] >= 0)
    assert torch.all(sample["mask"] <= 6)

def test_xbd_dataset_pipeline_and_scene_splitting(temp_training_dir):
    """Verify xBD pre/post pairing, polygon parsing, and scene-separated splitting."""
    XBDDataset.create_synthetic_fixture(temp_training_dir, num_scenes=3, pairs_per_scene=2)

    # Train and Val datasets
    train_ds = XBDDataset(temp_training_dir, split="train", target_size=(128, 128), val_ratio=0.33, seed=42)
    val_ds = XBDDataset(temp_training_dir, split="val", target_size=(128, 128), val_ratio=0.33, seed=42)

    # Scene separation test: no scene in train should be present in val
    train_scenes = {p["scene"] for p in train_ds.pairs}
    val_scenes = {p["scene"] for p in val_ds.pairs}
    assert train_scenes.isdisjoint(val_scenes), f"Scene leakage detected! Overlap: {train_scenes & val_scenes}"

    sample = train_ds[0]
    assert sample["pre_image"].shape == (3, 128, 128)
    assert sample["post_image"].shape == (3, 128, 128)
    assert sample["damage_mask"].shape == (128, 128)
    assert torch.all(sample["damage_mask"] >= 0)
    assert torch.all(sample["damage_mask"] <= 3)

    # Class imbalance weights
    weights = train_ds.compute_class_weights()
    assert len(weights) == 4
    assert torch.all(weights > 0)

def test_levir_cd_dataset_pipeline(temp_training_dir):
    """Verify LEVIR-CD bi-temporal image pairing and mask generation."""
    LevirCDDataset.create_synthetic_fixture(temp_training_dir, num_samples=3)

    ds = LevirCDDataset(temp_training_dir, split="train", target_size=(128, 128))
    assert len(ds) > 0
    sample = ds[0]

    assert sample["image_a"].shape == (3, 128, 128)
    assert sample["image_b"].shape == (3, 128, 128)
    assert sample["mask"].shape == (128, 128)
    # Binary mask: 0 or 1
    assert torch.all((sample["mask"] == 0) | (sample["mask"] == 1))

def test_evaluation_metrics_computation():
    """Verify accuracy, IoU, F1, precision, recall computations without fabrication."""
    # 1. Segmentation metrics
    cm_seg = np.array([
        [80, 10, 10],
        [5,  85, 10],
        [5,   5, 90]
    ], dtype=np.int64)
    seg_res = compute_segmentation_metrics(cm_seg, class_names=["Bg", "Building", "Road"])
    assert 0.8 < seg_res["pixel_accuracy"] < 1.0
    assert 0.7 < seg_res["mean_iou"] < 1.0
    assert "Building" in seg_res["per_class_iou"]

    # 2. Damage assessment metrics (Macro-F1)
    cm_dam = np.array([
        [100, 5, 0, 0],
        [5, 80, 5, 0],
        [0, 5, 75, 5],
        [0, 0, 5, 90]
    ], dtype=np.int64)
    dam_res = compute_damage_metrics(cm_dam)
    assert 0.8 < dam_res["macro_f1"] < 1.0
    assert "no-damage" in dam_res["per_class_precision"]
    assert "destroyed" in dam_res["per_class_f1"]

    # 3. Change detection metrics
    cm_cd = np.array([
        [900, 50],   # TN=900, FP=50
        [30, 200]    # FN=30,  TP=200
    ], dtype=np.int64)
    cd_res = compute_change_detection_metrics(cm_cd)
    expected_prec = 200 / (200 + 50)
    expected_rec = 200 / (200 + 30)
    assert abs(cd_res["precision"] - expected_prec) < 1e-3
    assert abs(cd_res["recall"] - expected_rec) < 1e-3
    assert cd_res["f1"] > 0.8
    assert cd_res["iou"] > 0.7

def test_training_loop_and_resume(temp_training_dir):
    """Verify model training on CPU, checkpoint generation, and resume."""
    data_dir = os.path.join(temp_training_dir, "data")
    save_dir = os.path.join(temp_training_dir, "checkpoints")
    LoveDADataset.create_synthetic_fixture(data_dir, num_samples=2)

    train_ds = LoveDADataset(data_dir, split="train", target_size=(64, 64))
    val_ds = LoveDADataset(data_dir, split="val", target_size=(64, 64))
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=2, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=2, shuffle=False)

    cfg = TrainingConfig(
        experiment_name="test_exp",
        model_name="deeplab_test",
        model_version="v0.1",
        dataset_name="LoveDA",
        num_classes=7,
        epochs=1,
        batch_size=2,
        image_size=64,
        save_dir=save_dir,
        device="cpu"
    )

    model = DeepLabV3Aerial(num_classes=7)
    trainer = AerialModelTrainer(cfg, model, train_loader, val_loader)
    summary = trainer.run_training()

    assert summary["best_epoch"] == 1
    best_ckpt = summary["best_checkpoint_path"]
    assert os.path.isfile(best_ckpt)

    # Test resume training from checkpoint
    cfg_resume = TrainingConfig(
        experiment_name="test_exp",
        model_name="deeplab_test",
        model_version="v0.2",
        dataset_name="LoveDA",
        num_classes=7,
        epochs=2,
        batch_size=2,
        image_size=64,
        save_dir=save_dir,
        resume_checkpoint_path=best_ckpt,
        device="cpu"
    )
    model_resume = DeepLabV3Aerial(num_classes=7)
    trainer_resume = AerialModelTrainer(cfg_resume, model_resume, train_loader, val_loader)
    assert trainer_resume.start_epoch == 2

def test_checkpoint_verification_and_registry_export(temp_training_dir):
    """Verify checkpoint contract verification before registration in ModelRegistry."""
    ckpt_path = os.path.join(temp_training_dir, "test_seg_model.pth")
    model = DeepLabV3Aerial(num_classes=7)
    torch.save({"state_dict": model.state_dict(), "metrics": {"mean_iou": 0.82}}, ckpt_path)

    # 1. Invalid path
    res_bad = verify_and_register_checkpoint(
        checkpoint_path="non_existent.pth",
        task_type="segmentation",
        model_name="seg_test",
        version="v1",
        dataset_name="LoveDA",
        input_size=128
    )
    assert res_bad["registered"] is False

    # 2. Valid registration
    res_ok = verify_and_register_checkpoint(
        checkpoint_path=ckpt_path,
        task_type="segmentation",
        model_name="loveda_deeplabv3",
        version="v1.0.0",
        dataset_name="LoveDA",
        input_size=128
    )
    assert res_ok["registered"] is True
    assert res_ok["model_name"] == "loveda_deeplabv3"

    registry = ModelRegistry()
    entry = registry.get("loveda_deeplabv3", "v1.0.0")
    assert entry["architecture"] == "DeepLabV3Aerial"

def test_training_api_endpoints(temp_training_dir):
    """Verify training endpoints for dataset listing, training trigger, and checkpoint export."""
    from backend.app.api.v1.training import get_dataset_info, trigger_training, export_checkpoint
    from backend.app.schemas.training import TrainTriggerRequest, ExportCheckpointRequest

    # 1. List datasets
    datasets = get_dataset_info(current_user=None)
    assert len(datasets) == 3
    names = [d.dataset_name for d in datasets]
    assert "LoveDA" in names
    assert "xBD" in names
    assert "LEVIR-CD" in names

    # 2. Train endpoint with synthetic data
    train_req = TrainTriggerRequest(
        experiment_name="api_test_run",
        model_name="api_seg_model",
        model_version="v1.0.0",
        dataset_name="LoveDA",
        epochs=1,
        batch_size=2,
        image_size=64,
        use_synthetic_data=True
    )
    tdata = trigger_training(train_req, current_user=None)
    assert tdata.best_epoch == 1
    assert os.path.isfile(tdata.best_checkpoint_path)

    # 3. Export endpoint
    export_req = ExportCheckpointRequest(
        checkpoint_path=tdata.best_checkpoint_path,
        task_type="segmentation",
        model_name="api_seg_model",
        version="v1.0.0",
        dataset_name="LoveDA",
        input_size=64
    )
    edata = export_checkpoint(export_req, current_user=None)
    assert edata.registered is True
    assert edata.model_name == "api_seg_model"
