<p align="center">
  <img src="https://img.shields.io/badge/status-alpha-red?style=for-the-badge" alt="Status: Alpha">
  <img src="https://img.shields.io/badge/python-3.13+-blue?style=for-the-badge&logo=python" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/react-19-61DAFB?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License: MIT">
</p>

<h1 align="center">⚡ ATELIX ViralClip AI Pipeline</h1>
<p align="center"><strong>Autonomous AI-Powered Video Processing Engine<br>Long-Form YouTube → Viral Short-Form Content (TikTok/Reels/Shorts)</strong></p>

---

## 🧠 Project Overview

**ATELIX ViralClip AI Pipeline** is an end-to-end autonomous media processing engine powered by advanced artificial intelligence. It downloads long-duration YouTube videos, analyzes their narrative structure using Large Language Models (LLM) via the Model Context Protocol (MCP), identifies the most viral-worthy moments, and transforms them into premium-quality vertical short-form content (9:16 ratio) with professional-grade editing — all without human intervention.

### The Problem It Solves

| Pain Point | ATELIX Solution |
|---|---|
| Manual editing takes hours per clip | Fully autonomous pipeline — zero human intervention |
| Random trimming misses viral moments | AI Director analyzes narrative, sentiment, and emotional peaks |
| Subtitle creation is tedious | Word-level dynamic subtitles with keyword highlighting (Hormozi-style) |
| 9:16 cropping cuts off speakers | MediaPipe face tracking → smart center-crop following the speaker |
| Audio sounds amateur | Professional noise reduction, voice EQ, loudness normalization |
| TikTok publishing is time-consuming | Playwright stealth automation — upload with captions, hashtags, trending audio |

---

## 🏗️ Architecture (End-to-End Pipeline)

```
┌─────────────────────────────────────────────────────────────────┐
│                    📥 INGESTION LAYER                            │
│  YouTube URL  ──►  yt-dlp (best quality)  ──►  MP4 + Audio WAV │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🎙️ TRANSCRIPTION LAYER                        │
│  Audio WAV  ──►  faster-whisper (large-v3)  ──►  Word-level     │
│                  timestamps + silence detection                  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              🧠 AI DIRECTOR — CORE BRAIN (MCP)                   │
│  Transcript + Timestamps  ──►  OpenCode (via MCP Protocol)      │
│                                 ──►  Viral segments identified   │
│                                 ──►  Hook text extraction        │
│                                 ──►  Captions + Hashtags + Mood  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ✂️ EDITING ENGINE                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Smart Crop (9:16)  │ Face Tracking (MediaPipe)          │    │
│  │ Dynamic Subtitles  │ Zoom/Retention Effects             │    │
│  │ Audio Enhancement   │ BGM Mood Matching                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  FFmpeg orchestration  ──►  1080×1920 rendered clips            │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🚀 PUBLISHING LAYER                           │
│  Playwright + Stealth  ──►  TikTok upload                       │
│  Caption + Hashtags + Trending Audio  ──►  Live/Published       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
User POST /api/v1/videos/  { youtube_url }
         │
         ▼
    Celery Chain:
    ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐    ┌──────────┐
    │ Download  │───►│  Transcribe  │───►│   Analyze    │───►│   Edit    │───►│  Render  │
    │  Video   │    │  (Whisper)   │    │  (MCP/LLM)   │    │  (Crop+)  │    │ (FFmpeg) │
    └──────────┘    └──────────────┘    └──────────────┘    └───────────┘    └──────────┘
                                                                                  │
                                                                                  ▼
                                                                         ┌──────────────┐
                                                                         │   Publish    │
                                                                         │  (Playwright)│
                                                                         └──────────────┘
```

---

## 🧩 Tech Stack

