import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class TrainingConfig(BaseModel):
    """Configuration for reproducible training runs in JATAYUV-AI."""
    experiment_name: str = "aerial_experiment"
    model_name: str = "aerial_model"
    model_version: str = "v1.0.0"
    model_architecture: str = "deeplabv3_resnet50"
    
    # Dataset
    dataset_name: str = "LoveDA"  # "LoveDA", "xBD", "LEVIR-CD"
    dataset_version: str = "1.0"
    data_dir: str = "./storage/datasets"
    num_classes: int = 7
    
    # Hardware & Precision
    device: str = "cuda" if os.environ.get("USE_CUDA", "false").lower() == "true" else "cpu"
    num_workers: int = 0
    mixed_precision: bool = False
    
    # Hyperparameters
    seed: int = 42
    epochs: int = 10
    batch_size: int = 4
    image_size: int = 256
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    min_lr: float = 1e-6
    scheduler_type: str = "cosine"  # "cosine", "step", "plateau"
    
    # Checkpointing & Validation
    save_dir: str = "./storage/models/checkpoints"
    val_interval: int = 1
    early_stopping_patience: int = 5
    resume_checkpoint_path: Optional[str] = None
    
    # Metadata
    dataset_license: str = "CC BY-NC-SA 4.0"
    author: str = "JATAYUV-AI ML Engineering Team"
