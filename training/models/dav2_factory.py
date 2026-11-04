"""Factory / loader for the official Depth Anything V2 **Small** model.

The architecture itself is the vendored official implementation in
``training/models/depth_anything_v2`` (Apache-2.0, DepthAnything/Depth-Anything-V2).
This module only builds the *Small* preset, verifies the checkpoint against it and
manages freezing/unfreezing for fine-tuning.

Small preset (from the official README / ``run.py``)::

    encoder='vits', features=64, out_channels=[48, 96, 192, 384]

which yields 24,785,089 parameters and a 239-tensor state dict, matching the official
``depth_anything_v2_vits.pth`` release byte-for-byte in keys and shapes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import torch
import torch.nn as nn

from training.models.depth_anything_v2.dpt import DepthAnythingV2
from training.utils.io import sha256_file

SMALL_PRESET: Dict[str, object] = {
    "encoder": "vits",
    "features": 64,
    "out_channels": [48, 96, 192, 384],
    "use_bn": False,
    "use_clstoken": False,
}

# Official release: https://huggingface.co/depth-anything/Depth-Anything-V2-Small
OFFICIAL_SMALL_URL = (
    "https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/"
    "depth_anything_v2_vits.pth"
)
OFFICIAL_SMALL_SHA256 = "715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378"
OFFICIAL_SMALL_BYTES = 99218434
SMALL_PARAM_COUNT = 24_785_089
SMALL_STATE_DICT_TENSORS = 239


@dataclass
class ModelLoadReport:
    """Verifiable facts about a loaded checkpoint (never guessed)."""

    checkpoint_path: str
    sha256: str
    bytes: int
    encoder: str
    total_params: int
    encoder_params: int
    head_params: int
    tensor_count: int
    strict_load: bool
    source: str = "official_depth_anything_v2_small"
    extra: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return dict(self.__dict__)


def build_dav2_small() -> DepthAnythingV2:
    """Instantiate the official Depth Anything V2 *Small* architecture."""
    return DepthAnythingV2(**SMALL_PRESET)


def vit_backbone(model: DepthAnythingV2) -> nn.Module:
    """Return the DINOv2 ViT backbone of the official DAv2 model.

    The official implementation stores it as ``model.pretrained`` (``model.encoder`` is
    only the preset string). We keep the vendored code unmodified and expose this helper.
    """
    return model.pretrained


def _extract_state_dict(payload: object) -> Tuple[Dict[str, torch.Tensor], Dict[str, object]]:
    """Accept a raw official state dict or a wrapped fine-tuning checkpoint."""
    if isinstance(payload, dict):
        for key in ("state_dict", "model_state", "model_state_dict", "model"):
            nested = payload.get(key)
            if isinstance(nested, dict) and nested and all(
                isinstance(k, str) for k in list(nested.keys())[:5]
            ):
                meta = {k: v for k, v in payload.items() if k not in (key,)}
                state = nested
                # Strip a possible "module." prefix from DataParallel saves.
                if all(k.startswith("module.") for k in list(state.keys())[:5]):
                    state = {k[len("module."):]: v for k, v in state.items()}
                return {k: v for k, v in state.items() if torch.is_tensor(v)}, meta
        if all(torch.is_tensor(v) for v in payload.values()):
            return dict(payload), {}
    raise ValueError("Checkpoint does not contain a recognisable state dict")


def load_checkpoint_strict(
    model: nn.Module,
    checkpoint_path: str,
    verify_official_hash: bool = False,
    expected_sha256: Optional[str] = None,
) -> ModelLoadReport:
    """Load weights with ``strict=True`` and return verified load facts.

    ``strict=True`` guarantees no parameter is silently missing or unexpected; a model
    that merely *downloads* the weights is never reported as trained.
    """
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}. "
            "Run `python -m training.models.dav2_factory --download` to fetch the official "
            "Small weights, or point the config at an existing fine-tuned checkpoint."
        )
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state, meta = _extract_state_dict(payload)
    result = model.load_state_dict(state, strict=True)

    digest = sha256_file(checkpoint_path)
    if verify_official_hash and digest != OFFICIAL_SMALL_SHA256:
        raise ValueError(
            "Official Depth Anything V2 Small checkpoint hash mismatch.\n"
            f"  expected {OFFICIAL_SMALL_SHA256}\n  actual   {digest}\n"
            "Refusing to continue: this is not the official pretrained release."
        )
    if expected_sha256 and digest != expected_sha256:
        raise ValueError(
            f"Checkpoint SHA256 mismatch for {checkpoint_path}: expected {expected_sha256}, got {digest}"
        )

    encoder_params = sum(p.numel() for p in vit_backbone(model).parameters())
    head_params = sum(p.numel() for p in model.depth_head.parameters())
    return ModelLoadReport(
        checkpoint_path=os.path.abspath(checkpoint_path),
        sha256=digest,
        bytes=os.path.getsize(checkpoint_path),
        encoder=str(model.encoder),
        total_params=sum(p.numel() for p in model.parameters()),
        encoder_params=encoder_params,
        head_params=head_params,
        tensor_count=len(state),
        strict_load=True,
        extra={"checkpoint_metadata": meta, "missing_keys": list(result.missing_keys)},
    )


def parameter_counts(model: nn.Module) -> Dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable, "frozen": total - trainable}


# --------------------------------------------------------------------------------------
# Freezing strategies
# --------------------------------------------------------------------------------------
def _encoder_blocks(model: nn.Module) -> List[nn.Module]:
    return list(vit_backbone(model).blocks)


def configure_trainable(
    model: nn.Module,
    strategy: str = "full",
    unfreeze_last_n_blocks: int = 2,
    epoch: int = 0,
) -> Dict[str, int]:
    """Apply a fine-tuning strategy; returns parameter counts.

    Strategies
    ----------
    full             : train backbone + head (full fine-tuning)
    decoder_only     : frozen ViT-S backbone, DPT head + norm + neck trainable
    last_n_blocks    : frozen patches/pos-embed/early blocks; last N blocks + head trainable
    gradual          : like last_n_blocks, but unfreezes one extra block per epoch
    """
    for param in model.parameters():
        param.requires_grad = True

    strategy = (strategy or "full").lower()
    if strategy == "full":
        return parameter_counts(model)

    # Freeze the DINOv2 backbone, then selectively re-enable parts.
    backbone = vit_backbone(model)
    for param in backbone.parameters():
        param.requires_grad = False

    blocks = _encoder_blocks(model)
    n_total = len(blocks)

    if strategy == "decoder_only":
        pass
    elif strategy == "last_n_blocks":
        n = max(0, min(int(unfreeze_last_n_blocks), n_total))
        for block in blocks[n_total - n:]:
            for param in block.parameters():
                param.requires_grad = True
        for param in backbone.norm.parameters():
            param.requires_grad = True
    elif strategy == "gradual":
        base = max(0, min(int(unfreeze_last_n_blocks), n_total))
        n = min(n_total, base + max(0, int(epoch)))
        for block in blocks[n_total - n:]:
            for param in block.parameters():
                param.requires_grad = True
        for param in backbone.norm.parameters():
            param.requires_grad = True
    else:
        raise ValueError(
            f"Unknown freeze strategy '{strategy}'. "
            "Use one of: full, decoder_only, last_n_blocks, gradual."
        )
    return parameter_counts(model)


def param_groups(
    model: nn.Module,
    base_lr: float,
    backbone_lr_scale: float,
    weight_decay: float,
) -> List[Dict[str, object]]:
    """AdamW parameter groups: discriminative LR for the ViT-S backbone vs DPT head."""
    backbone_ids = {id(p) for p in vit_backbone(model).parameters()}
    backbone, head = [], []
    for param in model.parameters():
        if not param.requires_grad:
            continue
        (backbone if id(param) in backbone_ids else head).append(param)

    groups: List[Dict[str, object]] = []
    if backbone:
        groups.append(
            {
                "params": backbone,
                "lr": base_lr * backbone_lr_scale,
                "weight_decay": weight_decay,
                "name": "backbone",
            }
        )
    if head:
        groups.append(
            {"params": head, "lr": base_lr, "weight_decay": weight_decay, "name": "head"}
        )
    return groups


def iter_named_trainable(model: nn.Module) -> Iterable[Tuple[str, nn.Parameter]]:
    for name, param in model.named_parameters():
        if param.requires_grad:
            yield name, param


def download_official_weights(dest: str, force: bool = False) -> ModelLoadReport:
    """Download the official Small checkpoint and verify its SHA256.

    Never overwrites a verified file; a mismatching existing file is re-downloaded once.
    """
    import urllib.request

    from training.utils.io import ensure_dir

    ensure_dir(os.path.dirname(os.path.abspath(dest)))
    if os.path.isfile(dest) and not force:
        if sha256_file(dest) == OFFICIAL_SMALL_SHA256:
            tmp = build_dav2_small()
            return load_checkpoint_strict(tmp, dest, verify_official_hash=True)

    tmp_path = dest + ".part"
    with urllib.request.urlopen(OFFICIAL_SMALL_URL, timeout=600) as response, open(
        tmp_path, "wb"
    ) as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)
    digest = sha256_file(tmp_path)
    if digest != OFFICIAL_SMALL_SHA256:
        os.remove(tmp_path)
        raise ValueError(
            "Downloaded Depth Anything V2 Small checkpoint failed SHA256 verification: "
            f"{digest} != {OFFICIAL_SMALL_SHA256}"
        )
    os.replace(tmp_path, dest)
    model = build_dav2_small()
    return load_checkpoint_strict(model, dest, verify_official_hash=True)


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Verify/download official DAv2 Small weights")
    parser.add_argument(
        "--checkpoint",
        default=os.path.join(
            "training", "checkpoints", "pretrained", "depth_anything_v2_vits.pth"
        ),
    )
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.download:
        report = download_official_weights(args.checkpoint, force=args.force)
    else:
        model = build_dav2_small()
        report = load_checkpoint_strict(model, args.checkpoint, verify_official_hash=True)
    print(json.dumps(report.as_dict(), indent=2))
