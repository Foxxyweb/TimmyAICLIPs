"""
AI Video Clipper — API Routes
================================
Semua REST endpoints dan WebSocket endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
import json
from loguru import logger

from database import get_db
from models import Job, JobStatus
from workers.tasks import process_video_task
from workers.celery_app import celery_app
from config import settings


router = APIRouter()


# ── Pydantic Schemas ─────────────────────────────────────────
class ProcessVideoRequest(BaseModel):
    youtube_url: str
    max_clips: Optional[int] = 5
    min_duration: Optional[int] = 30
    max_duration: Optional[int] = 90


class JobResponse(BaseModel):
    job_id: str
    message: str
    status: str


# ── WebSocket Connection Manager ─────────────────────────────
class ConnectionManager:
    """Manage WebSocket connections per job_id."""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"📡 WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"📡 WebSocket disconnected for job {job_id}")

    async def broadcast_to_job(self, job_id: str, data: dict):
        """Kirim update ke semua client yang subscribe ke job_id."""
        if job_id in self.active_connections:
            dead_connections = []
            for websocket in self.active_connections[job_id]:
                try:
                    await websocket.send_json(data)
                except Exception:
                    dead_connections.append(websocket)
            for ws in dead_connections:
                self.active_connections[job_id].remove(ws)


manager = ConnectionManager()


# ── POST /api/process-video ───────────────────────────────────
@router.post("/process-video", response_model=JobResponse)
async def process_video(
    request: ProcessVideoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint utama — Menerima URL YouTube dan memulai pipeline processing.
    """
    logger.info(f"📥 Received request for URL: {request.youtube_url}")
    
    # Validasi format URL YouTube sederhana
    url = request.youtube_url.strip()
    if not ("youtube.com" in url or "youtu.be" in url):
        raise HTTPException(status_code=400, detail="URL harus berupa link YouTube yang valid.")
    
    # Buat Job record
    job = Job(
        youtube_url=url,
        status=JobStatus.PENDING,
        progress=0,
        status_message="Job dibuat, menunggu antrian...",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    logger.info(f"✅ Job created: {job.id}")
    
    # Kirim ke Celery background task
    task = process_video_task.apply_async(
        args=[job.id, url],
        kwargs={
            "max_clips": request.max_clips or settings.MAX_CLIPS,
            "min_duration": request.min_duration or settings.CLIP_MIN_DURATION,
            "max_duration": request.max_duration or settings.CLIP_MAX_DURATION,
        }
    )
    
    # Simpan celery task ID
    job.celery_task_id = task.id
    await db.commit()
    
    return JobResponse(
        job_id=job.id,
        message="Processing dimulai! Track progress via WebSocket.",
        status="pending"
    )


# ── POST /api/jobs/{job_id}/cancel ───────────────────────────
@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Membatalkan proses pemrosesan video."""
    result = await db.execute(
        select(Job).options(selectinload(Job.clips)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")

    # Update status ke CANCELLED
    job.status = JobStatus.CANCELLED
    job.status_message = "Proses telah dibatalkan oleh pengguna."
    job.error_message = "Cancelled by user"
    await db.commit()

    # Hentikan/Revoke Task di Celery
    if job.celery_task_id:
        try:
            celery_app.control.revoke(job.celery_task_id, terminate=True, signal='SIGKILL')
            logger.info(f"🛑 Celery task {job.celery_task_id} revoked.")
        except Exception as e:
            logger.error(f"Gagal revoke task Celery: {e}")

    return {"message": f"Job {job_id} berhasil dibatalkan.", "status": "cancelled"}


# ── GET /api/jobs/{job_id} ────────────────────────────────────
@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Ambil status dan detail sebuah job."""
    result = await db.execute(
        select(Job).options(selectinload(Job.clips)).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} tidak ditemukan.")
    
    return job.to_dict()


# ── GET /api/jobs ─────────────────────────────────────────────
@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    """Daftar semua jobs (untuk history)."""
    result = await db.execute(
        select(Job).options(selectinload(Job.clips)).order_by(Job.created_at.desc()).limit(50)
    )
    jobs = result.scalars().all()
    return [j.to_dict() for j in jobs]


# ── DELETE /api/jobs/{job_id} ─────────────────────────────────
@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Hapus sebuah job dan semua clip-nya."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    
    await db.delete(job)
    await db.commit()
    return {"message": f"Job {job_id} berhasil dihapus."}


# ── WebSocket /api/ws/{job_id} ────────────────────────────────
@router.websocket("/ws/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint — Push real-time status updates ke frontend.
    """
    await manager.connect(websocket, job_id)
    
    try:
        # Loop interval kirim status ke frontend
        while True:
            # Query status job terbaru dari DB beserta relasi clips
            result = await db.execute(
                select(Job).options(selectinload(Job.clips)).where(Job.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                await websocket.send_json(job.to_dict())
                
                # 🛑 KUNCI PERBAIKAN: Jika job Selesai, Gagal, ATAU Dibatalkan, hentikan loop & WS secara bersih!
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    logger.info(f"🛑 Stream selesai/dibatalkan untuk job {job_id}. Memutus WebSocket.")
                    break

            await asyncio.sleep(1.5)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        manager.disconnect(websocket, job_id)