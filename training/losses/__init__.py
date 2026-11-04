"""Depth losses (all in the network's inverse-depth output space)."""
from training.losses.depth_losses import (  # noqa: F401
    BerHuLoss,
    CombinedDepthLoss,
    GradientLoss,
    MaskedL1Loss,
    OrdinalLoss,
    SILogLoss,
    masked_mean,
)
