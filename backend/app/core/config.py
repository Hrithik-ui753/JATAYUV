import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JATAYUV-AI Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jatayuv-production-insecure-secret-key-change-in-env-39485")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./storage/jatayuv.db")

    # Storage Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", os.path.join(BASE_DIR, "storage"))
    UPLOAD_DIR: str = os.path.join(STORAGE_DIR, "uploads")
    PROCESSED_DIR: str = os.path.join(STORAGE_DIR, "processed")
    MODELS_DIR: str = os.path.join(STORAGE_DIR, "models")
    RECONSTRUCTION_DIR: str = os.path.join(STORAGE_DIR, "reconstructions")

    # Binaries & Tools
    COLMAP_EXE: str = os.getenv("COLMAP_EXE", os.path.join(BASE_DIR, ".tools", "colmap", "bin", "colmap.exe"))

    # File validation
    MAX_UPLOAD_SIZE_BYTES: int = 500 * 1024 * 1024  # 500 MB
    ALLOWED_IMAGE_MIME_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    ]

    # Celery & Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    # Development-only: run tasks inline in the calling process. Must stay
    # false in production because it blocks the API request for the whole
    # pipeline and provides none of Celery's durability guarantees.
    CELERY_TASK_ALWAYS_EAGER: bool = (
        os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
    )

    # Development flags
    ALLOW_ANONYMOUS_ACCESS: bool = os.getenv("ALLOW_ANONYMOUS_ACCESS", "true").lower() == "true"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
for d in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.MODELS_DIR, settings.RECONSTRUCTION_DIR]:
    os.makedirs(d, exist_ok=True)

