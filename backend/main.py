"""
AI Video Clipper — FastAPI Main Application
============================================
Entry point untuk backend API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import os
import shutil
import time

from database import init_db
from api.routes import router
from config import settings


def cleanup_directory(directory: str, max_age_seconds: int = 3600):
    """Hapus file di folder jika umurnya sudah lebih dari max_age_seconds (default 1 jam)."""
    if not os.path.exists(directory):
        return

    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                if os.stat(file_path).st_mtime < (now - max_age_seconds):
                    os.remove(file_path)
                    logger.info(f"🧹 Auto-cleaned old file: {file_path}")
            elif os.path.isdir(file_path):
                if os.stat(file_path).st_mtime < (now - max_age_seconds):
                    shutil.rmtree(file_path)
                    logger.info(f"🧹 Auto-cleaned old dir: {file_path}")
        except Exception as e:
            logger.warning(f"Gagal menghapus file {file_path}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events."""
    logger.info("🚀 AI Video Clipper backend starting...")
    await init_db()

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CLIPS_DIR, exist_ok=True)

    cleanup_directory(settings.UPLOAD_DIR, max_age_seconds=1800)  # 30 menit
    cleanup_directory(settings.CLIPS_DIR, max_age_seconds=3600)  # 1 jam

    logger.info("✅ Database initialized")
    logger.info(f"📁 Upload dir: {settings.UPLOAD_DIR}")
    logger.info(f"📁 Clips dir: {settings.CLIPS_DIR}")

    yield

    logger.info("👋 Shutting down... cleaning temporary files.")
    cleanup_directory(settings.UPLOAD_DIR, max_age_seconds=0)
    logger.info("✅ Cleanup done.")


app = FastAPI(
    title="AI Video Clipper API",
    description="Backend API untuk AI Video Clipper",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Regex wildcard yang valid bersama allow_credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ── Middleware Khusus Header Video & Ngrok ───────────────────
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


# ── Routes ──────────────────────────────────────────────────
app.include_router(router, prefix="/api")

# ── Serve Static Clips & Uploads dengan Header Aman ─────────
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response


app.mount("/clips", CORSStaticFiles(directory=settings.CLIPS_DIR), name="clips")
app.mount("/uploads", CORSStaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Video Clipper API", "version": "1.0.0"}


@app.post("/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Endpoint manual jika ingin trigger pembersihan disk."""
    background_tasks.add_task(cleanup_directory, settings.UPLOAD_DIR, 0)
    background_tasks.add_task(cleanup_directory, settings.CLIPS_DIR, 0)
    return {"message": "Pembersihan disk sedang berjalan di latar belakang"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )