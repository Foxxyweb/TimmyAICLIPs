"""
AI Video Clipper — Video Processor Service
============================================
Menggunakan FFmpeg untuk:
1. Memotong video berdasarkan timestamp
2. Center crop ke rasio 9:16 (vertikal) dengan Color Correction
3. Menambahkan Title Hook otomatis di 3 detik pertama
4. Menambahkan subtitle estetik berbasis SRT (Windows path & Fontconfig safe)
5. Auto-cleanup video mentah & klip lama agar harddisk tidak penuh
"""

import subprocess
import os
import json
import time
import tempfile
from pathlib import Path
from loguru import logger
from typing import Callable, Optional, List

from config import settings

# Set environment variable fallback untuk Fontconfig di Windows
os.environ["FONTCONFIG_PATH"] = "C:/Windows/Fonts"


class VideoProcessor:
    """
    Service untuk memproses video dengan FFmpeg dan mengelola pembersihan storage.
    """
    
    def __init__(self):
        self.clips_dir = Path(settings.CLIPS_DIR)
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Cek apakah FFmpeg tersedia di PATH."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True
            )
            version_line = result.stdout.split("\n")[0]
            logger.info(f"✅ FFmpeg tersedia: {version_line}")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg tidak ditemukan! "
                "Install dari: https://ffmpeg.org/download.html"
            )

    def cleanup_raw_video(self, video_path: str) -> None:
        """Hapus file video mentah YouTube setelah selesai di-crop."""
        try:
            abs_path = Path(video_path).resolve()
            if abs_path.exists():
                os.remove(abs_path)
                logger.info(f"🗑️ Auto-clean: Video mentah berhasil dihapus -> {abs_path.name}")
        except Exception as e:
            logger.warning(f"⚠️ Gagal menghapus video mentah {video_path}: {e}")

    def cleanup_old_clips(self, max_age_hours: int = 2) -> None:
        """Hapus klip video di folder output yang umurnya sudah melebihi max_age_hours."""
        now = time.time()
        cutoff = now - (max_age_hours * 3600)

        for file in self.clips_dir.glob("*.mp4"):
            if file.is_file():
                if file.stat().st_mtime < cutoff:
                    try:
                        file.unlink()
                        logger.info(f"🗑️ Auto-clean: Klip lama dihapus -> {file.name}")
                    except Exception as e:
                        logger.error(f"Gagal menghapus klip lama {file.name}: {e}")

    def get_video_dimensions(self, video_path: str) -> tuple[int, int]:
        """Dapatkan dimensi video (width, height) menggunakan FFprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(Path(video_path).resolve()),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if not result.stdout.strip():
            raise RuntimeError(f"FFprobe gagal membaca metadata video: {video_path}")
            
        data = json.loads(result.stdout)
        
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return int(stream["width"]), int(stream["height"])
        
        raise RuntimeError(f"Tidak bisa mendapatkan dimensi video: {video_path}")

    def _format_srt_time(self, seconds: float) -> str:
        """Konversi detik ke format waktu SRT (HH:MM:SS,ms)."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis >= 1000:
            secs += 1
            millis = 0
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def _generate_srt_file(self, words: List[dict], start_time: float, end_time: float) -> Optional[str]:
        """Membuat file temporary .srt dari word-level timestamps."""
        clip_words = [
            w for w in words
            if w.get("end", 0) >= start_time and w.get("start", 0) <= end_time
        ]
        
        if not clip_words:
            return None

        srt_content = []
        srt_index = 1

        for w in clip_words:
            w_start = max(0.0, w["start"] - start_time)
            w_end = max(w_start + 0.1, w["end"] - start_time)
            text = w.get("word", "").strip()
            
            if not text:
                continue

            srt_content.append(f"{srt_index}")
            srt_content.append(f"{self._format_srt_time(w_start)} --> {self._format_srt_time(w_end)}")
            srt_content.append(f"{text}\n")
            srt_index += 1

        if not srt_content:
            return None

        temp_srt = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".srt", delete=False)
        temp_srt.write("\n".join(srt_content))
        temp_srt.close()
        return temp_srt.name

    def create_clip(
        self,
        video_path: str,
        job_id: str,
        clip_index: int,
        start_time: float,
        end_time: float,
        title: str,
        words: Optional[List[dict]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """
        Buat satu klip video 9:16 vertikal dengan Title Hook & Subtitle Estetik.
        """
        duration = end_time - start_time
        if duration <= 0:
            raise ValueError(f"Durasi klip tidak valid: start={start_time}, end={end_time}")

        filename = f"clip_{job_id[:8]}_{clip_index:03d}.mp4"
        output_path = str((self.clips_dir / filename).resolve())
        abs_video_path = str(Path(video_path).resolve())
        
        logger.info(f"🎬 Creating clip {clip_index}: {start_time:.1f}s → {end_time:.1f}s ({duration:.1f}s)")
        
        if progress_callback:
            progress_callback(10, f"Memproses klip {clip_index}...")
        
        orig_w, orig_h = self.get_video_dimensions(abs_video_path)
        
        # ── Crop & Scale ke 9:16 (1080x1920) ───────────────────
        target_ratio = 9 / 16
        if orig_w / orig_h > target_ratio:
            crop_h = orig_h
            crop_w = int(orig_h * target_ratio)
        else:
            crop_w = orig_w
            crop_h = int(orig_w / target_ratio)
        
        crop_w = (crop_w // 2) * 2
        crop_h = (crop_h // 2) * 2
        crop_x = ((orig_w - crop_w) // 2 // 2) * 2
        crop_y = ((orig_h - crop_h) // 2 // 2) * 2
        output_w, output_h = 1080, 1920

        # ── Generate Subtitle File ─────────────────────────────
        srt_file_path = None
        if words:
            srt_file_path = self._generate_srt_file(words, start_time, end_time)

        # ── Filter Chain FFmpeg ────────────────────────────────
        filters = [
            f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}",
            f"scale={output_w}:{output_h}:flags=lanczos",
            "eq=contrast=1.08:saturation=1.15:brightness=0.01"
        ]

        # Path Font Windows eksplisit (Aman dari Fontconfig Error)
        font_file_path = "C\\:/Windows/Fonts/arial.ttf"

        # 1. Intro Hook Filter (Direct Fontfile & Escape-Safe)
        if title:
            safe_title = (
                title.replace("'", "")
                .replace('"', "")
                .replace(":", " ")
                .replace("\\", "/")
                .replace("%", "")
            )
            hook_filter = (
                f"drawtext=fontfile='{font_file_path}':"
                f"text='{safe_title}':"
                f"fontsize=42:"
                f"fontcolor=yellow:"
                f"box=1:boxcolor=black@0.7:boxborderw=15:"
                f"x=(w-text_w)/2:y=300:"
                f"enable='between(t,0,3)'"
            )
            filters.append(hook_filter)

        # 2. Subtitle Filter (Windows Escape Fix & Explicit Font)
        if srt_file_path:
            raw_path = str(Path(srt_file_path).resolve()).replace("\\", "/")
            if ":" in raw_path:
                drive, rest = raw_path.split(":", 1)
                safe_srt_path = f"{drive}\\:{rest}"
            else:
                safe_srt_path = raw_path
                
            style = (
                "Fontname=Arial,"
                "FontSize=22,"
                "PrimaryColour=&H0000FFFF,"
                "OutlineColour=&H00000000,"
                "BorderStyle=1,"
                "Outline=4,"
                "Shadow=2,"
                "Alignment=2,"
                "MarginV=120"
            )
            filters.append(f"subtitles=filename='{safe_srt_path}':force_style='{style}'")

        filter_chain = ",".join(filters)
        
        # FFmpeg Command
        cmd = [
            "ffmpeg",
            "-ss", f"{start_time:.3f}",
            "-to", f"{end_time:.3f}",
            "-i", abs_video_path,
            "-vf", filter_chain,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        if progress_callback:
            progress_callback(30, f"Rendering klip {clip_index} dengan FFmpeg...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=300,
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg Error Output: {result.stderr}")
                raise RuntimeError(f"FFmpeg gagal untuk klip {clip_index}: {result.stderr[-300:]}")
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file tidak ditemukan: {output_path}")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Clip {clip_index} created: {filename} ({file_size / 1024 / 1024:.1f} MB)")
            
            if progress_callback:
                progress_callback(100, f"Klip {clip_index} selesai!")
            
            return filename

        finally:
            if srt_file_path and os.path.exists(srt_file_path):
                try:
                    os.remove(srt_file_path)
                except Exception:
                    pass

    def process_all_clips(
        self,
        video_path: str,
        job_id: str,
        clips_data: List[dict],
        transcription_words: Optional[List[dict]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> List[dict]:
        results = []
        total_clips = len(clips_data)
        
        # JALANKAN AUTO-CLEANUP KLIP LAMA DI AWAL PROSES (Lebih dari 2 jam)
        self.cleanup_old_clips(max_age_hours=2)
        
        for i, clip in enumerate(clips_data):
            clip_num = i + 1
            base_percent = (i / total_clips) * 100
            
            def clip_progress(pct, msg):
                if progress_callback:
                    overall = base_percent + (pct / total_clips)
                    progress_callback(overall, msg)
            
            try:
                filename = self.create_clip(
                    video_path=video_path,
                    job_id=job_id,
                    clip_index=clip_num,
                    start_time=float(clip["start_time"]),
                    end_time=float(clip["end_time"]),
                    title=clip.get("title", f"Clip {clip_num}"),
                    words=transcription_words,
                    progress_callback=clip_progress,
                )
                
                file_path = self.clips_dir / filename
                
                results.append({
                    **clip,
                    "filename": filename,
                    "file_size": os.path.getsize(str(file_path)),
                    "status": "success",
                })
                
                logger.info(f"✅ Clip {clip_num}/{total_clips} diproses sukses!")
                
            except Exception as e:
                logger.error(f"❌ Error processing clip {clip_num}: {e}")
                results.append({
                    **clip,
                    "filename": None,
                    "status": "failed",
                    "error": str(e),
                })
        
        # SELALU HAPUS VIDEO MENTAH YOUTUBE DI AKHIR PROSES
        self.cleanup_raw_video(video_path)
        
        return results


# Singleton instance
video_processor = VideoProcessor()