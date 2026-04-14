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
- [Setup & Installation](#-setup--installation)
- [Running the Application](#-running-the-application)
- [Deployment to Cloud Run](#-deployment-to-cloud-run)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
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
│  NFC Badge   │────▶│  FastAPI API    │────▶│  Google Gemini   │
│  Scanner     │     │  /api/scan      │     │  (Dialogue Gen)  │
└──────────────┘     └───────┬────────┘     └────────┬─────────┘
                             │                        │
                             ▼                        ▼
                     ┌───────────────┐     ┌──────────────────┐
                     │  WebSocket    │◀────│  Google Cloud    │
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
3. **Gemini generates dialogue** → contextual, in-character, with quests/advice
4. **TTS converts to speech** → Google Cloud Text-to-Speech creates audio
5. **WebSocket pushes to actor** → dialogue + stage directions appear instantly
6. **Actor delivers lines** → improvising based on AI-generated cues

---

## 🏗 Architecture

```
npc-actor-system/
├── backend/
│   ├── app.py              # FastAPI app + WebSocket + routes
│   ├── config.py           # Environment configuration
│   ├── models.py           # Pydantic data models
│   ├── database.py         # In-memory DB + Firestore integration
│   ├── gemini_service.py   # Google Gemini dialogue generation
│   ├── tts_service.py      # Google Cloud TTS integration
│   └── tests/              # Pytest test suite
├── frontend/
│   ├── index.html          # Admin Dashboard
│   ├── actor.html          # Actor Earpiece Interface
│   ├── scanner.html        # NFC Badge Scanner Simulator
│   ├── css/style.css       # Design system
│   └── js/                 # Frontend JavaScript
├── Dockerfile              # Multi-stage Docker build
├── cloudbuild.yaml         # Cloud Build → Cloud Run deploy
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🔗 Google Services Integration

| Google Service | Purpose | Implementation |
|---|---|---|
| **Google Gemini API** | Core AI — generates personalized NPC dialogue | `gemini_service.py` — context-aware prompts with attendee data, character personality, and event schedule |
| **Google Cloud TTS** | Converts dialogue to speech for actor earpiece | `tts_service.py` — Neural2 voices with configurable rate, pitch, and headphone-optimized audio |
| **Google Cloud Firestore** | Production database for attendees, characters, events | `database.py` — dual-mode with in-memory fallback for demos |
| **Google Cloud Run** | Serverless container deployment | `Dockerfile` + `cloudbuild.yaml` — auto-scaling, health checks |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI** | Google Gemini 2.0 Flash |
| **Audio** | Google Cloud TTS (Neural2) + Web Speech API fallback |
| **Database** | In-memory (demo) / Google Cloud Firestore (production) |
| **Real-time** | WebSocket (actor earpiece) |
| **Frontend** | Vanilla HTML/CSS/JS, Glassmorphism dark theme |
| **Deployment** | Docker, Google Cloud Run |
| **Testing** | Pytest, FastAPI TestClient |

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
# Copy the example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-api-key-here
```

### Minimum Required Config:
```env
GEMINI_API_KEY=your-gemini-api-key
DATABASE_MODE=memory
TTS_MODE=browser
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

### Quick Demo Flow:
1. Open **Dashboard** → see pre-loaded attendees & NPC characters
2. Open **Actor Earpiece** in another tab → connect as "Zephyr the Chronicler"
3. Open **Badge Scanner** in another tab → select an attendee + character
4. Click **"Generate NPC Dialogue"** → watch dialogue appear in the actor's earpiece!

---

## ☁️ Deployment to Cloud Run

### Option A: Using Cloud Build (Recommended)
```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Set Gemini API key as a build variable
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_GEMINI_API_KEY="your-key" .
```

### Option B: Manual Deploy
```bash
# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/npc-actor-system .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/npc-actor-system

# Deploy to Cloud Run
gcloud run deploy npc-actor-system \
  --image gcr.io/YOUR_PROJECT_ID/npc-actor-system \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key,APP_ENV=production
```

### Option C: Deploy from source
```bash
gcloud run deploy npc-actor-system \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
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

### Test Categories
| Test File | What It Tests |
|-----------|--------------|
| `test_models.py` | Pydantic model validation, enums, defaults |
| `test_api.py` | REST endpoints, CRUD, badge scan, WebSocket |

---

## 📡 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + system status |
| `GET` | `/api/attendees` | List all attendees |
| `POST` | `/api/attendees` | Create new attendee |
| `GET` | `/api/characters` | List NPC characters |
| `POST` | `/api/characters` | Create new character |
| `GET` | `/api/event` | Get event configuration |
| `POST` | `/api/scan` | **Badge scan → Generate dialogue** |
| `POST` | `/api/more-lines` | Actor requests more dialogue |
| `GET` | `/api/interactions` | List interaction history |
| `WS` | `/ws/actor/{character_id}` | Actor earpiece WebSocket |

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
  "audio_base64": "base64-encoded-mp3..."
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
