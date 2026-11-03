import os
import sys
import importlib
import pytest

def test_directory_structure():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    required_dirs = [
        "backend",
        "backend/app",
        "backend/app/api/v1",
        "backend/app/core",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/workers",
        "backend/tests",
        "frontend",
        "storage/uploads",
        "storage/processed",
        "storage/models",
        "storage/reconstructions",
        "docs",
    ]
    for rel_path in required_dirs:
        full_path = os.path.join(base_dir, rel_path)
        assert os.path.isdir(full_path), f"Required directory {rel_path} does not exist at {full_path}"

def test_gitignore_and_clean_workspace():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    gitignore_path = os.path.join(base_dir, ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore is missing"
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify critical exclusions
    assert ".env" in content
    assert "node_modules" in content
    assert "*.pt" in content or "*.pth" in content
    assert "uploads/*" in content

def test_core_dependencies():
    modules = [
        "torch",
        "torchvision",
        "transformers",
        "timm",
        "cv2",
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "alembic",
        "celery",
        "redis",
    ]
    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None, f"Module {mod} could not be imported"

def test_frontend_manifest_and_config():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    configs = [
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/tailwind.config.js",
        "frontend/next.config.js",
    ]
    for c in configs:
        full_path = os.path.join(base_dir, c)
        assert os.path.exists(full_path), f"Configuration file {c} is missing"
