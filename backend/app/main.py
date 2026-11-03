import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.api.v1 import auth, projects, images, analysis, reconstruction, jobs, training
from backend.app.api.v1 import models as models_router

# Initialize Database Schema — creates tables for all registered models
import backend.app.models  # noqa: F401 — ensures all models are imported before create_all
Base.metadata.create_all(bind=engine)

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
