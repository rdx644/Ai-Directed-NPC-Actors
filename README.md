# AI-Directed NPC Actor System v2.0

> **Production-grade AI system for augmented live-action events, powered by 8+ Google Cloud services.**

An intelligent NPC (Non-Player Character) direction system that generates personalized, in-character dialogue for live actors at events. When an attendee scans their NFC badge, the system uses **Google Gemini** to create contextual dialogue, synthesizes speech via **Google Cloud Text-to-Speech**, and delivers real-time cues to actors through WebSocket-connected earpieces.

[![CI — NPC Actor System](https://github.com/rdx644/Ai-Directed-NPC-Actors/actions/workflows/ci.yml/badge.svg)](https://github.com/rdx644/Ai-Directed-NPC-Actors/actions)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Integrated-4285F4?logo=googlecloud)

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Cloud    │  │   Secret     │  │   Cloud Run              │  │
│  │  Build    │──│   Manager    │──│   (FastAPI + Uvicorn)    │  │
│  │  (CI/CD)  │  │  (API Keys)  │  │                          │  │
│  └──────────┘  └──────────────┘  │  ┌────────────────────┐  │  │
│                                   │  │  Gemini 2.0 Flash  │  │  │
│  ┌──────────┐  ┌──────────────┐  │  │  (AI Dialogue Gen) │  │  │
│  │  Cloud    │  │   Cloud      │  │  └────────────────────┘  │  │
│  │  Logging  │  │   Storage    │  │                          │  │
│  │ (Metrics) │  │  (Audio/Data)│  │  ┌────────────────────┐  │  │
│  └──────────┘  └──────────────┘  │  │  Cloud TTS          │  │  │
│                                   │  │  (Speech Synthesis) │  │  │
│  ┌──────────┐  ┌──────────────┐  │  └────────────────────┘  │  │
│  │  Cloud    │  │  Container   │  │                          │  │
│  │ Firestore │  │  Registry    │  │  ┌────────────────────┐  │  │
│  │(Database) │  │  (Images)    │  │  │  WebSocket Manager │  │  │
│  └──────────┘  └──────────────┘  │  │  (Actor Earpieces)  │  │  │
│                                   │  └────────────────────┘  │  │
│                                   └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

##  Google Cloud Services Integration

| Service | Purpose | Integration Point |
|---|---|---|
| **Google Gemini 2.0 Flash** | AI dialogue generation with personality, context awareness | `gemini_service.py` — Contextual NPC dialogue |
| **Google Cloud Text-to-Speech** | Speech synthesis for actor earpiece audio | `tts_service.py` — Real-time audio delivery |
| **Google Cloud Firestore** | Production database for attendees, characters, interactions | `database.py` — FirestoreDatabase class |
| **Google Cloud Run** | Serverless container hosting with auto-scaling | `Dockerfile` + `cloudbuild.yaml` |
| **Google Cloud Logging** | Structured JSON logging with severity and trace correlation | `cloud_logging.py` — Event metrics & latency |
| **Google Cloud Secret Manager** | Secure credential management (API keys, tokens) | `secret_manager.py` — IAM-based secrets |
| **Google Cloud Storage** | Audio clip persistence, interaction data export, analytics | `cloud_storage.py` — Audio & data storage |
| **Google Cloud Build** | CI/CD pipeline for automated build and deployment | `cloudbuild.yaml` — Full pipeline |
| **Google Container Registry** | Docker image storage and versioning | `cloudbuild.yaml` — Image management |

##  Features

### Core System
- **NFC Badge Scanning** — Scan → AI generation → Actor delivery in <2 seconds
- **AI Dialogue Generation** — Google Gemini creates personalized, in-character responses
- **Real-time Actor Cues** — WebSocket-connected earpieces for instant dialogue delivery
- **Speech Synthesis** — Google Cloud TTS converts dialogue to natural-sounding audio
- **Character Memory** — NPCs remember past interactions for contextual conversations

### Production Infrastructure
- **Multi-layer Security** — Rate limiting, CSP headers, input sanitization, content filtering
- **Smart Caching** — LRU cache with TTL for Gemini API responses (reduces latency & cost)
- **Structured Logging** — Google Cloud Logging integration with latency tracking
- **Secure Secrets** — Google Cloud Secret Manager for credential management
- **Cloud Storage** — Audio clips and interaction exports stored in GCS
- **Analytics Dashboard** — Real-time metrics for interactions, engagement, and system health
- **WCAG AA Accessible** — Skip-nav, ARIA labels, keyboard navigation, focus management

### Architecture
- **Abstract Database Protocol** — Type-safe interface for seamless backend swapping
- **Custom Exception Hierarchy** — Structured errors with HTTP status mapping
- **Modular Router Architecture** — Separate route modules for attendees, characters, scanner, analytics
- **Middleware Stack** — Security headers, rate limiting, request logging, error handling

##  Project Structure

```
npc-actor-system/
├── backend/
│   ├── app.py                 # FastAPI application factory + WebSocket manager
│   ├── config.py              # Pydantic settings with validation
│   ├── models.py              # Pydantic v2 data models
│   ├── database.py            # DatabaseProtocol + InMemory + Firestore
│   ├── gemini_service.py      # Google Gemini AI dialogue generation
│   ├── tts_service.py         # Google Cloud Text-to-Speech integration
│   ├── cloud_logging.py       # Google Cloud Logging structured events
│   ├── cloud_storage.py       # Google Cloud Storage (audio + exports)
│   ├── secret_manager.py      # Google Cloud Secret Manager client
│   ├── analytics.py           # Analytics computation service
│   ├── cache.py               # LRU cache with TTL for API responses
│   ├── middleware.py           # Security + rate limiting middleware stack
│   ├── security.py            # Input sanitization + content filtering
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── routes/
│   │   ├── attendees.py       # Attendee CRUD endpoints
│   │   ├── characters.py      # NPC Character CRUD endpoints
│   │   ├── scanner.py         # Badge scan → Dialogue pipeline
│   │   └── analytics.py       # Analytics & export endpoints
│   └── tests/
│       ├── conftest.py        # Shared fixtures
│       ├── test_api.py        # API endpoint tests
│       ├── test_models.py     # Pydantic model tests
│       ├── test_database.py   # Database CRUD tests
│       ├── test_middleware.py  # Middleware tests
│       ├── test_exceptions.py # Exception hierarchy tests
│       └── test_cloud_services.py  # Google Cloud integration tests
├── frontend/
│   ├── index.html             # Admin Dashboard (WCAG AA)
│   ├── actor.html             # Actor Earpiece Interface
│   ├── scanner.html           # Badge Scanner Simulator
│   ├── css/style.css          # Design system
│   └── js/                    # Frontend logic
├── .github/workflows/ci.yml  # CI/CD pipeline
├── Dockerfile                 # Multi-stage build (non-root)
├── cloudbuild.yaml            # Google Cloud Build config
├── pyproject.toml             # Project config + tooling
└── requirements.txt           # Python dependencies
```

##  Setup & Installation

### Prerequisites
- Python 3.11+
- Google Cloud SDK (for production deployment)
- Google Gemini API key

### Local Development

```bash
# Clone the repository
git clone https://github.com/rdx644/Ai-Directed-NPC-Actors.git
cd Ai-Directed-NPC-Actors

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run the application
python -m uvicorn backend.app:app --reload --port 8080
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `GOOGLE_CLOUD_PROJECT` | Production | — | GCP project ID |
| `APP_ENV` | No | development | Environment mode |
| `DATABASE_MODE` | No | memory | `memory` or `firestore` |
| `TTS_MODE` | No | browser | `browser` or `google` |
| `GCS_BUCKET_NAME` | No | auto | Cloud Storage bucket |
| `ADMIN_API_KEY` | No | — | Admin endpoint auth |
| `RATE_LIMIT_RPM` | No | 60 | Rate limit per minute |
| `LOG_LEVEL` | No | INFO | Logging level |

##  Testing

```bash
# Run all tests with coverage
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# Run specific test suites
pytest backend/tests/test_cloud_services.py -v   # Google Cloud tests
pytest backend/tests/test_exceptions.py -v        # Exception hierarchy tests
pytest backend/tests/test_api.py -v               # API endpoint tests

# Security scan
ruff check backend/ --select S --ignore S101,S104,S106

# Code quality
ruff check backend/
ruff format --check backend/
```

##  Deployment (Google Cloud Run)

```bash
# Option 1: Cloud Build (recommended)
gcloud builds submit --config cloudbuild.yaml .

# Option 2: Direct deploy
gcloud run deploy npc-actor-system \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,DATABASE_MODE=memory \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

##  API Endpoints

### Core
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scan` | Process NFC badge scan → Generate dialogue |
| `POST` | `/api/more-lines` | Request additional dialogue lines |
| `GET` | `/api/interactions` | List interaction history |
| `GET` | `/api/health` | System health + Google service status |
| `GET` | `/api/event` | Event configuration |

### Attendees & Characters
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/attendees` | List all attendees |
| `POST` | `/api/attendees` | Register attendee |
| `GET` | `/api/characters` | List NPC characters |
| `POST` | `/api/characters` | Create character |

### Analytics & Export
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary` | Interaction analytics dashboard |
| `GET` | `/api/analytics/characters` | Per-character performance |
| `GET` | `/api/analytics/engagement` | Attendee engagement metrics |
| `GET` | `/api/analytics/health` | System health for Cloud Monitoring |
| `POST` | `/api/analytics/export` | Export data to Cloud Storage |

### WebSocket
| Endpoint | Description |
|---|---|
| `ws://host/ws/actor/{character_id}` | Actor earpiece connection |

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
