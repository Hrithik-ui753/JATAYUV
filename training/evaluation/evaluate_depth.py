"""Evaluate the pretrained vs fine-tuned Depth Anything V2 Small on identical test data.

    python -m training.evaluation.evaluate_depth \
        --config training/configs/depth_anything_v2_small.yaml \
        --checkpoint training/checkpoints/finetuned/exp_b_skyscenes_relative/best_model.pth

Outputs (under ``evaluation.output_dir``):

* ``metrics.json``           -- per-model, per-condition and overall metrics
* ``evaluation_report.md``   -- human-readable comparison
* ``comparisons/*.png``      -- RGB | baseline | fine-tuned | GT | error | valid mask

The report states the supervision unit explicitly and never converts relative depth
numbers into metres.
"""
from __future__ import annotations

import argparse
import os
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

from training.datasets.drone_depth import DroneDepthDataset, collate_depth_batch
from training.evaluation.metrics import (
    align_scale_shift,
    evaluate_pair,
    inverse_to_depth,
    valid_mask,
)
from training.models.dav2_factory import build_dav2_small, load_checkpoint_strict
from training.utils.io import (
    REPO_ROOT,
    get,
    load_config,
    utc_now_iso,
    write_json,
)
from training.utils.seed import git_revision, resolve_device

MODEL_LABELS = {
    "baseline": "Pretrained Depth Anything V2 Small (official)",
    "finetuned": "JATAYUV fine-tuned Depth Anything V2 Small",
}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _depth_to_rgb(depth: np.ndarray, mask: np.ndarray, robust: float = 2.0) -> np.ndarray:
    """Colourise depth using robust percentiles of the valid pixels (visual only)."""
    valid = mask > 0.5
    img = np.zeros_like(depth, dtype=np.float32)
    if valid.any():
        lo, hi = np.percentile(depth[valid], [2, 98])
        if hi - lo < 1e-9:
            hi = lo + 1e-9
        img = np.clip((depth - lo) / (hi - lo), 0.0, 1.0)
    img8 = (img * 255).astype(np.uint8)
    return cv2.applyColorMap(img8, cv2.COLORMAP_TURBO)


