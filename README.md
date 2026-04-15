# 🎭 NPC Actor System — AI-Directed NPC Actors for Augmented Live Action

> **Vertical:** Event Technology / Augmented Live Entertainment

An AI-powered system that transforms human actors into intelligent "Non-Player Characters" (NPCs) at live events. Actors receive real-time, AI-generated dialogue through an earpiece interface, personalized based on each attendee's profile, interests, and event history — turning any conference into an immersive, interactive theatre experience.

---

## 📋 Table of Contents

- [Concept](#-concept)
- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Google Services Integration](#-google-services-integration)
- [Tech Stack](#-tech-stack)
- [Security & Production Hardening](#-security--production-hardening)
- [Setup & Installation](#-setup--installation)
- [Running the Application](#-running-the-application)
- [Deployment to Cloud Run](#-deployment-to-cloud-run)
- [Testing](#-testing)
- [Accessibility](#-accessibility)
- [API Reference](#-api-reference)
- [Assumptions](#-assumptions)

---

## 🎯 Concept

**Problem:** Live events and conferences lack personalized, interactive engagement. Attendees often feel like passive consumers of content.

**Solution:** Deploy human actors as AI-directed NPCs who can:
- **Recognize attendees** via NFC/RFID badge scanning
- **Know their context** — name, interests, sessions attended, and history
- **Deliver personalized dialogue** — cryptic quests, tailored advice, riddles, and lore
- **Stay perfectly in character** — powered by rich AI personality prompts

This creates a "pervasive theatre game" where the conference itself becomes an immersive adventure.

---

## ⚡ How It Works

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐
│  NFC Badge   │────▶│  FastAPI API    │────▶│  Google Gemini │
│  Scanner     │     │  /api/scan      │     │  (Dialogue Gen) │
└──────────────┘     └───────┬────────┘     └────────┬─────────┘
                             │                        │
                             ▼                        ▼
                     ┌───────────────┐     ┌──────────────────┐
                     │  WebSocket    │◀────│  Google Cloud   │
                     │  Push to      │     │  Text-to-Speech  │
                     │  Actor Device │     │  (Audio Gen)     │
                     └───────┬───────┘     └──────────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │  🎧 Actor     │
                     │  Earpiece UI  │
                     │  (Lines +     │
                     │   Audio)      │
                     └───────────────┘
```

### Step-by-Step Flow:
1. **Attendee approaches NPC** → their badge is scanned (NFC/RFID)
2. **System looks up profile** → name, interests, sessions attended, XP points
3. **Cache check** → avoids duplicate Gemini calls for rapid re-scans
4. **Gemini generates dialogue** → contextual, in-character, with quests/advice
5. **Content safety filter** → removes any unsafe patterns from AI output
6. **TTS converts to speech** → Google Cloud Text-to-Speech creates audio
7. **WebSocket pushes to actor** → dialogue + stage directions appear instantly
8. **Actor delivers lines** → improvising based on AI-generated cues
9. **Interaction logged** → XP awarded, history recorded

---

## 🏗 Architecture

The backend follows a **modular router architecture** with separated concerns:

```
npc-actor-system/
├── backend/
│   ├── app.py                # FastAPI app factory, WebSocket, lifespan
│   ├── config.py             # Validated environment configuration
│   ├── models.py             # Pydantic models with field-level constraints
│   ├── database.py           # Dual-mode DB (in-memory + Firestore)
│   ├── gemini_service.py     # Google Gemini dialogue generation
│   ├── tts_service.py        # Google Cloud TTS integration
│   ├── middleware.py          # Security headers, rate limiting, logging, error handling
│   ├── security.py           # Input sanitization, API auth, content filtering
│   ├── cache.py              # LRU cache with TTL for Gemini responses
│   ├── routes/
│   │   ├── attendees.py      # Attendee CRUD endpoints
│   │   ├── characters.py     # NPC Character CRUD endpoints
│   │   └── scanner.py        # Badge scan → dialogue pipeline
│   └── tests/
│       ├── conftest.py       # Shared fixtures & mock factories
│       ├── test_models.py    # Model validation tests (~30 tests)
│       ├── test_api.py       # API endpoint tests (~30 tests)
│       ├── test_security.py  # Security & sanitization tests (~25 tests)
│       ├── test_database.py  # Database CRUD tests (~15 tests)
│       ├── test_cache.py     # Cache algorithm tests (~15 tests)
│       └── test_middleware.py # Rate limiting tests (~5 tests)
├── frontend/
│   ├── index.html            # Admin Dashboard (WCAG AA accessible)
│   ├── actor.html            # Actor Earpiece Interface
│   ├── scanner.html          # NFC Badge Scanner Simulator
│   ├── css/style.css         # Design system (dark theme, glassmorphism)
│   └── js/
│       ├── admin.js          # Dashboard logic
│       ├── actor.js          # WebSocket + real-time dialogue
│       └── scanner.js        # Badge scan workflow
├── .github/workflows/ci.yml  # CI/CD: lint → test → security → Docker
├── Dockerfile                # Multi-stage Docker build
├── cloudbuild.yaml           # Cloud Build → Cloud Run deploy
├── pyproject.toml            # Project config (ruff, mypy, pytest, coverage)
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🔗 Google Services Integration

| Google Service | Purpose | Implementation |
|---|---|---|
| **Google Gemini API** | Core AI — generates personalized NPC dialogue with safety settings | `gemini_service.py` — context-aware prompts, temperature tuning, fallback templates |
| **Google Cloud TTS** | Converts dialogue to speech for actor earpiece | `tts_service.py` — Neural2 voices, configurable rate/pitch, headphone-optimized |
| **Google Cloud Firestore** | Production database for attendees, characters, events | `database.py` — dual-mode with in-memory fallback, automatic demo data seeding |
| **Google Cloud Run** | Serverless container deployment with auto-scaling | `Dockerfile` + `cloudbuild.yaml` — health checks, memory/CPU limits |
| **Google Cloud Logging** | Structured production logging | `google-cloud-logging` integration for Cloud Run environments |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI** | Google Gemini 2.0 Flash |
| **Audio** | Google Cloud TTS (Neural2) + Web Speech API fallback |
| **Database** | In-memory (demo) / Google Cloud Firestore (production) |
| **Caching** | Custom LRU cache with TTL (5 min, 100 entries) |
| **Real-time** | WebSocket (actor earpiece) |
| **Frontend** | Vanilla HTML/CSS/JS, Glassmorphism dark theme, WCAG AA |
| **Security** | Rate limiting, CSP headers, input sanitization, API key auth |
| **Deployment** | Docker, Google Cloud Run, GitHub Actions CI/CD |
| **Testing** | Pytest (100+ tests), 80%+ coverage threshold |
| **Code Quality** | Ruff (linting + formatting), mypy (type checking) |

---

## 🔒 Security & Production Hardening

### Middleware Stack (`middleware.py`)
The application uses a composable middleware pipeline:

| Middleware | Purpose |
|-----------|---------|
| **`SecurityHeadersMiddleware`** | OWASP headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| **`RateLimitMiddleware`** | Token-bucket rate limiting per client IP (configurable RPM/burst, returns 429) |
| **`RequestLoggingMiddleware`** | Structured logging with correlation IDs (`X-Request-ID`), response timing |
| **`ErrorHandlerMiddleware`** | Safe error responses — never leaks stack traces or file paths |

### Input Security (`security.py`)
| Feature | Description |
|---------|-------------|
| **HTML Escaping** | All user inputs are HTML-escaped to prevent stored XSS |
| **Length Limits** | Field-level max lengths enforced (name: 100, email: 254, prompt: 2000) |
| **Badge ID Validation** | Regex pattern: alphanumeric + hyphens only |
| **Email Validation** | Format validation with RFC-compliant regex |
| **Content Filtering** | AI-generated output is scanned for `<script>`, `javascript:`, event handlers |
| **API Key Auth** | `X-API-Key` header with constant-time comparison for admin endpoints |
| **CORS** | Restricted origins, methods, and headers in production |

### Caching (`cache.py`)
| Feature | Description |
|---------|-------------|
| **LRU Eviction** | Bounded at 100 entries — oldest unused entry evicted first |
| **TTL Expiry** | 5-minute time-to-live keeps dialogue fresh |
| **SHA-256 Keys** | Cache keys derived from (character_id, attendee_id, interaction_type) |
| **Hit/Miss Stats** | Exposed via `/api/health` for monitoring |

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+ installed
- A Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
- (Optional) Google Cloud project for TTS & Firestore

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/npc-actor-system.git
cd npc-actor-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### Minimum Required Config:
```env
GEMINI_API_KEY=your-gemini-api-key
DATABASE_MODE=memory
TTS_MODE=browser
```

### Full Configuration Options:
```env
# Google Services
GEMINI_API_KEY=your-key
GOOGLE_CLOUD_PROJECT=your-project-id

# App
APP_ENV=development          # development | production | testing
LOG_LEVEL=INFO               # DEBUG | INFO | WARNING | ERROR

# Security
ADMIN_API_KEY=your-secret    # Required in production
RATE_LIMIT_RPM=60            # Requests per minute per IP
RATE_LIMIT_BURST=20          # Burst size
ALLOWED_ORIGINS=https://your-domain.com
```

---

## ▶️ Running the Application

### Start the Server
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080 --reload
```

### Access the Application
| Page | URL | Purpose |
|------|-----|---------|
| **Admin Dashboard** | http://localhost:8080 | Manage attendees, characters, view interactions |
| **Actor Earpiece** | http://localhost:8080/actor | Real-time dialogue feed for actors |
| **Badge Scanner** | http://localhost:8080/scanner | Simulate NFC badge scans |
| **API Docs** | http://localhost:8080/api/docs | Interactive Swagger documentation |

### Quick Demo Flow:
1. Open **Dashboard** → see pre-loaded attendees & NPC characters
2. Open **Actor Earpiece** in another tab → connect as "Zephyr the Chronicler"
3. Open **Badge Scanner** in another tab → select an attendee + character
4. Click **"Generate NPC Dialogue"** → watch dialogue appear in the actor's earpiece!

---

## ☁️ Deployment to Cloud Run

### Deploy from Source (Recommended)
```bash
gcloud run deploy npc-actor-system \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --set-env-vars "GEMINI_API_KEY=your-key,APP_ENV=production,DATABASE_MODE=memory,TTS_MODE=browser"
```

### Using Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml .
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest backend/tests/ -v
```

### Run with Coverage
```bash
pytest backend/tests/ -v --cov=backend --cov-report=term-missing
```

### Run by Category
```bash
pytest backend/tests/ -v -m unit        # Fast unit tests only
pytest backend/tests/ -v -m security    # Security tests only
```

### Lint & Format
```bash
ruff check backend/                     # Check for issues
ruff format backend/                    # Auto-format code
```

### Test Suite Overview

| Test File | Tests | What It Covers |
|-----------|-------|---------------|
| `test_models.py` | ~30 | Pydantic validation, field constraints, boundary values, edge cases |
| `test_api.py` | ~30 | REST endpoints, CRUD, WebSocket, security headers, validation errors |
| `test_security.py` | ~25 | XSS prevention, input sanitization, badge/email validation, content filtering |
| `test_database.py` | ~15 | CRUD operations, demo data integrity, interaction logging |
| `test_cache.py` | ~15 | LRU eviction, TTL expiry, hit/miss stats, key determinism |
| `test_middleware.py` | ~5 | Token-bucket algorithm, per-IP isolation, rate limit 429 responses |
| **Total** | **~120** | **80%+ branch coverage** |

### CI/CD Pipeline (`.github/workflows/ci.yml`)
```
lint (ruff) → test (pytest + coverage) → security scan (bandit) → Docker build
```

---

## ♿ Accessibility

The frontend implements **WCAG 2.1 Level AA** compliance:

| Feature | Implementation |
|---------|---------------|
| **Skip Navigation** | `<a class="skip-link">` on all pages — visible on Tab key |
| **ARIA Live Regions** | `aria-live="polite"` for dynamic stat updates, `aria-live="assertive"` for screen reader announcements |
| **Semantic HTML** | `<main>`, `<header>`, `<nav>`, `<footer>`, `<aside>` landmarks on all pages |
| **Focus Management** | Enhanced `focus-visible` (3px cyan outline), keyboard-only focus rings |
| **Color Contrast** | WCAG AA 4.5:1 ratio for text, `prefers-contrast: high` media query |
| **Reduced Motion** | `prefers-reduced-motion: reduce` — disables all animations |
| **Keyboard Navigation** | All interactive elements reachable via Tab, modals trap focus |
| **Form Labels** | All inputs have explicit `<label>` elements and `aria-label` attributes |
| **Table Headers** | `scope="col"` on all `<th>` elements |
| **Print Styles** | `@media print` — clean, readable layout without UI chrome |

---

## 📡 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + cache stats + system status |
| `GET` | `/api/attendees` | List all attendees |
| `POST` | `/api/attendees` | Create new attendee (validated + sanitized) |
| `PUT` | `/api/attendees/{id}` | Update attendee (typed schema) |
| `DELETE` | `/api/attendees/{id}` | Delete attendee |
| `GET` | `/api/characters` | List NPC characters |
| `POST` | `/api/characters` | Create new character (validated + sanitized) |
| `PUT` | `/api/characters/{id}` | Update character (typed schema) |
| `DELETE` | `/api/characters/{id}` | Delete character |
| `GET` | `/api/event` | Get event configuration |
| `POST` | `/api/scan` | **Badge scan → Generate dialogue** |
| `POST` | `/api/more-lines` | Actor requests more dialogue |
| `GET` | `/api/interactions` | List interaction history (limit: 1-100) |
| `WS` | `/ws/actor/{character_id}` | Actor earpiece WebSocket |

### Response Headers
| Header | Value |
|--------|-------|
| `X-Request-ID` | Unique correlation ID for request tracing |
| `X-Response-Time` | Processing time in milliseconds |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | Full CSP policy (see middleware.py) |

### Badge Scan Request
```json
{
  "badge_id": "NFC-1001",
  "character_id": "chr-001",
  "interaction_type": "quest",
  "custom_context": "attendee just won a hackathon"
}
```

### Dialogue Response
```json
{
  "character_name": "Zephyr the Chronicler",
  "attendee_name": "Priya Sharma",
  "dialogue": "Priya! The ancient data streams whisper of your prowess in machine learning...",
  "interaction_type": "quest",
  "quest": "Seek the NLP in Production session and unlock the secrets of language models",
  "stage_direction": "Speak with gravitas, lean in conspiratorially.",
  "audio_base64": "base64-encoded-mp3...",
  "timestamp": "2026-04-15T12:00:00Z"
}
```

---

## 📌 Assumptions

1. **Prototype Scope:** This is a functional prototype demonstrating the core concept. In production, NFC hardware would replace the badge scanner simulator.

2. **Demo Data:** The system ships with 6 pre-loaded attendees and 4 NPC characters with rich personalities for immediate demonstration.

3. **Gemini Fallback:** When the Gemini API key is not configured, the system falls back to template-based dialogue generation, ensuring the prototype always works.

4. **TTS Fallback:** When Google Cloud TTS credentials aren't available, the system uses the browser's built-in Web Speech API for audio output.

5. **In-Memory Database:** The default mode uses in-memory storage for simplicity. In production, Google Cloud Firestore provides persistence.

6. **Single Event:** The current design supports one event configuration at a time, suitable for the prototype scope.

7. **Actor Count:** The WebSocket system supports multiple concurrent actor connections, each assigned to different characters.

8. **Rate Limiting:** The default rate limit (60 req/min per IP) prevents abuse while allowing smooth demo usage. Configurable via environment variables.

---

## 🎭 NPC Characters (Pre-loaded)

| Character | Archetype | Personality |
|-----------|-----------|-------------|
| **Zephyr the Chronicler** | 🧙 Wizard | Time-traveling sage from year 3000, speaks in prophecies |
| **Nova the Oracle** | 🔮 Oracle | Sentient AI from a parallel dimension, reads "digital auras" |
| **Bolt the Inventor** | ⚡ Inventor | Eccentric genius tinkerer, high-energy and enthusiastic |
| **Cipher the Trickster** | 🃏 Trickster | Digital rogue who speaks in riddles and puzzles |

---

## 📄 License

MIT License — Built for the Google AI Challenge
