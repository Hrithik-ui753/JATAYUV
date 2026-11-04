"""Fine-tune the official Depth Anything V2 Small model on drone depth supervision.

Reproducible training CLI::

    python -m training.trainers.train_depth \
        --config training/configs/depth_anything_v2_small.yaml

Optional flags: ``--resume <checkpoint>``, ``--epochs N``, ``--device auto|cpu|cuda``,
``--set key.path=value``, ``--limit-train-batches N``.

What this script guarantees
---------------------------
* the base weights are the *official* DAv2-Small release (SHA256 + strict load verified
  before the first optimiser step);
* the model architecture is the vendored official implementation (Small preset only);
* the test split is never used for model selection -- it is evaluated once, after
  training, for reporting;
* checkpoints record the config, dataset manifest hash, base checkpoint hash, loss
  weights and the exact trainable parameter counts.
"""
from __future__ import annotations

import argparse
import math
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from training.datasets.drone_depth import DroneDepthDataset, collate_depth_batch
from training.evaluation.metrics import evaluate_pair
from training.losses.depth_losses import CombinedDepthLoss
from training.models.dav2_factory import (
    SMALL_PARAM_COUNT,
    SMALL_PRESET,
    build_dav2_small,
    configure_trainable,
    load_checkpoint_strict,
    param_groups,
    parameter_counts,
)
from training.utils.io import (
    REPO_ROOT,
    apply_overrides,
    dump_config,
    get,
    load_config,
    sha256_file,
    utc_now_iso,
    write_json,
)
from training.utils.logging import ExperimentLogger
from training.utils.seed import git_revision, resolve_device, seed_worker, set_seed

CHECKPOINT_SCHEMA = "jatayuv.depth.finetune/1"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


