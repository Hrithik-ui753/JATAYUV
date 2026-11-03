import os
import json
import torch
from torch.utils.data import DataLoader
from typing import Dict, Any, Optional

from .utils.metrics import (
    ConfusionMatrix,
    compute_segmentation_metrics,
    compute_damage_metrics,
    compute_change_detection_metrics
)
from .datasets.loveda import LoveDADataset
from .datasets.xbd import XBDDataset
from .datasets.levir_cd import LevirCDDataset
from .models.segmentation_loveda import DeepLabV3Aerial
from .models.damage_xbd import SiameseDamageModel
from .models.change_levir import BiTemporalChangeDetectionModel

def evaluate_model_checkpoint(
    checkpoint_path: str,
    dataset_name: str,
    dataset_dir: str,
    split: str = "val",
    batch_size: int = 4,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Evaluates a trained model checkpoint against real or benchmark aerial datasets.
    Computes exact, un-fabricated metrics:
    - LoveDA: Pixel Accuracy, Per-class IoU, Mean IoU, Precision, Recall
    - xBD: Macro-F1, Per-class Precision, Per-class Recall, Confusion Matrix
    - LEVIR-CD: Precision, Recall, F1, IoU
    """
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    dev = torch.device(device if (device == "cuda" and torch.cuda.is_available()) else "cpu")
    raw = torch.load(checkpoint_path, map_location=dev)
    state_dict = raw["state_dict"] if "state_dict" in raw else raw

    if dataset_name == "LoveDA":
        dataset = LoveDADataset(dataset_dir, split=split, transform=False)
        model = DeepLabV3Aerial(num_classes=7).to(dev)
        num_classes = 7
        class_names = LoveDADataset.CLASS_NAMES
    elif dataset_name == "xBD":
        dataset = XBDDataset(dataset_dir, split=split, transform=False)
        model = SiameseDamageModel(num_damage_classes=4).to(dev)
        num_classes = 4
        class_names = XBDDataset.CLASS_NAMES
    elif dataset_name in ["LEVIR-CD", "ChangeDetection"]:
        dataset = LevirCDDataset(dataset_dir, split=split, transform=False)
        model = BiTemporalChangeDetectionModel(num_classes=2).to(dev)
        num_classes = 2
        class_names = LevirCDDataset.CLASS_NAMES
    else:
        raise ValueError(f"Unsupported dataset '{dataset_name}'")

    model.load_state_dict(state_dict)
    model.eval()

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    cm = ConfusionMatrix(num_classes=num_classes)

    with torch.no_grad():
        for batch in loader:
            if dataset_name == "LoveDA":
                imgs = batch["image"].to(dev)
                targets = batch["mask"].to(dev)
                preds = torch.argmax(model(imgs), dim=1)
            elif dataset_name == "xBD":
                pre_img = batch["pre_image"].to(dev)
                post_img = batch["post_image"].to(dev)
                targets = batch["damage_mask"].to(dev)
                preds = torch.argmax(model(pre_img, post_img), dim=1)
            else:
                img_a = batch["image_a"].to(dev)
                img_b = batch["image_b"].to(dev)
                targets = batch["mask"].to(dev)
                preds = torch.argmax(model(img_a, img_b), dim=1)

            cm.update(targets.cpu().numpy(), preds.cpu().numpy())

    # Compute genuine metrics
    if dataset_name == "LoveDA":
        results = compute_segmentation_metrics(cm.matrix, class_names=class_names)
    elif dataset_name == "xBD":
        results = compute_damage_metrics(cm.matrix, damage_classes=class_names)
    else:
        results = compute_change_detection_metrics(cm.matrix)

    results["dataset_name"] = dataset_name
    results["split"] = split
    results["num_evaluated_samples"] = len(dataset)
    results["checkpoint_path"] = checkpoint_path

    return results
