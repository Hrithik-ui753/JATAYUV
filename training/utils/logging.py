"""Experiment logging: plain-text run log + CSV history."""
from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


class ExperimentLogger:
    """Minimal, dependency-free experiment logger.

    Writes a human-readable ``train.log`` and a machine-readable
    ``training_history.csv`` inside the experiment directory.
    """

    def __init__(self, experiment_dir: str, name: str = "depth"):
        self.experiment_dir = experiment_dir
        os.makedirs(experiment_dir, exist_ok=True)
        self.log_path = os.path.join(experiment_dir, "train.log")
        self.history_path = os.path.join(experiment_dir, "training_history.csv")
        self.name = name
        self._fieldnames: List[str] | None = None
        self._write_header = not os.path.isfile(self.history_path)

    def log(self, message: str) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"[{stamp}] {message}"
        print(line, flush=True)
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def log_dict(self, prefix: str, payload: Dict[str, Any]) -> None:
        flat = ", ".join(f"{k}={v}" for k, v in payload.items())
        self.log(f"{prefix}: {flat}")

    def log_epoch(self, row: Dict[str, Any]) -> None:
        fields = list(row.keys())
        if self._fieldnames is None:
            self._fieldnames = fields
        extra = [f for f in fields if f not in self._fieldnames]
        if extra:
            self._fieldnames.extend(extra)
            self._write_header = True

        rows: List[Dict[str, Any]] = []
        if os.path.isfile(self.history_path):
            with open(self.history_path, "r", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))

        if self._write_header:
            self._rewrite(rows + [row])
        else:
            with open(self.history_path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=self._fieldnames, extrasaction="ignore")
                writer.writerow(row)

    def _rewrite(self, rows: Iterable[Dict[str, Any]]) -> None:
        with open(self.history_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self._fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        self._write_header = False


class Tee:
    """Duplicate stdout writes into a file (used by CLI entry points)."""

    def __init__(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.file = open(path, "a", encoding="utf-8")
        self.stdout = sys.stdout

    def write(self, data: str) -> None:
        self.stdout.write(data)
        self.file.write(data)

    def flush(self) -> None:
        self.stdout.flush()
        self.file.flush()

    def close(self) -> None:
        self.file.close()
