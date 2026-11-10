from __future__ import annotations

from typing import Optional, Tuple
import numpy as np
from numpy.linalg import svd, norm, det, pinv


def compute_similarity_transform(
    source: np.ndarray, target: np.ndarray
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Estimate X_target = s R X_source + t from corresponding point sets.

    Returns (scale, rotation_matrix, translation, residuals).
    """
    assert source.shape == target.shape, "Point sets must match in shape"
    n = source.shape[0]
    assert n >= 3, "Need at least 3 correspondences"

    src_mean = source.mean(axis=0)
    tgt_mean = target.mean(axis=0)
    src_centered = source - src_mean
    tgt_centered = target - tgt_mean

    H = src_centered.T @ tgt_centered
    U, S, Vt = svd(H)
    R = Vt.T @ U.T
    if det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    scale = np.trace(np.diag(S)) / np.trace(src_centered.T @ src_centered) if np.trace(src_centered.T @ src_centered) != 0 else 1.0
    if scale <= 0:
        scale = 1.0

    translation = tgt_mean - scale * R @ src_mean
    predicted = scale * (R @ source.T).T + translation
    residuals = target - predicted
    return scale, R, translation, residuals


def compute_weighted_similarity_transform(
    source: np.ndarray,
    target: np.ndarray,
    weights: Optional[np.ndarray] = None,
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, float]:
    if weights is None:
        weights = np.ones(source.shape[0])
    weights = weights / weights.sum()
    sw = weights.sum()
    src_mean = np.average(source, axis=0, weights=weights)
    tgt_mean = np.average(target, axis=0, weights=weights)
    src_centered = source - src_mean
    tgt_centered = target - tgt_mean
    H = (src_centered * weights[:, None]).T @ tgt_centered
    U, S, Vt = svd(H)
    R = Vt.T @ U.T
    if det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
<<<<<<< HEAD
    R_src = (R @ src_centered.T).T
    scale_num = float(np.sum(weights * np.sum(tgt_centered * R_src, axis=1)))
    scale_den = float(np.sum(weights * np.sum(src_centered * src_centered, axis=1)))
=======
    scale_num = np.sum(weights * np.sum((tgt_centered * R @ src_centered.T).T * src_centered, axis=1))
    scale_den = np.sum(weights * np.sum(src_centered * src_centered, axis=1))
>>>>>>> origin/main
    scale = scale_num / scale_den if scale_den != 0 else 1.0
    if scale <= 0:
        scale = 1.0
    translation = tgt_mean - scale * R @ src_mean
    predicted = scale * (R @ source.T).T + translation
    residuals = target - predicted
    residual_var = np.average(np.sum(residuals * residuals, axis=1), weights=weights)
    return scale, R, translation, residuals, float(residual_var)