| Layer | Technology | Justification |
|---|---|---|
| **API Framework** | FastAPI (Python) | Async-native, auto OpenAPI docs, best AI/ML ecosystem |
| **Task Queue** | Celery + Redis | Reliable async job processing for long-running video tasks |
| **Database** | PostgreSQL (prod) / SQLite (dev) | Video metadata, transcription, clips, pipeline state |
| **Transcription** | faster-whisper (CTranslate2) | 4× faster than OG Whisper, word-level timestamps, offline |
| **LLM Integration** | OpenCode via MCP + OpenAI fallback | AI Director for viral analysis, sentiment, caption generation |
| **Face Tracking** | MediaPipe Face Mesh | 468-point mesh, Kalman filter smoothing, robust detection |
| **Video Processing** | FFmpeg + ffmpeg-python | Industry standard, GPU-accelerated encoding, all formats |
| **Audio Processing** | librosa + pydub + noisereduce | Spectral analysis, noise reduction, loudness normalization |
| **Browser Automation** | Playwright + playwright-stealth | Anti-detect TikTok publishing, human-like behavior |
| **YouTube Download** | yt-dlp | Best quality extraction, format merging, metadata |
| **Frontend** | React 19 + Vite + TailwindCSS v4 | Modern SPA, sub-400ms build, dark theme, responsive |
| **Containerization** | Docker + Docker Compose | Reproducible environments, GPU passthrough support |

---

## 🗂️ Project Structure

```
ai-cliper/
│
├── backend/                          # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                      # HTTP API Layer
│   │   │   ├── deps.py               # FastAPI dependencies
│   │   │   └── routes/
│   │   │       ├── videos.py         # POST/GET/DELETE /api/v1/videos/
│   │   │       └── pipeline.py       # GET /api/v1/pipeline/ + POST publish
│   │   │
│   │   ├── core/                     # Application Core
│   │   │   ├── config.py             # Typed settings (pydantic-settings)
│   │   │   ├── database.py           # Async SQLAlchemy + SQLite/PostgreSQL
│   │   │   └── celery_app.py         # Celery instance + configuration
│   │   │
│   │   ├── models/__init__.py        # ORM Models
│   │   │   ├── Video                 # Source video metadata
│   │   │   ├── Transcription         # Whisper output (word-level JSON)
│   │   │   ├── Clip                  # Viral clip segments + metadata
│   │   │   └── PipelineTask          # Task tracking + progress
│   │   │
│   │   ├── schemas/__init__.py       # Pydantic request/response schemas
│   │   │
│   │   ├── services/                 # Business Logic Layer
│   │   │   ├── ingestion/
│   │   │   │   ├── downloader.py     # yt-dlp YouTube downloader
│   │   │   │   └── transcriber.py    # faster-whisper + silence detection
│   │   │   │
│   │   │   ├── analysis/
│   │   │   │   └── viral_analyzer.py # LLM analysis + clip validation
│   │   │   │
│   │   │   ├── editing/
│   │   │   │   ├── video_composer.py # Pipeline orchestration (edit + render)
│   │   │   │   ├── face_tracker.py   # MediaPipe face mesh + Kalman smoothing
│   │   │   │   ├── subtitle_renderer.py # ASS subtitle generation
│   │   │   │   └── video_renderer.py # FFmpeg filter complex builder
│   │   │   │
│   │   │   ├── audio/
│   │   │   │   └── enhancer.py       # Noise reduction, EQ, loudnorm, mood
│   │   │   │
│   │   │   └── publishing/
│   │   │       └── tiktok_bot.py     # Playwright stealth TikTok uploader
│   │   │
│   │   ├── mcp/
│   │   │   └── client.py             # OpenCode MCP bridge + OpenAI fallback
│   │   │
│   │   ├── workers/
│   │   │   └── tasks.py              # Celery task definitions (full pipeline chain)
│   │   │
│   │   └── main.py                   # FastAPI application entry point
│   │
│   ├── alembic/                      # Database migrations
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container
│   └── run_server.py                 # Dev server launcher
│
├── frontend/                         # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   └── Layout.tsx            # App shell (header, nav, dark theme)
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx         # YouTube URL input + video job list
│   │   │   └── VideoDetail.tsx       # Clip details + publish actions
│   │   ├── lib/
│   │   │   ├── api.ts                # API client functions
│   │   │   ├── client.ts             # Axios instance
│   │   │   └── types.ts              # TypeScript interfaces
│   │   ├── main.tsx                  # React entry (QueryClient + Router)
│   │   └── App.tsx                   # Route definitions
│   ├── vite.config.ts                # Vite + TailwindCSS plugin
│   ├── tsconfig.json                 # TypeScript config
│   └── Dockerfile                    # Frontend container
│
├── data/                             # Runtime data (gitignored)
│   ├── models/                       # Whisper model files (~3GB)
│   ├── temp/                         # Temporary download/processing
│   └── output/                       # Rendered clips output
│
├── scripts/
│   ├── setup.ps1                     # One-command environment setup
│   └── dev.ps1                       # Start backend + worker + frontend
│
├── docker-compose.yml                # Full stack: PG + Redis + Backend + Worker + Frontend
├── .env.example                      # Environment configuration template
├── .gitignore                        # Git ignore rules
├── test_core.py                      # Core engine test suite (10 tests)
└── README.md                         # This file
```

