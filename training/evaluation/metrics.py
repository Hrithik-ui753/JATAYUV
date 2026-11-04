"""Depth evaluation metrics, alignment and ordinal consistency.

Two families of numbers, never mixed:

* **metric depth** (``gt_unit == 'metre'``): AbsRel, SqRel, RMSE, RMSE-log, delta1/2/3
  are computed directly in metres.
* **relative depth**: no absolute scale exists, so depth is first aligned
  (least-squares scale+shift or median scale) and only scale-invariant / aligned
  numbers plus ordinal consistency are reported. Such numbers are *aligned relative*
  metrics and are never presented as metric accuracy.

``raw_silog`` is always reported in the network's inverse-depth space and needs no
alignment.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np

EPS = 1e-8


def valid_mask(depth: np.ndarray, mask: Optional[np.ndarray]) -> np.ndarray:
    valid = np.isfinite(depth) & (depth > 0)
    if mask is not None:
        valid &= mask > 0.5
    return valid


def align_scale_median(pred: np.ndarray, gt: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Scale prediction so its median matches the GT median on valid pixels."""
    if mask.sum() == 0:
        return pred
    ratio = float(np.median(gt[mask]) / max(np.median(pred[mask]), EPS))
    return pred * ratio


def align_scale_shift(
    pred: np.ndarray, gt: np.ndarray, mask: np.ndarray
) -> Tuple[np.ndarray, Tuple[float, float]]:
    """Least-squares ``a * pred + b`` fit to GT over valid pixels (MiDaS-style)."""
    if mask.sum() < 2:
        return pred, (1.0, 0.0)
    x = pred[mask].astype(np.float64)
    y = gt[mask].astype(np.float64)
    design = np.stack([x, np.ones_like(x)], axis=1)
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    a, b = float(coeffs[0]), float(coeffs[1])
    return (a * pred + b).astype(np.float32), (a, b)


def depth_metrics(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, float]:
    """Standard monocular depth metrics on aligned depth (both in the same unit)."""
    valid = valid_mask(gt, mask) & np.isfinite(pred) & (pred > 0)
    if valid.sum() == 0:
        return {}
    p = pred[valid].astype(np.float64)
    g = gt[valid].astype(np.float64)
    thresh = np.maximum(p / g, g / p)
    return {
        "abs_rel": float(np.mean(np.abs(p - g) / g)),
        "sq_rel": float(np.mean(((p - g) ** 2) / g)),
        "rmse": float(np.sqrt(np.mean((p - g) ** 2))),
        "rmse_log": float(np.sqrt(np.mean((np.log(p) - np.log(g)) ** 2))),
        "delta1": float(np.mean(thresh < 1.25)),
        "delta2": float(np.mean(thresh < 1.25 ** 2)),
        "delta3": float(np.mean(thresh < 1.25 ** 3)),
        "mae": float(np.mean(np.abs(p - g))),
        "num_valid_pixels": int(valid.sum()),
    }


def silog(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray] = None, variance_focus: float = 0.85) -> float:
    """Scale-invariant log error on positive depth-like quantities."""
    valid = valid_mask(gt, mask) & np.isfinite(pred) & (pred > 0)
    if valid.sum() == 0:
        return float("nan")
    diff = np.log(pred[valid].astype(np.float64)) - np.log(gt[valid].astype(np.float64))
    return float(10.0 * np.sqrt(max(np.mean(diff ** 2) - variance_focus * np.mean(diff) ** 2, EPS)))


def ordinal_consistency(
    pred: np.ndarray,
    gt: np.ndarray,
    mask: Optional[np.ndarray] = None,
    num_pairs: int = 20000,
    seed: int = 0,
) -> float:
    """Fraction of sampled pixel pairs whose depth ordering matches the GT ordering."""
    rng = np.random.default_rng(seed)
    valid = valid_mask(gt, mask) & np.isfinite(pred) & (pred > 0)
    idx = np.flatnonzero(valid.reshape(-1))
    if idx.size < 64:
        return float("nan")
    p = pred.reshape(-1)[idx]
    g = gt.reshape(-1)[idx]
    n = min(num_pairs, idx.size // 2)
    i = rng.integers(0, idx.size, n)
    j = rng.integers(0, idx.size, n)
    keep = np.abs(g[i] - g[j]) > 1e-4
    if not np.any(keep):
        return float("nan")
    agree = (np.sign(p[i] - p[j]) == np.sign(g[i] - g[j]))[keep]
    return float(np.mean(agree))


def inverse_to_depth(pred_inverse: np.ndarray, inverse_scale: float) -> np.ndarray:
    """Convert network output to native depth units: depth = inverse_scale / pred."""
    return inverse_scale / np.clip(pred_inverse, EPS, None)


def evaluate_pair(
    pred_inverse: np.ndarray,
    native_depth: np.ndarray,
    mask: np.ndarray,
    inverse_scale: float,
    gt_unit: str,
    align: str = "scale_shift",
) -> Dict[str, float]:
    """Full metric set for one sample, honouring the GT unit."""
    pred_depth = inverse_to_depth(pred_inverse, inverse_scale)
    result: Dict[str, float] = {
        "raw_silog_inverse": silog(
            pred_inverse, inverse_scale / np.clip(native_depth, EPS, None), mask
        )
    }

    if gt_unit == "metre":
        result.update(depth_metrics(pred_depth, native_depth, mask))
        result["aligned"] = 0.0
        return result

    # Relative supervision: align first, and say so.
    if align == "none":
        aligned = pred_depth
        coeffs = (1.0, 0.0)
    elif align == "scale":
        aligned = align_scale_median(pred_depth, native_depth, valid_mask(native_depth, mask))
        coeffs = (1.0, 0.0)
    else:
        aligned, coeffs = align_scale_shift(
            pred_depth, native_depth, valid_mask(native_depth, mask)
        )
    result.update(depth_metrics(aligned, native_depth, mask))
    result["ordinal_consistency"] = ordinal_consistency(pred_depth, native_depth, mask)
    result["align_a"] = coeffs[0]
    result["align_b"] = coeffs[1]
    return result


def aggregate(per_sample: Dict[str, float], count: int) -> Dict[str, float]:
    """Convert per-sample sums into means (helper for the evaluator)."""
    return {k: (v / count if count else float("nan")) for k, v in per_sample.items()}
