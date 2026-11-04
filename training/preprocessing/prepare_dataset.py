"""Build the unified JATAYUV depth dataset: manifests, leakage-free splits, report.

This module never invents labels. It consumes:

* real depth-annotated sources (``paired`` adapter: images + depth maps produced by
  LiDAR/stereo/photogrammetry, or a research dataset such as SkyScenes),
* teacher pseudo-labels produced by ``training.depth_generation.teacher_pseudo_depth``,
* an already-built manifest from ``training.preprocessing.media_ingest``.

It validates RGB/depth alignment, computes validity statistics and the dataset-level
inverse-depth scale, assigns splits **by sequence/flight** (never by random frame) and
writes a summary report.

Usage::

    python -m training.preprocessing.prepare_dataset \
        --config training/configs/depth_anything_v2_small.yaml
"""
from __future__ import annotations

import argparse
import glob
import os
import re
from typing import Any, Dict, Iterable, List, Optional

import cv2
import numpy as np

from training.datasets.manifest import (
    CameraInfo,
    DatasetManifest,
    DepthLabel,
    DepthSample,
    GPSCoords,
)
from training.utils.io import (
    REPO_ROOT,
    ensure_dir,
    get,
    load_config,
    read_json,
    sha256_file,
    utc_now_iso,
    write_json,
)

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
SKYSCENES_LICENSE = "MIT"


# --------------------------------------------------------------------------------------
# Source adapters
# --------------------------------------------------------------------------------------
def _rel(path: str) -> str:
    """Store paths relative to the repository root when possible (portable manifests)."""
    absolute = os.path.abspath(path)
    if absolute.startswith(REPO_ROOT + os.sep):
        return os.path.relpath(absolute, REPO_ROOT)
    return absolute


def _frame_key(name: str) -> str:
    match = re.match(r"(\d+)", os.path.basename(name))
    return match.group(1) if match else os.path.splitext(os.path.basename(name))[0]


