import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict, Any, Optional
import numpy as np

from .config import TrainingConfig
from .utils.seed import set_seed
from .utils.logger import ExperimentLogger
from .utils.checkpoints import CheckpointManager
from .utils.metrics import (
    ConfusionMatrix,
    compute_segmentation_metrics,
    compute_damage_metrics,
    compute_change_detection_metrics,
)

class AerialModelTrainer:
    """
    Unified, reproducible ML trainer for aerial imagery tasks.
    Supports LoveDA (Segmentation), xBD (Damage), and LEVIR-CD (Change Detection).
    """

    def __init__(
        self,
        config: TrainingConfig,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: Optional[nn.Module] = None,
        test_loader: Optional[DataLoader] = None
    ):
        self.config = config
        self.device = torch.device(config.device if (config.device == "cuda" and torch.cuda.is_available()) else "cpu")
        
        # Enforce reproducibility
        set_seed(config.seed)

        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader

        # Loss function
        self.criterion = criterion or nn.CrossEntropyLoss()

        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        # Learning rate scheduler
        if config.scheduler_type == "cosine":
            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=config.epochs,
                eta_min=config.min_lr
            )
        else:
            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=max(1, config.epochs // 2),
                gamma=0.5
            )

        # Logging & Checkpoint managers
        self.logger = ExperimentLogger(
            log_dir=os.path.join(config.save_dir, "logs"),
            experiment_name=config.experiment_name,
            config=config.model_dump()
        )
        self.checkpoint_mgr = CheckpointManager(
            save_dir=config.save_dir,
            experiment_name=config.experiment_name,
            model_version=config.model_version
        )

        self.start_epoch = 1
        self.best_metric = -1.0
        self.best_epoch = 0

        # Resume if specified
        if config.resume_checkpoint_path:
            self._resume(config.resume_checkpoint_path)

    def _resume(self, checkpoint_path: str):
        self.logger.log(f"Resuming training from checkpoint: {checkpoint_path}")
        info = self.checkpoint_mgr.load_checkpoint(
            checkpoint_path=checkpoint_path,
            model=self.model,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
            device=str(self.device)
        )
        self.start_epoch = info["epoch"] + 1
        self.logger.log(f"Resumed at epoch {self.start_epoch} (recorded metrics: {info['metrics']})")

    def train_epoch(self, epoch: int) -> float:
        self.model.train()
        total_loss = 0.0
        num_batches = len(self.train_loader)

        for batch_idx, batch in enumerate(self.train_loader):
            self.optimizer.zero_grad()

            if self.config.dataset_name == "LoveDA":
                images = batch["image"].to(self.device)
                targets = batch["mask"].to(self.device)
                outputs = self.model(images)
                loss = self.criterion(outputs, targets)

            elif self.config.dataset_name == "xBD":
                pre_img = batch["pre_image"].to(self.device)
                post_img = batch["post_image"].to(self.device)
                targets = batch["damage_mask"].to(self.device)
                outputs = self.model(pre_img, post_img)
                loss = self.criterion(outputs, targets)

            elif self.config.dataset_name in ["LEVIR-CD", "ChangeDetection"]:
                img_a = batch["image_a"].to(self.device)
                img_b = batch["image_b"].to(self.device)
                targets = batch["mask"].to(self.device)
                outputs = self.model(img_a, img_b)
                loss = self.criterion(outputs, targets)
            else:
                raise ValueError(f"Unsupported dataset: {self.config.dataset_name}")

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss

    def validate(self, loader: Optional[DataLoader] = None) -> Dict[str, Any]:
        """Evaluates model performance and reports true metrics."""
        val_loader = loader or self.val_loader
        self.model.eval()

        cm = ConfusionMatrix(num_classes=self.config.num_classes)
        val_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                if self.config.dataset_name == "LoveDA":
                    images = batch["image"].to(self.device)
                    targets = batch["mask"].to(self.device)
                    outputs = self.model(images)
                    preds = torch.argmax(outputs, dim=1)

                elif self.config.dataset_name == "xBD":
                    pre_img = batch["pre_image"].to(self.device)
                    post_img = batch["post_image"].to(self.device)
                    targets = batch["damage_mask"].to(self.device)
                    outputs = self.model(pre_img, post_img)
                    preds = torch.argmax(outputs, dim=1)

                elif self.config.dataset_name in ["LEVIR-CD", "ChangeDetection"]:
                    img_a = batch["image_a"].to(self.device)
                    img_b = batch["image_b"].to(self.device)
                    targets = batch["mask"].to(self.device)
                    outputs = self.model(img_a, img_b)
                    preds = torch.argmax(outputs, dim=1)
                else:
                    break

                loss = self.criterion(outputs, targets)
                val_loss += loss.item()

                cm.update(targets.cpu().numpy(), preds.cpu().numpy())

        # Compute task-specific metrics
        if self.config.dataset_name == "LoveDA":
            metrics = compute_segmentation_metrics(cm.matrix)
            primary_metric_key = "mean_iou"
        elif self.config.dataset_name == "xBD":
            metrics = compute_damage_metrics(cm.matrix)
            primary_metric_key = "macro_f1"
        else:
            metrics = compute_change_detection_metrics(cm.matrix)
            primary_metric_key = "f1"

        metrics["val_loss"] = round(val_loss / max(len(val_loader), 1), 4)
        metrics["primary_metric"] = metrics.get(primary_metric_key, 0.0)
        return metrics

    def run_training(self) -> Dict[str, Any]:
        """Executes full training loop, validation, scheduling, and checkpointing."""
        self.logger.log(
            f"Starting training on device '{self.device}' | Epochs: {self.config.epochs} | "
            f"Batch Size: {self.config.batch_size} | Model: {self.config.model_name}"
        )

        for epoch in range(self.start_epoch, self.config.epochs + 1):
            train_loss = self.train_epoch(epoch)
            
            # Step learning rate scheduler
            current_lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step()

            # Validation
            val_metrics = self.validate()
            self.logger.log_epoch(epoch, train_loss, val_metrics, current_lr)

            # Check if best checkpoint
            score = val_metrics["primary_metric"]
            is_best = score > self.best_metric
            if is_best:
                self.best_metric = score
                self.best_epoch = epoch

            # Save checkpoint
            self.checkpoint_mgr.save_checkpoint(
                epoch=epoch,
                model=self.model,
                optimizer=self.optimizer,
                scheduler=self.scheduler,
                metrics=val_metrics,
                is_best=is_best,
                config=self.config.model_dump()
            )

        # Final testing if test_loader provided
        test_metrics = None
        if self.test_loader is not None and len(self.test_loader) > 0:
            self.logger.log("Evaluating best checkpoint on held-out test split...")
            best_path = os.path.join(self.checkpoint_mgr.save_dir, "best_model.pth")
            if os.path.isfile(best_path):
                self.checkpoint_mgr.load_checkpoint(best_path, self.model, device=str(self.device))
            test_metrics = self.validate(loader=self.test_loader)
            self.logger.log(f"Final Test Metrics: {test_metrics}")

        return {
            "best_epoch": self.best_epoch,
            "best_metric": self.best_metric,
            "best_checkpoint_path": os.path.join(self.checkpoint_mgr.save_dir, "best_model.pth"),
            "test_metrics": test_metrics,
            "history_file": self.logger.history_file
        }