---

## 🎯 Core Algorithms

### 1. Viral Segment Detection

The AI Director (OpenCode via MCP) analyzes the full transcript with this prompt strategy:

```
Input: Full transcript + word-level timestamps + segment breakdown
Analysis Criteria:
  - Hook Potential (0-10):   Does it grab attention in 1-3 seconds?
  - Emotional Impact (0-10): Shock, laughter, anger, inspiration, curiosity?
  - Shareability (0-10):     Would someone send this to a friend?
  - Controversy/Novelty:     Is it surprising or debate-sparking?
  - Completeness (0-10):     Can it stand alone as a micro-story?

Output: Structured JSON with ranked clips, captions, hashtags, mood
Constraints: Max 5 clips, 15-90s each, non-overlapping, sorted by virality
```

**Fallback**: If MCP/OpenCode is unavailable, the system automatically falls back to OpenAI GPT-4o with JSON mode enabled.

### 2. Smart 9:16 Cropping with Face Tracking

```
1. Sample frames at 1-second intervals using OpenCV
2. Detect faces using MediaPipe Face Mesh (468 landmarks)
3. Store relative face center positions (cx, cy) per frame
4. Apply Exponential Moving Average (α=0.3) for jitter reduction
5. Calculate stability score (0-1) based on frame-to-frame movement
6. Build FFmpeg crop filter centered on mean face position:
   - If face detected:  crop=iw*0.5625:ih:centered_on_face
   - If no face:        crop=iw*0.5625:ih:centered
7. Scale to 1080×1920 with force_original_aspect_ratio
```

### 3. Dynamic Subtitle Rendering (Hormozi-Style)

```
Input: Word-level timestamps from Whisper
Process:
  1. Filter words within clip time range
  2. Group into display lines (max 5 words, split at >300ms gaps)
  3. Apply mood-based color palette (8 mood presets)
  4. Detect emotional keywords from dictionary (anger, excitement, etc.)
  5. Tag keywords with highlight color + emoji insertion
  6. Generate ASS (Advanced SubStation Alpha) subtitle file
  7. FFmpeg burns subtitles with per-word timing and styling
```

**Mood Color Presets:**

| Mood | Primary | Highlight |
|---|---|---|
| inspirational | `#FFD700` (gold) | `#FF6B35` (orange) |
| humorous | `#00FF88` (green) | `#FF3366` (pink) |
| controversial | `#FF4444` (red) | `#FF0000` |
| educational | `#4FC3F7` (blue) | `#FFA726` (amber) |
| emotional | `#FF80AB` (pink) | `#E040FB` (purple) |
| shocking | `#FF1744` (red) | `#FF9100` (deep orange) |

