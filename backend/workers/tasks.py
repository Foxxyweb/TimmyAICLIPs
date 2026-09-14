"""
AI Video Clipper — Celery Background Tasks
============================================
Pipeline utama video processing yang berjalan di background.

Pipeline:
  1. Fetch video metadata (info)
  2. Download video (yt-dlp)
  3. Extract audio (FFmpeg)
  4. Transcribe audio (faster-whisper)
  5. Detect viral moments (Google Gemini)
  6. Render clips (FFmpeg)
  7. Save results to database
"""

import asyncio
import os
from datetime import datetime, timezone
from loguru import logger
from celery import Task

from workers.celery_app import celery_app
from database import AsyncSessionLocal
from models import Job, Clip, JobStatus
from services.downloader import VideoDownloader
from services.transcriber import TranscriptionService
from services.ai_analyzer import AIAnalyzer
from services.video_processor import VideoProcessor
from config import settings


# ── Helper: update job status ─────────────────────────────────
def update_job_sync(job_id: str, **kwargs):
    """
    Update job di database secara synchronous (dari Celery task).
    Karena Celery berjalan di thread terpisah, kita buat event loop baru.
    """
    async def _update():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                for key, value in kwargs.items():
                    setattr(job, key, value)
                await db.commit()
                logger.info(f"📊 Job {job_id[:8]}... → status={kwargs.get('status', '-')}, progress={kwargs.get('progress', '-')}%")
    
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_update())
    finally:
        loop.close()


def check_job_cancelled_sync(job_id: str) -> bool:
    """Cek apakah status job di database bernilai CANCELLED."""
    async def _check() -> bool:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                status_val = job.status.value if hasattr(job.status, "value") else str(job.status)
                return status_val == "CANCELLED"
            return False

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_check())
    finally:
        loop.close()


def save_clips_sync(job_id: str, clips_data: list):
    """Simpan data clips ke database."""
    async def _save():
        async with AsyncSessionLocal() as db:
            for clip_info in clips_data:
                if clip_info.get("status") != "success":
                    continue
                
                clip = Clip(
                    job_id=job_id,
                    clip_index=clip_info.get("clip_number", 0),
                    title=clip_info.get("title", ""),
                    description=clip_info.get("description", ""),
                    start_time=clip_info.get("start_time", 0),
                    end_time=clip_info.get("end_time", 0),
                    duration=clip_info.get("duration", 0),
                    viral_score=clip_info.get("viral_score", 0),
                    filename=clip_info.get("filename"),
                    file_size=clip_info.get("file_size"),
                )
                db.add(clip)
            
            await db.commit()
            logger.info(f"✅ Saved {len(clips_data)} clips to database for job {job_id}")
    
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_save())
    finally:
        loop.close()


