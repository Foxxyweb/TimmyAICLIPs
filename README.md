<div align="center">

# TimmyAICLIPs 🎬✂️
### Platform Pembuat Video Pendek Otomatis Berbasis AI

Platform pemrosesan video asinkron untuk mengubah video panjang YouTube menjadi klip vertikal format 9:16 siap posting menggunakan Speech-to-Text, Large Language Model, dan rendering FFmpeg terprogram.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Upstash_Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://upstash.com/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## 📌 Ringkasan Proyek

**TimmyAICLIPs** adalah solusi otomatis untuk memotong video panjang menjadi konten pendek (Shorts/Reels/TikTok). Seluruh sistem, mulai dari arsitektur backend, antarmuka frontend, hingga pipeline pemrosesan media berbasis AI, saya rancang dan kembangkan secara mandiri.

Fokus utama pengembangan aplikasi ini berpusat pada **pemrosesan tugas asinkron yang andal**, **antrean tugas yang efisien tanpa membebani server web**, dan **antarmuka reaktif yang memperbarui status proses secara real-time**.

---

## ⚡ Fitur Utama & Implementasi Teknis

* **Distributed Task Offloading:** Beban komputasi berat dialihkan ke **Celery Worker** mandiri dengan antrean pesan **Upstash Cloud Redis** agar server API FastAPI tidak mengalami timeout.
* **Sinkronisasi Real-Time:** Memanfaatkan **WebSockets** pada FastAPI untuk mengirimkan status pemrosesan (`DOWNLOADING` → `TRANSCRIBING` → `ANALYZING` → `RENDERING` → `COMPLETED`) secara langsung ke halaman frontend.
* **Transkripsi Berbasis Timestamp Kata:** Menggunakan model `faster-whisper` untuk mengekstrak teks percakapan beserta posisi waktu presisi tingkat milidetik demi kebutuhan animasi subtitle otomatis.
* **Deteksi Momen Viral via LLM:** Mengintegrasikan **Google Gemini 2.5 Flash** untuk menganalisis isi transkrip, mendeteksi hook cerita yang kuat, menentukan klimaks, serta memberikan penilaian kelayakan klip secara semantik.
* **Transformasi Format 9:16 via FFmpeg:** Melakukan pemotongan durasi otomatis, pemusatan rasio gambar (center crop 9:16), penyesuaian resolusi ke 1080x1920, serta penempelan subtitle animasi ke dalam video.

---

## 🏗️ Alur Sistem & Arsitektur

```mermaid
sequenceDiagram
    autonumber
    actor Pengguna as Klien / Browser
    participant API as FastAPI Gateway
    participant DB as SQLite (Async SQLAlchemy)
    participant Broker as Upstash Redis (Broker Antrean)
    participant Worker as Celery Worker
    participant AI as Gemini & Whisper AI
    participant Media as yt-dlp & FFmpeg

    Pengguna->>API: POST /api/process-video (Link YouTube)
    API->>DB: Simpan Data Job (Status: PENDING)
    API->>Broker: Kirim Task process_video_task(job_id)
    API-->>Pengguna: Respon 202 Accepted { job_id }
    
    Broker->>Worker: Ambil Task dari Antrean
    Worker->>Media: Unduh Video & Ekstrak Audio (16kHz WAV)
    Worker->>AI: Transkripsi Teks (faster-whisper)
    Worker->>AI: Analisis Momen Menarik (Gemini Flash)
    Worker->>Media: Render Klip 9:16 & Tempel Subtitle
    Worker->>DB: Simpan Data Hasil Klip & Status COMPLETED
    Worker-->>API: Kirim Sinyal Update Progress
    API-->>Pengguna: Push Pembaruan Status via WebSocket