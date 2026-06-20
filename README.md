<div align="center">

<img src="https://img.shields.io/badge/status-alpha-FF4757?style=for-the-badge&logo=statuspal&logoColor=white" alt="Status Alpha">
<img src="https://img.shields.io/badge/python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/react-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
<img src="https://img.shields.io/badge/fastapi-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
<img src="https://img.shields.io/badge/stars-⭐_beri_bintang-yellow?style=for-the-badge" alt="Stars">

<br><br>

<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/TypeScript.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/React-Dark.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/TailwindCSS-Dark.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/PostgreSQL-Dark.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Redis-Dark.svg" width="48" height="48">
<img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Docker.svg" width="48" height="48">

</div>

<br>

<h1 align="center">
  ⚡ ATELIX ViralClip AI
</h1>

<p align="center">
  <strong>Engine AI Otonom untuk Mengubah Video Panjang YouTube<br>
  Menjadi Konten Vertikal Viral (TikTok • Reels • Shorts)</strong>
</p>

<br>

---

## 🤖 Tentang Proyek

**ATELIX ViralClip AI** adalah mesin pemrosesan media otonom berbasis kecerdasan buatan. Sistem ini menelan video YouTube berdurasi panjang, menganalisis struktur naratifnya menggunakan AI Director melalui protokol MCP (*Model Context Protocol*), mengidentifikasi momen paling berpotensi viral, lalu mengubahnya menjadi konten vertikal pendek berkualitas premium — **tanpa campur tangan manusia sedikit pun.**

> 🎬 Dari video 2 jam → 5 klip TikTok viral dalam hitungan menit. AI yang memutuskan, AI yang mengedit, AI yang mempublikasi.

### 🎯 Masalah yang Diselesaikan

<table>
<tr>
<td width="50%">

❌ **Tanpa ATELIX**  
• Editor manusia butuh 2-4 jam per klip  
• Pemotongan acak — momen viral terlewat  
• Subtitle manual membosankan & lambat  
• Cropping 9:16 sering salah fokus  
• Audio amatir — noise, volume nggak rata  
• Upload TikTok manual satu per satu  

</td>
<td width="50%">

✅ **Dengan ATELIX**  
• Full otomatis — nol intervensi manusia  
• AI Director analisis naratif & emosi  
• Subtitle dinamis *Hormozi-style* per kata  
• Face tracking speaker — crop selalu pas  
• Audio enhancement profesional (EQ + noise removal)  
• Publish otomatis — caption, hashtag, trending audio  

</td>
</tr>
</table>

---

## 🏗️ Arsitektur Sistem

```
                      📥 INGESTION
   YouTube URL ──► yt-dlp (best quality) ──► Video MP4 + Audio WAV
                            │
                      🎙️ TRANSCRIPTION
   Audio ──► faster‑whisper (large‑v3) ──► Transkrip per‑kata + deteksi jeda
                            │
                    🧠 AI DIRECTOR (MCP)
   Transkrip ──► OpenCode via MCP ──► Deteksi momen viral
                            │            ├─ Hook text (3 detik pertama)
                            │            ├─ Caption + Hashtag + Mood
                            │            └─ Skor viralitas per segmen
                            │
                    ✂️ EDITING ENGINE
   ┌─────────────────────────────────────────────────┐
   │ Smart Crop 9:16  │  Face Tracking (MediaPipe)    │
   │ Subtitle Animasi │  Zoom Retention Effects       │
   │ Audio Pro        │  BGM Mood Matching            │
   └─────────────────────────────────────────────────┘
     FFmpeg ──► Render final 1080×1920 @ 30fps
                            │
                      🚀 PUBLISHING
   Playwright + Stealth ──► Upload TikTok ──► Live!
```

### Alur Celery Pipeline

```
POST /api/v1/videos/  { youtube_url }
         │
         ▼
   ┌──────────┐   ┌──────────────┐   ┌──────────────┐   ┌───────────┐   ┌──────────┐
   │ Download │──►│  Transcribe  │──►│   Analyze    │──►│   Edit    │──►│  Render  │
   └──────────┘   └──────────────┘   └──────────────┘   └───────────┘   └──────────┘
                                                                              │
                                                                              ▼
                                                                     ┌──────────────┐
                                                                     │   Publish    │
                                                                     └──────────────┘
```

