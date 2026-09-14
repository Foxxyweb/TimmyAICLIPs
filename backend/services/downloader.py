"""
AI Video Clipper — Video Downloader Service
==============================================
Menggunakan yt-dlp untuk download video YouTube.
"""

import subprocess
import json
import os
import re
from pathlib import Path
# pyrefly: ignore [missing-import]
from loguru import logger

from config import settings


class VideoDownloader:
    """
    Service untuk download video YouTube menggunakan yt-dlp.
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def get_video_info(self, url: str) -> dict:
        """
        Ambil metadata video tanpa download.
        Returns: dict dengan title, duration, thumbnail, dll.
        """
        logger.info(f"🔍 Fetching video info: {url}")
        
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            "--skip-download",
            "--no-check-certificates",
            url,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"yt-dlp info error: {result.stderr}")
            raise RuntimeError(f"Gagal ambil info video: {result.stderr}")
        
        info = json.loads(result.stdout)
        
        return {
            "title": info.get("title", "Unknown Title"),
            "duration": int(info.get("duration", 0)),
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", ""),
            "view_count": info.get("view_count", 0),
            "description": info.get("description", "")[:500],  # truncate
        }
    
    def download_video(
        self, 
        url: str, 
        job_id: str, 
        progress_callback=None,
        is_cancelled_callback=None
    ) -> str:
        """
        Download video dari YouTube dengan batasan resolusi maksimal 720p 
        dan dukungan pembatalan (Cancellation Support).
        """
        logger.info(f"⬇️  Downloading video for job {job_id}: {url}")
        
        output_template = str(self.upload_dir / f"{job_id}.%(ext)s")
        
        # Format dibuat fleksibel (menerima webm/m4a/any) lalu digabung ke mp4 via FFmpeg
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "--merge-output-format", "mp4",
            "--output", output_template,
            "--newline",
            "--no-warnings",
            "--no-check-certificates",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            url,
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        downloaded_path = None
        error_logs = []
        
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                error_logs.append(line)
                if len(error_logs) > 20:
                    error_logs.pop(0)  # Simpan 20 baris terakhir output untuk keperluan debugging
                
                # ── CHEK STATUS CANCEL ──────────────────────────────────────────────
                if is_cancelled_callback and is_cancelled_callback():
                    logger.warning(f"🛑 Job {job_id} dibatalkan oleh user! Membunuh proses yt-dlp...")
                    process.kill()
                    process.wait()
                    self._cleanup_temp_files(job_id)
                    raise RuntimeError(f"Download dibatalkan oleh pengguna untuk job {job_id}")
                # ───────────────────────────────────────────────────────────────────
                
                logger.debug(f"yt-dlp: {line}")
                
                # Parse progress dari output yt-dlp
                if "[download]" in line:
                    percent_match = re.search(r"(\d+\.\d+)%", line)
                    if percent_match and progress_callback:
                        percent = float(percent_match.group(1))
                        progress_callback(percent, f"Mengunduh video... {percent:.0f}%")
                
                # Deteksi path file yang selesai didownload
                if "[Merger]" in line or "has already been downloaded" in line or "Destination:" in line:
                    path_match = re.search(r'Destination:\s+(.+\.mp4)', line)
                    if path_match:
                        downloaded_path = path_match.group(1).strip()
            
            process.wait()
            
            if process.returncode != 0:
                full_err = "\n".join(error_logs)
                logger.error(f"yt-dlp failed output:\n{full_err}")
                raise RuntimeError(f"yt-dlp gagal dengan exit code {process.returncode}: {error_logs[-1] if error_logs else ''}")
                
        except Exception as e:
            if process.poll() is None:
                process.kill()
                process.wait()
            self._cleanup_temp_files(job_id)
            raise e
        
        # Cari file yang baru saja didownload
        if not downloaded_path or not os.path.exists(downloaded_path):
            all_files = list(self.upload_dir.glob(f"{job_id}.*"))
            video_files = [f for f in all_files if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".mov"]]
            if video_files:
                downloaded_path = str(video_files[0])
        
        if not downloaded_path or not os.path.exists(downloaded_path):
            raise RuntimeError(f"File video tidak ditemukan setelah download untuk job {job_id}")
        
        file_size_mb = os.path.getsize(downloaded_path) / (1024 * 1024)
        logger.info(f"✅ Video downloaded: {downloaded_path} ({file_size_mb:.1f} MB)")
        
        return downloaded_path

    def _cleanup_temp_files(self, job_id: str):
        """Pembersih file parsial (.part, .ytdl, mp4 mentah) saat job dibatalkan."""
        for temp_file in self.upload_dir.glob(f"{job_id}.*"):
            try:
                os.remove(temp_file)
                logger.info(f"🧹 File sampah dibersihkan: {temp_file.name}")
            except Exception as e:
                logger.error(f"Gagal menghapus file sampah {temp_file}: {e}")

    def extract_audio(self, video_path: str, job_id: str) -> str:
        """
        Extract audio dari video ke format WAV untuk Whisper.
        """
        audio_path = str(self.upload_dir / f"{job_id}_audio.wav")
        
        logger.info(f"🎵 Extracting audio: {video_path} → {audio_path}")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",                  # no video
            "-acodec", "pcm_s16le",   # WAV format
            "-ar", "16000",           # 16kHz sample rate
            "-ac", "1",               # mono
            "-y",                     # overwrite
            audio_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction gagal: {result.stderr}")
        
        logger.info(f"✅ Audio extracted: {audio_path}")
        return audio_path


# Singleton instance
downloader = VideoDownloader()