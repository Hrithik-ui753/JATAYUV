"""Generate teacher pseudo-depth labels with the pretrained Depth Anything V2 Small.

These labels are **not** ground truth. They are stored with ``depth.type = "pseudo"``
and ``label_method = "teacher_dav2"`` and must never be used to claim real-depth
accuracy or to validate a model that was trained on them (that would be circular).

Confidence is estimated with horizontal-flip test-time augmentation: the relative
disagreement between the two predictions is mapped to ``exp(-||diff|| / scale)``.
Agreement is a proxy for stability, not correctness.

Usage::

    python -m training.depth_generation.teacher_pseudo_depth \
        --input datasets/manifests/own_flights.json \
        --output datasets/manifests/own_flights_pseudo.json \
        --output-dir datasets/pseudo_depth/own_flights \
        --teacher-checkpoint training/checkpoints/pretrained/depth_anything_v2_vits.pth
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F

from training.datasets.manifest import DatasetManifest, DepthLabel, DepthSample
from training.models.dav2_factory import build_dav2_small, load_checkpoint_strict
from training.utils.io import REPO_ROOT, ensure_dir, utc_now_iso, write_json
from training.utils.seed import resolve_device


def _preprocess(image_bgr: np.ndarray, input_size: int, device: torch.device) -> torch.Tensor:
    from torchvision.transforms import Compose

    from training.models.depth_anything_v2.util.transform import (
        NormalizeImage,
        PrepareForNet,
        Resize,
    )

    transform = Compose(
        [
            Resize(
                width=input_size,
                height=input_size,
                resize_target=False,
                keep_aspect_ratio=True,
                ensure_multiple_of=14,
                resize_method="lower_bound",
                image_interpolation_method=cv2.INTER_CUBIC,
            ),
            NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            PrepareForNet(),
        ]
    )
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) / 255.0
    return torch.from_numpy(transform({"image": rgb})["image"]).unsqueeze(0).to(device)


class TeacherLabeler:
    def __init__(
        self,
        checkpoint: str,
        device: Optional[str] = None,
        input_size: int = 518,
        tta: bool = True,
    ):
        self.device = resolve_device(device or "auto")
        self.input_size = input_size
        self.tta = tta
        self.model = build_dav2_small()
        self.report = load_checkpoint_strict(
            self.model, checkpoint, verify_official_hash=True
        )
        self.model.to(self.device).eval()

    @torch.no_grad()
    def label(self, image_bgr: np.ndarray) -> Dict[str, np.ndarray]:
        h, w = image_bgr.shape[:2]
        tensor = _preprocess(image_bgr, self.input_size, self.device)
        pred = self.model(tensor)
        depth = F.interpolate(pred[:, None], (h, w), mode="bilinear", align_corners=True)[0, 0]
        inverse = depth.detach().float().cpu().numpy()

        confidence = np.ones_like(inverse, dtype=np.float32)
        if self.tta:
            flipped = torch.flip(tensor, dims=[3])
            pred_f = self.model(flipped)
            depth_f = F.interpolate(
                pred_f[:, None], (h, w), mode="bilinear", align_corners=True
            )[0, 0]
            inverse_f = torch.flip(depth_f, dims=[2]).detach().float().cpu().numpy()
            scale = np.median(np.abs(inverse)) + 1e-6
            disagreement = np.abs(inverse - inverse_f) / scale
            confidence = np.exp(-disagreement).astype(np.float32)
        return {"inverse": inverse, "confidence": confidence}


def generate(
    input_manifest: str,
    output_manifest: str,
    output_dir: str,
    teacher_checkpoint: str,
    device: Optional[str] = None,
    input_size: int = 518,
    tta: bool = True,
    max_samples: Optional[int] = None,
    only_flights: Optional[List[str]] = None,
) -> Dict[str, Any]:
    manifest = DatasetManifest.load(input_manifest)
    labeler = TeacherLabeler(teacher_checkpoint, device=device, input_size=input_size, tta=tta)
    ensure_dir(output_dir)

    written = 0
    skipped = 0
    for sample in manifest.samples:
        if only_flights and sample.flight_id not in only_flights:
            continue
        if max_samples and written >= max_samples:
            break
        image_path = os.path.join(REPO_ROOT, sample.image_path)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            skipped += 1
            continue
        result = labeler.label(image)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        rel_dir = os.path.join(output_dir, sample.flight_id)
        ensure_dir(os.path.join(REPO_ROOT, rel_dir))
        npy_rel = os.path.join(rel_dir, f"{stem}_pseudo_inverse.npy")
        png_rel = os.path.join(rel_dir, f"{stem}_pseudo_16bit.png")
        conf_rel = os.path.join(rel_dir, f"{stem}_confidence.png")

        np.save(os.path.join(REPO_ROOT, npy_rel), result["inverse"].astype(np.float32))
        norm = labeler_normalise(result["inverse"])
        cv2.imwrite(
            os.path.join(REPO_ROOT, png_rel), (norm * 65535).astype(np.uint16)
        )
        cv2.imwrite(
            os.path.join(REPO_ROOT, conf_rel), (result["confidence"] * 255).astype(np.uint8)
        )

        sample.depth = DepthLabel(
            path=npy_rel.replace(os.sep, "/"),
            type="pseudo",
            unit="inverse_relative",
            encoding="npy_float32",
            label_method="teacher_dav2",
            confidence=float(result["confidence"].mean()),
            mask_path=conf_rel.replace(os.sep, "/"),
            inverse_scale=None,  # use dataset-level inverse scale
            notes=(
                "TEACHER PSEUDO-LABEL generated by the pretrained Depth Anything V2 Small "
                f"(sha256 {labeler.report.sha256[:12]}). Not ground truth."
            ),
        )
        sample.annotation_status = "pseudo_depth"
        sample.extra["pseudo_label"] = {
            "teacher_checkpoint": teacher_checkpoint,
            "teacher_sha256": labeler.report.sha256,
            "tta": tta,
            "input_size": input_size,
            "generated_utc": utc_now_iso(),
            "depth_encoding": "inverse_depth (higher = nearer)",
        }
        written += 1

    manifest.depth_types_present = sorted(
        {s.depth.type for s in manifest.samples if s.depth and s.depth.type != "none"}
    )
    manifest.statistics["pseudo_labelled"] = written
    manifest.save(output_manifest)
    summary = {
        "written": written,
        "skipped": skipped,
        "output_manifest": output_manifest,
        "teacher_sha256": labeler.report.sha256,
        "warning": (
            "Pseudo-labels are teacher outputs, not ground truth. Do not report real-depth "
            "accuracy from them, and do not validate on data the teacher labelled."
        ),
    }
    write_json(summary, os.path.join(REPO_ROOT, output_dir, "pseudo_label_summary.json"))
    return summary


def labeler_normalise(inverse: np.ndarray) -> np.ndarray:
    valid = np.isfinite(inverse)
    if not valid.any():
        return np.zeros_like(inverse, dtype=np.float32)
    lo, hi = np.percentile(inverse[valid], [1, 99])
    return np.clip((inverse - lo) / max(hi - lo, 1e-9), 0, 1).astype(np.float32)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Teacher pseudo-depth generation")
    parser.add_argument("--input", required=True, help="input manifest JSON")
    parser.add_argument("--output", required=True, help="output manifest JSON")
    parser.add_argument("--output-dir", default="datasets/pseudo_depth/teacher")
    parser.add_argument(
        "--teacher-checkpoint",
        default=os.path.join(
            "training", "checkpoints", "pretrained", "depth_anything_v2_vits.pth"
        ),
    )
    parser.add_argument("--device", default=None)
    parser.add_argument("--input-size", type=int, default=518)
    parser.add_argument("--no-tta", action="store_true")
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--flight", action="append", default=None)
    args = parser.parse_args(argv)

    summary = generate(
        input_manifest=os.path.join(REPO_ROOT, args.input) if not os.path.isabs(args.input) else args.input,
        output_manifest=os.path.join(REPO_ROOT, args.output) if not os.path.isabs(args.output) else args.output,
        output_dir=args.output_dir,
        teacher_checkpoint=os.path.join(REPO_ROOT, args.teacher_checkpoint),
        device=args.device,
        input_size=args.input_size,
        tta=not args.no_tta,
        max_samples=args.max_samples,
        only_flights=args.flight,
    )
    print(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
