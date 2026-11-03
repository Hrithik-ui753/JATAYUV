import os
import json
import torch
import shutil
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class CheckpointManager:
    """Manages saving, versioning, loading, and resuming model checkpoints."""

    def __init__(self, save_dir: str, experiment_name: str, model_version: str):
        self.save_dir = os.path.join(save_dir, experiment_name, model_version)
        os.makedirs(self.save_dir, exist_ok=True)
        self.experiment_name = experiment_name
        self.model_version = model_version

    def save_checkpoint(
        self,
        epoch: int,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[Any],
        metrics: Dict[str, Any],
        is_best: bool = False,
        config: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None
    ) -> str:
        """Saves a training checkpoint with full state and reproducible metadata."""
        if filename is None:
            filename = f"checkpoint_epoch_{epoch:03d}.pth"
        filepath = os.path.join(self.save_dir, filename)

        checkpoint = {
            "epoch": epoch,
            "experiment_name": self.experiment_name,
            "model_version": self.model_version,
            "state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
            "metrics": metrics,
            "config": config or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        torch.save(checkpoint, filepath)

        # Save metadata JSON for quick auditing without loading PyTorch weights
        meta_path = filepath.replace(".pth", "_meta.json")
        meta = {
            "epoch": epoch,
            "experiment_name": self.experiment_name,
            "model_version": self.model_version,
            "metrics": metrics,
            "timestamp": checkpoint["timestamp"],
            "config": config or {},
            "is_best": is_best
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        if is_best:
            best_path = os.path.join(self.save_dir, "best_model.pth")
            shutil.copyfile(filepath, best_path)
            shutil.copyfile(meta_path, os.path.join(self.save_dir, "best_model_meta.json"))

        return filepath

    def load_checkpoint(
        self,
        checkpoint_path: str,
        model: torch.nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        device: str = "cpu"
    ) -> Dict[str, Any]:
        """Loads weights and optionally restores optimizer and scheduler state for resuming training."""
        if not os.path.isfile(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at '{checkpoint_path}'")

        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["state_dict"])

        if optimizer and "optimizer_state_dict" in ckpt and ckpt["optimizer_state_dict"]:
            optimizer.load_state_dict(ckpt["optimizer_state_dict"])

        if scheduler and "scheduler_state_dict" in ckpt and ckpt["scheduler_state_dict"]:
            scheduler.load_state_dict(ckpt["scheduler_state_dict"])

        return {
            "epoch": ckpt.get("epoch", 0),
            "metrics": ckpt.get("metrics", {}),
            "config": ckpt.get("config", {}),
            "model_version": ckpt.get("model_version", "unknown"),
            "timestamp": ckpt.get("timestamp")
        }
