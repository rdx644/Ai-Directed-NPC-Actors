"""
NPC Character management routes.

Provides CRUD operations for NPC characters:
  - GET    /api/characters          — List all characters
  - GET    /api/characters/{id}     — Get character by ID
  - POST   /api/characters          — Create new character
  - PUT    /api/characters/{id}     — Update character
  - DELETE /api/characters/{id}     — Delete character
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.database import db
from backend.models import Character, CharacterCreate, CharacterUpdate
from backend.security import sanitize_string

logger = logging.getLogger("npc-system.routes.characters")

router = APIRouter(prefix="/api/characters", tags=["Characters"])


@router.get("", response_model=list[dict[str, Any]])
async def list_characters() -> list[dict[str, Any]]:
    """List all NPC characters."""
    characters = db.list_characters()
    return [c.model_dump() for c in characters]


@router.get("/{character_id}")
async def get_character(character_id: str) -> dict[str, Any]:
    """Get a specific character by ID."""
    character = db.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character.model_dump()


@router.post("", status_code=201)
async def create_character(data: CharacterCreate) -> dict[str, Any]:
    """
    Create a new NPC character.

    Validates personality prompt length and sanitizes all text fields.
    """
    try:
        sanitized = CharacterCreate(
            name=sanitize_string(data.name, "name"),
            archetype=data.archetype,
            personality_prompt=sanitize_string(
                data.personality_prompt, "personality_prompt"
            ),
            backstory=(
                sanitize_string(data.backstory, "backstory")
                if data.backstory else None
            ),
            catchphrase=(
                sanitize_string(data.catchphrase, "catchphrase")
                if data.catchphrase else None
            ),
            voice_style=data.voice_style,
            speaking_rate=data.speaking_rate,
            pitch=data.pitch,
            assigned_actor=(
                sanitize_string(data.assigned_actor, "name")
                if data.assigned_actor else None
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    character = Character(**sanitized.model_dump())
    created = db.create_character(character)
    logger.info(f"Created character: {created.id} ({created.name})")
    return created.model_dump()


@router.put("/{character_id}")
async def update_character(
    character_id: str, data: CharacterUpdate
) -> dict[str, Any]:
    """Update an existing character with validated data."""
    update_data = data.model_dump(exclude_unset=True)

    # Sanitize provided text fields
    for field_name in ("name", "personality_prompt", "backstory", "catchphrase"):
        if field_name in update_data and update_data[field_name]:
            update_data[field_name] = sanitize_string(
                update_data[field_name], field_name
            )

    updated = db.update_character(character_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    logger.info(f"Updated character: {character_id}")
    return updated.model_dump()


@router.delete("/{character_id}")
async def delete_character(character_id: str) -> dict[str, str]:
    """Delete a character."""
    if not db.delete_character(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    logger.info(f"Deleted character: {character_id}")
    return {"status": "deleted", "id": character_id}
