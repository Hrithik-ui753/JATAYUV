import os
import json
from typing import Dict, Any, Optional
import threading

class ModelRegistry:
    """Central registry for AI models used in the platform.
    Supports lazy loading, checkpoint path management and metadata lookup.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelRegistry":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._models: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    def register(self, name: str, version: str, architecture: str, checkpoint_path: str,
                 dataset: str, input_size: int, class_labels: Optional[Dict[int, str]] = None,
                 preprocessing: Optional[Dict[str, Any]] = None,
                 hardware: str = "cpu", metrics: Optional[Dict[str, Any]] = None) -> None:
        """Register a model with its metadata.
        Overwrites any existing entry with the same name+version.
        """
        key = f"{name}:{version}"
        self._models[key] = {
            "name": name,
            "version": version,
            "architecture": architecture,
            "checkpoint_path": checkpoint_path,
            "dataset": dataset,
            "input_size": input_size,
            "class_labels": class_labels,
            "preprocessing": preprocessing,
            "hardware": hardware,
            "metrics": metrics or {},
            "_loaded": None,  # placeholder for lazy loaded model object
        }

    def get(self, name: str, version: str) -> Dict[str, Any]:
        key = f"{name}:{version}"
        if key not in self._models:
            raise KeyError(f"Model '{name}' version '{version}' not registered.")
        return self._models[key]

    def load(self, name: str, version: str, loader_callable) -> Any:
        """Load the model lazily using the provided callable.
        The callable should accept the checkpoint path and return a model instance.
        """
        meta = self.get(name, version)
        if meta["_loaded"] is None:
            meta["_loaded"] = loader_callable(meta["checkpoint_path"])
        return meta["_loaded"]

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the registry dictionary for introspection."""
        return {k: v.copy() for k, v in self._models.items()}

