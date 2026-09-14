# AI Video Clipper 🎬✂️
> **Mirip Opus Clip / Vizard.ai — 100% Open Source & Gratis**

Platform web full-stack untuk mengubah video YouTube panjang menjadi klip viral format vertikal 9:16 secara otomatis menggunakan AI.

---

## 🚀 Tech Stack

| Layer | Teknologi |
|-------|-----------|
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **Backend API** | FastAPI (Python) |
| **Task Queue** | Celery + Redis |
| **Transcription** | faster-whisper (Whisper AI) |
| **AI Analysis** | Google Gemini 2.5 Flash API |
| **Video Processing** | FFmpeg + yt-dlp |
| **Database** | SQLite (via SQLAlchemy async) |

---

## 📁 Folder Structure

```
projek AI CLIP VIDEO/
├── backend/
│   ├── api/
│   │   └── routes.py          # REST + WebSocket endpoints
│   ├── services/
│   │   ├── downloader.py      # yt-dlp wrapper
│   │   ├── transcriber.py     # faster-whisper wrapper
│   │   ├── ai_analyzer.py     # Gemini API integration
│   │   └── video_processor.py # FFmpeg processing
│   ├── workers/
│   │   ├── celery_app.py      # Celery configuration
│   │   └── tasks.py           # Pipeline background task
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Settings management
│   ├── database.py            # SQLite async setup
│   ├── models.py              # SQLAlchemy models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx       # URL input + hero page
│   │   │   ├── Results.jsx    # Live progress + clips gallery
│   │   │   └── History.jsx    # All jobs history
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProgressTracker.jsx  # Animated pipeline steps
│   │   │   ├── ClipCard.jsx         # Video clip preview + download
│   │   │   └── LoadingSpinner.jsx
│   │   └── hooks/
│   │       └── useJobStatus.js  # WebSocket hook
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── uploads/                   # Downloaded raw videos
└── clips/                     # Output video clips
```

---

## ⚙️ Prasyarat

Sebelum memulai, pastikan sudah terinstal:

1. **Python 3.10+** — https://python.org
2. **Node.js 18+** — https://nodejs.org
3. **FFmpeg** — https://ffmpeg.org/download.html
4. **Redis** — https://redis.io/download (untuk Celery)
5. **Google Gemini API Key** — https://aistudio.google.com/app/apikey (GRATIS)

### Install FFmpeg (Windows)
```powershell
# Via winget
winget install Gyan.FFmpeg

# Atau via Chocolatey
choco install ffmpeg
```

### Install Redis (Windows)
```powershell
# Via WSL (direkomendasikan)
wsl --install
# Di dalam WSL:
sudo apt install redis-server
sudo service redis-server start

# Atau download Redis for Windows dari:
# https://github.com/microsoftarchive/redis/releases
```

---

## 🛠️ Setup & Installation

### Step 1 — Clone & Setup Backend

```powershell
# Masuk ke folder backend
cd backend

# Buat virtual environment
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Salin .env dan isi API key
copy .env.example .env
```

Edit file `.env`:
```env
GEMINI_API_KEY=AIzaSy...    # ← ISI API KEY GEMINI ANDA DI SINI
REDIS_URL=redis://localhost:6379/0
WHISPER_MODEL=base           # tiny/base/small/medium
```

### Step 2 — Setup Frontend

```powershell
# Masuk ke folder frontend
cd frontend

# Install dependencies
npm install
```

---

## ▶️ Cara Menjalankan

Anda butuh **3 terminal** yang berjalan bersamaan:

### Terminal 1 — FastAPI Backend Server
```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend akan berjalan di: `http://localhost:8000`  
Swagger docs di: `http://localhost:8000/docs`

### Terminal 2 — Celery Worker
```powershell
cd backend
.\venv\Scripts\activate
celery -A workers.celery_app worker --loglevel=info --concurrency=1 -Q video_processing
```

### Terminal 3 — React Frontend
```powershell
cd frontend
npm run dev
```
Frontend akan berjalan di: `http://localhost:5173`

---