---

## 🧰 Tech Stack

| Layer | Teknologi | Alasan Pemilihan |
|---|---|---|
| **API** | FastAPI (Python) | Async-native, auto docs, ekosistem AI/ML terbaik |
| **Queue** | Celery + Redis | Job processing async yang andal untuk tugas berat |
| **Database** | PostgreSQL (prod) / SQLite (dev) | Metadata video, transkrip, klip, status pipeline |
| **Transkripsi** | faster-whisper (CTranslate2) | 4× lebih cepat dari Whisper asli, gratis selamanya |
| **AI Director** | OpenCode via MCP + OpenAI fallback | Analisis viralitas, sentimen, caption, hashtag |
| **Face Tracker** | MediaPipe Face Mesh | 468 titik landmark, smoothing Kalman filter |
| **Video** | FFmpeg + ffmpeg-python | Standar industri, GPU encoding, semua format |
| **Audio** | librosa + pydub + noisereduce | Analisis spektral, noise reduction, loudnorm |
| **Browser** | Playwright + stealth | Anti-deteksi TikTok, perilaku human-like |
| **Download** | yt-dlp | Ekstraksi kualitas terbaik, merge format, metadata |
| **Frontend** | React 19 + Vite + TailwindCSS v4 | Build < 400ms, dark theme, responsive |
| **Container** | Docker + Compose | Reproducible, GPU passthrough |

---

## 📁 Struktur Proyek

> 🗂️ **67 file • 6.480 baris kode** — modular, clean architecture, single responsibility

```
ai-cliper/
│
├── backend/                         # ⚙️ Core Engine (Python FastAPI)
│   ├── app/
│   │   ├── api/                     # 🔌 REST API Layer
│   │   │   ├── deps.py              #    Dependency injection (DB session, settings)
│   │   │   └── routes/
│   │   │       ├── videos.py        #    CRUD video + trigger pipeline
│   │   │       └── pipeline.py      #    Monitoring + publish endpoint
│   │   │
│   │   ├── core/                    # 🧬 Application Core
│   │   │   ├── config.py            #    Konfigurasi typed (pydantic-settings)
│   │   │   ├── database.py          #    Async engine (SQLite & PostgreSQL)
│   │   │   └── celery_app.py        #    Celery instance + konfigurasi
│   │   │
│   │   ├── models/                  # 🗃️ ORM Models (SQLAlchemy)
│   │   │   └── __init__.py          #    Video, Transcription, Clip, PipelineTask
│   │   │
│   │   ├── schemas/                 # 📋 Pydantic Schemas
│   │   │   └── __init__.py          #    Request/response validation
│   │   │
│   │   ├── services/                # 🧠 Business Logic (5 modul)
│   │   │   ├── ingestion/           #    📥 Downloader + Transcriber
│   │   │   ├── analysis/            #    🔬 AI Viral Analyzer
│   │   │   ├── editing/             #    ✂️ Video Composer + Renderer
│   │   │   ├── audio/               #    🎵 Audio Enhancer + Mood Detector
│   │   │   └── publishing/          #    🚀 TikTok Bot (Playwright)
│   │   │
│   │   ├── mcp/                     # 🔗 MCP Integration
│   │   │   └── client.py            #    OpenCode bridge + OpenAI fallback
│   │   │
│   │   ├── workers/tasks.py         # ⚡ Celery Tasks (full pipeline chain)
│   │   └── main.py                  # 🚀 FastAPI entry point
│   │
│   ├── alembic/                     # Database migrations
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile
│   └── run_server.py
│
├── frontend/                        # 🖥️ Dashboard (React + Vite)
│   ├── src/
│   │   ├── components/Layout.tsx    #    Shell aplikasi (header, nav, dark theme)
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        #    Input URL + daftar job video
│   │   │   └── VideoDetail.tsx      #    Detail klip + aksi publish
│   │   └── lib/                     #    API client, types, utilities
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── package.json
│
├── data/                            # 💾 Runtime data (gitignored)
│   ├── models/                      #    Model Whisper (~3GB)
│   ├── temp/                        #    File sementara download
│   └── output/                      #    Hasil render klip
│
├── scripts/                         # 🔧 Development scripts
│   ├── setup.ps1                    #    One-command install dependencies
│   └── dev.ps1                      #    Start backend + worker + frontend
│
├── docker-compose.yml               # Full stack (PG + Redis + BE + Worker + FE)
├── .env.example                     # Template konfigurasi environment
├── test_core.py                     # Test suite (10 tes)
└── README.md                        # 📖 Anda di sini
```

