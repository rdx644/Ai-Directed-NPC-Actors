"""
NPC Actor System — Main FastAPI Application

Production-grade application factory with:
  - Modular route registration via APIRouter
  - Security middleware stack (headers, rate limiting, error handling)
  - Structured request logging with correlation IDs
  - WebSocket connection management for actor earpieces
  - Static file serving for the frontend UI
  - Health check endpoint for Cloud Run

Architecture:
  Routes are organized into separate modules under backend/routes/:
    - attendees.py  — Attendee CRUD
    - characters.py — NPC Character CRUD
    - scanner.py    — Badge scan → Dialogue generation pipeline
  Middleware is registered from backend/middleware.py
  Security utilities are in backend/security.py
  Caching is handled by backend/cache.py
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.cache import dialogue_cache
from backend.config import settings
from backend.database import db
from backend.middleware import register_middleware
from backend.models import ActorCueMessage
from backend.routes.attendees import router as attendees_router
from backend.routes.characters import router as characters_router
from backend.routes.scanner import router as scanner_router

# ──────────────────────────────────────────────
#  Structured Logging Configuration
# ──────────────────────────────────────────────


def _configure_logging() -> None:
    """Set up structured logging with appropriate level and format."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s │ %(name)-28s │ %(levelname)-5s │ %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


_configure_logging()
logger = logging.getLogger("npc-system")


# ──────────────────────────────────────────────
#  WebSocket Connection Manager
# ──────────────────────────────────────────────


class ActorConnectionManager:
    """
    Manages WebSocket connections for actor earpiece devices.

    Supports multiple concurrent actors per character and handles
    graceful disconnection with dead-connection cleanup.
    """

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, character_id: str) -> None:
        """Accept and register a new WebSocket connection for a character."""
        await websocket.accept()
        if character_id not in self._connections:
            self._connections[character_id] = []
        self._connections[character_id].append(websocket)
        logger.info(f"Actor connected for character: {character_id}")

    def disconnect(self, websocket: WebSocket, character_id: str) -> None:
        """Remove a WebSocket connection from the registry."""
        if character_id in self._connections:
            self._connections[character_id] = [
                ws for ws in self._connections[character_id] if ws != websocket
            ]
            # Clean up empty lists
            if not self._connections[character_id]:
                del self._connections[character_id]
        logger.info(f"Actor disconnected from character: {character_id}")

    async def send_cue(self, character_id: str, cue: ActorCueMessage) -> int:
        """
        Send a dialogue cue to all actors connected for a character.

        Returns:
            Number of actors that received the cue.
        """
        if character_id not in self._connections:
            logger.debug(f"No actors connected for character: {character_id}")
            return 0

        sent_count = 0
        disconnected: list[WebSocket] = []

        for ws in self._connections[character_id]:
            try:
                await ws.send_json(cue.model_dump())
                sent_count += 1
            except Exception:
                disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            if ws in self._connections.get(character_id, []):
                self._connections[character_id].remove(ws)

        return sent_count

    def get_connected_characters(self) -> list[str]:
        """Return list of character IDs with active WebSocket connections."""
        return [cid for cid, conns in self._connections.items() if conns]

    @property
    def total_connections(self) -> int:
        """Total number of active WebSocket connections."""
        return sum(len(conns) for conns in self._connections.values())


# Singleton connection manager
manager = ActorConnectionManager()


# ──────────────────────────────────────────────
#  Application Lifespan
# ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    logger.info("═" * 60)
    logger.info("  NPC Actor System v1.0.0 — Starting")
    logger.info(f"  Environment  : {settings.app_env}")
    logger.info(f"  Database     : {settings.database_mode}")
    logger.info(f"  TTS Mode     : {settings.tts_mode}")
    logger.info(f"  Gemini API   : {'✓ configured' if settings.gemini_api_key else '✗ NOT SET'}")
    logger.info(f"  Rate Limit   : {settings.rate_limit_rpm} req/min")
    logger.info(f"  CORS Origins : {settings.cors_origins}")
    logger.info("═" * 60)
    yield
    # Cleanup
    dialogue_cache.clear()
    logger.info("NPC Actor System — Shut down gracefully")


# ──────────────────────────────────────────────
#  FastAPI Application Factory
# ──────────────────────────────────────────────

app = FastAPI(
    title="NPC Actor System",
    description=(
        "AI-Directed NPC Actors for Augmented Live Action Events. "
        "Generates personalized, in-character dialogue using Google Gemini "
        "and delivers it to actor earpieces in real-time via WebSocket."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
)

# ── GZip Compression ──
app.add_middleware(GZipMiddleware, minimum_size=500)

# ── CORS Configuration ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# ── Security, Rate Limiting, Logging, Error Handling ──
register_middleware(app)

# ──────────────────────────────────────────────
#  Route Registration
# ──────────────────────────────────────────────

app.include_router(attendees_router)
app.include_router(characters_router)
app.include_router(scanner_router)


# ──────────────────────────────────────────────
#  Health & System Endpoints
# ──────────────────────────────────────────────


@app.get("/api/health", tags=["System"])
async def health_check() -> dict:
    """
    Health check endpoint for Cloud Run and monitoring.

    Returns system status including service health, configuration,
    connected actors, and cache performance metrics.
    """
    return {
        "status": "healthy",
        "service": "npc-actor-system",
        "version": "1.0.0",
        "environment": settings.app_env,
        "gemini_configured": bool(settings.gemini_api_key),
        "tts_mode": settings.tts_mode,
        "database_mode": settings.database_mode,
        "connected_actors": manager.get_connected_characters(),
        "total_actor_connections": manager.total_connections,
        "cache_stats": dialogue_cache.stats,
    }


@app.get("/api/event", tags=["Event"])
async def get_event() -> dict:
    """Get the current event configuration and schedule."""
    return db.get_event().model_dump()


# ──────────────────────────────────────────────
#  WebSocket: Actor Earpiece
# ──────────────────────────────────────────────


@app.websocket("/ws/actor/{character_id}")
async def actor_websocket(websocket: WebSocket, character_id: str) -> None:
    """
    WebSocket endpoint for actor earpiece connections.

    Lifecycle:
      1. Validates the character exists
      2. Accepts connection and sends welcome message
      3. Listens for actor commands (ping, status)
      4. Receives dialogue cues pushed by the scan pipeline
      5. Handles disconnection gracefully
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
            try:
                msg = json.loads(data)
                cmd = msg.get("command", "")

                if cmd == "ping":
                    await websocket.send_json({"type": "pong"})

                elif cmd == "status":
                    await websocket.send_json(
                        {
                            "type": "system",
                            "dialogue": f"You are {character.name}. System is active.",
                            "character_name": character.name,
                        }
                    )

            except json.JSONDecodeError:
                logger.debug(f"Non-JSON message from actor: {data[:50]}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, character_id)
    except Exception as e:
        logger.error(f"WebSocket error for {character_id}: {e}")
        manager.disconnect(websocket, character_id)


# ──────────────────────────────────────────────
#  Static Files (Frontend)
# ──────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/", tags=["Frontend"], include_in_schema=False)
    async def serve_admin() -> FileResponse:
        """Serve the Admin Dashboard."""
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/actor", tags=["Frontend"], include_in_schema=False)
    async def serve_actor() -> FileResponse:
        """Serve the Actor Earpiece interface."""
        return FileResponse(FRONTEND_DIR / "actor.html")

    @app.get("/scanner", tags=["Frontend"], include_in_schema=False)
    async def serve_scanner() -> FileResponse:
        """Serve the Badge Scanner simulator."""
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
        log_level=settings.log_level.lower(),
    )
