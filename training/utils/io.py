"""Config loading, hashing and small filesystem helpers."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def repo_path(*parts: str) -> str:
    """Join a path relative to the repository root."""
    return os.path.join(REPO_ROOT, *parts)


def load_config(path: str) -> Dict[str, Any]:
    """Load a YAML training/evaluation config."""
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config at {path} is not a YAML mapping")
    cfg.setdefault("_config_path", os.path.abspath(path))
    return cfg


def apply_overrides(cfg: Dict[str, Any], overrides: list[str] | None) -> Dict[str, Any]:
    """Apply ``--set a.b=value`` style overrides in place.

    Values are parsed as YAML scalars, so ``--set training.epochs=2`` yields an int
    and ``--set model.freeze=none`` a string.
    """
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"Override '{item}' must be in key.path=value form")
        key, raw = item.split("=", 1)
        value = yaml.safe_load(raw)
        node = cfg
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return cfg


def get(cfg: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    """Read ``a.b.c`` from a nested dict."""
    node: Any = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def dump_config(cfg: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(payload: Any, path: str, indent: int = 2) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=indent, default=str)


def sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def human_bytes(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024 or unit == "TB":
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"
