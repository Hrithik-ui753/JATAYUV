"""Depth losses for fine-tuning Depth Anything V2 Small.

All losses operate on the network's native output space: Depth Anything predicts a
non-negative *inverse* depth (disparity-like) field, ``pred ~ 1 / depth``. Ground-truth
depth is therefore converted to inverse depth by the dataset (see
``training/datasets/drone_depth.py``), and every loss here is computed in that space
unless stated otherwise.

Why each loss exists (do not add losses without a stated reason):

* ``SILogLoss`` -- scale-invariant log loss. The primary objective when the supervision
  has unknown global scale (photogrammetry, teacher pseudo-labels, per-frame-normalised
  relative depth). It penalises relative rather than absolute error, so an arbitrary
  global scale factor does not dominate the gradient.
* ``MaskedL1Loss`` -- absolute error in inverse-depth space over valid pixels only.
  Used as an auxiliary/validation objective for metrically-calibrated supervision, and
  to keep the loss interpretable (it is reported in the training history).
* ``BerHuLoss`` -- robust L1/L2 hybrid: L1 for small residuals, L2 for large ones. It
  tolerates the heavy tail of aerial depth histograms (thin structures, sky) without
  letting outliers dominate as plain L2 would.
* ``GradientLoss`` -- first-order (Sobel) edge consistency. Aerial scenes contain roofs,
  kerbs and vegetation boundaries with strong depth discontinuities; the plain
  photometric losses over-smooth them. The term is masked so that invalid GT pixels
  never contribute edges.
* ``OrdinalLoss`` -- optional pairwise ranking loss on sampled pixel pairs; used only for
  ordinal-consistency ablations on relative-only supervision (default weight 0).

Weights are explicit in the YAML config (``loss.weights``) and are recorded in the
checkpoint so a run can always be reproduced. No loss weight is hidden in code.
"""
from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

EPS = 1e-8


