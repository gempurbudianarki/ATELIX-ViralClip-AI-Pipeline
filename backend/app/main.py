"""
ATELIX ViralClip AI Pipeline — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api.routes import videos, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ATELIX ViralClip AI Pipeline",
        description="AI-powered autonomous video processing engine for viral short-form content",
        version="0.1.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(videos.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "service": "atelix-viralclip",
            "environment": settings.app_env,
        }

    return app


app = create_app()