### 4. Audio Enhancement Pipeline

```
1. Extract audio track (16kHz mono WAV) for Whisper
2. Voice EQ:
   - Highpass 80Hz (remove rumble)
   - Lowpass 15kHz (remove hiss)
   - Voice boost: +3dB at 2.5kHz, -2dB at 120Hz
3. Noise reduction: FFmpeg anlmdn (non-local means)
4. Dynamic compression: compand -80/-80|-30/-10|-20/-5|0/-3
5. Loudness normalization: loudnorm I=-14 LUFS
6. BGM mood detection: librosa spectral centroid + tempo analysis
```

---

## 📡 API Reference

### Base URL: `http://localhost:8000`

### Authentication
Currently open (no auth). Add API keys via middleware for production.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/videos/` | Submit YouTube URL → triggers full pipeline |
| `GET` | `/api/v1/videos/` | List all video jobs (supports `?status=` filter) |
| `GET` | `/api/v1/videos/{id}` | Get video details + all clips |
| `GET` | `/api/v1/videos/{id}/status` | Pipeline status + progress + clip count |
| `DELETE` | `/api/v1/videos/{id}` | Delete video and all related data |
| `GET` | `/api/v1/pipeline/clips/{video_id}` | List all clips for a video |
| `GET` | `/api/v1/pipeline/tasks/{video_id}` | List pipeline task history |
| `POST` | `/api/v1/pipeline/publish` | Publish a rendered clip to TikTok |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger API documentation |
| `GET` | `/redoc` | ReDoc API documentation |

### Example: Submit a Video

```bash
curl -X POST http://localhost:8000/api/v1/videos/ \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Example Response: Video Detail

```json
{
  "id": "c35014df-6ee5-4fb2-a9c9-1fbbd8c0af36",
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "title": "How AI Will Change Everything",
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
      "hook_text": "In the next 5 years, AI will...",
      "caption": "This changed everything for me 🤯 #AI #Future",
      "hashtags": ["ai", "future", "tech", "fyp", "viral"],
      "mood": "shocking",
      "output_path": "/data/output/abc123/clips/clip_001.mp4",
      "status": "completed"
    }
  ]
}
```

---

## 🚀 Installation & Setup

### Prerequisites

| Software | Version | Required For |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 22+ | Frontend build |
| FFmpeg | 5.0+ | Video encoding/decoding |
| PostgreSQL | 16+ | Production database |
| Redis | 7+ | Celery task queue |
| Git | 2.40+ | Version control |
| CUDA (optional) | 12+ | GPU acceleration for Whisper |

### Quick Start (Windows)

```powershell
# 1. Clone repository
git clone <repo-url> ai-cliper
cd ai-cliper

# 2. Run setup script (creates venv, installs deps)
.\scripts\setup.ps1

# 3. Configure environment
copy .env.example .env
# Edit .env — add your OpenAI key, TikTok credentials, etc.

# 4. Install FFmpeg (if not already installed)
# Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
# Extract and add bin/ folder to PATH

# 5. Ensure PostgreSQL & Redis are running

# 6. Start all services
.\scripts\dev.ps1
```

### Docker Setup (All-in-One)

```bash
# Start full stack (PostgreSQL + Redis + Backend + Worker + Frontend)
docker compose up -d

# View logs
docker compose logs -f backend

# Stop everything
docker compose down
```

### Manual Setup (Linux/macOS)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

---

## 📊 Project Status

### Completed ✅