def masked_mean(values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Mean over valid pixels; returns 0 when a mask is empty (never NaN)."""
    mask = mask.to(values.dtype)
    denom = mask.sum()
    if float(denom) == 0.0:
        return values.sum() * 0.0
    return (values * mask).sum() / denom


class SILogLoss(nn.Module):
    """Scale-invariant logarithmic loss (Eigen et al. 2014, as used by DAv2).

        L = 10 * sqrt(mean(g^2) - lambda * mean(g)^2),  g = log(pred) - log(target)

    ``lambda`` close to 1 removes most of the scale sensitivity. ``variance_focus`` of
    0.85 follows the Depth Anything / MiDaS training recipe.
    """

    def __init__(self, variance_focus: float = 0.85, eps: float = 1e-4):
        super().__init__()
        self.variance_focus = variance_focus
        self.eps = eps

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if mask is None:
            mask = torch.ones_like(target)
        valid = mask > 0.5
        pred_v = pred[valid].clamp(min=self.eps)
        target_v = target[valid].clamp(min=self.eps)
        if pred_v.numel() == 0:
            return pred.sum() * 0.0
        diff = torch.log(pred_v) - torch.log(target_v)
        return 10.0 * torch.sqrt(
            torch.clamp(diff.pow(2).mean() - self.variance_focus * diff.mean().pow(2), min=self.eps)
        )


class MaskedL1Loss(nn.Module):
    """Mean absolute error in inverse-depth space over valid pixels."""

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if mask is None:
            mask = torch.ones_like(target)
        return masked_mean((pred - target).abs(), mask)


class BerHuLoss(nn.Module):
    """Reverse Huber (BerHu) loss with the standard 0.2 threshold."""

    def __init__(self, threshold: float = 0.2):
        super().__init__()
        self.threshold = threshold

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if mask is None:
            mask = torch.ones_like(target)
        diff = (pred - target).abs()
        valid = mask > 0.5
        if int(valid.sum()) == 0:
            return pred.sum() * 0.0
        d = diff[valid]
        c = self.threshold * float(d.max().detach())
        if c <= 0:
            return d.abs().mean()
        return torch.where(d <= c, d, (d.pow(2) + c * c) / (2 * c)).mean()


class GradientLoss(nn.Module):
    """Edge-weighted depth-gradient consistency (Sobel, masked)."""

    def __init__(self):
        super().__init__()
        kx = torch.tensor([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]) / 8.0
        ky = kx.t()
        self.register_buffer("kx", kx.view(1, 1, 3, 3), persistent=False)
        self.register_buffer("ky", ky.contiguous().view(1, 1, 3, 3), persistent=False)

    def _grad(self, x: torch.Tensor) -> torch.Tensor:
        gx = F.conv2d(x, self.kx, padding=1)
        gy = F.conv2d(x, self.ky, padding=1)
        return torch.sqrt(gx * gx + gy * gy + EPS)

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if pred.dim() == 3:
            pred = pred.unsqueeze(1)
            target = target.unsqueeze(1)
            if mask is not None and mask.dim() == 3:
                mask = mask.unsqueeze(1)
        gp = self._grad(pred)
        gt = self._grad(target)
        if mask is None:
            return (gp - gt).abs().mean()
        valid = (mask > 0.5).to(pred.dtype)
        # Edge weight from the GT gradient, normalised by its mean valid magnitude.
        weight = gt.detach()
        denom = masked_mean(weight, valid).clamp(min=EPS)
        weight = weight / denom
        return masked_mean((gp - gt).abs() * weight, valid)


class OrdinalLoss(nn.Module):
    """Pairwise ranking loss on pixel pairs sampled from the valid mask.

    Used only for ordinal-consistency ablations on relative-only supervision; the
    default training config gives it zero weight.
    """

    def __init__(self, num_pairs: int = 8192, margin: float = 0.05):
        super().__init__()
        self.num_pairs = num_pairs
        self.margin = margin

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        p = pred.reshape(-1)
        t = target.reshape(-1)
        if mask is not None:
            m = (mask > 0.5).reshape(-1)
            p, t = p[m], t[m]
        n = p.numel()
        if n < 32:
            return pred.sum() * 0.0
        pairs = min(self.num_pairs, n // 2)
        idx = torch.randint(0, n, (2, pairs), device=p.device)
        i, j = idx[0], idx[1]
        sign = torch.sign(t[i] - t[j])
        keep = sign != 0
        if int(keep.sum()) == 0:
            return pred.sum() * 0.0
        diff = (p[i] - p[j]) * sign
        return torch.relu(self.margin - diff[keep]).mean()


class CombinedDepthLoss(nn.Module):
    """Weighted sum of the losses above, with per-term reporting.

    ``weights`` keys must be known loss names; the trainer records both the weights and
    the per-term values so the objective of a run is auditable.
    """

    SUPPORTED = ("silog", "l1", "berhu", "gradient", "ordinal")

    def __init__(self, weights: Dict[str, float]):
        super().__init__()
        unknown = {k for k in weights if k not in self.SUPPORTED}
        if unknown:
            raise ValueError(f"Unsupported loss terms: {sorted(unknown)}; allowed: {self.SUPPORTED}")
        if not any(float(v) != 0.0 for v in weights.values()):
            raise ValueError("At least one loss weight must be non-zero")
        self.weights = {k: float(v) for k, v in weights.items()}
        self.terms: Dict[str, nn.Module] = {}
        for name, weight in self.weights.items():
            if weight == 0.0:
                continue
            self.terms[name] = {
                "silog": SILogLoss,
                "l1": MaskedL1Loss,
                "berhu": BerHuLoss,
                "gradient": GradientLoss,
                "ordinal": OrdinalLoss,
            }[name]()

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, Dict[str, float]]:
        breakdown: Dict[str, float] = {}
        total = pred.sum() * 0.0
        for name, module in self.terms.items():
            value = module(pred, target, mask)
            breakdown[name] = float(value.detach())
            total = total + self.weights[name] * value
        breakdown["total"] = float(total.detach())
        return total, breakdown