---

## 🧮 Algoritma Inti

### 1. Deteksi Momen Viral (AI Director)

AI Director menerima transkrip lengkap + timestamp per kata dan menganalisisnya dengan prompt terstruktur:

```
Input:   Transkrip penuh + Word-level timeline + Segment breakdown

Kriteria Analisis:
├── Hook Potential      (0-10) — Apakah 1-3 detik pertama menarik perhatian?
├── Emotional Impact    (0-10) — Kaget, lucu, marah, inspirasi, penasaran?
├── Shareability        (0-10) — Apakah orang akan kirim ke teman?
├── Controversy/Novelty (0-10) — Mengejutkan atau memicu debat?
└── Completeness        (0-10) — Bisa berdiri sendiri sebagai cerita utuh?

Output:   JSON terstruktur — klip teranking, caption, hashtag, mood
Batasan:  Maksimal 5 klip, durasi 15-90 detik, tidak boleh tumpang tindih
```

> 🔄 **Fallback otomatis**: Jika OpenCode/MCP tidak tersedia, sistem langsung beralih ke OpenAI GPT-4o.

### 2. Smart Crop 9:16 + Face Tracking

```
1.  Sampling frame setiap 1 detik dengan OpenCV
2.  Deteksi wajah menggunakan MediaPipe Face Mesh (468 landmark)
3.  Simpan posisi relatif wajah (cx, cy) per frame
4.  Smoothing Exponential Moving Average (α=0.3) — kurangi jitter
5.  Hitung skor stabilitas (0-1) dari pergerakan antar frame
6.  Bangun FFmpeg crop filter berpusat pada posisi rata-rata wajah:
    ├── Ada wajah → crop centered on face
    └── Tidak ada → crop centered (fallback)
7.  Scale ke 1080×1920
```

### 3. Subtitle Dinamis (Hormozi-Style)

```
Input:    Word-level timestamps dari Whisper
Proses:
  1. Filter kata dalam rentang waktu klip
  2. Kelompokkan jadi baris (maks 5 kata, pisah di jeda >300ms)
  3. Terapkan palet warna berdasarkan mood (8 preset)
  4. Deteksi kata kunci emosional dari kamus (marah, semangat, sedih, kaget)
  5. Tandai kata kunci dengan warna highlight + sisipkan emoji
  6. Generate file subtitle ASS (Advanced SubStation Alpha)
  7. FFmpeg burn subtitle dengan timing per kata + styling
```

**Palet Warna Mood:**

| Mood | Warna Utama | Highlight |
|---|---|---|
| ✨ Inspiratif | `#FFD700` emas | `#FF6B35` oranye |
| 😂 Lucu | `#00FF88` hijau | `#FF3366` pink |
| 🔥 Kontroversial | `#FF4444` merah | `#FF0000` merah tua |
| 📚 Edukatif | `#4FC3F7` biru | `#FFA726` amber |
| 😢 Emosional | `#FF80AB` pink | `#E040FB` ungu |
| 😱 Mengejutkan | `#FF1744` merah | `#FF9100` oranye tua |

### 4. Audio Enhancement Pipeline

