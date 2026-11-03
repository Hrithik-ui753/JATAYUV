import os
import json
from typing import Dict, Any, List
from datetime import datetime, timezone

class ExperimentLogger:
    """Logs training metrics, learning rates, losses, and validation results."""

    def __init__(self, log_dir: str, experiment_name: str, config: Dict[str, Any]):
        self.exp_dir = os.path.join(log_dir, experiment_name)
        os.makedirs(self.exp_dir, exist_ok=True)
        self.log_file = os.path.join(self.exp_dir, "experiment.log")
        self.history_file = os.path.join(self.exp_dir, "history.json")
        self.config_file = os.path.join(self.exp_dir, "config.json")
        
        self.history: List[Dict[str, Any]] = []

        # Save config
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        self.log(f"Initialized Experiment '{experiment_name}' at {datetime.now(timezone.utc).isoformat()}")

    def log(self, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def log_epoch(self, epoch: int, train_loss: float, val_metrics: Dict[str, Any], lr: float):
        record = {
            "epoch": epoch,
            "train_loss": round(float(train_loss), 6),
            "lr": float(lr),
            "val_metrics": val_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.history.append(record)

        # Write history JSON
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

        self.log(
            f"Epoch {epoch:03d} | Train Loss: {train_loss:.4f} | LR: {lr:.2e} | "
            f"Val: {json.dumps({k: v for k, v in val_metrics.items() if not isinstance(v, (dict, list))})}"
        )
