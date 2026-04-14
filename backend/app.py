"""
NPC Actor System — Main FastAPI Application

Routes:
  - /api/attendees        — Attendee CRUD
  - /api/characters       — NPC Character CRUD
  - /api/event            — Event configuration
  - /api/scan             — NFC badge scan → dialogue generation
  - /api/interactions     — Interaction log
  - /api/more-lines       — Actor requests additional lines
  - /ws/actor/{char_id}   — WebSocket for actor earpiece
  - /*                    — Static frontend files
"""

from __future__ import annotations
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models import (
    Attendee, AttendeeCreate, Character, CharacterCreate,
    Interaction, InteractionType, BadgeScanRequest,
    ActorCueMessage, MoreLinesRequest,
)
from backend.database import db
from backend.gemini_service import generate_dialogue
from backend.tts_service import synthesize_speech

# ──────────────────────────────────────────────
#  Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("npc-system")


# ──────────────────────────────────────────────
#  WebSocket Connection Manager
# ──────────────────────────────────────────────

class ActorConnectionManager:
    """Manages WebSocket connections for actor earpieces."""

    def __init__(self):
        # character_id → list of active WebSocket connections
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, character_id: str):
        await websocket.accept()
        if character_id not in self.connections:
            self.connections[character_id] = []
        self.connections[character_id].append(websocket)
        logger.info(f"Actor connected for character {character_id}")

    def disconnect(self, websocket: WebSocket, character_id: str):
        if character_id in self.connections:
            self.connections[character_id] = [
                ws for ws in self.connections[character_id] if ws != websocket
            ]
        logger.info(f"Actor disconnected from character {character_id}")

    async def send_cue(self, character_id: str, cue: ActorCueMessage):
        """Send a dialogue cue to all actors connected for a character."""
        if character_id not in self.connections:
            logger.warning(f"No actors connected for character {character_id}")
            return
        disconnected = []
        for ws in self.connections[character_id]:
            try:
                await ws.send_json(cue.model_dump())
            except Exception:
                disconnected.append(ws)
        # Clean up dead connections
        for ws in disconnected:
            self.connections[character_id].remove(ws)

    def get_connected_characters(self) -> list[str]:
        """Return list of character IDs with active connections."""
        return [
            cid for cid, conns in self.connections.items()
            if len(conns) > 0
        ]


manager = ActorConnectionManager()


# ──────────────────────────────────────────────
#  App Lifespan
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("═" * 60)
    logger.info("  NPC Actor System — Starting Up")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Database    : {settings.database_mode}")
    logger.info(f"  TTS Mode    : {settings.tts_mode}")
    logger.info(f"  Gemini API  : {'configured' if settings.gemini_api_key else 'NOT SET'}")
    logger.info("═" * 60)
    yield
    logger.info("NPC Actor System — Shutting Down")


# ──────────────────────────────────────────────
#  FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(
    title="NPC Actor System",
    description="AI-Directed NPC Actors for Augmented Live Action Events",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
#  Health Check
# ──────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "npc-actor-system",
        "environment": settings.app_env,
        "gemini_configured": bool(settings.gemini_api_key),
        "tts_mode": settings.tts_mode,
        "database_mode": settings.database_mode,
        "connected_actors": manager.get_connected_characters(),
    }


# ──────────────────────────────────────────────
#  Attendee Routes
# ──────────────────────────────────────────────

@app.get("/api/attendees")
async def list_attendees():
    """List all registered attendees."""
    attendees = db.list_attendees()
    return [a.model_dump() for a in attendees]