class DepthFineTuner:
    """Training loop for Depth Anything V2 Small on (RGB, inverse-depth) pairs."""

    def __init__(
        self,
        cfg: Dict[str, Any],
        device: Optional[str] = None,
        resume_path: Optional[str] = None,
        epochs_override: Optional[int] = None,
        limit_train_batches: Optional[int] = None,
    ):
        self.cfg = cfg
        self.device = resolve_device(device or get(cfg, "training.device", "auto"))
        self.experiment = get(cfg, "experiment.name", "depth_finetune")
        self.out_dir = _repo_path(get(cfg, "experiment.output_dir", f"training/experiments/{self.experiment}"))
        os.makedirs(self.out_dir, exist_ok=True)
        self.logger = ExperimentLogger(self.out_dir)
        self.seed = int(get(cfg, "experiment.seed", 42))
        set_seed(self.seed, deterministic=True)
        self.generator = torch.Generator()
        self.generator.manual_seed(self.seed)

        self.epochs = int(epochs_override or get(cfg, "training.epochs", 1))
        self.limit_train_batches = (
            limit_train_batches
            if limit_train_batches is not None
            else get(cfg, "training.limit_train_batches", None)
        )
        self.limit_eval_batches = get(cfg, "training.limit_eval_batches", None)
        self.grad_accum = int(get(cfg, "training.grad_accum_steps", 1))
        self.grad_clip = float(get(cfg, "training.grad_clip_norm", 1.0))

        self.amp_enabled = self._resolve_amp()
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.amp_enabled)

        self.start_epoch = 0
        self.global_step = 0
        self.best_val = math.inf
        self.best_epoch = -1
        self.epochs_without_improvement = 0
        self.history: List[Dict[str, Any]] = []
        self.base_report: Dict[str, Any] = {}
        self.resumed_from: Optional[str] = None

        self._build_data()
        self._build_model()
        self._build_loss()
        self._build_optimizer()

        if resume_path:
            self._resume(resume_path)

    # ------------------------------------------------------------------ setup
    def _resolve_amp(self) -> bool:
        setting = get(self.cfg, "training.amp", "auto")
        if isinstance(setting, str):
            if setting.lower() == "auto":
                return self.device.type == "cuda"
            return setting.lower() in ("true", "1", "yes")
        return bool(setting) and self.device.type == "cuda"

    def _build_data(self) -> None:
        manifest = _repo_path(get(self.cfg, "data.manifest", "datasets/manifests/dataset.json"))
        if not os.path.isfile(manifest):
            raise FileNotFoundError(
                f"Dataset manifest not found: {manifest}. "
                "Run `python -m training.preprocessing.prepare_dataset --config <config>` first."
            )
        self.manifest_path = manifest
        self.manifest_sha256 = sha256_file(manifest)
        image_size = int(get(self.cfg, "data.image_size", 518))
        aug = bool(get(self.cfg, "data.augment", True))
        rotate90 = bool(get(self.cfg, "data.rotate90", False))
        num_workers = int(get(self.cfg, "data.num_workers", 0))

        self.train_ds = DroneDepthDataset(
            manifest, split="train", image_size=image_size, augment=aug,
            seed=self.seed, rotate90=rotate90,
        )
        self.val_ds = DroneDepthDataset(
            manifest, split="val", image_size=image_size, augment=False, seed=self.seed
        )
        self.test_ds = DroneDepthDataset(
            manifest, split="test", image_size=image_size, augment=False, seed=self.seed
        )
        if len(self.train_ds) == 0:
            raise RuntimeError("Training split is empty; check data.splits.by_flight in the config.")

        self.train_loader = DataLoader(
            self.train_ds,
            batch_size=int(get(self.cfg, "data.train_batch_size", 2)),
            shuffle=True,
            num_workers=num_workers,
            collate_fn=collate_depth_batch,
            worker_init_fn=seed_worker,
            generator=self.generator,
            drop_last=False,
        )
        eval_bs = int(get(self.cfg, "data.eval_batch_size", 1))
        self.val_loader = DataLoader(
            self.val_ds, batch_size=eval_bs, shuffle=False, num_workers=num_workers,
            collate_fn=collate_depth_batch,
        )
        self.test_loader = DataLoader(
            self.test_ds, batch_size=eval_bs, shuffle=False, num_workers=num_workers,
            collate_fn=collate_depth_batch,
        )
        self.inverse_scale = float(self.train_ds.inverse_scale)
        self.logger.log(
            f"data: train={len(self.train_ds)} val={len(self.val_ds)} test={len(self.test_ds)} "
            f"image_size={image_size} inverse_scale={self.inverse_scale:.6f}"
        )

    def _build_model(self) -> None:
        preset = get(self.cfg, "model", {}) or {}
        encoder = str(preset.get("encoder", SMALL_PRESET["encoder"]))
        if encoder != "vits":
            raise ValueError(
                f"Only the official Small encoder ('vits') is supported, got '{encoder}'. "
                "JATAYUV ships Depth Anything V2 Small; do not silently switch variants."
            )
        self.model = build_dav2_small()
        ckpt = _repo_path(get(self.cfg, "model.pretrained_checkpoint", ""))
        expected_sha = get(self.cfg, "model.expected_sha256", None)
        self.base_report = load_checkpoint_strict(
            self.model, ckpt, verify_official_hash=bool(expected_sha), expected_sha256=expected_sha
        ).as_dict()
        expected_params = get(self.cfg, "model.expected_params", SMALL_PARAM_COUNT)
        if self.base_report["total_params"] != int(expected_params):
            raise ValueError(
                f"Base checkpoint has {self.base_report['total_params']} parameters, "
                f"expected {expected_params} for DAv2-Small."
            )
        self.logger.log(
            f"model: DAv2-Small encoder={encoder} params={self.base_report['total_params']} "
            f"tensors={self.base_report['tensor_count']} sha256={self.base_report['sha256'][:12]}…"
        )
        self.logger.log(f"base checkpoint: {self.base_report['checkpoint_path']}")

        strategy = get(self.cfg, "model.finetune.freeze", "full")
        n_blocks = int(get(self.cfg, "model.finetune.unfreeze_last_n_blocks", 2))
        counts = configure_trainable(self.model, strategy, n_blocks, epoch=0)
        self.freeze_strategy = strategy
        self.unfreeze_last_n_blocks = n_blocks
        self.param_counts = counts
        self.model.to(self.device)
        self.logger.log(
            f"freeze strategy: {strategy} | trainable {counts['trainable']:,} / {counts['total']:,} params"
        )

    def _build_loss(self) -> None:
        weights = get(self.cfg, "loss.weights", {"silog": 1.0})
        self.loss_weights = {k: float(v) for k, v in weights.items()}
        self.criterion = CombinedDepthLoss(self.loss_weights)
        self.logger.log(f"loss weights: {self.loss_weights}")

    def _build_optimizer(self) -> None:
        lr = float(get(self.cfg, "training.learning_rate", 3e-5))
        wd = float(get(self.cfg, "training.weight_decay", 1e-4))
        backbone_scale = float(get(self.cfg, "model.finetune.backbone_lr_scale", 0.1))
        groups = param_groups(self.model, lr, backbone_scale, wd)
        if not groups:
            raise RuntimeError("No trainable parameters: check model.finetune.freeze")
        self.optimizer = torch.optim.AdamW(groups, lr=lr, weight_decay=wd)
        self.scheduler = self._make_scheduler()

    def _make_scheduler(self):
        total_steps = max(
            1,
            self.epochs
            * math.ceil(len(self.train_loader) / self.grad_accum)
            - self.global_step,
        )
        warmup = int(get(self.cfg, "training.warmup_steps", 0))
        min_ratio = float(get(self.cfg, "training.min_lr_ratio", 0.05))
        kind = str(get(self.cfg, "training.scheduler", "cosine")).lower()

        if kind == "constant":
            return torch.optim.lr_scheduler.LambdaLR(self.optimizer, lambda step: 1.0)

        def schedule(step: int) -> float:
            if warmup > 0 and step < warmup:
                return max(1e-3, (step + 1) / warmup)
            progress = min(1.0, max(0.0, (step - warmup) / max(1, total_steps - warmup)))
            cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
            return min_ratio + (1.0 - min_ratio) * cosine

        return torch.optim.lr_scheduler.LambdaLR(self.optimizer, schedule)

    # ------------------------------------------------------------------ checkpoints
    def checkpoint_payload(self, epoch: int, metrics: Dict[str, Any], is_best: bool) -> Dict[str, Any]:
        return {
            "schema": CHECKPOINT_SCHEMA,
            "experiment": self.experiment,
            "architecture": "DepthAnythingV2Small",
            "encoder": SMALL_PRESET["encoder"],
            "model_preset": dict(SMALL_PRESET),
            "epoch": epoch,
            "global_step": self.global_step,
            "is_best": is_best,
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "scheduler_state": self.scheduler.state_dict(),
            "scaler_state": self.scaler.state_dict() if self.amp_enabled else None,
            "best_val": self.best_val,
            "metrics": metrics,
            "config": self.cfg,
            "loss_weights": self.loss_weights,
            "freeze_strategy": self.freeze_strategy,
            "param_counts": self.param_counts,
            "dataset": {
                "manifest": os.path.relpath(self.manifest_path, REPO_ROOT),
                "manifest_sha256": self.manifest_sha256,
                "inverse_scale": self.inverse_scale,
                "train_size": len(self.train_ds),
                "val_size": len(self.val_ds),
                "test_size": len(self.test_ds),
                "depth_types": sorted({s.depth.type for s in self.train_ds.samples if s.depth}),
            },
            "base_checkpoint": {
                "path": self.base_report.get("checkpoint_path"),
                "sha256": self.base_report.get("sha256"),
                "source": "official Depth-Anything-V2-Small",
            },
            "depth_claim": "relative",  # never claim metric depth from relative training
            "calibration": None,
            "git_commit": git_revision(REPO_ROOT),
            "saved_utc": utc_now_iso(),
            "resumed_from": self.resumed_from,
        }

    def save_checkpoint(self, name: str, epoch: int, metrics: Dict[str, Any], is_best: bool) -> str:
        directory = os.path.join(
            _repo_path(get(self.cfg, "checkpoint.dir", "training/checkpoints/finetuned")),
            self.experiment,
        )
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name)
        torch.save(self.checkpoint_payload(epoch, metrics, is_best), path)
        return path

    def _resume(self, path: str) -> None:
        path = _repo_path(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Resume checkpoint not found: {path}")
        payload = torch.load(path, map_location="cpu", weights_only=False)
        schema = payload.get("schema")
        if schema != CHECKPOINT_SCHEMA:
            raise ValueError(
                f"Checkpoint schema {schema!r} is not a JATAYUV fine-tuning checkpoint "
                f"({CHECKPOINT_SCHEMA}); refusing to resume."
            )
        self.model.load_state_dict(payload["model_state"], strict=True)
        if "optimizer_state" in payload:
            self.optimizer.load_state_dict(payload["optimizer_state"])
        if payload.get("scheduler_state") and hasattr(self.scheduler, "load_state_dict"):
            try:
                self.scheduler.load_state_dict(payload["scheduler_state"])
            except Exception as exc:  # pragma: no cover - scheduler shape drift
                self.logger.log(f"warning: scheduler state not restored ({exc})")
        if self.amp_enabled and payload.get("scaler_state"):
            self.scaler.load_state_dict(payload["scaler_state"])
        self.start_epoch = int(payload.get("epoch", 0))
        self.global_step = int(payload.get("global_step", 0))
        self.best_val = float(payload.get("best_val", math.inf))
        self.best_epoch = int(payload.get("epoch", -1))
        self.resumed_from = os.path.relpath(path, REPO_ROOT)
        self.logger.log(
            f"resumed from {self.resumed_from} (epoch {self.start_epoch}, best_val {self.best_val:.6f})"
        )

    # ------------------------------------------------------------------ train/val
    def _forward(self, batch: Dict[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
        images = batch["image"].to(self.device, non_blocking=True)
        pred = self.model(images)
        if pred.dim() == 3:
            pred = pred.unsqueeze(1)
        return pred, images

    def train_epoch(self, epoch: int) -> Dict[str, Any]:
        self.model.train()
        self.train_ds.set_epoch(epoch)
        started = time.time()
        running = 0.0
        batches = 0
        term_totals: Dict[str, float] = {}
        num_batches = len(self.train_loader)
        limit = int(self.limit_train_batches) if self.limit_train_batches else num_batches
        self.optimizer.zero_grad(set_to_none=True)

        for step, batch in enumerate(self.train_loader):
            if step >= limit:
                break
            target = batch["target"].to(self.device)
            mask = batch["mask"].to(self.device)

            with torch.amp.autocast("cuda", enabled=self.amp_enabled):
                pred, _ = self._forward(batch)
                loss, terms = self.criterion(pred, target, mask)
                scaled = loss / self.grad_accum

            if self.amp_enabled:
                self.scaler.scale(scaled).backward()
            else:
                scaled.backward()

            if (step + 1) % self.grad_accum == 0 or (step + 1) == limit:
                if self.amp_enabled:
                    self.scaler.unscale_(self.optimizer)
                if self.grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(
                        [p for p in self.model.parameters() if p.requires_grad], self.grad_clip
                    )
                if self.amp_enabled:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad(set_to_none=True)
                self.global_step += 1

            running += float(loss.detach())
            for key, value in terms.items():
                term_totals[key] = term_totals.get(key, 0.0) + value
            batches += 1
            if self.logger and (
                batches % int(get(self.cfg, "training.log_every_n_steps", 5)) == 0
            ):
                lr_now = max(g["lr"] for g in self.optimizer.param_groups)
                self.logger.log(
                    f"epoch {epoch} step {batches}/{limit} loss={float(loss.detach()):.4f} "
                    f"silog={terms.get('silog', float('nan')):.4f} lr={lr_now:.3e}"
                )

        elapsed = time.time() - started
        metrics = {
            "train_loss": running / max(batches, 1),
            "epoch_seconds": round(elapsed, 2),
            # Head LR is the nominal learning rate; the backbone group scales it down.
            "lr": max(group["lr"] for group in self.optimizer.param_groups),
            "lr_backbone": min(group["lr"] for group in self.optimizer.param_groups),
            "steps": batches,
        }
        for key, value in term_totals.items():
            metrics[f"train_{key}"] = value / max(batches, 1)
        if torch.cuda.is_available():
            metrics["peak_gpu_mb"] = round(torch.cuda.max_memory_allocated() / 2**20, 1)
        metrics["rss_mb"] = _process_rss_mb()
        return metrics

    @torch.no_grad()
    def validate(self, loader: Optional[DataLoader] = None, split: str = "val") -> Dict[str, float]:
        self.model.eval()
        loader = loader or self.val_loader
        total_loss = 0.0
        batches = 0
        sums: Dict[str, float] = {}
        counts = 0
        limit = int(self.limit_eval_batches) if self.limit_eval_batches else len(loader)

        for step, batch in enumerate(loader):
            if step >= limit:
                break
            target = batch["target"].to(self.device)
            mask = batch["mask"].to(self.device)
            with torch.amp.autocast("cuda", enabled=self.amp_enabled):
                pred, _ = self._forward(batch)
                loss, _terms = self.criterion(pred, target, mask)
            total_loss += float(loss)
            batches += 1

            pred_np = pred.detach().float().cpu().numpy()
            target_np = target.detach().float().cpu().numpy()
            mask_np = mask.detach().float().cpu().numpy()
            native_np = batch["native_depth"].numpy()
            scales = batch["inverse_scale"].numpy()
            for i in range(pred_np.shape[0]):
                gt_unit = batch["meta"][i]["depth_unit"]
                res = evaluate_pair(
                    pred_np[i, 0],
                    native_np[i, 0],
                    mask_np[i, 0],
                    float(scales[i]),
                    "metre" if gt_unit == "metre" else "relative",
                    align="scale_shift" if gt_unit != "metre" else "none",
                )
                for key in ("abs_rel", "rmse", "delta1", "ordinal_consistency", "raw_silog_inverse"):
                    if key in res and np.isfinite(res[key]):
                        sums[key] = sums.get(key, 0.0) + float(res[key])
                counts += 1

        metrics: Dict[str, float] = {
            f"{split}_loss": total_loss / max(batches, 1),
            f"{split}_samples": counts,
        }
        for key, value in sums.items():
            metrics[f"{split}_{key}"] = value / max(counts, 1)
        return metrics

    # ------------------------------------------------------------------ main loop
    def run(self) -> Dict[str, Any]:
        self.logger.log(
            f"experiment={self.experiment} device={self.device} epochs={self.epochs} "
            f"amp={self.amp_enabled} grad_accum={self.grad_accum}"
        )
        dump_config(self.cfg, os.path.join(self.out_dir, "experiment_config.yaml"))
        write_json(self.base_report, os.path.join(self.out_dir, "base_checkpoint_verification.json"))

        patience = int(get(self.cfg, "training.early_stopping_patience", 0) or 0)
        stopped_early = False

        for epoch in range(self.start_epoch + 1, self.epochs + 1):
            # Gradual unfreezing re-opens blocks as training progresses.
            if self.freeze_strategy == "gradual" and epoch > 1:
                counts = configure_trainable(
                    self.model, "gradual", self.unfreeze_last_n_blocks, epoch=epoch
                )
                if counts["trainable"] != self.param_counts["trainable"]:
                    self.logger.log(
                        f"gradual unfreezing: {counts['trainable']:,} trainable params, "
                        "rebuilding optimiser for newly unfrozen blocks"
                    )
                    self.param_counts = counts
                    self._build_optimizer()

            train_metrics = self.train_epoch(epoch)
            val_metrics = self.validate(split="val")
            row = {
                "epoch": epoch,
                "global_step": self.global_step,
                "train_loss": round(train_metrics["train_loss"], 6),
                "val_loss": round(val_metrics["val_loss"], 6),
                "lr": train_metrics["lr"],
                "epoch_seconds": train_metrics["epoch_seconds"],
            }
            for key, value in {**train_metrics, **val_metrics}.items():
                if key not in row:
                    row[key] = value
            self.history.append(row)
            self.logger.log_epoch({k: _round(v) for k, v in row.items()})

            improved = val_metrics["val_loss"] < self.best_val - 1e-6
            if improved:
                self.best_val = val_metrics["val_loss"]
                self.best_epoch = epoch
                self.epochs_without_improvement = 0
                best_path = self.save_checkpoint(
                    "best_model.pth", epoch, {**train_metrics, **val_metrics}, is_best=True
                )
                self.logger.log(f"new best val_loss={self.best_val:.6f} -> {os.path.basename(best_path)}")
            else:
                self.epochs_without_improvement += 1

            last_path = self.save_checkpoint(
                "last_checkpoint.pth", epoch, {**train_metrics, **val_metrics}, is_best=False
            )
            self.logger.log(f"last checkpoint -> {os.path.basename(last_path)}")

            if patience and self.epochs_without_improvement >= patience:
                self.logger.log(
                    f"early stopping at epoch {epoch} "
                    f"({self.epochs_without_improvement} epochs without improvement)"
                )
                stopped_early = True
                break

        summary: Dict[str, Any] = {
            "experiment": self.experiment,
            "status": "completed",
            "epochs_run": len(self.history),
            "best_epoch": self.best_epoch,
            "best_val": self.best_val,
            "stopped_early": stopped_early,
            "device": str(self.device),
            "amp": self.amp_enabled,
            "freeze_strategy": self.freeze_strategy,
            "param_counts": self.param_counts,
            "base_checkpoint_sha256": self.base_report.get("sha256"),
            "dataset_manifest_sha256": self.manifest_sha256,
            "inverse_scale": self.inverse_scale,
            "loss_weights": self.loss_weights,
            "depth_claim": "relative",
            "completed_utc": utc_now_iso(),
        }

        test_metrics = None
        if get(self.cfg, "training.evaluate_test_after_training", True):
            best_file = os.path.join(
                _repo_path(get(self.cfg, "checkpoint.dir", "training/checkpoints/finetuned")),
                self.experiment,
                "best_model.pth",
            )
            if os.path.isfile(best_file):
                payload = torch.load(best_file, map_location=self.device, weights_only=False)
                self.model.load_state_dict(payload["model_state"], strict=True)
                test_metrics = self.validate(loader=self.test_loader, split="test")
                summary["checkpoint_evaluated"] = os.path.relpath(best_file, REPO_ROOT)
                summary["checkpoint_epoch"] = payload.get("epoch")
                self.logger.log(f"held-out test metrics (evaluated once, not used for selection): {test_metrics}")
            else:
                summary["test_metrics_status"] = "no best checkpoint saved (validation never improved)"

        summary["test_metrics"] = test_metrics
        write_json(summary, os.path.join(self.out_dir, "metrics.json"))
        write_json(
            {"experiment": self.experiment, "history": self.history},
            os.path.join(self.out_dir, "training_history.json"),
        )
        self.logger.log(f"done. summary -> {os.path.join(self.out_dir, 'metrics.json')}")
        return summary


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def _process_rss_mb() -> Optional[float]:
    try:
        import psutil  # type: ignore

        return round(psutil.Process().memory_info().rss / 2**20, 1)
    except Exception:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fine-tune Depth Anything V2 Small on drone depth")
    parser.add_argument("--config", required=True)
    parser.add_argument("--resume", default=None, help="checkpoint to resume from")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--device", default=None, help="auto | cpu | cuda")
    parser.add_argument("--limit-train-batches", type=int, default=None)
    parser.add_argument("--set", action="append", default=None, dest="overrides",
                        help="override config values, e.g. --set training.epochs=2")
    args = parser.parse_args(argv)

    cfg = apply_overrides(load_config(args.config), args.overrides)
    tuner = DepthFineTuner(
        cfg,
        device=args.device,
        resume_path=args.resume,
        epochs_override=args.epochs,
        limit_train_batches=args.limit_train_batches,
    )
    summary = tuner.run()
    print(
        f"\nTrained {summary['epochs_run']} epoch(s); best val_loss={summary['best_val']:.6f} "
        f"at epoch {summary['best_epoch']} on {summary['device']}."
    )
    print("NOTE: the network predicts relative (inverse) depth. No metric claim is made.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
