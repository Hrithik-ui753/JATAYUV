import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.api.v1 import auth, projects, images, analysis, reconstruction, jobs, training
from backend.app.api.v1 import models as models_router
from backend.app.api.v1 import (
    mission_camera_poses,
    mission_flight_metadata,
    mission_validation,
    mission_videos,
    missions,
)
from backend.app.api.v1.routers import video_processing_router

logger = logging.getLogger(__name__)


def _warn_if_schema_unmigrated() -> None:
    """Warn (do not silently mutate) when the database has no Alembic stamp.

    Schema provisioning is owned by Alembic (``alembic upgrade head``). The
    application never calls ``create_all`` at startup, because doing so hides
    missing migrations and produces schema drift on existing installations.
    """
    from sqlalchemy import inspect

    try:
        tables = set(inspect(engine).get_table_names())
    except Exception as exc:  # database unreachable
        logger.warning("Could not inspect database schema: %s", exc)
        return
    if not tables:
        logger.error(
            "Database has no tables. Run 'alembic upgrade head' before starting "
            "the API (see backend/alembic.ini)."
        )
    elif "alembic_version" not in tables:
        logger.warning(
            "Database has no alembic_version table; run 'alembic upgrade head' "
            "to bring the schema under migration control."
        )


_warn_if_schema_unmigrated()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "JATAYUV-AI — Aerial Intelligence and 3D Photogrammetry Platform. "
        "Full REST API for project management, image analysis, background job orchestration, "
        "and 3D reconstruction workflows."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "JATAYUV Platform", "url": "https://jatayuv.ai"},
    license_info={"name": "Proprietary"},
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage for fast binary asset serving (images, thumbnails, PLY models)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include API v1 Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(images.router, prefix=settings.API_V1_STR)
app.include_router(analysis.router, prefix=settings.API_V1_STR)
app.include_router(reconstruction.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(models_router.router, prefix=settings.API_V1_STR)
app.include_router(training.router, prefix=settings.API_V1_STR)

# Mission / video routers
app.include_router(missions.router, prefix=settings.API_V1_STR)
app.include_router(mission_videos.router, prefix=settings.API_V1_STR)
app.include_router(mission_flight_metadata.router, prefix=settings.API_V1_STR)
app.include_router(mission_camera_poses.router, prefix=settings.API_V1_STR)
app.include_router(mission_validation.router, prefix=settings.API_V1_STR)
app.include_router(video_processing_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Platform"])
def health_check():
    return {
        "status": "healthy",
        "platform": "JATAYUV-AI",
        "version": "2.0.0",
        "engine": "PyTorch + OpenCV + Depth Anything V2 + SegFormer + xBD Damage",
        "api_version": "v1",
    }


@app.get("/", tags=["Platform"])
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