# ── Main Task ─────────────────────────────────────────────────
@celery_app.task(
    name="workers.tasks.process_video_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    track_started=True,
)
def process_video_task(
    self: Task,
    job_id: str,
    youtube_url: str,
    max_clips: int = 5,
    min_duration: int = 30,
    max_duration: int = 90,
):
    """
    Main Celery task — Menjalankan full pipeline processing video.
    """
    
    logger.info(f"🚀 Starting pipeline for job {job_id}")
    logger.info(f"   URL: {youtube_url}")
    logger.info(f"   Settings: max_clips={max_clips}, duration={min_duration}-{max_duration}s")
    
    # Services
    downloader   = VideoDownloader()
    transcriber  = TranscriptionService()
    ai_analyzer  = AIAnalyzer()
    processor    = VideoProcessor()
    
    video_path  = None
    audio_path  = None
    
    def is_cancelled() -> bool:
        return check_job_cancelled_sync(job_id)
    
    try:
        if is_cancelled():
            logger.warning(f"🛑 Job {job_id} sudah dibatalkan sebelum diproses.")
            return {"job_id": job_id, "status": "cancelled"}

        # ── STEP 1: Fetch video info ─────────────────────────
        update_job_sync(
            job_id,
            status=JobStatus.DOWNLOADING,
            progress=2,
            status_message="Mengambil informasi video..."
        )
        
        try:
            video_info = downloader.get_video_info(youtube_url)
            update_job_sync(
                job_id,
                video_title=video_info["title"],
                video_duration=video_info["duration"],
                thumbnail_url=video_info["thumbnail"],
                status_message=f"Mengunduh: {video_info['title'][:50]}..."
            )
            logger.info(f"📹 Video: {video_info['title']} ({video_info['duration']}s)")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch video info: {e}")
        
        # ── STEP 2: Download video ───────────────────────────
        def download_progress(percent, message):
            progress = int(2 + (percent * 0.23))  # 2% → 25%
            update_job_sync(
                job_id,
                status=JobStatus.DOWNLOADING,
                progress=progress,
                status_message=message,
            )
        
        update_job_sync(
            job_id,
            status=JobStatus.DOWNLOADING,
            progress=5,
            status_message="Mengunduh video dari YouTube..."
        )
        
        video_path = downloader.download_video(
            url=youtube_url,
            job_id=job_id,
            progress_callback=download_progress,
            is_cancelled_callback=is_cancelled,
        )
        
        update_job_sync(
            job_id,
            progress=25,
            status_message="Video berhasil diunduh! Mengekstrak audio..."
        )
        
        if is_cancelled():
            raise RuntimeError(f"Download dibatalkan oleh pengguna untuk job {job_id}")

        # ── STEP 3: Extract audio ────────────────────────────
        audio_path = downloader.extract_audio(video_path, job_id)
        
        update_job_sync(
            job_id,
            progress=30,
            status_message="Audio berhasil diekstrak!"
        )
        
        if is_cancelled():
            raise RuntimeError(f"Proses dibatalkan oleh pengguna untuk job {job_id}")

        # ── STEP 4: Transcribe audio ─────────────────────────
        def transcribe_progress(percent, message):
            progress = int(30 + (percent * 0.25))  # 30% → 55%
            update_job_sync(
                job_id,
                status=JobStatus.TRANSCRIBING,
                progress=progress,
                status_message=message,
            )
        
        update_job_sync(
            job_id,
            status=JobStatus.TRANSCRIBING,
            progress=31,
            status_message="Transkripsi audio dengan Whisper AI..."
        )
        
        transcription = transcriber.transcribe(
            audio_path=audio_path,
            progress_callback=transcribe_progress,
        )
        
        formatted_transcript = transcriber.format_for_ai(transcription)
        video_duration = transcription["duration"]
        
        update_job_sync(
            job_id,
            progress=55,
            status_message=f"Transkripsi selesai! {len(transcription['segments'])} segmen ditemukan."
        )
        
        if is_cancelled():
            raise RuntimeError(f"Proses dibatalkan oleh pengguna untuk job {job_id}")

        # ── STEP 5: AI Viral Moment Detection ────────────────
        def ai_progress(percent, message):
            progress = int(55 + (percent * 0.15))  # 55% → 70%
            update_job_sync(
                job_id,
                status=JobStatus.ANALYZING,
                progress=progress,
                status_message=message,
            )
        
        update_job_sync(
            job_id,
            status=JobStatus.ANALYZING,
            progress=56,
            status_message="Menganalisis momen viral dengan Gemini AI..."
        )
        
        ai_result = ai_analyzer.detect_viral_moments(
            transcript=formatted_transcript,
            video_duration=video_duration,
            max_clips=max_clips,
            min_duration=min_duration,
            max_duration=max_duration,
            progress_callback=ai_progress,
        )
        
        clips_to_render = ai_result.get("clips", [])
        
        update_job_sync(
            job_id,
            progress=70,
            status_message=f"AI menemukan {len(clips_to_render)} momen viral! Mulai rendering..."
        )
        
        if is_cancelled():
            raise RuntimeError(f"Proses dibatalkan oleh pengguna untuk job {job_id}")

        # ── STEP 6: Render video clips ───────────────────────
        def render_progress(percent, message):
            progress = int(70 + (percent * 0.28))  # 70% → 98%
            update_job_sync(
                job_id,
                status=JobStatus.RENDERING,
                progress=progress,
                status_message=message,
            )
        
        update_job_sync(
            job_id,
            status=JobStatus.RENDERING,
            progress=71,
            status_message=f"Rendering {len(clips_to_render)} klip video..."
        )
        
        rendered_clips = processor.process_all_clips(
            video_path=video_path,
            job_id=job_id,
            clips_data=clips_to_render,
            transcription_words=transcription.get("words", []),
            progress_callback=render_progress,
        )
        
        # ── STEP 7: Save results to database ─────────────────
        successful_clips = [c for c in rendered_clips if c.get("status") == "success"]
        failed_clips     = [c for c in rendered_clips if c.get("status") == "failed"]
        
        save_clips_sync(job_id, rendered_clips)
        
        update_job_sync(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            status_message=f"✅ Selesai! {len(successful_clips)} klip viral berhasil dibuat.",
            completed_at=datetime.now(timezone.utc),
        )
        
        logger.info(f"🎉 Pipeline completed for job {job_id}!")
        return {
            "job_id": job_id,
            "status": "completed",
            "clips_created": len(successful_clips),
            "clips_failed": len(failed_clips),
        }
    
    except Exception as exc:
        error_message = str(exc)
        
        if "dibatalkan" in error_message.lower() or is_cancelled():
            logger.warning(f"🛑 Pipeline dihentikan untuk job {job_id}: {error_message}")
            update_job_sync(
                job_id,
                status=JobStatus.CANCELLED if hasattr(JobStatus, 'CANCELLED') else "CANCELLED",
                progress=0,
                status_message="Proses berhasil dibatalkan.",
                error_message="Dibatalkan oleh pengguna.",
            )
            return {"job_id": job_id, "status": "cancelled"}
        
        logger.error(f"❌ Pipeline failed for job {job_id}: {error_message}")
        update_job_sync(
            job_id,
            status=JobStatus.FAILED,
            progress=0,
            status_message="Processing gagal. Lihat detail error.",
            error_message=error_message[:2000],
        )
        raise self.retry(exc=exc)
    
    finally:
        # Cleanup audio mentah
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.debug(f"🧹 Cleaned up temp audio: {audio_path}")
            except Exception:
                pass
                
        # Cleanup video mentah (selalu hapus video sumber setelah klip terpotong agar hemat penyimpanan disk)
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                logger.debug(f"🧹 Cleaned up temp video: {video_path}")
            except Exception:
                pass