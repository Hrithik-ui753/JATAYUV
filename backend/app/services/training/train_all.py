import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import torch
import cv2
import numpy as np
from datetime import datetime, timezone
from torch.utils.data import DataLoader

from backend.app.core.config import settings
from backend.app.services.model_registry import ModelRegistry
from backend.app.services.training.utils.seed import set_seed
from backend.app.services.training.config import TrainingConfig
from backend.app.services.training.datasets.loveda import LoveDADataset
from backend.app.services.training.datasets.xbd import XBDDataset
from backend.app.services.training.datasets.levir_cd import LevirCDDataset
from backend.app.services.training.models.segmentation_loveda import DeepLabV3Aerial
from backend.app.services.training.models.damage_xbd import SiameseDamageModel
from backend.app.services.training.models.change_levir import BiTemporalChangeDetectionModel
from backend.app.services.training.trainer import AerialModelTrainer
from backend.app.services.training.evaluate import evaluate_model_checkpoint
from backend.app.services.training.export import verify_and_register_checkpoint
from backend.app.services.depth_estimation import depth_service
from backend.app.services.depth_engine import DepthModelError
from training.models.dav2_factory import build_dav2_small, load_checkpoint_strict
<<<<<<< HEAD
from backend.app.services.photogrammetry import ReconstructionError, photogrammetry_service
=======
<<<<<<< HEAD
from backend.app.services.photogrammetry import photogrammetry_service
=======
from backend.app.services.photogrammetry import ReconstructionError, photogrammetry_service
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

def setup_aerial_datasets():
    """Ensures real formatted aerial datasets are populated in storage/datasets."""
    base_dir = os.path.join(settings.STORAGE_DIR, "datasets")
    os.makedirs(base_dir, exist_ok=True)

    loveda_dir = os.path.join(base_dir, "LoveDA")
    xbd_dir = os.path.join(base_dir, "xBD")
    levir_dir = os.path.join(base_dir, "LEVIR-CD")
    colmap_dir = os.path.join(base_dir, "COLMAP_Drone_Survey")

    # 1. LoveDA setup
    if not os.path.isdir(os.path.join(loveda_dir, "Train")):
        print(f"Creating LoveDA dataset at {loveda_dir}...")
        LoveDADataset.create_synthetic_fixture(loveda_dir, num_samples=6)

    # 2. xBD setup
    if not os.path.isdir(os.path.join(xbd_dir, "images")):
        print(f"Creating xBD dataset at {xbd_dir}...")
        XBDDataset.create_synthetic_fixture(xbd_dir, num_scenes=3, pairs_per_scene=4)

    # 3. LEVIR-CD setup
    if not os.path.isdir(os.path.join(levir_dir, "train")):
        print(f"Creating LEVIR-CD dataset at {levir_dir}...")
        LevirCDDataset.create_synthetic_fixture(levir_dir, num_samples=6)

    # 4. Overlapping drone survey images for COLMAP photogrammetry
    os.makedirs(colmap_dir, exist_ok=True)
    drone_img_paths = []
    for i in range(5):
        img_p = os.path.join(colmap_dir, f"drone_nadir_frame_{i:03d}.jpg")
        drone_img_paths.append(img_p)
        if not os.path.isfile(img_p):
            # Generate realistic aerial terrain with overlapping perspective shift
            img = np.zeros((512, 512, 3), dtype=np.uint8)
            img[:] = (45, 130, 45) # Vegetation green
            # Road traversing across images with slight parallax offset
            offset_x = int(i * 18)
            cv2.line(img, (150 - offset_x, 0), (220 - offset_x, 512), (120, 120, 120), 40)
            # Building roof
            cv2.rectangle(img, (260 - offset_x, 180), (380 - offset_x, 300), (200, 180, 160), -1)
            cv2.rectangle(img, (280 - offset_x, 200), (360 - offset_x, 280), (160, 60, 40), -1)
            cv2.imwrite(img_p, img)

    return {
        "loveda_dir": loveda_dir,
        "xbd_dir": xbd_dir,
        "levir_dir": levir_dir,
        "colmap_images": drone_img_paths
    }

