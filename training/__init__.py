"""JATAYUV drone-specific Depth Anything V2 (Small) training package.

This package contains the research pipeline for fine-tuning the *official*
Depth Anything V2 **Small** checkpoint on aerial/drone imagery:

    training/
      models/        vendored official DAv2 implementation + model factory
      losses/        depth losses (SILog, masked L1, BerHu, gradient)
      datasets/      unified manifest, torch dataset, dataset acquisition
      preprocessing/ drone media ingestion + dataset preparation / splits
      depth_generation/  teacher pseudo-labels, COLMAP photogrammetry depth
      trainers/      fine-tuning CLI
      evaluation/    metrics, calibration, baseline-vs-finetuned comparison
      configs/       YAML experiment configurations
      checkpoints/   pretrained + fine-tuned weights (git-ignored)

Entry points (run from the repository root):

    python -m training.preprocessing.prepare_dataset --config training/configs/depth_anything_v2_small.yaml
    python -m training.trainers.train_depth --config training/configs/depth_anything_v2_small.yaml
    python -m training.evaluation.evaluate_depth --config training/configs/depth_anything_v2_small.yaml \
        --checkpoint training/checkpoints/finetuned/best_model.pth
"""
