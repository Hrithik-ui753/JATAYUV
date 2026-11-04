"""Metric calibration for a relative-depth network.

Depth Anything V2 Small predicts inverse relative depth ``p``. A *relative* prediction
cannot be turned into metres by scaling with a flight altitude; that would fabricate
metric accuracy. The only legitimate route is fitting a calibration against **real
metric ground truth** (LiDAR, stereo, validated photogrammetry) and validating it on
held-out metric data.

This module fits ``depth ≈ 1 / (a * p + b)`` by least squares on log-depth over the
calibration split and reports the residual error on a separate validation split. The
fitted coefficients are written into the checkpoint (``calibration`` key) so the API can
optionally emit metric output with the correct provenance.

Usage::

    python -m training.evaluation.calibration \
        --config training/configs/depth_anything_v2_small_metric.yaml \
        --checkpoint training/checkpoints/finetuned/<exp>/best_model.pth
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader

from training.datasets.drone_depth import DroneDepthDataset, collate_depth_batch
from training.evaluation.metrics import depth_metrics, inverse_to_depth, valid_mask
from training.models.dav2_factory import build_dav2_small, load_checkpoint_strict
from training.utils.io import REPO_ROOT, get, load_config, utc_now_iso, write_json
from training.utils.seed import resolve_device


class CalibrationError(RuntimeError):
    pass


def fit_calibration(
    pairs: List[Dict[str, np.ndarray]], iterations: int = 60
) -> Dict[str, float]:
    """Fit ``depth = 1/(a*p + b)`` on metric ground truth.

    A scipy-free Nelder-Mead/coordinate search would be noise; instead we fit a linear
    model on the *inverse* depth, which is the physically meaningful direction:
    ``1/depth ≈ a*p + b``. That is a plain least-squares problem with a closed form.
    """
    xs: List[np.ndarray] = []
    ys: List[np.ndarray] = []
    for pair in pairs:
        pred = pair["pred"]
        gt = pair["gt"]
        mask = valid_mask(gt, pair.get("mask")) & np.isfinite(pred) & (pred > 0)
        if mask.sum() < 100:
            continue
        xs.append(pred[mask])
        ys.append(1.0 / np.maximum(gt[mask], 1e-6))
    if not xs:
        raise CalibrationError("No valid metric pixels available for calibration")
    x = np.concatenate(xs).astype(np.float64)
    y = np.concatenate(ys).astype(np.float64)
    design = np.stack([x, np.ones_like(x)], axis=1)
    (a, b), *_ = np.linalg.lstsq(design, y, rcond=None)
    if not np.isfinite(a) or abs(a) < 1e-9:
        raise CalibrationError("Degenerate calibration fit (scale coefficient ~0)")
    return {
        "a": float(a),
        "b": float(b),
        "form": "depth = 1 / (a * pred + b)",
        "num_pixels": int(x.size),
        "fitted_utc": utc_now_iso(),
    }


@torch.no_grad()
def collect_predictions(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
    max_batches: Optional[int] = None,
) -> List[Dict[str, np.ndarray]]:
    model.eval()
    collected: List[Dict[str, np.ndarray]] = []
    for index, batch in enumerate(loader):
        if max_batches and index >= max_batches:
            break
        pred = model(batch["image"].to(device)).detach().float().cpu().numpy()
        for i in range(pred.shape[0]):
            collected.append(
                {
                    "pred": pred[i],
                    "gt": batch["native_depth"].numpy()[i, 0],
                    "mask": batch["mask"].numpy()[i, 0],
                    "unit": batch["meta"][i]["depth_unit"],
                }
            )
    return collected


def validate_calibration(
    pairs: List[Dict[str, np.ndarray]], calibration: Dict[str, float]
) -> Dict[str, Any]:
    results: List[Dict[str, float]] = []
    for pair in pairs:
        gt = pair["gt"]
        unit = pair.get("unit")
        if unit != "metre":
            raise CalibrationError(
                f"Calibration validation requires metric GT, got unit={unit!r}"
            )
        depth = 1.0 / (calibration["a"] * pair["pred"] + calibration["b"] + 1e-9)
        metrics = depth_metrics(depth, gt, pair.get("mask"))
        if metrics:
            results.append(metrics)
    if not results:
        return {"status": "no_valid_pixels"}
    keys = ["abs_rel", "rmse", "delta1", "delta2", "delta3", "rmse_log"]
    return {
        "status": "ok",
        "num_samples": len(results),
        **{
            key: float(np.mean([r[key] for r in results if key in r]))
            for key in keys
            if any(key in r for r in results)
        },
        "note": "Metrics are metric (metres) on held-out calibrated validation data.",
    }


def calibrate_from_config(cfg: Dict[str, Any], checkpoint: str) -> Dict[str, Any]:
    device = resolve_device(get(cfg, "training.device", "auto"))
    manifest = os.path.join(REPO_ROOT, get(cfg, "data.manifest", ""))
    image_size = int(get(cfg, "data.image_size", 518))

    cal_ds = DroneDepthDataset(manifest, split="train", image_size=image_size, augment=False)
    val_ds = DroneDepthDataset(manifest, split="val", image_size=image_size, augment=False)
    cal_loader = DataLoader(cal_ds, batch_size=1, shuffle=False, collate_fn=collate_depth_batch)
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, collate_fn=collate_depth_batch)

    model = build_dav2_small()
    report = load_checkpoint_strict(model, checkpoint).as_dict()
    model.to(device).eval()

    pairs = collect_predictions(model, cal_loader, device)
    if pairs and pairs[0]["unit"] != "metre":
        raise CalibrationError(
            "Metric calibration requires a dataset with metric ground truth "
            f"(depth.unit == 'metre'); got {pairs[0]['unit']!r}. Relative data cannot "
            "produce a metric calibration."
        )
    calibration = fit_calibration(pairs)
    validation = validate_calibration(collect_predictions(model, val_loader, device), calibration)
    return {
        "checkpoint": checkpoint,
        "checkpoint_sha256": report["sha256"],
        "calibration": calibration,
        "validation": validation,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fit metric calibration for relative depth")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--write-back", action="store_true",
                        help="store calibration inside the checkpoint (adds a 'calibration' key)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    checkpoint = os.path.join(REPO_ROOT, args.checkpoint) if not os.path.isabs(args.checkpoint) else args.checkpoint
    try:
        result = calibrate_from_config(cfg, checkpoint)
    except CalibrationError as exc:
        print(f"[calibration] unavailable: {exc}")
        return 3

    output = os.path.join(REPO_ROOT, os.path.dirname(args.checkpoint), "calibration.json")
    write_json(result, output)
    print(f"[calibration] {result['calibration']}")
    print(f"[calibration] validation: {result['validation']}")

    if args.write_back and result["validation"].get("status") == "ok":
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        payload["calibration"] = result["calibration"]
        payload["calibration_validation"] = result["validation"]
        torch.save(payload, checkpoint)
        print("[calibration] written into checkpoint")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
