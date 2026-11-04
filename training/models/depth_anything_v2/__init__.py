"""Vendored official Depth Anything V2 implementation (unmodified).

Source : https://github.com/DepthAnything/Depth-Anything-V2 (main branch)
Files  : depth_anything_v2/{dpt.py,dinov2.py,dinov2_layers/*,util/*}
License: Apache-2.0 (see LICENSE_Apache-2.0)
Fetched: 2026-11-04

Only the model code is vendored; the official training scripts, datasets and CLI are
*not* copied. Fine-tuning code lives in ``training/`` and reuses these modules so the
architecture is bit-identical to the released official model.
"""
from training.models.depth_anything_v2.dpt import DPTHead, DepthAnythingV2  # noqa: F401