```
1. Ekstrak track audio (16kHz mono WAV) — untuk Whisper
2. Voice EQ:
   ├── Highpass 80Hz     → buang suara rendah mengganggu
   ├── Lowpass 15kHz     → buang desis
   └── Voice boost       → +3dB @ 2.5kHz, -2dB @ 120Hz
3. Noise reduction       → FFmpeg anlmdn (non-local means)
4. Dynamic compression   → compand multi-threshold
5. Loudness normalisasi  → loudnorm I=-14 LUFS (standar TikTok)
6. Deteksi mood BGM      → librosa spectral centroid + tempo
```

---

## 📡 API Reference

> Base URL: `http://localhost:8000` • Docs interaktif: `/docs` • ReDoc: `/redoc`

### Endpoints

| Method | Endpoint | Keterangan |
|---|---|---|
| `POST` | `/api/v1/videos/` | Submit URL YouTube → trigger full pipeline |
| `GET` | `/api/v1/videos/` | Daftar semua job video (`?status=` untuk filter) |
| `GET` | `/api/v1/videos/{id}` | Detail video + semua klip |
| `GET` | `/api/v1/videos/{id}/status` | Status pipeline real-time + progres |
| `DELETE` | `/api/v1/videos/{id}` | Hapus video beserta data terkait |
| `GET` | `/api/v1/pipeline/clips/{id}` | Daftar klip hasil analisis |
| `GET` | `/api/v1/pipeline/tasks/{id}` | Riwayat task per video |
| `POST` | `/api/v1/pipeline/publish` | Publish klip ke TikTok |
| `GET` | `/health` | Health check server |

### Contoh: Submit Video Baru

```bash
curl -X POST http://localhost:8000/api/v1/videos/ \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Contoh Response: Detail Video

```json
{
  "id": "c35014df-6ee5-4fb2-a9c9-1fbbd8c0af36",
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "title": "Bagaimana AI Akan Mengubah Segalanya",
  "duration_seconds": 1247.0,
  "status": "completed",
  "clips": [
    {
      "id": "abc123...",
      "clip_index": 1,
      "start_time": 245.5,
      "end_time": 305.2,
      "duration": 59.7,
      "virality_score": 92,
      "hook_text": "Dalam 5 tahun ke depan, AI akan...",
      "caption": "Ini mengubah segalanya buat saya 🤯 #AI #MasaDepan",
      "hashtags": ["ai", "masadepan", "teknologi", "fyp", "viral"],
      "mood": "shocking",
      "output_path": "/data/output/abc123/clips/clip_001.mp4",
      "status": "completed"
    }
  ]
}
```

---

## 🚀 Panduan Instalasi

### Prasyarat

| Software | Versi | Dibutuhkan Untuk |
|---|---|---|
| Python | 3.11+ | Runtime backend |
| Node.js | 22+ | Build frontend |
| FFmpeg | 5.0+ | Encoding/decoding video |
| PostgreSQL | 16+ | Database production |
| Redis | 7+ | Celery task queue |
| CUDA | 12+ | GPU acceleration (opsional) |

### ⚡ Quick Start (Windows)

```powershell
# 1. Clone repository
git clone https://github.com/gempurbudianarki/ATELIX-ViralClip-AI-Pipeline.git
cd ATELIX-ViralClip-AI-Pipeline

# 2. Jalankan script setup (buat venv + install dependencies)
.\scripts\setup.ps1

# 3. Konfigurasi environment
copy .env.example .env
# ✏️ Edit .env — isi OPENAI_API_KEY, kredensial TikTok, dll

# 4. Install FFmpeg (jika belum ada)
# Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
# Extract dan tambahkan folder bin/ ke PATH

# 5. Pastikan PostgreSQL & Redis berjalan

# 6. Jalankan semua layanan
.\scripts\dev.ps1
```

### 🐳 Docker (All-in-One)

```bash
# Start full stack
docker compose up -d

# Cek logs
docker compose logs -f backend

# Stop semua
docker compose down
```

### 🐧 Manual (Linux/macOS)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1 — Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3 — Frontend
cd ../frontend
npm install && npm run dev
```

---

## 📊 Status Pengembangan

### ✅ Selesai (17 Modul)

