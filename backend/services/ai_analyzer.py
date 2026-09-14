"""
AI Video Clipper — AI Analyzer Service (Google Gemini)
========================================================
Menggunakan Gemini 2.5 Flash untuk mendeteksi momen viral dari transkripsi.
"""

import google.generativeai as genai
import json
import re
from loguru import logger
from typing import Callable, Optional

from config import settings


# Konfigurasi Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)


# ── System Prompt ─────────────────────────────────────────────
VIRAL_DETECTION_PROMPT = """Kamu adalah AI expert dalam analisis konten video viral untuk platform short-form video (TikTok, Instagram Reels, YouTube Shorts).

Tugasmu adalah menganalisis transkripsi video dan menemukan {max_clips} momen paling berpotensi viral.

KRITERIA MOMEN VIRAL (pertimbangkan semua ini):
1. 🎯 Hook kuat di awal (pertanyaan menarik, statement mengejutkan, atau masalah relatable)
2. 💡 Insight berharga atau informasi mengejutkan yang membuat orang ingin membagikan
3. 😂 Momen lucu, awkward, atau emosional yang tinggi
4. ⚡ Energi dan delivery yang tinggi dari pembicara
5. 📖 Cerita atau contoh konkret yang mudah dipahami
6. 🔥 Kontroversi atau pendapat kuat yang memicu diskusi
7. ✅ Kesimpulan yang kuat dan actionable

ATURAN PEMILIHAN:
- Durasi setiap klip: {min_duration} - {max_duration} detik
- Pilih momen yang memiliki AWAL dan AKHIR yang natural (jangan potong di tengah kalimat)
- Prioritaskan momen dengan konteks yang lengkap dan mandiri (bisa dimengerti tanpa konteks lain)
- Hindari memilih momen yang terlalu mirip satu sama lain

TRANSKRIPSI VIDEO:
---
{transcript}
---

RESPONS DALAM FORMAT JSON BERIKUT (HANYA JSON, TIDAK ADA TEKS LAIN):
{{
  "video_summary": "Ringkasan singkat konten video dalam 2 kalimat",
  "main_topic": "Topik utama video",
  "clips": [
    {{
      "clip_number": 1,
      "title": "Judul klip yang menarik dan clickbait-friendly (max 60 karakter)",
      "description": "Mengapa momen ini viral - jelaskan dalam 1-2 kalimat",
      "start_time": 45.5,
      "end_time": 89.2,
      "viral_score": 87,
      "hook_type": "surprising_fact|emotional|funny|valuable_insight|controversial|story",
      "suggested_caption": "Caption untuk social media dengan emoji dan hashtag"
    }}
  ]
}}

PENTING:
- start_time dan end_time HARUS berupa angka desimal dalam satuan DETIK
- viral_score adalah angka 0-100
- Pilih TEPAT {max_clips} klip terbaik
- Pastikan tidak ada overlap waktu antar klip
"""


class AIAnalyzer:
    """
    Service untuk menganalisis transkripsi dan menemukan momen viral
    menggunakan Google Gemini 2.5 Flash API.
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",  # Force JSON output
            }
        )
    
    def detect_viral_moments(
        self,
        transcript: str,
        video_duration: float,
        max_clips: int = 5,
        min_duration: int = 30,
        max_duration: int = 90,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Kirim transkripsi ke Gemini dan dapatkan timestamp momen viral.
        
        Args:
            transcript: Teks transkripsi terformat (dari TranscriptionService.format_for_ai)
            video_duration: Durasi total video dalam detik
            max_clips: Jumlah maksimum klip yang ingin dihasilkan
            min_duration: Durasi minimum klip dalam detik
            max_duration: Durasi maksimum klip dalam detik
            progress_callback: Callable(percent: float, message: str)
        
        Returns:
            dict hasil analisis dengan list clips
        """
        logger.info(f"🤖 Sending transcript to Gemini {settings.GEMINI_MODEL}...")
        logger.info(f"   Transcript length: {len(transcript)} chars")
        
        if progress_callback:
            progress_callback(10, "Mengirim transkripsi ke Gemini AI...")
        
        # Build prompt dengan variabel
        prompt = VIRAL_DETECTION_PROMPT.format(
            transcript=transcript,
            max_clips=max_clips,
            min_duration=min_duration,
            max_duration=max_duration,
        )
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text
            
            logger.info(f"✅ Gemini response received ({len(raw_text)} chars)")
            logger.debug(f"Raw response: {raw_text[:500]}...")
            
            if progress_callback:
                progress_callback(80, "Memproses hasil analisis AI...")
            
            # Parse JSON response
            result = self._parse_json_response(raw_text)
            
            # Validasi dan sanitasi timestamps
            result = self._validate_clips(result, video_duration, min_duration, max_duration)
            
            logger.info(f"🎯 Found {len(result.get('clips', []))} viral moments!")
            for clip in result.get("clips", []):
                logger.info(
                    f"   Clip {clip['clip_number']}: "
                    f"{clip['start_time']:.1f}s - {clip['end_time']:.1f}s "
                    f"(score: {clip['viral_score']})"
                )
            
            if progress_callback:
                progress_callback(100, "Analisis AI selesai!")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise RuntimeError(f"Gagal analisis AI: {str(e)}")
    
    def _parse_json_response(self, raw_text: str) -> dict:
        """Parse JSON dari response Gemini. Handle edge cases."""
        # Coba parse langsung
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass
        
        # Coba ekstrak JSON dari markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Coba ekstrak objek JSON dari teks
        json_match = re.search(r"(\{[\s\S]*\})", raw_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Gagal parse JSON dari response Gemini:\n{raw_text[:500]}")
    
    def _validate_clips(
        self, 
        result: dict, 
        video_duration: float,
        min_duration: int,
        max_duration: int,
    ) -> dict:
        """Validasi dan sanitasi timestamp clips."""
        clips = result.get("clips", [])
        validated = []
        
        for clip in clips:
            start = float(clip.get("start_time", 0))
            end   = float(clip.get("end_time", 0))
            
            # Sanitasi bounds
            start = max(0, min(start, video_duration))
            end   = max(0, min(end, video_duration))
            
            if start >= end:
                logger.warning(f"Invalid clip timestamps: {start}s → {end}s. Skipping.")
                continue
            
            duration = end - start
            
            # Clamp durasi ke range yang valid
            if duration < min_duration:
                end = min(start + min_duration, video_duration)
            elif duration > max_duration:
                end = start + max_duration
            
            clip["start_time"] = round(start, 2)
            clip["end_time"]   = round(end, 2)
            clip["duration"]   = round(end - start, 2)
            clip["viral_score"] = max(0, min(100, int(clip.get("viral_score", 70))))
            
            validated.append(clip)
        
        # Sort by start_time
        validated.sort(key=lambda x: x["start_time"])
        
        result["clips"] = validated
        return result


# Singleton instance
ai_analyzer = AIAnalyzer()
