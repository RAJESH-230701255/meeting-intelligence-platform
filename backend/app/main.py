"""Meeting Intelligence Platform — FastAPI Application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import auth, users, meetings, transcripts, analysis, tasks, dashboards, notifications

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — create upload directory on startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Meeting Intelligence Platform",
    description="AI-Powered Meeting Intelligence and Task Tracking Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(meetings.router)
app.include_router(transcripts.router)
app.include_router(analysis.router)
app.include_router(tasks.router)
app.include_router(dashboards.router)
app.include_router(notifications.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Meeting Intelligence Platform",
        "ai_provider": settings.AI_PROVIDER,
        "speech_provider": settings.SPEECH_PROVIDER,
    }
