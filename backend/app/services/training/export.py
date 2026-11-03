import os
import torch
import numpy as np
from typing import Dict, Any, Optional

from ..model_registry import ModelRegistry
from .models.segmentation_loveda import DeepLabV3Aerial
from .models.damage_xbd import SiameseDamageModel
from .models.change_levir import BiTemporalChangeDetectionModel

def verify_and_register_checkpoint(
    checkpoint_path: str,
    task_type: str,  # "segmentation", "damage_assessment", "change_detection"
    model_name: str,
    version: str,
    dataset_name: str,
    input_size: int = 512,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Comprehensive verification and model registration pipeline.
    Ensures:
    1. Checkpoint file exists and contains valid state dict.
    2. Model architecture can be instantiated and load weights cleanly.
    3. Forward inference passes on synthetic aerial tensor.
    4. Output shapes and class ranges strictly conform to API contracts.
    5. ONLY when tests pass, registers the model into central ModelRegistry.
    """
    if not os.path.isfile(checkpoint_path):
        return {
            "success": False,
            "error": f"Checkpoint file does not exist at {checkpoint_path}",
            "registered": False
        }

    dev = torch.device(device if (device == "cuda" and torch.cuda.is_available()) else "cpu")

    try:
        raw = torch.load(checkpoint_path, map_location=dev)
        state_dict = raw["state_dict"] if "state_dict" in raw else raw

        # Instantiate appropriate model architecture
        if task_type == "segmentation":
            model = DeepLabV3Aerial(num_classes=7).to(dev)
            class_labels = {
                0: "Background", 1: "Building", 2: "Road",
                3: "Water", 4: "Barren", 5: "Forest", 6: "Agricultural"
            }
            model.load_state_dict(state_dict)
            model.eval()

            # Test forward inference
            dummy = torch.randn(1, 3, input_size, input_size).to(dev)
            with torch.no_grad():
                out = model(dummy)

            if out.shape != (1, 7, input_size, input_size):
                raise ValueError(f"Output shape mismatch: expected (1, 7, {input_size}, {input_size}), got {out.shape}")

        elif task_type == "damage_assessment":
            model = SiameseDamageModel(num_damage_classes=4).to(dev)
            class_labels = {
                0: "no-damage", 1: "minor-damage", 2: "major-damage", 3: "destroyed"
            }
            model.load_state_dict(state_dict)
            model.eval()

            # Test dual forward inference
            dummy_pre = torch.randn(1, 3, input_size, input_size).to(dev)
            dummy_post = torch.randn(1, 3, input_size, input_size).to(dev)
            with torch.no_grad():
                out = model(dummy_pre, dummy_post)

            if out.shape != (1, 4, input_size, input_size):
                raise ValueError(f"Output shape mismatch: expected (1, 4, {input_size}, {input_size}), got {out.shape}")

        elif task_type == "change_detection":
            model = BiTemporalChangeDetectionModel(num_classes=2).to(dev)
            class_labels = {0: "No Change", 1: "Building Change"}
            model.load_state_dict(state_dict)
            model.eval()

            dummy_t0 = torch.randn(1, 3, input_size, input_size).to(dev)
            dummy_t1 = torch.randn(1, 3, input_size, input_size).to(dev)
            with torch.no_grad():
                out = model(dummy_t0, dummy_t1)

            if out.shape != (1, 2, input_size, input_size):
                raise ValueError(f"Output shape mismatch: expected (1, 2, {input_size}, {input_size}), got {out.shape}")

        else:
            raise ValueError(f"Unsupported task_type: '{task_type}'")

        # Extract metrics if stored in checkpoint
        metrics = raw.get("metrics", {}) if isinstance(raw, dict) else {}

        # Register in central ModelRegistry
        registry = ModelRegistry()
        registry.register(
            name=model_name,
            version=version,
            architecture=model.__class__.__name__,
            checkpoint_path=checkpoint_path,
            dataset=dataset_name,
            input_size=input_size,
            class_labels=class_labels,
            hardware="cpu/cuda",
            metrics=metrics
        )

        return {
            "success": True,
            "registered": True,
            "model_name": model_name,
            "version": version,
            "architecture": model.__class__.__name__,
            "class_labels": class_labels,
            "metrics": metrics
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "registered": False
        }