| Module | Status | Details |
|---|---|---|
| Project Structure | ✅ Done | 46 files, Clean Architecture pattern |
| Config System | ✅ Done | pydantic-settings, .env, typed, dual DB support |
| Database Models | ✅ Done | Video, Transcription, Clip, PipelineTask (SQLite + PG) |
| API Routes | ✅ Done | Videos CRUD, Pipeline monitoring, Publish endpoint |
| YouTube Downloader | ✅ Done | yt-dlp best quality, auto format merge |
| Whisper Transcriber | ✅ Done | faster-whisper, word-level, VAD, silence detection |
| MCP/LLM Analyzer | ✅ Done | OpenCode MCP bridge + OpenAI GPT-4o fallback |
| Viral Segment Validator | ✅ Done | Overlap detection, duration clamping, score ranking |
| Face Tracker | ✅ Done | MediaPipe 468-point mesh, Kalman smoothing |
| Subtitle Renderer | ✅ Done | ASS format, 8 mood presets, keyword highlighting |
| Audio Enhancer | ✅ Done | Noise reduction, voice EQ, loudnorm, mood detection |
| FFmpeg Video Renderer | ✅ Done | Smart crop, zoom effects, subtitle burn, AAC audio |
| TikTok Publisher | ✅ Done | Playwright stealth, human-like delays, caption + hashtags |
| Celery Workers | ✅ Done | Full pipeline chain: download→transcribe→analyze→edit→render→publish |
| Frontend Dashboard | ✅ Done | React 19, Vite, TailwindCSS v4, dark theme |
| Docker Setup | ✅ Done | Full stack compose with GPU passthrough |
| Test Suite | ✅ Done | 10 core tests passing |
| README | ✅ Done | This document |

### In Progress 🔧

| Task | Priority | Blockers |
|---|---|---|
| FFmpeg binary installation | High | Network download timeout |
| Whisper model download | High | Requires FFmpeg for audio extraction |
| End-to-end pipeline test | High | Requires FFmpeg + Whisper model |
| PostgreSQL migration test | Medium | Requires running PostgreSQL instance |
| TikTok live publishing test | Medium | Requires burner TikTok account |
| GPU acceleration setup | Medium | Requires NVIDIA CUDA toolkit |

### Pending (Phase 2) 📋

- YouTube OAuth for private/unlisted videos
- Multi-platform publishing (YouTube Shorts, Instagram Reels)
- Trending audio auto-matching (scrape TikTok trending sounds)
- A/B testing framework for captions/thumbnails
- Analytics dashboard (views, engagement tracking)
- User authentication & multi-tenant support
- Webhook notifications (Discord, Slack, Telegram)
- Batch processing (playlist → multiple videos)
- Custom branding overlay (watermark, logo, lower thirds)

---

## 🔐 Security Considerations

- **API Keys**: Store in `.env` (never committed). Use secret management in production (AWS Secrets Manager, HashiCorp Vault)
- **TikTok Credentials**: Never log or expose. Use environment variables only
- **File Uploads**: Validate YouTube URLs server-side. No arbitrary file upload
- **CORS**: Currently open for development. Lock down to specific origins in production
- **Database**: Use PostgreSQL with SSL in production. Parameterized queries via SQLAlchemy (SQL injection safe)
- **Dependencies**: Regularly audit with `pip audit` and `npm audit`
- **GPU Access**: Docker GPU passthrough restricted to specific containers

---

## 🧪 Running Tests

```powershell
# Core engine tests (10 tests)
cd backend
.\.venv\Scripts\python.exe ..\test_core.py

# Python unit tests (requires pytest)
pytest app/tests/ -v

# Frontend build check
cd frontend
npm run build
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- Python: Strict typing, docstrings on all public functions
- React: Functional components, hooks, TypeScript
- Commits: Conventional Commits format (`feat:`, `fix:`, `docs:`, `refactor:`)

---

## 📝 License

MIT License — see [LICENSE](LICENSE) file for details.

---

## 👤 Author & Team

**ATELIX ViralClip AI Pipeline** — Built with ❤️ by the ATELIX Core Team

---

<p align="center">
  <sub>Built with Python, React, FFmpeg, OpenAI, MediaPipe, and relentless ambition 🚀</sub>
</p>