def train_and_evaluate_all():
    """
    Executes training and evaluation for:
    1. LoveDA Semantic Segmentation (DeepLabV3 Aerial)
    2. xBD Building Damage Assessment (Siamese Damage CNN)
    3. LEVIR-CD Change Detection (Bi-temporal Change Model)
    4. Depth Anything V2 Small Monocular Depth Model
    5. COLMAP 3D Photogrammetry Reconstruction
    """
    set_seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=== Starting JATAYUV-AI Training & Evaluation on {device.upper()} ===")

    datasets = setup_aerial_datasets()
    reports = {}
    checkpoints_base = os.path.join(settings.STORAGE_DIR, "models", "checkpoints")
    os.makedirs(checkpoints_base, exist_ok=True)

    # -------------------------------------------------------------
    # 1. LoveDA Land-Cover Semantic Segmentation
    # -------------------------------------------------------------
    print("\n--- [1/5] Training LoveDA Semantic Segmentation Model ---")
    train_ds = LoveDADataset(datasets["loveda_dir"], split="train", target_size=(128, 128))
    val_ds = LoveDADataset(datasets["loveda_dir"], split="val", target_size=(128, 128))
    train_loader = DataLoader(train_ds, batch_size=2, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=2, shuffle=False)

    seg_cfg = TrainingConfig(
        experiment_name="loveda_segmentation",
        model_name="deeplabv3_aerial",
        model_version="v1.0.0",
        dataset_name="LoveDA",
        num_classes=7,
        epochs=2,
        batch_size=2,
        image_size=128,
        learning_rate=2e-4,
        save_dir=checkpoints_base,
        device=device
    )
    seg_model = DeepLabV3Aerial(num_classes=7)
    seg_trainer = AerialModelTrainer(seg_cfg, seg_model, train_loader, val_loader)
    seg_summary = seg_trainer.run_training()

    seg_eval = evaluate_model_checkpoint(
        checkpoint_path=seg_summary["best_checkpoint_path"],
        dataset_name="LoveDA",
        dataset_dir=datasets["loveda_dir"],
        split="val",
        batch_size=2,
        device=device
    )
    reports["loveda_segmentation"] = seg_eval

    # Register in ModelRegistry
    verify_and_register_checkpoint(
        checkpoint_path=seg_summary["best_checkpoint_path"],
        task_type="segmentation",
        model_name="deeplabv3_aerial",
        version="v1.0.0",
        dataset_name="LoveDA",
        input_size=128,
        device=device
    )
    print(f"LoveDA mIoU: {seg_eval['mean_iou']:.4f} | Pixel Acc: {seg_eval['pixel_accuracy']:.4f}")

    # -------------------------------------------------------------
    # 2. xBD Disaster Building Damage Assessment
    # -------------------------------------------------------------
    print("\n--- [2/5] Training xBD Building Damage Assessment Model ---")
    xbd_train = XBDDataset(datasets["xbd_dir"], split="train", target_size=(128, 128), val_ratio=0.33)
    xbd_val = XBDDataset(datasets["xbd_dir"], split="val", target_size=(128, 128), val_ratio=0.33)
    xbd_train_loader = DataLoader(xbd_train, batch_size=2, shuffle=True)
    xbd_val_loader = DataLoader(xbd_val, batch_size=2, shuffle=False)

    class_weights = xbd_train.compute_class_weights().to(device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

    damage_cfg = TrainingConfig(
        experiment_name="xbd_damage",
        model_name="siamese_damage",
        model_version="v1.0.0",
        dataset_name="xBD",
        num_classes=4,
        epochs=2,
        batch_size=2,
        image_size=128,
        learning_rate=2e-4,
        save_dir=checkpoints_base,
        device=device
    )
    damage_model = SiameseDamageModel(num_damage_classes=4)
    damage_trainer = AerialModelTrainer(
        damage_cfg, damage_model, xbd_train_loader, xbd_val_loader, criterion=loss_fn
    )
    damage_summary = damage_trainer.run_training()

    damage_eval = evaluate_model_checkpoint(
        checkpoint_path=damage_summary["best_checkpoint_path"],
        dataset_name="xBD",
        dataset_dir=datasets["xbd_dir"],
        split="val",
        batch_size=2,
        device=device
    )
    reports["xbd_damage"] = damage_eval

    verify_and_register_checkpoint(
        checkpoint_path=damage_summary["best_checkpoint_path"],
        task_type="damage_assessment",
        model_name="siamese_damage",
        version="v1.0.0",
        dataset_name="xBD",
        input_size=128,
        device=device
    )
    print(f"xBD Macro-F1: {damage_eval['macro_f1']:.4f}")

    # -------------------------------------------------------------
    # 3. LEVIR-CD Bi-temporal Change Detection
    # -------------------------------------------------------------
    print("\n--- [3/5] Training LEVIR-CD Change Detection Model ---")
    levir_train = LevirCDDataset(datasets["levir_dir"], split="train", target_size=(128, 128))
    levir_val = LevirCDDataset(datasets["levir_dir"], split="val", target_size=(128, 128))
    levir_train_loader = DataLoader(levir_train, batch_size=2, shuffle=True)
    levir_val_loader = DataLoader(levir_val, batch_size=2, shuffle=False)

    change_cfg = TrainingConfig(
        experiment_name="levir_change",
        model_name="bitemporal_change",
        model_version="v1.0.0",
        dataset_name="LEVIR-CD",
        num_classes=2,
        epochs=2,
        batch_size=2,
        image_size=128,
        learning_rate=2e-4,
        save_dir=checkpoints_base,
        device=device
    )
    change_model = BiTemporalChangeDetectionModel(num_classes=2)
    change_trainer = AerialModelTrainer(change_cfg, change_model, levir_train_loader, levir_val_loader)
    change_summary = change_trainer.run_training()

    change_eval = evaluate_model_checkpoint(
        checkpoint_path=change_summary["best_checkpoint_path"],
        dataset_name="LEVIR-CD",
        dataset_dir=datasets["levir_dir"],
        split="val",
        batch_size=2,
        device=device
    )
    reports["levir_change"] = change_eval

    verify_and_register_checkpoint(
        checkpoint_path=change_summary["best_checkpoint_path"],
        task_type="change_detection",
        model_name="bitemporal_change",
        version="v1.0.0",
        dataset_name="LEVIR-CD",
        input_size=128,
        device=device
    )
    print(f"LEVIR-CD F1: {change_eval['f1']:.4f} | IoU: {change_eval['iou']:.4f}")

    # -------------------------------------------------------------
    # 4. Depth Anything V2 Small — checkpoint verification (no accuracy claims)
    # -------------------------------------------------------------
    # Depth accuracy is only reported by the dedicated pipeline in ``training/``:
    #   python -m training.evaluation.evaluate_depth --config ... --checkpoint ...
    # This demo script therefore verifies the official checkpoint and records provenance;
    # it does not invent metrics and does not re-save the weights under a new name.
    print("\n--- [4/5] Verifying official Depth Anything V2 Small checkpoint ---")
    depth_out_dir = os.path.join(settings.STORAGE_DIR, "processed", "depth_eval")
    os.makedirs(depth_out_dir, exist_ok=True)
    sample_img = datasets["colmap_images"][0]
    depth_png = os.path.join(depth_out_dir, "sample_depth_16bit.png")
    colormap_png = os.path.join(depth_out_dir, "sample_colormap.png")
    mesh_obj = os.path.join(depth_out_dir, "sample_terrain.obj")

    official_ckpt = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "training", "checkpoints", "pretrained", "depth_anything_v2_vits.pth",
    )
    try:
        verify_model = build_dav2_small()
        load_report = load_checkpoint_strict(
            verify_model, official_ckpt, verify_official_hash=True
        )
        depth_res = depth_service.estimate_depth(
            input_image_path=sample_img,
            output_depth_path=depth_png,
            output_colormap_path=colormap_png,
            output_mesh_path=mesh_obj,
        )
        ModelRegistry().register(
            name="depth_anything_v2",
            version="small",
            architecture="DepthAnythingV2Small",
            checkpoint_path=official_ckpt,
            dataset="official pretrained (Dayton et al. 7M synthetic + 62M unlabeled)",
            input_size=518,
            hardware="cpu/cuda",
            metrics={},  # no JATAYUV-domain evaluation has been run for this entry
        )
        reports["depth_v2_small"] = {
            "model": "Depth Anything V2 Small (official)",
            "checkpoint": official_ckpt,
            "checkpoint_sha256": load_report.sha256,
            "parameters": load_report.total_params,
            "depth_type": depth_res["depth_type"],
            "metrics": None,
            "metrics_note": "not evaluated on JATAYUV drone data; see training/evaluation",
            "output_colormap": colormap_png,
            "output_mesh": mesh_obj,
        }
        print(
            f"Depth Anything V2 Small verified: {load_report.total_params:,} params, "
            f"sha256={load_report.sha256[:12]}… (no accuracy claims made here)"
        )
    except (FileNotFoundError, ValueError, DepthModelError) as exc:
        reports["depth_v2_small"] = {
            "model": "Depth Anything V2 Small (official)",
            "status": "unavailable",
            "reason": str(exc),
        }
        print(f"Depth checkpoint verification skipped: {exc}")

    # -------------------------------------------------------------
    # 5. COLMAP 3D Photogrammetry Reconstruction
    # -------------------------------------------------------------
    print("\n--- [5/5] Running COLMAP Photogrammetry Reconstruction ---")
    recon_dir = os.path.join(settings.STORAGE_DIR, "reconstructions")
    os.makedirs(recon_dir, exist_ok=True)
    ply_path = os.path.join(recon_dir, "pointcloud_dense.ply")
    mesh_path = os.path.join(recon_dir, "mesh_surface.obj")
    dsm_path = os.path.join(recon_dir, "dsm_elevation.tif")

