"""Model construction for the JATAYUV depth pipeline.

``dav2_factory`` is the only supported entry point: it builds the official Depth
Anything V2 **Small** architecture and verifies checkpoints against it.
"""
from training.models.dav2_factory import (  # noqa: F401
    SMALL_PRESET,
    SMALL_PARAM_COUNT,
    OFFICIAL_SMALL_SHA256,
    ModelLoadReport,
    build_dav2_small,
    configure_trainable,
    download_official_weights,
    load_checkpoint_strict,
    param_groups,
    parameter_counts,
    vit_backbone,
)
