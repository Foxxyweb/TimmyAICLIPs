"""
AI Video Clipper — FastAPI Main Application
============================================
Entry point untuk backend API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import os

from database import init_db
from api.routes import router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events."""
    # Startup
    logger.info("🚀 AI Video Clipper backend starting...")
    await init_db()
    
    # Pastikan direktori upload & clips ada
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CLIPS_DIR, exist_ok=True)
    
    logger.info("✅ Database initialized")
    logger.info(f"📁 Upload dir: {settings.UPLOAD_DIR}")
    logger.info(f"📁 Clips dir: {settings.CLIPS_DIR}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="AI Video Clipper API",
    description="Backend API untuk AI Video Clipper — Mirip Opus Clip / Vizard.ai",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────
app.include_router(router, prefix="/api")

# ── Serve static clips & uploads ────────────────────────────
app.mount("/clips", StaticFiles(directory=settings.CLIPS_DIR), name="clips")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Video Clipper API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