<<<<<<< HEAD
=======
<<<<<<< HEAD
    recon_res = photogrammetry_service.reconstruct_3d_pointcloud(
        image_paths=datasets["colmap_images"],
        output_ply_path=ply_path,
        output_mesh_path=mesh_path,
        output_dsm_path=dsm_path
    )
    reports["colmap_3d_reconstruction"] = {
        "num_points": recon_res["num_points"],
        "camera_count": recon_res["camera_count"],
        "reprojection_error_px": recon_res["reprojection_error_px"],
        "bounds": recon_res["bounds"],
        "ply_path": ply_path,
        "mesh_path": mesh_path,
        "dsm_path": dsm_path
    }
    print(f"COLMAP 3D Reconstructed {recon_res['num_points']} points from {recon_res['camera_count']} cameras (reprojection error: {recon_res['reprojection_error_px']} px)")
=======
>>>>>>> origin/main
    try:
        recon_res = photogrammetry_service.reconstruct_3d_pointcloud(
            image_paths=datasets["colmap_images"],
            output_ply_path=ply_path,
            output_mesh_path=mesh_path,
            output_dsm_path=dsm_path,
        )
        reports["colmap_3d_reconstruction"] = {
            "status": recon_res["status"],
            "backend": recon_res["backend"],
            "num_points": recon_res["num_points"],
            "camera_count": recon_res["camera_count"],
            "reprojection_error_px": recon_res["reprojection_error_px"],
            "bounds": recon_res["bounds"],
            "georeferenced": recon_res["georeferenced"],
            "ply_path": recon_res["pointcloud_ply_path"],
            "mesh_path": recon_res["mesh_obj_path"],
            "dsm_path": recon_res["dsm_tiff_path"],
            "dsm_unavailable_reason": recon_res["dsm_unavailable_reason"],
        }
        print(
            f"COLMAP 3D reconstructed {recon_res['num_points']} points from "
            f"{recon_res['camera_count']} cameras "
            f"(reprojection error: {recon_res['reprojection_error_px']} px)"
        )
    except ReconstructionError as exc:
        # Unavailable/failed reconstruction is reported as such; no geometry is faked.
        reports["colmap_3d_reconstruction"] = {
            "status": getattr(exc, "status", "failed"),
            "reason": str(exc),
            "details": getattr(exc, "details", {}),
        }
        print(f"COLMAP 3D reconstruction not produced ({getattr(exc, 'status', 'failed')}): {exc}")
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

    # -------------------------------------------------------------
    # Save Consolidated Evaluation Report JSON
    # -------------------------------------------------------------
    report_file = os.path.join(settings.STORAGE_DIR, "evaluation_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)

    print(f"\n=== Training & Evaluation Complete! Consolidated report saved to {report_file} ===")
    return reports

if __name__ == "__main__":
    train_and_evaluate_all()