def _error_heatmap(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> np.ndarray:
    valid = valid_mask(gt, mask) & np.isfinite(pred) & (pred > 0)
    err = np.zeros_like(gt, dtype=np.float32)
    if valid.any():
        rel = np.abs(pred - gt) / np.maximum(gt, 1e-6)
        cap = np.percentile(rel[valid], 95)
        err = np.clip(rel / max(cap, 1e-6), 0, 1)
    return cv2.applyColorMap((err * 255).astype(np.uint8), cv2.COLORMAP_MAGMA)


def _mask_to_rgb(mask: np.ndarray) -> np.ndarray:
    out = (np.clip(mask, 0, 1) * 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def _label(img: np.ndarray, text: str) -> np.ndarray:
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 26), (0, 0, 0), -1)
    cv2.putText(out, text, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def _summarise(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    keys = [
        "raw_silog_inverse",
        "abs_rel",
        "sq_rel",
        "rmse",
        "rmse_log",
        "delta1",
        "delta2",
        "delta3",
        "mae",
        "ordinal_consistency",
    ]
    out: Dict[str, Any] = {"num_samples": len(records)}
    for key in keys:
        values = [r[key] for r in records if key in r and np.isfinite(r[key])]
        if values:
            out[key] = float(np.mean(values))
    out["num_valid_pixels_total"] = int(sum(r.get("num_valid_pixels", 0) for r in records))
    return out


class DepthEvaluator:
    def __init__(self, cfg: Dict[str, Any], device: Optional[str] = None):
        self.cfg = cfg
        self.device = resolve_device(device or get(cfg, "training.device", "auto"))
        eval_cfg = cfg.get("evaluation", {}) or {}
        self.image_size = int(eval_cfg.get("image_size", get(cfg, "data.image_size", 518)))
        self.align = str(eval_cfg.get("align", "scale_shift"))
        self.batch_size = int(eval_cfg.get("batch_size", 1))
        self.output_dir = _repo_path(
            eval_cfg.get("output_dir", "training/experiments/eval_comparison")
        )
        self.max_visual = int(eval_cfg.get("max_visual_samples", 6))
        self.latency_warmup = int(eval_cfg.get("latency_warmup", 2))
        self.latency_runs = int(eval_cfg.get("latency_runs", 5))

        manifest = _repo_path(get(cfg, "data.manifest", "datasets/manifests/dataset.json"))
        self.dataset = DroneDepthDataset(
            manifest, split="test", image_size=self.image_size, augment=False
        )
        self.loader = DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0,
            collate_fn=collate_depth_batch,
        )
        self.manifest_path = manifest
        # id -> per-model visual payload, filled during evaluation and composed at the end.
        self.visual_cache: Dict[str, Dict[str, Any]] = {}
        self._visual_order: List[str] = []

    # ------------------------------------------------------------------ models
    def load_model(self, checkpoint: str) -> Dict[str, Any]:
        model = build_dav2_small()
        report = load_checkpoint_strict(model, _repo_path(checkpoint)).as_dict()
        model.to(self.device).eval()
        payload: Dict[str, Any] = {}
        if checkpoint.endswith(".pth"):
            try:
                payload = torch.load(_repo_path(checkpoint), map_location="cpu", weights_only=False)
            except Exception:
                payload = {}
        report["checkpoint_epoch"] = payload.get("epoch")
        report["checkpoint_experiment"] = payload.get("experiment")
        report["depth_claim"] = payload.get("depth_claim", "relative")
        report["model"] = model
        report["size_mb"] = round(report["bytes"] / 2**20, 1)
        return report

    # ------------------------------------------------------------------ inference
    @torch.no_grad()
    def predict(self, batch: Dict[str, Any]) -> np.ndarray:
        images = batch["image"].to(self.device)
        depth = self.model(images)
        return depth.detach().float().cpu().numpy()

    def latency(self, batch: Dict[str, Any]) -> Dict[str, float]:
        images = batch["image"].to(self.device)
        if self.device.type == "cuda":
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        with torch.no_grad():
            for _ in range(self.latency_warmup):
                self.model(images)
            if self.device.type == "cuda":
                torch.cuda.synchronize()
            started = time.perf_counter()
            for _ in range(self.latency_runs):
                self.model(images)
            if self.device.type == "cuda":
                torch.cuda.synchronize()
            elapsed = time.perf_counter() - started
        n = max(1, images.shape[0])
        per_run_ms = elapsed / self.latency_runs * 1000.0
        return {
            "batch_size": int(n),
            "latency_ms_per_batch": round(per_run_ms, 2),
            "latency_ms_per_image": round(per_run_ms / n, 2),
            "fps": round(1000.0 * n / per_run_ms, 2) if per_run_ms > 0 else float("nan"),
            "input_size": self.image_size,
            "device": str(self.device),
            "peak_gpu_mb": (
                round(torch.cuda.max_memory_allocated() / 2**20, 1)
                if self.device.type == "cuda"
                else None
            ),
        }

    def evaluate_model(
        self, model_key: str, checkpoint: str, write_visuals: bool = False
    ) -> Dict[str, Any]:
        report = self.load_model(checkpoint)
        self.model = report["model"]
        records: List[Dict[str, Any]] = []
        condition_records: Dict[str, List[Dict[str, Any]]] = {}
        visual_dir = os.path.join(self.output_dir, "comparisons")
        os.makedirs(visual_dir, exist_ok=True)

        started = time.time()
        for batch in self.loader:
            preds = self.predict(batch)
            native = batch["native_depth"].numpy()
            masks = batch["mask"].numpy()
            scales = batch["inverse_scale"].numpy()
            for i in range(preds.shape[0]):
                meta = batch["meta"][i]
                gt_unit = meta["depth_unit"]
                unit = "metre" if gt_unit == "metre" else "relative"
                result = evaluate_pair(
                    preds[i], native[i, 0], masks[i, 0], float(scales[i]), unit, align=self.align
                )
                result["id"] = meta["id"]
                records.append(result)
                extra = meta.get("extra") or {}
                condition = " | ".join(
                    str(extra.get(k))
                    for k in ("town", "weather", "altitude_config")
                    if extra.get(k)
                ) or meta.get("source_dataset", "unknown")
                condition_records.setdefault(condition, []).append(result)

                if write_visuals and len(self._visual_order) < self.max_visual:
                    pred_depth = inverse_to_depth(preds[i], float(scales[i]))
                    self.visual_cache.setdefault(meta["id"], {})[model_key] = {
                        "rgb": self._denormalise(batch["image"][i]),
                        "pred_depth": pred_depth,
                        "native": native[i, 0],
                        "mask": masks[i, 0],
                        "unit": meta.get("depth_unit"),
                        "meta": meta,
                    }
                    if meta["id"] not in self._visual_order:
                        self._visual_order.append(meta["id"])
        elapsed = time.time() - started

        latency = self.latency(next(iter(self.loader)))
        summary = _summarise(records)
        summary.update(
            {
                "model_key": model_key,
                "label": MODEL_LABELS.get(model_key, model_key),
                "checkpoint": os.path.relpath(_repo_path(checkpoint), REPO_ROOT),
                "checkpoint_sha256": report["sha256"],
                "checkpoint_bytes": report["bytes"],
                "model_size_mb": report["size_mb"],
                "encoder": report["encoder"],
                "num_parameters": report["total_params"],
                "depth_claim": report["depth_claim"],
                "gt_unit": "relative (normalized)" if records and "align_a" in records[0] else "metre",
                "alignment": self.align if records and "align_a" in records[0] else "none",
                "latency": latency,
                "wall_seconds": round(elapsed, 2),
                "per_condition": {k: _summarise(v) for k, v in sorted(condition_records.items())},
            }
        )
        return summary

    def write_comparisons(self) -> List[str]:
        """Compose RGB | baseline | fine-tuned | GT | error | mask grids."""
        out_dir = os.path.join(self.output_dir, "comparisons")
        os.makedirs(out_dir, exist_ok=True)
        written: List[str] = []
        for sample_id in self._visual_order:
            entry = self.visual_cache.get(sample_id, {})
            base = entry.get("baseline")
            tuned = entry.get("finetuned")
            reference = tuned or base
            if reference is None:
                continue
            native = reference["native"]
            mask = reference["mask"]
            unit = reference["unit"]
            panels = [_label(reference["rgb"], "RGB")]
            for key, payload in (("baseline", base), ("finetuned", tuned)):
                if payload is None:
                    continue
                pred_depth = payload["pred_depth"]
                aligned = pred_depth
                if unit != "metre":
                    aligned, _ = align_scale_shift(
                        pred_depth, native, valid_mask(native, mask)
                    )
                panels.append(
                    _label(_depth_to_rgb(pred_depth, mask), f"{MODEL_LABELS[key].split(' (' )[0]}")
                )
                panels.append(_label(_error_heatmap(aligned, native, mask), f"{key} |rel err|"))
            panels.append(_label(_depth_to_rgb(native, mask), f"GT depth ({unit})"))
            panels.append(_label(_mask_to_rgb(mask), "valid-depth mask"))
            grid = np.concatenate(panels, axis=1)
            name = f"comparison_{sample_id}.png".replace("/", "_")
            path = os.path.join(out_dir, name)
            cv2.imwrite(path, grid)
            written.append(path)
        return written

    @staticmethod
    def _denormalise(tensor: torch.Tensor) -> np.ndarray:
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = tensor.detach().cpu().numpy().transpose(1, 2, 0)
        img = (img * std + mean) * 255.0
        return cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)

    # ------------------------------------------------------------------ reporting
    def run(self, checkpoint: str, baseline_checkpoint: str) -> Dict[str, Any]:
        os.makedirs(self.output_dir, exist_ok=True)
        if not baseline_checkpoint:
            baseline_checkpoint = get(self.cfg, "model.pretrained_checkpoint", "")
        results = {
            "generated_utc": utc_now_iso(),
            "git_commit": git_revision(REPO_ROOT),
            "config_path": self.cfg.get("_config_path"),
            "split": "test",
            "num_test_samples": len(self.dataset),
            "inverse_depth_scale": self.dataset.inverse_scale,
            "dataset_manifest": os.path.relpath(self.manifest_path, REPO_ROOT),
            "note": (
                "Both models are evaluated on the identical held-out test split. "
                "Depth Anything V2 Small predicts relative inverse depth; for non-metric "
                "GT, depth is scale+shift aligned before error metrics, so numbers are "
                "'aligned relative' metrics and are NOT metric accuracy in metres."
            ),
            "models": {},
        }
        for key, ckpt, visuals in (
            ("baseline", baseline_checkpoint, True),
            ("finetuned", checkpoint, True),
        ):
            if not ckpt or not os.path.isfile(_repo_path(ckpt)):
                results["models"][key] = {"status": "checkpoint_missing", "checkpoint": ckpt}
                continue
            print(f"[eval] {key}: {ckpt}")
            results["models"][key] = self.evaluate_model(key, ckpt, write_visuals=visuals)

        results["comparison"] = self._comparison(results["models"])
        results["visual_comparisons"] = [
            os.path.relpath(p, REPO_ROOT) for p in self.write_comparisons()
        ]
        write_json(results, os.path.join(self.output_dir, "metrics.json"))
        self._write_markdown(results, os.path.join(self.output_dir, "evaluation_report.md"))
        return results

    @staticmethod
    def _comparison(models: Dict[str, Any]) -> Dict[str, Any]:
        base = models.get("baseline") or {}
        tuned = models.get("finetuned") or {}
        if "abs_rel" not in base or "abs_rel" not in tuned:
            return {"status": "incomplete"}
        keys = ["raw_silog_inverse", "abs_rel", "rmse", "delta1", "ordinal_consistency"]
        delta = {}
        for key in keys:
            if key in base and key in tuned:
                delta[key] = {
                    "baseline": base[key],
                    "finetuned": tuned[key],
                    "absolute_change": tuned[key] - base[key],
                    "relative_change_pct": (
                        (tuned[key] - base[key]) / base[key] * 100.0 if base[key] else None
                    ),
                    "better": "lower" if key in ("raw_silog_inverse", "abs_rel", "rmse") else "higher",
                }
        return {"status": "ok", "metrics": delta}

    def _write_markdown(self, results: Dict[str, Any], path: str) -> None:
        base = results["models"].get("baseline", {})
        tuned = results["models"].get("finetuned", {})
        lines = [
            "# JATAYUV depth model evaluation",
            "",
            f"Generated: {results['generated_utc']}  ",
            f"Test split: `{results['split']}` ({results['num_test_samples']} samples)  ",
            f"Manifest: `{results['dataset_manifest']}`",
            "",
            "> Depth Anything V2 Small predicts **relative inverse depth**. Non-metric ground",
            "> truth is scale+shift aligned per image before error metrics, so the numbers",
            "> below are aligned-relative metrics. No metric (metre) accuracy is claimed.",
            "",
            "## Checkpoints",
            "",
            "| Model | Checkpoint | SHA256 (12) | Params | Size | Verified load |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for key in ("baseline", "finetuned"):
            m = results["models"].get(key, {})
            if m.get("status") == "checkpoint_missing":
                lines.append(f"| {key} | {m.get('checkpoint')} | - | - | - | missing |")
                continue
            lines.append(
                f"| {m.get('label')} | `{m.get('checkpoint')}` | `{str(m.get('checkpoint_sha256'))[:12]}` | "
                f"{m.get('num_parameters'):,} | {m.get('model_size_mb')} MB | yes |"
            )

        lines += [
            "",
            "## Metrics",
            "",
            "| Metric | Pretrained | Fine-tuned | Change | Direction |",
            "| --- | --- | --- | --- | --- |",
        ]
        for key, entry in (results.get("comparison", {}).get("metrics") or {}).items():
            pct = entry["relative_change_pct"]
            lines.append(
                f"| {key} | {entry['baseline']:.4f} | {entry['finetuned']:.4f} | "
                f"{(f'{pct:+.1f}%' if pct is not None else 'n/a')} | {entry['better']} is better |"
            )

        lines += ["", "## Runtime", "", "| Item | Pretrained | Fine-tuned |", "| --- | --- | --- |"]
        for key in ("latency_ms_per_image", "fps", "peak_gpu_mb", "wall_seconds"):
            b = (base.get("latency") or {}).get(key, base.get(key, "n/a"))
            t = (tuned.get("latency") or {}).get(key, tuned.get(key, "n/a"))
            lines.append(f"| {key} | {b} | {t} |")

        if base.get("per_condition") and tuned.get("per_condition"):
            lines += ["", "## Per-condition aligned AbsRel", "", "| Condition | Pretrained | Fine-tuned |", "| --- | --- | --- |"]
            for condition in sorted(set(base["per_condition"]) | set(tuned["per_condition"])):
                b = base["per_condition"].get(condition, {}).get("abs_rel")
                t = tuned["per_condition"].get(condition, {}).get("abs_rel")
                lines.append(
                    f"| {condition} | {b:.4f} | {t:.4f} |"
                    if b is not None and t is not None
                    else f"| {condition} | {b} | {t} |"
                )

        lines += [
            "",
            "## Visual comparisons",
            "",
            f"See `comparisons/` in the evaluation output (RGB, predicted depth, GT depth,",
            "absolute-relative-error heatmap, valid-depth mask).",
            "",
        ]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate DAv2 Small baseline vs fine-tuned")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True, help="fine-tuned checkpoint to evaluate")
    parser.add_argument("--baseline-checkpoint", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--set", action="append", default=None, dest="overrides")
    args = parser.parse_args(argv)

    from training.utils.io import apply_overrides

    cfg = apply_overrides(load_config(args.config), args.overrides)
    evaluator = DepthEvaluator(cfg, device=args.device)
    results = evaluator.run(args.checkpoint, args.baseline_checkpoint or "")
    comparison = results.get("comparison", {})
    print(f"[eval] output: {evaluator.output_dir}")
    if comparison.get("status") == "ok":
        for key, entry in comparison["metrics"].items():
            print(
                f"  {key:<20} baseline={entry['baseline']:.4f} "
                f"finetuned={entry['finetuned']:.4f}"
            )
    else:
        print("  comparison incomplete: need both baseline and fine-tuned checkpoints")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
