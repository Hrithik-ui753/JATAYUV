
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, ensure_depth_result_schema
from backend.app.api.v1 import (
    auth,
    projects,
    images,
    analysis,
    reconstruction,
    jobs,
    training,
)
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
    """Warn if the database is not managed by Alembic."""
    from sqlalchemy import inspect

    try:
        tables = set(inspect(engine).get_table_names())
    except Exception as exc:
        logger.warning("Could not inspect database schema: %s", exc)
        return

    if not tables:
        logger.error(
            "Database has no tables. Run Alembic migrations before "
            "starting the API."
        )
    elif "alembic_version" not in tables:
        logger.warning(
            "Database has no alembic_version table. "
            "Run alembic upgrade head."
        )


_warn_if_schema_unmigrated()

# Retain the existing compatibility schema check.
ensure_depth_result_schema()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "JATAYUV-AI - Aerial Intelligence and 3D Photogrammetry Platform. "
        "REST API for project management, video processing, AI perception, "
        "geospatial analysis, and 3D reconstruction."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "JATAYUV Platform",
        "url": "https://jatayuv.ai",
    },
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/storage",
    StaticFiles(directory=settings.STORAGE_DIR),
    name="storage",
)

# Core API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(images.router, prefix=settings.API_V1_STR)
app.include_router(analysis.router, prefix=settings.API_V1_STR)
app.include_router(reconstruction.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(models_router.router, prefix=settings.API_V1_STR)
app.include_router(training.router, prefix=settings.API_V1_STR)

# Mission and drone-video routers
app.include_router(missions.router, prefix=settings.API_V1_STR)
app.include_router(mission_videos.router, prefix=settings.API_V1_STR)
app.include_router(
    mission_flight_metadata.router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    mission_camera_poses.router,
    prefix=settings.API_V1_STR,
)
app.include_router(
    mission_validation.router,
    prefix=settings.API_V1_STR,
)
app.include_router(video_processing_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Platform"])
def health_check():
    return {
        "status": "healthy",
        "platform": "JATAYUV-AI",
        "version": "2.0.0",
        "engine": (
            "PyTorch + OpenCV + Depth Anything V2 + "
            "SegFormer + xBD Damage"
        ),
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

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
