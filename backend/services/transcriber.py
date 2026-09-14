"""
AI Video Clipper — Transcription Service
==========================================
Menggunakan faster-whisper untuk transkripsi audio dengan word-level timestamps.
"""

# pyrefly: ignore [missing-import]
from faster_whisper import WhisperModel
from pathlib import Path
# pyrefly: ignore [missing-import]
from loguru import logger
from typing import Callable, Optional

from config import settings


class TranscriptionService:
    """
    Service transkripsi menggunakan faster-whisper.
    faster-whisper adalah implementasi yang jauh lebih cepat dari OpenAI Whisper.
    """
    
    def __init__(self):
        self._model: Optional[WhisperModel] = None
        self.model_size = settings.WHISPER_MODEL
    
    @property
    def model(self) -> WhisperModel:
        """Lazy load model — hanya load saat pertama kali digunakan."""
        if self._model is None:
            logger.info(f"🧠 Loading Whisper model: {self.model_size}...")
            logger.info("   (Model akan didownload otomatis jika belum ada)")
            
            self._model = WhisperModel(
                self.model_size,
                device="cpu",        # Ganti ke "cuda" jika ada GPU NVIDIA
                compute_type="int8", # int8 lebih cepat di CPU
            )
            logger.info(f"✅ Whisper model '{self.model_size}' loaded!")
        return self._model
    
    def transcribe(
        self, 
        audio_path: str, 
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Transkripsi file audio ke teks dengan word-level timestamps.
        
        Args:
            audio_path: Path ke file audio (.wav / .mp3 / .m4a)
            progress_callback: Callable(percent: float, message: str)
        
        Returns:
            dict dengan keys:
                - full_text: str — teks lengkap
                - segments: list[dict] — segment dengan timestamps
                - words: list[dict] — word-level timestamps
                - language: str — bahasa yang terdeteksi
                - duration: float — durasi total audio
        """
        logger.info(f"📝 Starting transcription: {audio_path}")
        
        if progress_callback:
            progress_callback(5, "Memuat model Whisper AI...")
        
        # Jalankan transkripsi dengan word timestamps
        segments_gen, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,          # PENTING: word-level timestamps
            vad_filter=True,               # Voice Activity Detection — lebih akurat
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200,
            },
            beam_size=5,
            best_of=5,
        )
        
        logger.info(f"🌍 Detected language: {info.language} (confidence: {info.language_probability:.1%})")
        logger.info(f"⏱️  Audio duration: {info.duration:.1f}s")
        
        if progress_callback:
            progress_callback(20, f"Transkripsi audio {info.duration:.0f}s... Mohon tunggu")
        
        # Kumpulkan semua segments
        all_segments = []
        all_words = []
        full_text_parts = []
        
        for segment in segments_gen:
            seg_dict = {
                "id": segment.id,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": [],
            }
            
            # Kumpulkan word-level timestamps
            if segment.words:
                for word in segment.words:
                    word_dict = {
                        "word": word.word.strip(),
                        "start": round(word.start, 3),
                        "end": round(word.end, 3),
                        "probability": round(word.probability, 3),
                    }
                    seg_dict["words"].append(word_dict)
                    all_words.append(word_dict)
            
            all_segments.append(seg_dict)
            full_text_parts.append(segment.text.strip())
        
        full_text = " ".join(full_text_parts)
        
        logger.info(f"✅ Transcription complete: {len(all_segments)} segments, {len(all_words)} words")
        logger.info(f"   Preview: {full_text[:200]}...")
        
        if progress_callback:
            progress_callback(100, "Transkripsi selesai!")
        
        return {
            "full_text": full_text,
            "segments": all_segments,
            "words": all_words,
            "language": info.language,
            "duration": info.duration,
            "num_segments": len(all_segments),
        }
    
    def format_for_ai(self, transcription: dict) -> str:
        """
        Format transkripsi ke format yang mudah dibaca oleh AI (Gemini).
        Setiap baris: [HH:MM:SS] teks segment
        """
        lines = []
        for seg in transcription["segments"]:
            start = self._seconds_to_timestamp(seg["start"])
            end   = self._seconds_to_timestamp(seg["end"])
            lines.append(f"[{start} → {end}] {seg['text']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _seconds_to_timestamp(seconds: float) -> str:
        """Konversi detik ke format HH:MM:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:05.2f}"


# Singleton instance
transcriber = TranscriptionService()
