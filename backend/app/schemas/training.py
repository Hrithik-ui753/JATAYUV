from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class DatasetInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    dataset_name: str
    full_name: str
    license: str
    license_url: str
    author: str
    citation: str
    commercial_use_allowed: bool
    classes: List[str]
    acquisition_procedure: str
    integrity_status: Dict[str, Any]

class TrainTriggerRequest(BaseModel):
    experiment_name: str = "aerial_loveda_run"
    model_name: str = "deeplabv3_loveda"
    model_version: str = "v1.0.0"
    dataset_name: str = "LoveDA"  # "LoveDA", "xBD", "LEVIR-CD"
    epochs: int = 2
    batch_size: int = 2
    image_size: int = 256
    learning_rate: float = 1e-4
    seed: int = 42
    use_synthetic_data: bool = True  # If dataset directory not present, use generated synthetic dataset fixture

class TrainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    experiment_name: str
    model_version: str
    best_epoch: int
    best_metric: float
    best_checkpoint_path: str
    test_metrics: Optional[Dict[str, Any]] = None
    history_file: str

class EvaluateRequest(BaseModel):
    checkpoint_path: str
    dataset_name: str
    dataset_dir: str
    split: str = "val"
    batch_size: int = 2

class EvaluateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    dataset_name: str
    split: str
    num_evaluated_samples: int
    checkpoint_path: str
    metrics: Dict[str, Any]

class ExportCheckpointRequest(BaseModel):
    checkpoint_path: str
    task_type: str  # "segmentation", "damage_assessment", "change_detection"
    model_name: str
    version: str
    dataset_name: str
    input_size: int = 512

class ExportCheckpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    success: bool
    registered: bool
    model_name: Optional[str] = None
    version: Optional[str] = None
    architecture: Optional[str] = None
    class_labels: Optional[Dict[int, str]] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