## 🔄 Data Flow (Pipeline)

```
[User input YouTube URL]
         │
         ▼
[POST /api/process-video]
         │ Buat Job record di SQLite
         │ Kirim task ke Celery queue
         ▼
[Celery Worker mulai proses]
         │
         ├─ Step 1: yt-dlp download video + metadata
         │   Progress: 0% → 25%
         │
         ├─ Step 2: FFmpeg extract audio (16kHz WAV)
         │   Progress: 25% → 30%
         │
         ├─ Step 3: faster-whisper transcribe audio
         │   Output: word-level timestamps
         │   Progress: 30% → 55%
         │
         ├─ Step 4: Gemini 2.5 Flash analyze transcript
         │   Output: JSON dengan viral timestamps
         │   Progress: 55% → 70%
         │
         └─ Step 5: FFmpeg render clips
             - Trim by timestamp
             - Center crop → 9:16 ratio
             - Scale → 1080x1920
             - Add animated word-by-word subtitles
             Progress: 70% → 100%
         │
         ▼
[Frontend WebSocket menerima real-time updates]
         │
         ▼
[Results page: preview video + download MP4]
```

---

## 🎯 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/process-video` | Submit URL YouTube untuk diproses |
| `GET` | `/api/jobs/{job_id}` | Ambil status dan hasil job |
| `GET` | `/api/jobs` | Daftar semua jobs |
| `DELETE` | `/api/jobs/{job_id}` | Hapus job |
| `WS` | `/api/ws/{job_id}` | WebSocket realtime updates |
| `GET` | `/clips/{filename}` | Stream/download video klip |
| `GET` | `/health` | Health check |

---

## 🎛️ Konfigurasi Advanced

Edit `.env` untuk mengatur:

```env
# Whisper model size (tradeoff: speed vs accuracy)
WHISPER_MODEL=base     # Cepat, OK untuk kebanyakan kasus
WHISPER_MODEL=small    # Lebih akurat, 2x lebih lambat
WHISPER_MODEL=medium   # Sangat akurat, butuh RAM lebih besar

# Jumlah dan durasi klip
MAX_CLIPS=5            # Default jumlah klip per video
CLIP_MIN_DURATION=30   # Minimum 30 detik per klip
CLIP_MAX_DURATION=90   # Maksimum 90 detik per klip

# GPU (jika punya NVIDIA GPU)
# Edit backend/services/transcriber.py:
# device="cuda" dan compute_type="float16"
```

---

## 🐛 Troubleshooting

### Error: "Redis connection refused"
```powershell
# Pastikan Redis berjalan
# Windows: Buka Redis server
redis-server

# WSL:
sudo service redis-server start
```

### Error: "FFmpeg not found"
```powershell
# Cek apakah FFmpeg ada di PATH
ffmpeg -version

# Jika tidak, tambahkan ke PATH atau install ulang
```

### Error: "GEMINI_API_KEY not set"
```
Pastikan file .env sudah dibuat dari .env.example
dan GEMINI_API_KEY sudah diisi dengan benar.
```

### Whisper model download lambat
```
Model akan otomatis didownload saat pertama kali dipakai.
Ukuran: tiny(72MB), base(142MB), small(461MB), medium(1.5GB)
```

---

## 📦 Dependencies Lengkap

### Python Backend
- `fastapi` + `uvicorn` — Web framework
- `celery` + `redis` — Task queue
- `yt-dlp` — YouTube downloader
- `faster-whisper` — Whisper AI (CTranslate2 backend)
- `google-generativeai` — Gemini API SDK
- `sqlalchemy` + `aiosqlite` — Database ORM

### Node.js Frontend
- `react` + `react-router-dom` — SPA framework
- `tailwindcss` — Utility-first CSS
- `framer-motion` — Animasi smooth
- `axios` — HTTP client
- `lucide-react` — Icon library
- `react-hot-toast` — Notifikasi

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

**Dibuat dengan ❤️ oleh AI Principal Engineer**  
*Stack: FastAPI + React + Whisper + Gemini + FFmpeg*