| Modul | Status | Detail Teknis |
|---|---|---|
| Struktur Proyek | ✅ | 67 file, Clean Architecture |
| Konfigurasi | ✅ | pydantic-settings, dual DB (SQLite + PG) |
| Database Models | ✅ | Video, Transcription, Clip, PipelineTask |
| API Routes | ✅ | 9 endpoint REST + Swagger docs |
| YouTube Downloader | ✅ | yt-dlp best quality, merge format |
| Whisper Transcriber | ✅ | faster-whisper, word-level, VAD, silence detection |
| MCP/LLM Analyzer | ✅ | OpenCode MCP bridge + OpenAI fallback |
| Clip Validator | ✅ | Overlap detection, durasi clamp, score ranking |
| Face Tracker | ✅ | MediaPipe 468-point, Kalman smoothing |
| Subtitle Renderer | ✅ | ASS format, 8 mood presets, keyword highlight |
| Audio Enhancer | ✅ | Noise reduction, voice EQ, loudnorm, mood |
| FFmpeg Renderer | ✅ | Smart crop, zoom, subtitle burn, AAC |
| TikTok Publisher | ✅ | Playwright stealth, human-like delays |
| Celery Workers | ✅ | Full pipeline chain: 6 task berurutan |
| Frontend Dashboard | ✅ | React 19, Vite, TailwindCSS v4 |
| Docker Setup | ✅ | Compose full stack + GPU passthrough |
| Test Suite | ✅ | 10/10 core tests passing |

### 🔧 Sedang Dikerjakan

| Tugas | Prioritas | Kendala |
|---|---|---|
| Install FFmpeg binary | HIGH | Timeout download (network) |
| Download model Whisper | HIGH | Butuh FFmpeg untuk ekstrak audio |
| Tes pipeline end-to-end | HIGH | Butuh FFmpeg + model Whisper |
| Tes PostgreSQL migration | MEDIUM | Butuh instance PostgreSQL aktif |
| Tes TikTok live publish | MEDIUM | Butuh akun TikTok burner |

### 📋 Fase 2 (Mendatang)

- OAuth YouTube untuk video private/unlisted
- Multi-platform (YouTube Shorts, Instagram Reels)
- Auto-matching trending audio TikTok
- A/B testing caption & thumbnail
- Dashboard analytics (views, engagement)
- Autentikasi user & multi-tenant
- Notifikasi webhook (Discord, Telegram)
- Batch processing (playlist → banyak video)
- Custom overlay branding (watermark, logo)

---

## 🧪 Menjalankan Tes

```powershell
# Core engine test (10 tes)
cd backend
.\.venv\Scripts\python.exe ..\test_core.py

# Unit test (butuh pytest)
pytest app/tests/ -v

# Build check frontend
cd frontend
npm run build
```

---

## 🔐 Keamanan

- **API Keys**: Simpan di `.env` (tidak pernah di-commit). Gunakan secret manager di production
- **Kredensial TikTok**: Variabel environment saja, tidak boleh di-log
- **Validasi URL**: Cek server-side, tidak ada arbitrary file upload
- **CORS**: Terbuka untuk development. Kunci ke origin spesifik di production
- **Database**: PostgreSQL + SSL di production. Parameterized query via SQLAlchemy (anti SQL injection)
- **Dependencies**: Audit rutin `pip audit` dan `npm audit`

---

## 🤝 Berkontribusi

1. Fork repository ini
2. Buat branch fitur (`git checkout -b feat/fitur-keren`)
3. Commit perubahan (`git commit -m 'feat: tambah fitur keren'`)
4. Push ke branch (`git push origin feat/fitur-keren`)
5. Buka Pull Request

### Standar Kode
- **Python**: Strict typing, docstring di setiap fungsi publik
- **React**: Functional components, hooks, TypeScript
- **Commit**: Format Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)

---

## 👥 Tim

**ATELIX ViralClip AI** — Dibangun oleh ATELIX Core Team

---

<br>

<div align="center">

<sub>Dibangun dengan Python, React, FFmpeg, OpenAI, MediaPipe, dan ambisi tanpa batas 🚀</sub>

<br>

[⬆ Kembali ke atas](#-atelix-viralclip-ai)

</div>
