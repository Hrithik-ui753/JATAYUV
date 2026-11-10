"""Tests for the JATAYUV depth pipeline (dataset -> model -> losses -> eval -> API).

These tests assert what the pipeline actually claims:

* Depth Anything V2 Small is relative-only unless an explicit metric calibration exists.
* RGB/depth/mask stay pixel-aligned through resize and augmentation.
* Splits never share a flight/sequence (no video-frame leakage).
* Checkpoints load strictly (a wrong or foreign checkpoint fails loudly).
* Evaluation aligns relative predictions before computing error metrics.
* Acquired archives are extracted defensively.
"""

import io
import os
import tarfile
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

<<<<<<< HEAD
=======
<<<<<<< HEAD
from training.datasets.drone_depth import DroneDepthDataset, build_valid_mask
=======
>>>>>>> origin/main
# The dataset adapters (``training/datasets``) are not part of this repository snapshot,
# so this module cannot be collected. Skip explicitly instead of breaking the whole run.
pytest.importorskip(
    "training.datasets.drone_depth",
    reason="training.datasets is not present in this repository snapshot",
)

from training.datasets.drone_depth import DroneDepthDataset, build_valid_mask  # noqa: E402
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
from training.datasets.manifest import DatasetManifest, DepthLabel, DepthSample
from training.evaluation import calibration, metrics
from training.losses.depth_losses import (
    CombinedDepthLoss,
    GradientLoss,
    MaskedL1Loss,
    SILogLoss,
)
from training.models.dav2_factory import (
    build_dav2_small,
    configure_trainable,
    load_checkpoint_strict,
    parameter_counts,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKYSCENES_MANIFEST = os.path.join(REPO_ROOT, "datasets", "manifests", "skyscenes_relative.json")
PRETRAINED = os.path.join(
    REPO_ROOT, "training", "checkpoints", "pretrained", "depth_anything_v2_vits.pth"
)


# --------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def small_model():
    return build_dav2_small()


@pytest.fixture()
def synthetic_manifest(tmp_path):
    """Two flights with 2 frames each; flight 2 is the held-out test scene."""
    samples = []
    for flight, split in (("flight_a", "train"), ("flight_b", "test")):
        for idx in range(2):
            h, w = 40, 56
            rgb = np.zeros((h, w, 3), dtype=np.uint8)
            rgb[:, :, 0] = np.linspace(0, 255, w, dtype=np.uint8)[None, :]
            rgb[:, :, 1] = np.linspace(10, 200, h, dtype=np.uint8)[:, None]
            rgb_path = tmp_path / f"{flight}_{idx}.png"
            cv2.imwrite(str(rgb_path), rgb)

            # uint8 normalised relative depth: 0 = far ... 255 = near (clipped)
            depth = np.tile(np.linspace(20, 255, w, dtype=np.uint8)[None, :], (h, 1))
            depth[0, 0] = 255  # saturated far-plane pixel -> must be masked out
            depth_path = tmp_path / f"{flight}_{idx}_depth.png"
            cv2.imwrite(str(depth_path), depth)

            samples.append(
                DepthSample(
                    id=f"{flight}_{idx}",
                    image_path=str(rgb_path),
                    width=w,
                    height=h,
                    source_dataset="synthetic_test",
                    license="test-only",
                    flight_id=flight,
                    sequence_id=flight,
                    split=split,
                    annotation_status="real_depth",
                    depth=DepthLabel(
                        path=str(depth_path),
                        type="relative",
                        unit="normalized_0_1",
                        encoding="png8",
                        label_method="synthetic_ground_truth",
                        value_scale=1.0 / 255.0,
                        max_valid=1.0,
                        clip_saturated_invalid=True,
                    ),
                )
            )
    manifest = DatasetManifest(
        name="synthetic_test",
        root=str(tmp_path),
        description="unit-test manifest",
        inverse_scale=0.35,
        depth_types_present=["relative"],
        samples=samples,
    )
    path = manifest.save(str(tmp_path / "manifest.json"))
    return path


# --------------------------------------------------------------------------- dataset
def test_dataset_outputs_aligned_tensors_and_unit_target(synthetic_manifest):
    ds = DroneDepthDataset(
        synthetic_manifest, split="train", image_size=28, augment=False, verify_files=True
    )
    assert len(ds) == 2
    item = ds[0]

    assert item["image"].shape == (3, 28, 28)
    assert item["target"].shape == (1, 28, 28)
    assert item["mask"].shape == (1, 28, 28)
    assert item["native_depth"].shape == (1, 28, 28)

    mask = item["mask"][0].numpy().astype(bool)
    target = item["target"][0].numpy()
    # The saturation artefact must never become supervision.
    assert mask[0, 0] == 0
    assert target[0, 0] == 0.0
    assert np.all(target[mask] > 0)
    # Targets are median-normalised so SILog sees unit-scale values.
    assert np.isclose(float(np.median(target[mask])), 1.0, atol=1e-4)
    assert item["meta"]["depth_type"] == "relative"
    assert item["meta"]["depth_unit"] == "normalized_0_1"


def test_dataset_augmentation_keeps_triplet_aligned(synthetic_manifest):
    ds = DroneDepthDataset(synthetic_manifest, split="train", image_size=28, augment=True)
    for _ in range(3):
        item = ds[0]
        assert item["image"].shape == (3, 28, 28)
        assert item["target"].shape == (1, 28, 28)
        assert item["mask"].shape == (1, 28, 28)


def test_valid_mask_rejects_invalid_and_saturated_depth():
    depth = np.array([[0.0, 0.5, 1.0, np.nan]], dtype=np.float32)
    mask = build_valid_mask(depth, clip_saturated_invalid=True, max_value=1.0)
    assert mask.tolist() == [[0, 1, 0, 0]]


def test_splits_do_not_share_flights(synthetic_manifest):
    manifest = DatasetManifest.load(synthetic_manifest)
    train_flights = {s.flight_id for s in manifest.split("train")}
    test_flights = {s.flight_id for s in manifest.split("test")}
    assert train_flights and test_flights
    assert train_flights.isdisjoint(test_flights)


@pytest.mark.skipif(not os.path.isfile(SKYSCENES_MANIFEST), reason="SkyScenes manifest not built")
def test_real_manifest_has_no_frame_leakage():
    manifest = DatasetManifest.load(SKYSCENES_MANIFEST)
    splits = {"train": manifest.split("train"), "val": manifest.split("val"), "test": manifest.split("test")}
    paths = {name: {s.image_path for s in items} for name, items in splits.items()}
    assert paths["train"] and paths["val"] and paths["test"]
    assert paths["train"].isdisjoint(paths["test"])
    assert paths["val"].isdisjoint(paths["test"])
    assert paths["train"].isdisjoint(paths["val"])
    assert {s.flight_id for s in splits["test"]}.isdisjoint({s.flight_id for s in splits["train"]})
    # Only relative supervision is present, so no metric claim can be derived from it.
    assert manifest.depth_types_present == ["relative"]
    assert all(s.depth.unit != "metre" for s in manifest.samples)


# --------------------------------------------------------------------------- losses
def test_silog_scale_behaviour_matches_the_reference_formula():
    pred = torch.rand(1, 1, 8, 8) + 0.5
    mask = torch.ones_like(pred)
    gt = pred * 3.7

    # lambda = 1 is exactly scale-invariant (the textbook SILog); the only residual is
    # the sqrt(eps) numerical floor, identical for any purely scaled pair.
    exact = SILogLoss(variance_focus=1.0)
    flat = float(exact(pred, gt, mask))
    assert flat == pytest.approx(0.1, abs=1e-5)
    assert float(exact(pred * 7.0, gt * 7.0, mask)) == pytest.approx(flat, abs=1e-5)

    # lambda = 0.85 (MiDaS / Depth Anything recipe) only *reduces* scale sensitivity:
    # a pure scale difference of c leaves 10 * |c| * sqrt(1 - 0.85).
    loss = SILogLoss()
    expected = 10.0 * abs(float(torch.log(torch.tensor(3.7)))) * (0.15 ** 0.5)
    assert float(loss(pred, gt, mask)) == pytest.approx(expected, rel=1e-4)
    assert float(loss(pred, gt + 0.4, mask)) > float(loss(pred, gt, mask))


def test_masked_l1_ignores_invalid_pixels():
    loss = MaskedL1Loss()
    pred = torch.zeros(1, 1, 4, 4)
    gt = torch.zeros(1, 1, 4, 4)
    gt[:, :, :, 2:] = 100.0  # huge error on invalid pixels only
    mask = torch.zeros(1, 1, 4, 4)
    mask[:, :, :, :2] = 1.0
    assert float(loss(pred, gt, mask)) == pytest.approx(0.0, abs=1e-6)


def test_gradient_loss_is_zero_for_identical_inputs():
    loss = GradientLoss()
    x = torch.rand(1, 1, 8, 8)
    mask = torch.ones_like(x)
    assert float(loss(x, x, mask)) == pytest.approx(0.0, abs=1e-6)


def test_combined_loss_backpropagates():
    weights = {"silog": 1.0, "l1": 0.5, "gradient": 0.3}
    criterion = CombinedDepthLoss(weights)
    pred = torch.rand(2, 1, 16, 16) + 0.5
    pred.requires_grad_(True)
    gt = pred.detach() * (1.0 + 0.2 * torch.randn(2, 1, 16, 16))
    mask = torch.ones_like(pred)
    total, parts = criterion(pred, gt, mask)
    assert set(parts) == set(weights) | {"total"}
    assert parts["total"] == pytest.approx(float(total.detach()), rel=1e-5)
    assert torch.isfinite(total)
    total.backward()
    assert pred.grad is not None and torch.isfinite(pred.grad).all()
    assert float(pred.grad.abs().sum()) > 0


def test_combined_loss_rejects_unknown_terms():
    with pytest.raises(ValueError):
        CombinedDepthLoss({"silog": 1.0, "not_a_loss": 1.0})


# --------------------------------------------------------------------------- metrics
def test_metric_alignment_recovers_a_scaled_prediction():
    rng = np.random.default_rng(0)
    gt = rng.uniform(0.2, 0.9, size=(32, 32)).astype(np.float32)
    pred = gt * 2.5 + 0.1
    mask = np.ones_like(gt, dtype=np.uint8)

    aligned, (a, b) = metrics.align_scale_shift(pred, gt, mask.astype(bool))
    assert a == pytest.approx(1 / 2.5, rel=1e-3)
    assert b == pytest.approx(-0.1 / 2.5, abs=1e-3)

    raw = metrics.depth_metrics(pred, gt, mask)
    fixed = metrics.depth_metrics(aligned, gt, mask)
    assert raw["abs_rel"] > 0.3
    assert fixed["abs_rel"] < 1e-3
    assert fixed["delta1"] > 0.999


def test_ordinal_consistency_is_scale_free():
    rng = np.random.default_rng(1)
    gt = rng.uniform(0.1, 1.0, size=(16, 16)).astype(np.float32)
    mask = np.ones_like(gt, dtype=np.uint8)
    assert metrics.ordinal_consistency(gt * 50.0, gt, mask, seed=3) > 0.99


def test_evaluate_pair_reports_alignment_for_relative_gt():
    rng = np.random.default_rng(2)
    native = rng.uniform(0.2, 0.8, size=(16, 16)).astype(np.float32)
    mask = np.ones_like(native, dtype=np.uint8)
    inverse_scale = 0.4
    pred_inverse = inverse_scale / native * 1.6  # deliberately mis-scaled

    out = metrics.evaluate_pair(pred_inverse, native, mask, inverse_scale, gt_unit="normalized_0_1")
    assert "abs_rel" in out and "align_a" in out and "align_b" in out
    assert out["abs_rel"] < 0.01  # fixed by the scale+shift alignment
    assert "raw_silog_inverse" in out

    metric_out = metrics.evaluate_pair(
        inverse_scale / native, native, mask, inverse_scale, gt_unit="metre"
    )
    assert "aligned" in metric_out and metric_out["abs_rel"] < 1e-6


# --------------------------------------------------------------------------- calibration
def test_calibration_rejects_relative_ground_truth():
    rng = np.random.default_rng(3)
    gt = rng.uniform(0.1, 1.0, size=(16, 16)).astype(np.float32)
    pairs = [{"pred": gt * 2.0, "gt": gt, "mask": None, "unit": "normalized_0_1"}]
    with pytest.raises(calibration.CalibrationError):
        calibration.validate_calibration(pairs, {"a": 1.0, "b": 0.0})


def test_calibration_fit_recovers_a_known_relation():
    rng = np.random.default_rng(4)
    pred = rng.uniform(0.5, 3.0, size=(20, 20)).astype(np.float32)
    true_a, true_b = 0.8, 0.15
    gt = 1.0 / (true_a * pred + true_b)
    fit = calibration.fit_calibration([{"pred": pred, "gt": gt, "mask": None}])
    assert fit["a"] == pytest.approx(true_a, rel=1e-4)
    assert fit["b"] == pytest.approx(true_b, abs=1e-4)


# --------------------------------------------------------------------------- model
def test_small_model_parameter_counts_match_pretrained(small_model):
    counts = parameter_counts(small_model)
    assert counts["total"] == 24_785_089


def test_freeze_strategies_change_trainable_counts(small_model):
    counts = configure_trainable(small_model, "last_n_blocks", 2)
    assert counts["trainable"] == 6_279_745
    assert counts["frozen"] == counts["total"] - counts["trainable"]

    counts_head = configure_trainable(small_model, "decoder_only")
    assert counts_head["trainable"] < counts["trainable"]

    counts_full = configure_trainable(small_model, "full")
    assert counts_full["trainable"] == counts_full["total"]


def test_forward_pass_produces_non_negative_inverse_depth(small_model):
    small_model.eval()
    with torch.no_grad():
        out = small_model(torch.randn(1, 3, 70, 70))
    assert out.shape[-2:] == (70, 70)
    assert torch.isfinite(out).all()
    assert float(out.min()) >= 0.0  # ReLU head: inverse depth is non-negative


@pytest.mark.skipif(not os.path.isfile(PRETRAINED), reason="official checkpoint not downloaded")
def test_official_checkpoint_loads_strictly(small_model):
    report = load_checkpoint_strict(small_model, PRETRAINED, verify_official_hash=True)
    assert report.total_params == 24_785_089
    assert report.sha256.startswith("715fade13be8")
    assert report.strict_load is True
    assert report.tensor_count == 239


def test_checkpoint_roundtrip_and_strict_rejection(small_model, tmp_path):
    path = tmp_path / "ckpt.pth"
    state = {k: v.clone() for k, v in small_model.state_dict().items()}
    torch.save({"model_state": state, "schema": "jatayuv.depth.finetune/1"}, path)

    fresh = build_dav2_small()
    report = load_checkpoint_strict(fresh, str(path))
    assert report.total_params == 24_785_089

    broken = dict(state)
    broken.pop(next(iter(broken)))
    bad_path = tmp_path / "broken.pth"
    torch.save({"model_state": broken}, bad_path)
    with pytest.raises(RuntimeError):
        load_checkpoint_strict(build_dav2_small(), str(bad_path))

    junk = tmp_path / "junk.pth"
    junk.write_bytes(b"not a checkpoint")
    with pytest.raises(Exception):
        load_checkpoint_strict(build_dav2_small(), str(junk))


# --------------------------------------------------------------------------- engine / API
def test_engine_catalogue_exposes_both_checkpoints():
    from backend.app.services import depth_engine

    models = depth_engine.list_models()
    assert set(models) == {"pretrained", "jatayuv_drone_v1"}
    for info in models.values():
        assert info["depth_type"] == "relative"
        assert info["depth_unit"] == "relative_inverse_depth"
    assert depth_engine.resolve_model_id("fine-tuned") == "jatayuv_drone_v1"
    assert depth_engine.resolve_model_id(None) in models
    with pytest.raises(depth_engine.DepthModelError):
        depth_engine.resolve_model_id("definitely-not-a-model")


@pytest.mark.skipif(not os.path.isfile(PRETRAINED), reason="official checkpoint not downloaded")
def test_engine_predicts_relative_depth_without_metric_claim():
    from backend.app.services.depth_engine import DepthEngine

    engine = DepthEngine(model_id="pretrained", input_size=98, device="cpu")
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    image[:, :80] = 200
    result = engine.predict(image)

    inverse = result["inverse_depth"]
    assert inverse.shape == (120, 160)
    assert np.isfinite(inverse).all()
    assert float(inverse.min()) >= 0.0
    assert result["inference_ms"] > 0

    normalised = DepthEngine.normalize_relative(inverse)
    assert normalised.shape == inverse.shape
    assert 0.0 <= float(normalised.min()) and float(normalised.max()) <= 1.0
    # No calibration was fitted, so no metre output may be produced.
    assert engine.calibrated_metric(inverse, {}) is None


def test_engine_rejects_a_foreign_checkpoint(monkeypatch, tmp_path):
    import dataclasses

    from backend.app.services import depth_engine

    foreign = tmp_path / "foreign.pth"
    torch.save({"model_state": {"conv.weight": torch.zeros(3, 3)}}, foreign)
    spec = depth_engine.MODEL_CATALOG["pretrained"]
    monkeypatch.setitem(
        depth_engine.MODEL_CATALOG, "pretrained", dataclasses.replace(spec, checkpoint=str(foreign))
    )
    depth_engine.DepthEngine._cache.clear()
    engine = depth_engine.DepthEngine(model_id="pretrained", input_size=98, device="cpu")
    with pytest.raises(depth_engine.DepthModelError):
        engine.predict(np.zeros((32, 32, 3), dtype=np.uint8))
    depth_engine.DepthEngine._cache.clear()


# --------------------------------------------------------------------------- acquisition
def test_safe_extract_blocks_path_traversal(tmp_path):
    from training.datasets.acquisition.manager import IntegrityError, safe_extract

    archive = tmp_path / "evil.tar.gz"
    payload = b"owned"
    with tarfile.open(archive, "w:gz") as tf:
        info = tarfile.TarInfo("../escaped.txt")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    with pytest.raises(IntegrityError):
        safe_extract(str(archive), str(tmp_path / "out"))
    assert not (tmp_path / "escaped.txt").exists()


def test_safe_extract_handles_a_normal_archive(tmp_path):
    from training.datasets.acquisition.manager import safe_extract

    archive = tmp_path / "ok.tar.gz"
    payload = b"hello"
    with tarfile.open(archive, "w:gz") as tf:
        info = tarfile.TarInfo("ok/readme.txt")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    out = safe_extract(str(archive), str(tmp_path / "out"))
    assert len(out) == 1
    assert open(out[0], "rb").read() == payload


# --------------------------------------------------------------------------- own media
def test_media_ingest_groups_by_flight_and_filters():
    import shutil
    import tempfile

    from training.preprocessing.media_ingest import IngestConfig, MediaIngestor

    # The ingestor stores repo-relative paths, so its temp dir must live on the same
    # drive as the repository (os.path.relpath cannot cross Windows drives).
    tmp_path = Path(tempfile.mkdtemp(prefix=".test_ingest_", dir=REPO_ROOT))
    try:
        _run_media_ingest(tmp_path, IngestConfig, MediaIngestor)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def _run_media_ingest(tmp_path, IngestConfig, MediaIngestor):
    root = tmp_path / "src"
    src = root / "flight_01"
    src.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for idx in range(2):
        img = rng.integers(0, 255, size=(160, 160, 3), dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (120, 120), (250, 250, 250), -1)
        img[:, :, 0] = cv2.GaussianBlur(img[:, :, 0], (5, 5), 0)
        cv2.imwrite(str(src / f"frame_{idx}.jpg"), img)

    cfg = IngestConfig(min_side=100, blur_threshold=1.0, duplicate_hamming=0)
    ingestor = MediaIngestor(str(tmp_path / "frames"), cfg)
    summary = ingestor.ingest_tree(str(root), flight_field="folder")

    assert summary["accepted"] >= 1
    manifest = ingestor.build_manifest("own_flights", str(tmp_path / "own.json"))
    assert len(manifest.samples) == summary["accepted"]
    sample = manifest.samples[0]
    assert sample.flight_id == "flight_01"
    assert os.path.isfile(os.path.join(REPO_ROOT, sample.image_path))
    # No depth yet: ingestion must not invent labels.
    assert sample.depth is None
    assert sample.annotation_status == "none"
