"""
Badge scanner and dialogue generation routes.

Core business logic:
  - POST /api/scan       — NFC badge scan → Gemini dialogue → WebSocket push
  - POST /api/more-lines — Actor requests additional dialogue
  - GET  /api/interactions — Interaction history log
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.cache import CacheKey, dialogue_cache
from backend.database import db
from backend.gemini_service import generate_dialogue
from backend.models import (
    ActorCueMessage,
    BadgeScanRequest,
    DialogueResponse,
    Interaction,
    InteractionType,
    MoreLinesRequest,
)
from backend.security import filter_generated_content, sanitize_string
from backend.tts_service import synthesize_speech

logger = logging.getLogger("npc-system.routes.scanner")

router = APIRouter(prefix="/api", tags=["Scanner"])


async def _generate_and_deliver(
    badge_id: str,
    character_id: str,
    interaction_type: InteractionType,
    custom_context: str | None = None,
    use_cache: bool = True,
) -> DialogueResponse:
    """
    Core pipeline: look up entities → generate dialogue → TTS → WebSocket push.

    This shared function is used by both /scan and /more-lines endpoints
    to avoid code duplication.

    Args:
        badge_id: NFC badge identifier for attendee lookup.
        character_id: NPC character identifier.
        interaction_type: Type of interaction to generate.
        custom_context: Optional additional context for the AI.
        use_cache: Whether to use the dialogue cache.

    Returns:
        DialogueResponse with generated dialogue and metadata.

    Raises:
        HTTPException: 404 if attendee or character not found.
    """
    # Import manager here to avoid circular imports
    from backend.app import manager

    # 1. Look up attendee
    attendee = db.get_attendee_by_badge(badge_id)
    if not attendee:
        raise HTTPException(
            status_code=404,
            detail=f"No attendee found with badge ID: {badge_id}",
        )

    # 2. Look up character
    character = db.get_character(character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail=f"Character not found: {character_id}",
        )

    # 3. Check cache (skip for custom context — those should be unique)
    cache_key = CacheKey(character_id, attendee.id, interaction_type.value)
    if use_cache and not custom_context:
        cached = dialogue_cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {attendee.name} ↔ {character.name}")
            return cached

    # 4. Get event context
    event = db.get_event()

    # 5. Generate dialogue via Gemini
    dialogue_response = await generate_dialogue(
        character=character,
        attendee=attendee,
        event=event,
        interaction_type=interaction_type,
        custom_context=custom_context,
    )

    # 6. Apply content safety filter
    dialogue_response.dialogue = filter_generated_content(dialogue_response.dialogue)

    # 7. Synthesize speech (if Google TTS is enabled)
    audio_b64 = await synthesize_speech(
        text=dialogue_response.dialogue,
        voice_name=character.voice_style,
        speaking_rate=character.speaking_rate,
        pitch=character.pitch,
    )
    dialogue_response.audio_base64 = audio_b64

    # 8. Push to actor via WebSocket
    cue = ActorCueMessage(
        type="cue",
        character_name=character.name,
        attendee_name=attendee.name,
        dialogue=dialogue_response.dialogue,
        stage_direction=dialogue_response.stage_direction,
        interaction_type=interaction_type.value,
        quest=dialogue_response.quest,
        audio_base64=audio_b64,
    )
    await manager.send_cue(character_id, cue)

    # 9. Log the interaction
    interaction = Interaction(
        attendee_id=attendee.id,
        attendee_name=attendee.name,
        character_id=character.id,
        character_name=character.name,
        interaction_type=interaction_type,
        dialogue_generated=dialogue_response.dialogue,
        quest_given=dialogue_response.quest,
        badge_id=badge_id,
    )
    db.add_interaction(interaction)

    # 10. Update attendee stats
    xp_gained = 50 if dialogue_response.quest else 10
    db.update_attendee(attendee.id, {
        "interaction_count": attendee.interaction_count + 1,
        "last_scanned": datetime.now(timezone.utc),
        "xp_points": attendee.xp_points + xp_gained,
    })

    # 11. Cache the response
    if use_cache and not custom_context:
        dialogue_cache.put(cache_key, dialogue_response)

    return dialogue_response


@router.post("/scan")
async def scan_badge(request: BadgeScanRequest) -> dict[str, Any]:
    """
    Process an NFC badge scan and generate NPC dialogue.

    Pipeline:
    1. Look up attendee by badge_id
    2. Look up the NPC character
    3. Check dialogue cache
    4. Generate dialogue using Google Gemini
    5. Apply content safety filter
    6. Synthesize speech via Google Cloud TTS
    7. Push dialogue to actor's earpiece via WebSocket
    8. Log the interaction to database
    9. Update attendee XP stats
    """
    # Sanitize optional custom context
    custom_ctx = None
    if request.custom_context:
        custom_ctx = sanitize_string(request.custom_context, "custom_context")

    response = await _generate_and_deliver(
        badge_id=request.badge_id,
        character_id=request.character_id,
        interaction_type=request.interaction_type,
        custom_context=custom_ctx,
    )
    return response.model_dump()


@router.post("/more-lines")
async def request_more_lines(request: MoreLinesRequest) -> dict[str, Any]:
    """Actor requests additional dialogue lines mid-conversation."""
    ctx = sanitize_string(request.context, "context") if request.context else None

    response = await _generate_and_deliver(
        badge_id=request.attendee_badge_id,
        character_id=request.character_id,
        interaction_type=InteractionType.LORE,
        custom_context=ctx,
        use_cache=False,  # Always generate fresh for "more lines"
    )
    return response.model_dump()


@router.get("/interactions")
async def list_interactions(
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List recent interactions sorted by newest first.

    Args:
        limit: Maximum number of interactions to return (1-100).
    """
    # Clamp limit to safe range
    safe_limit = max(1, min(limit, 100))
    interactions = db.list_interactions(limit=safe_limit)
    return [i.model_dump() for i in interactions]