@app.get("/api/attendees/{attendee_id}")
async def get_attendee(attendee_id: str):
    """Get a specific attendee by ID."""
    attendee = db.get_attendee(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return attendee.model_dump()


@app.post("/api/attendees", status_code=201)
async def create_attendee(data: AttendeeCreate):
    """Register a new attendee."""
    attendee = Attendee(**data.model_dump())
    created = db.create_attendee(attendee)
    return created.model_dump()


@app.put("/api/attendees/{attendee_id}")
async def update_attendee(attendee_id: str, data: dict):
    """Update an existing attendee."""
    updated = db.update_attendee(attendee_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return updated.model_dump()


@app.delete("/api/attendees/{attendee_id}")
async def delete_attendee(attendee_id: str):
    """Delete an attendee."""
    if not db.delete_attendee(attendee_id):
        raise HTTPException(status_code=404, detail="Attendee not found")
    return {"status": "deleted"}


# ──────────────────────────────────────────────
#  Character Routes
# ──────────────────────────────────────────────

@app.get("/api/characters")
async def list_characters():
    """List all NPC characters."""
    characters = db.list_characters()
    return [c.model_dump() for c in characters]


@app.get("/api/characters/{character_id}")
async def get_character(character_id: str):
    """Get a specific character by ID."""
    character = db.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character.model_dump()


@app.post("/api/characters", status_code=201)
async def create_character(data: CharacterCreate):
    """Create a new NPC character."""
    character = Character(**data.model_dump())
    created = db.create_character(character)
    return created.model_dump()


@app.put("/api/characters/{character_id}")
async def update_character(character_id: str, data: dict):
    """Update an existing character."""
    updated = db.update_character(character_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated.model_dump()


@app.delete("/api/characters/{character_id}")
async def delete_character(character_id: str):
    """Delete a character."""
    if not db.delete_character(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    return {"status": "deleted"}


# ──────────────────────────────────────────────
#  Event Routes
# ──────────────────────────────────────────────

@app.get("/api/event")
async def get_event():
    """Get the current event configuration."""
    return db.get_event().model_dump()


@app.put("/api/event")
async def update_event(data: dict):
    """Update the event configuration."""
    updated = db.update_event(data)
    return updated.model_dump()


# ──────────────────────────────────────────────
#  Interaction Routes
# ──────────────────────────────────────────────

@app.get("/api/interactions")
async def list_interactions(limit: int = 50):
    """List recent interactions (newest first)."""
    interactions = db.list_interactions(limit=limit)
    return [i.model_dump() for i in interactions]


# ──────────────────────────────────────────────
#  ⭐ Core Feature: Badge Scan → Dialogue
# ──────────────────────────────────────────────

@app.post("/api/scan")
async def scan_badge(request: BadgeScanRequest):
    """
    Process an NFC badge scan and generate NPC dialogue.

    Flow:
    1. Look up attendee by badge_id
    2. Look up the NPC character
    3. Generate dialogue using Gemini
    4. Optionally synthesize speech via Google TTS
    5. Push dialogue to actor's earpiece via WebSocket
    6. Log the interaction
    """
    # 1. Find the attendee
    attendee = db.get_attendee_by_badge(request.badge_id)
    if not attendee:
        raise HTTPException(
            status_code=404,
            detail=f"No attendee found with badge ID: {request.badge_id}"
        )

    # 2. Find the character
    character = db.get_character(request.character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail=f"Character not found: {request.character_id}"
        )

    # 3. Get event context
    event = db.get_event()

    # 4. Generate dialogue via Gemini
    dialogue_response = await generate_dialogue(
        character=character,
        attendee=attendee,
        event=event,
        interaction_type=request.interaction_type,
        custom_context=request.custom_context,
    )

    # 5. Synthesize speech (if Google TTS is enabled)
    audio_b64 = await synthesize_speech(
        text=dialogue_response.dialogue,
        voice_name=character.voice_style,
        speaking_rate=character.speaking_rate,
        pitch=character.pitch,
    )
    dialogue_response.audio_base64 = audio_b64

    # 6. Push to actor via WebSocket
    cue = ActorCueMessage(
        type="cue",
        character_name=character.name,
        attendee_name=attendee.name,
        dialogue=dialogue_response.dialogue,
        stage_direction=dialogue_response.stage_direction,
        interaction_type=request.interaction_type.value,
        quest=dialogue_response.quest,
        audio_base64=audio_b64,
    )
    await manager.send_cue(request.character_id, cue)

    # 7. Log the interaction
    interaction = Interaction(
        attendee_id=attendee.id,
        attendee_name=attendee.name,
        character_id=character.id,
        character_name=character.name,
        interaction_type=request.interaction_type,
        dialogue_generated=dialogue_response.dialogue,
        quest_given=dialogue_response.quest,
        badge_id=request.badge_id,
    )
    db.add_interaction(interaction)

    # 8. Update attendee stats
    db.update_attendee(attendee.id, {
        "interaction_count": attendee.interaction_count + 1,
        "last_scanned": datetime.utcnow(),
        "xp_points": attendee.xp_points + (50 if dialogue_response.quest else 10),
    })

    return dialogue_response.model_dump()


# ──────────────────────────────────────────────
#  Actor: Request More Lines
# ──────────────────────────────────────────────

@app.post("/api/more-lines")
async def request_more_lines(request: MoreLinesRequest):
    """Actor requests additional dialogue lines mid-conversation."""
    character = db.get_character(request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    attendee = db.get_attendee_by_badge(request.attendee_badge_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")

    event = db.get_event()

    dialogue_response = await generate_dialogue(
        character=character,
        attendee=attendee,
        event=event,
        interaction_type=InteractionType.LORE,
        custom_context=request.context,
    )

    audio_b64 = await synthesize_speech(
        text=dialogue_response.dialogue,
        voice_name=character.voice_style,
        speaking_rate=character.speaking_rate,
        pitch=character.pitch,
    )
    dialogue_response.audio_base64 = audio_b64

    # Push to actor
    cue = ActorCueMessage(
        type="cue",
        character_name=character.name,
        attendee_name=attendee.name,
        dialogue=dialogue_response.dialogue,
        stage_direction="Continue the conversation naturally.",
        interaction_type="lore",
        audio_base64=audio_b64,
    )
    await manager.send_cue(request.character_id, cue)

    return dialogue_response.model_dump()


# ──────────────────────────────────────────────
#  WebSocket: Actor Earpiece
# ──────────────────────────────────────────────

@app.websocket("/ws/actor/{character_id}")
async def actor_websocket(websocket: WebSocket, character_id: str):
    """
    WebSocket endpoint for actor earpiece connections.

    On connect: sends character info and welcome message.
    Listens for actor commands (e.g., "more", "hint").
    """
    character = db.get_character(character_id)
    if not character:
        await websocket.close(code=4004, reason="Character not found")
        return

    await manager.connect(websocket, character_id)

    # Send welcome message
    welcome = ActorCueMessage(
        type="system",
        character_name=character.name,
        dialogue=f"Connected as {character.name}. Waiting for badge scans...",
        stage_direction="Get into character. Your earpiece is live.",
    )
    try:
        await websocket.send_json(welcome.model_dump())

        while True:
            data = await websocket.receive_text()
            # Handle actor commands
            try:
                msg = json.loads(data)
                cmd = msg.get("command", "")

                if cmd == "ping":
                    await websocket.send_json({"type": "pong"})

                elif cmd == "status":
                    await websocket.send_json({
                        "type": "system",
                        "dialogue": f"You are {character.name}. System is active.",
                        "character_name": character.name,
                    })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, character_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, character_id)


# ──────────────────────────────────────────────
#  Static Files (Frontend)
# ──────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Serve static assets (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    async def serve_admin():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/actor")
    async def serve_actor():
        return FileResponse(FRONTEND_DIR / "actor.html")

    @app.get("/scanner")
    async def serve_scanner():
        return FileResponse(FRONTEND_DIR / "scanner.html")


# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=not settings.is_production,
        log_level="info",
    )