def build_skyscenes_samples(
    source: Dict[str, Any],
    altitude: str,
    weather: str,
    town: str,
    frames: Optional[int] = None,
    frame_stride: int = 1,
) -> List[DepthSample]:
    """Pair SkyScenes RGB with its 8-bit relative depth maps.

    SkyScenes depth is stored as uint8 PNG normalised per shard and the dataset
    publishes **no metric scale**, therefore samples are labelled
    ``type='relative'`` / ``unit='normalized_0_1'``. They are never treated as metres.
    """
    root = os.path.join(source["root"], altitude, weather, town)
    image_dir = os.path.join(root, "images")
    depth_dir = os.path.join(root, "depths")
    meta_dir = os.path.join(root, "meta")

    depth_by_key = {_frame_key(p): p for p in glob.glob(os.path.join(depth_dir, "*"))}
    image_paths = sorted(
        p for p in glob.glob(os.path.join(image_dir, "*")) if p.lower().endswith(IMAGE_EXTS)
    )
    if frame_stride > 1:
        image_paths = image_paths[::frame_stride]
    if frames:
        image_paths = image_paths[:frames]

    samples: List[DepthSample] = []
    for image_path in image_paths:
        key = _frame_key(image_path)
        depth_path = depth_by_key.get(key)
        if depth_path is None:
            continue
        with open(image_path, "rb") as fh:
            head = fh.read(8)
        if not head.startswith(b"\x89PNG"):
            continue
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
        if image is None or depth is None:
            continue
        h, w = image.shape[:2]
        if depth.shape[:2] != (h, w):
            raise ValueError(
                f"RGB/depth misalignment in {town}: image {w}x{h} vs depth "
                f"{depth.shape[1]}x{depth.shape[0]}"
            )

        meta: Dict[str, Any] = {}
        meta_path = os.path.join(meta_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.json")
        if os.path.isfile(meta_path) and os.path.getsize(meta_path) < 2_000_000:
            try:
                meta = read_json(meta_path)
            except Exception:
                meta = {}

        samples.append(
            DepthSample(
                id=f"skyscenes_{town}_{key}",
                image_path=_rel(image_path),
                width=w,
                height=h,
                source_dataset="skyscenes",
                license=f"{SKYSCENES_LICENSE} (SkyScenes, Khose et al. ECCV 2024)",
                flight_id=f"{town}_{altitude}_{weather}",
                sequence_id=f"{town}_{altitude}_{weather}",
                depth=DepthLabel(
                    path=_rel(depth_path),
                    type="relative",
                    unit="normalized_0_1",
                    encoding="png8",
                    label_method="synthetic_ground_truth",
                    confidence=1.0,
                    min_valid=0.0,
                    max_valid=1.0,
                    value_scale=1.0 / 255.0,
                    clip_saturated_invalid=True,
                    notes=(
                        "CARLA rendered depth, uint8 normalised per shard; no published "
                        "metric scale. Treated as relative depth only."
                    ),
                ),
                camera=CameraInfo(
                    make="CARLA simulator",
                    model="RGB camera (H_15_P_0 / ClearNoon shard)",
                    width=w,
                    height=h,
                    focal_length_px=None,
                ),
                gps=GPSCoords(altitude_m=meta.get("actual_height")),
                annotation_status="real_depth",
                extra={
                    "town": town,
                    "weather": weather,
                    "altitude_config": altitude,
                    "actual_height_m": meta.get("actual_height"),
                    "actual_pitch_deg": meta.get("actual_pitch"),
                    "ego_vehicle": meta.get("ego_vehicle"),
                    "synthetic": True,
                },
            )
        )
    return samples


def build_paired_samples(
    source: Dict[str, Any],
    flight_prefix: str = "flight",
) -> List[DepthSample]:
    """Generic adapter for real depth data: ``images/<seq>/*.png`` + ``depth/<seq>/*.npy``.

    Supports PNG16 (value_scale mm->m) and float32 ``.npy`` depth in metres. The
    sequence directory name is used as flight/sequence id so splits stay leakage-free.
    """
    root = source["root"]
    image_root = os.path.join(root, source.get("images_subdir", "images"))
    depth_root = os.path.join(root, source.get("depth_subdir", "depth"))
    encoding = source.get("depth_encoding", "npy_float32")
    value_scale = float(source.get("value_scale", 1.0))
    depth_type = source.get("depth_type", "metric")
    unit = source.get("depth_unit", "metre")
    label_method = source.get("label_method", "lidar")
    licence = source.get("license", "unknown")
    source_name = source.get("name", "paired")

    depth_lookup: Dict[str, str] = {}
    for path in glob.glob(os.path.join(depth_root, "**", "*"), recursive=True):
        if os.path.isfile(path):
            depth_lookup[os.path.splitext(path)[0]] = path

    samples: List[DepthSample] = []
    for image_path in sorted(glob.glob(os.path.join(image_root, "**", "*"), recursive=True)):
        if not image_path.lower().endswith(IMAGE_EXTS):
            continue
        stem = os.path.splitext(image_path)[0]
        depth_path = depth_lookup.get(stem)
        if depth_path is None:
            continue
        sequence = os.path.basename(os.path.dirname(image_path)) or flight_prefix
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            continue
        h, w = image.shape[:2]
        samples.append(
            DepthSample(
                id=f"{source_name}_{sequence}_{_frame_key(image_path)}",
                image_path=_rel(image_path),
                width=w,
                height=h,
                source_dataset=source_name,
                license=licence,
                flight_id=f"{source_name}_{sequence}",
                sequence_id=f"{source_name}_{sequence}",
                depth=DepthLabel(
                    path=_rel(depth_path),
                    type=depth_type,
                    unit=unit,
                    encoding=encoding,
                    label_method=label_method,
                    confidence=float(source.get("confidence", 1.0)),
                    value_scale=value_scale,
                    notes=source.get("notes"),
                ),
                annotation_status="real_depth" if depth_type == "metric" else "real_depth",
                extra={"sequence": sequence},
            )
        )
    return samples


def merge_manifest_samples(path: str, split_hint: Optional[str] = None) -> List[DepthSample]:
    manifest = DatasetManifest.load(path)
    samples = list(manifest.samples)
    if split_hint:
        for sample in samples:
            sample.split = split_hint
    return samples


# --------------------------------------------------------------------------------------
# Validation / statistics
# --------------------------------------------------------------------------------------
def validate_sample(sample: DepthSample, check_depth_values: bool = True) -> Dict[str, Any]:
    """Check alignment and validity of one sample; returns a statistics record."""
    image_abs = os.path.join(REPO_ROOT, sample.image_path)
    depth_abs = os.path.join(REPO_ROOT, sample.depth.path) if sample.depth else None
    record: Dict[str, Any] = {"id": sample.id, "ok": True, "problems": []}
    if not os.path.isfile(image_abs):
        record["ok"] = False
        record["problems"].append("missing image")
        return record
    image = cv2.imread(image_abs, cv2.IMREAD_REDUCED_COLOR_4)  # fast header+decode
    if image is None:
        record["ok"] = False
        record["problems"].append("unreadable image")
        return record
    full = cv2.imread(image_abs, cv2.IMREAD_UNCHANGED)
    h, w = full.shape[:2]
    if (w, h) != (sample.width, sample.height):
        record["problems"].append("manifest size differs from file")

    if depth_abs and os.path.isfile(depth_abs):
        depth = (
            np.load(depth_abs).astype(np.float32)
            if sample.depth.encoding == "npy_float32"
            else cv2.imread(depth_abs, cv2.IMREAD_UNCHANGED)
        )
        if depth is None:
            record["ok"] = False
            record["problems"].append("unreadable depth")
        else:
            if depth.ndim == 3:
                depth = depth[..., 0]
            if depth.shape[:2] != (h, w):
                record["ok"] = False
                record["problems"].append(
                    f"depth shape {depth.shape[:2]} != image shape {(h, w)}"
                )
            if check_depth_values:
                scaled = depth.astype(np.float32) * sample.depth.value_scale
                valid = np.isfinite(scaled) & (scaled > 0)
                if sample.depth.clip_saturated_invalid and sample.depth.max_valid is not None:
                    valid &= scaled < sample.depth.max_valid
                coverage = float(valid.mean())
                record.update(
                    {
                        "valid_coverage": round(coverage, 4),
                        "depth_min": float(scaled[valid].min()) if valid.any() else None,
                        "depth_max": float(scaled[valid].max()) if valid.any() else None,
                        "depth_median": float(np.median(scaled[valid])) if valid.any() else None,
                    }
                )
                if coverage < 0.05:
                    record["problems"].append("valid depth coverage below 5%")
    elif sample.depth is not None:
        record["ok"] = False
        record["problems"].append("missing depth file")
    return record


def compute_inverse_scale(samples: List[DepthSample], depth_type: str) -> float:
    """Dataset-level constant so ``target = inverse_scale / depth`` is ~O(1).

    For relative supervision the scale is the median native depth of the *training*
    split; for metric supervision it is 1.0 so the target stays in 1/metre.
    """
    if depth_type == "metric":
        return 1.0
    values: List[float] = []
    for sample in samples[:200]:
        if not sample.depth:
            continue
        path = os.path.join(REPO_ROOT, sample.depth.path)
        if not os.path.isfile(path):
            continue
        depth = (
            np.load(path).astype(np.float32)
            if sample.depth.encoding == "npy_float32"
            else cv2.imread(path, cv2.IMREAD_UNCHANGED)
        )
        if depth is None:
            continue
        if depth.ndim == 3:
            depth = depth[..., 0]
        scaled = depth.astype(np.float32) * sample.depth.value_scale
        valid = np.isfinite(scaled) & (scaled > 0)
        if sample.depth.clip_saturated_invalid and sample.depth.max_valid is not None:
            valid &= scaled < sample.depth.max_valid
        if valid.any():
            values.append(float(np.median(scaled[valid])))
    if not values:
        return 1.0
    return float(np.median(values))


# --------------------------------------------------------------------------------------
# Splitting
# --------------------------------------------------------------------------------------
def assign_splits(
    samples: List[DepthSample],
    split_config: Dict[str, Any],
) -> Dict[str, int]:
    """Assign splits by flight/sequence (never by random frame).

    ``split_config`` supports:
      * ``by_flight``: ``{train: [flight_id, ...], val: [...], test: [...]}``
      * ``temporal_holdout``: ``{<flight_id>: {"val_tail": N}}`` — the last N frames of a
        flight are held out in time order for validation (used when a second location is
        not available for validation).
    """
    counts = {"train": 0, "val": 0, "test": 0, "unassigned": 0}
    by_flight = split_config.get("by_flight", {})
    flight_to_split: Dict[str, str] = {}
    for split, flights in by_flight.items():
        for flight in flights:
            flight_to_split[flight] = split

    holdout = split_config.get("temporal_holdout", {}) or {}
    for sample in samples:
        split = flight_to_split.get(sample.flight_id, "unassigned")
        rule = holdout.get(sample.flight_id)
        if rule and split == "train":
            tail = int(rule.get("val_tail", 0))
            if tail > 0:
                same_flight = sorted(
                    (s for s in samples if s.flight_id == sample.flight_id),
                    key=lambda s: _frame_key(s.image_path),
                )
                tail_ids = {s.id for s in same_flight[-tail:]} if tail < len(same_flight) else set()
                if sample.id in tail_ids:
                    split = "val"
        sample.split = split
        counts[split] = counts.get(split, 0) + 1
    return counts


# --------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------
def build_report(manifest: DatasetManifest, validation: List[Dict[str, Any]]) -> Dict[str, Any]:
    samples = manifest.samples
    per_split: Dict[str, int] = {}
    per_source: Dict[str, int] = {}
    per_type: Dict[str, int] = {}
    per_unit: Dict[str, int] = {}
    resolutions: Dict[str, int] = {}
    pseudo = 0
    labelled = 0
    depths: List[float] = []

    for sample in samples:
        per_split[sample.split] = per_split.get(sample.split, 0) + 1
        per_source[sample.source_dataset] = per_source.get(sample.source_dataset, 0) + 1
        resolutions[f"{sample.width}x{sample.height}"] = (
            resolutions.get(f"{sample.width}x{sample.height}", 0) + 1
        )
        if sample.depth and sample.depth.type != "none":
            labelled += 1
            per_type[sample.depth.type] = per_type.get(sample.depth.type, 0) + 1
            per_unit[sample.depth.unit] = per_unit.get(sample.depth.unit, 0) + 1
            if sample.depth.type == "pseudo":
                pseudo += 1

    for record in validation:
        for key in ("depth_min", "depth_max", "depth_median"):
            value = record.get(key)
            if value is not None:
                depths.append(float(value))

    flights = sorted({s.flight_id for s in samples})
    overlap = []
    split_by_flight: Dict[str, set] = {}
    for sample in samples:
        split_by_flight.setdefault(sample.flight_id, set()).add(sample.split)
    for flight, splits in split_by_flight.items():
        if len({s for s in splits if s in ("test",)}) and len({s for s in splits if s in ("train",)}):
            overlap.append(flight)

    problems = [r for r in validation if not r["ok"]]
    return {
        "generated_utc": utc_now_iso(),
        "manifest_name": manifest.name,
        "manifest_version": manifest.version,
        "total_samples": len(samples),
        "total_sequences": len(flights),
        "labelled_samples": labelled,
        "pseudo_labelled_samples": pseudo,
        "real_depth_samples": labelled - pseudo,
        "per_split": per_split,
        "per_source": per_source,
        "per_depth_type": per_type,
        "per_depth_unit": per_unit,
        "resolutions": resolutions,
        "depth_native_range": {
            "min": min(depths) if depths else None,
            "max": max(depths) if depths else None,
            "median_of_medians": float(np.median(depths)) if depths else None,
        },
        "inverse_scale": manifest.inverse_scale,
        "validity_coverage_mean": round(
            float(np.mean([r["valid_coverage"] for r in validation if "valid_coverage" in r]))
            if any("valid_coverage" in r for r in validation)
            else 0.0,
            4,
        ),
        "flights_with_train_test_overlap": overlap,
        "validation_problems": problems[:20],
        "num_validation_problems": len(problems),
    }


def write_report_markdown(report: Dict[str, Any], path: str) -> None:
    ensure_dir(os.path.dirname(path))
    lines = [
        "# JATAYUV depth dataset summary",
        "",
        f"Generated: {report['generated_utc']}",
        f"Manifest: `{report['manifest_name']}` v{report['manifest_version']}",
        "",
        "## Counts",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Total samples | {report['total_samples']} |",
        f"| Total sequences / flights | {report['total_sequences']} |",
        f"| Depth-labelled samples | {report['labelled_samples']} |",
        f"| Real depth supervision | {report['real_depth_samples']} |",
        f"| Teacher pseudo-labelled | {report['pseudo_labelled_samples']} |",
        f"| Mean valid-depth coverage | {report['validity_coverage_mean']} |",
        f"| Inverse-depth scale | {report['inverse_scale']} |",
        "",
        "## Splits",
        "",
        "| Split | Samples |",
        "| --- | --- |",
    ]
    for split, count in sorted(report["per_split"].items()):
        lines.append(f"| {split} | {count} |")
    lines += ["", "## Sources", "", "| Source | Samples |", "| --- | --- |"]
    for source, count in sorted(report["per_source"].items()):
        lines.append(f"| {source} | {count} |")
    lines += ["", "## Depth supervision", "", "| Type | Unit | Samples |", "| --- | --- | --- |"]
    for depth_type, count in sorted(report["per_depth_type"].items()):
        unit = next(iter(report["per_depth_unit"]), "n/a")
        lines.append(f"| {depth_type} | {unit} | {count} |")
    lines += [
        "",
        "## Resolutions",
        "",
        *[f"- {res}: {count}" for res, count in sorted(report["resolutions"].items())],
        "",
        "## Depth value range (native units)",
        "",
        f"- min: {report['depth_native_range']['min']}",
        f"- max: {report['depth_native_range']['max']}",
        f"- median of per-sample medians: {report['depth_native_range']['median_of_medians']}",
        "",
        "> Relative depth units are **not** metres. Only `depth.unit == 'metre'` supports",
        "> metric error claims.",
        "",
        "## Split hygiene",
        "",
        f"- Flights appearing in more than one split: {report['flights_with_train_test_overlap'] or 'none'}",
        f"- Validation problems: {report['num_validation_problems']}",
    ]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------
def prepare(cfg: Dict[str, Any], sources_override: Optional[List[str]] = None) -> Dict[str, Any]:
    data_cfg = cfg.get("data", {})
    manifest_name = data_cfg.get("manifest_name", "jatayuv_drone_depth")
    out_manifest = os.path.join(REPO_ROOT, data_cfg.get("manifest", "datasets/manifests/jatayuv_drone_depth.json"))
    report_json = os.path.join(REPO_ROOT, data_cfg.get("report_json", "datasets/reports/dataset_summary.json"))
    report_md = os.path.join(REPO_ROOT, data_cfg.get("report_md", "datasets/reports/dataset_summary.md"))

    samples: List[DepthSample] = []
    for source in data_cfg.get("sources", []):
        if sources_override and source.get("name") not in sources_override:
            continue
        kind = source.get("type")
        if kind == "skyscenes":
            for altitude in source["altitudes"]:
                for weather in source["weathers"]:
                    for town in source["towns"]:
                        built = build_skyscenes_samples(
                            source,
                            altitude,
                            weather,
                            town,
                            frames=source.get("frames_per_shard"),
                            frame_stride=int(source.get("frame_stride", 1)),
                        )
                        print(f"[prepare] skyscenes {altitude}/{weather}/{town}: {len(built)} samples")
                        samples.extend(built)
        elif kind == "paired":
            built = build_paired_samples(source)
            print(f"[prepare] paired source '{source.get('name')}': {len(built)} samples")
            samples.extend(built)
        elif kind == "manifest":
            built = merge_manifest_samples(
                os.path.join(REPO_ROOT, source["path"]), source.get("split_hint")
            )
            print(f"[prepare] manifest source '{source['path']}': {len(built)} samples")
            samples.extend(built)
        else:
            raise ValueError(f"Unknown data source type: {kind}")

    if not samples:
        raise RuntimeError(
            "No samples were built. Check data.sources in the config and that the raw "
            "datasets are present (see docs/DEPTH_DATASET_RESEARCH.md)."
        )

    # Deduplicate by image path (a --force re-run must not double-count).
    unique: Dict[str, DepthSample] = {}
    for sample in samples:
        unique.setdefault(sample.image_path, sample)
    samples = list(unique.values())

    counts = assign_splits(samples, data_cfg.get("splits", {}))
    print(f"[prepare] split counts: {counts}")
    if counts.get("unassigned"):
        raise RuntimeError(
            f"{counts['unassigned']} samples have no split assignment. Add their flight_ids "
            "to data.splits.by_flight; random frame-level fallback splits are deliberately "
            "not implemented."
        )
    if counts.get("test", 0) == 0:
        raise RuntimeError("No test split: refusing to build a dataset without held-out data.")

    depth_type = get(data_cfg, "supervision.depth_type", "relative")
    inverse_scale = compute_inverse_scale(
        [s for s in samples if s.split == "train"], depth_type
    )

    validation = [
        validate_sample(sample, check_depth_values=data_cfg.get("validate_values", True))
        for sample in samples
    ]

    manifest = DatasetManifest(
        name=manifest_name,
        version=str(data_cfg.get("manifest_version", "1.0.0")),
        created_at=utc_now_iso(),
        root=os.path.abspath(data_cfg.get("root", "datasets")),
        description=get(data_cfg, "description", ""),
        depth_types_present=sorted({s.depth.type for s in samples if s.depth}),
        inverse_scale=inverse_scale,
        inverse_scale_unit="inverse_relative" if depth_type != "metric" else "inverse_metre",
        samples=samples,
    )
    report = build_report(manifest, validation)
    report["config_path"] = cfg.get("_config_path")
    manifest.statistics = {
        k: report[k]
        for k in (
            "total_samples",
            "per_split",
            "per_depth_type",
            "per_source",
            "inverse_scale",
            "validity_coverage_mean",
        )
    }
    manifest.save(out_manifest)
    write_json(report, report_json)
    write_report_markdown(report, report_md)

    splits_dir = os.path.join(REPO_ROOT, "datasets", "splits")
    ensure_dir(splits_dir)
    for split in ("train", "val", "test"):
        ids = [s.id for s in samples if s.split == split]
        write_json(
            {"manifest": os.path.relpath(out_manifest, REPO_ROOT), "split": split, "ids": ids},
            os.path.join(splits_dir, f"{manifest_name}_{split}.json"),
        )

    print(f"[prepare] manifest : {out_manifest}")
    print(f"[prepare] report   : {report_md}")
    print(
        f"[prepare] inverse_scale={inverse_scale:.6g} "
        f"depth_type={depth_type} samples={len(samples)}"
    )
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare the JATAYUV drone depth dataset")
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--source",
        action="append",
        help="only prepare these data source names (repeatable)",
    )
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    prepare(cfg, sources_override=args.source)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
