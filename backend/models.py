"""
Pydantic data models for the NPC Actor System.

Defines strictly-typed schemas with field-level validation for:
  - Attendees (event participants with NFC badges)
  - Characters (AI-directed NPC personas)
  - Events (schedule, sessions, tracks)
  - Interactions (logged NPC-attendee encounters)
  - API request/response payloads
  - WebSocket message formats
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────


class CharacterArchetype(str, Enum):
    """Pre-built NPC archetypes with distinct personality styles."""

    WIZARD = "wizard"
    ORACLE = "oracle"
    INVENTOR = "inventor"
    HISTORIAN = "historian"
    TRICKSTER = "trickster"
    MENTOR = "mentor"
    CUSTOM = "custom"


class InteractionType(str, Enum):
    """Types of NPC-attendee interactions."""

    QUEST = "quest"
    ADVICE = "advice"
    RIDDLE = "riddle"
    GREETING = "greeting"
    LORE = "lore"
    FAREWELL = "farewell"


class QuestDifficulty(str, Enum):
    """Difficulty levels for generated quests."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    LEGENDARY = "legendary"


# ──────────────────────────────────────────────
#  Core Models
# ──────────────────────────────────────────────


class Attendee(BaseModel):
    """Represents an event attendee identified by their NFC/RFID badge."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    badge_id: str = Field(
        ..., min_length=1, max_length=50, description="Unique NFC/RFID badge identifier"
    )
    name: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    company: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    interests: list[str] = Field(default_factory=list, max_length=20)
    sessions_attended: list[str] = Field(default_factory=list, max_length=50)
    quests_completed: list[str] = Field(default_factory=list, max_length=50)
    xp_points: int = Field(default=0, ge=0, le=100000)
    last_scanned: datetime | None = None
    interaction_count: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("interests", "sessions_attended", "quests_completed")
    @classmethod
    def validate_list_items(cls, v: list[str]) -> list[str]:
        """Ensure list items are non-empty and reasonably sized."""
        return [item.strip() for item in v if item and len(item.strip()) <= 200]


class Character(BaseModel):
    """Represents an NPC character that an actor will portray."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., min_length=1, max_length=100)
    archetype: CharacterArchetype = CharacterArchetype.WIZARD
    personality_prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="System prompt defining the character's personality and behavior",
    )
    backstory: str | None = Field(default=None, max_length=1000)
    catchphrase: str | None = Field(default=None, max_length=200)
    voice_style: str = Field(default="en-US-Neural2-D", max_length=50)
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0)
    active: bool = True
    assigned_actor: str | None = Field(default=None, max_length=100)


class EventSession(BaseModel):
    """Represents a session/talk at the event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(..., min_length=1, max_length=200)
    speaker: str = Field(..., min_length=1, max_length=100)
    track: str = Field(default="General", max_length=50)
    time_slot: str = Field(default="", max_length=50)
    room: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=10)


class EventConfig(BaseModel):
    """Top-level event configuration."""

    event_name: str = Field(default="TechCon 3000", max_length=200)
    event_theme: str = Field(default="The Future of Technology", max_length=200)
    event_date: str = Field(default="2026-04-15", max_length=20)
    venue: str = Field(default="Innovation Center", max_length=200)
    sessions: list[EventSession] = Field(default_factory=list)


class Interaction(BaseModel):
    """Log entry for an NPC-attendee interaction."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    attendee_id: str
    attendee_name: str
    character_id: str
    character_name: str
    interaction_type: InteractionType = InteractionType.GREETING
    dialogue_generated: str = ""
    quest_given: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    badge_id: str = ""


# ──────────────────────────────────────────────
#  API Request / Response Models
# ──────────────────────────────────────────────


class BadgeScanRequest(BaseModel):
    """Payload when an NFC badge is scanned."""

    badge_id: str = Field(..., min_length=1, max_length=50)
    character_id: str = Field(..., min_length=1, max_length=50)
    interaction_type: InteractionType = InteractionType.GREETING
    custom_context: str | None = Field(default=None, max_length=500)


class DialogueResponse(BaseModel):
    """Response containing generated NPC dialogue."""

    character_name: str
    attendee_name: str
    dialogue: str
    interaction_type: InteractionType
    quest: str | None = None
    stage_direction: str | None = None
    audio_base64: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActorCueMessage(BaseModel):
    """WebSocket message sent to the actor's earpiece."""

    type: str = "cue"
    character_name: str = ""
    attendee_name: str = ""
    dialogue: str = ""
    stage_direction: str | None = None
    interaction_type: str = "greeting"
    quest: str | None = None
    audio_base64: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class MoreLinesRequest(BaseModel):
    """Request from actor for additional dialogue lines."""

    character_id: str = Field(..., min_length=1, max_length=50)
    attendee_badge_id: str = Field(..., min_length=1, max_length=50)
    context: str = Field(default="continue the conversation", max_length=500)


# ──────────────────────────────────────────────
#  CRUD Request Models (with proper validation)
# ──────────────────────────────────────────────


class AttendeeCreate(BaseModel):
    """Schema for creating a new attendee — all inputs validated."""

    badge_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    company: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    interests: list[str] = Field(default_factory=list, max_length=20)
    sessions_attended: list[str] = Field(default_factory=list, max_length=50)
    notes: str | None = Field(default=None, max_length=500)


class AttendeeUpdate(BaseModel):
    """Schema for updating an attendee — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    company: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    interests: list[str] | None = Field(default=None, max_length=20)
    sessions_attended: list[str] | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=500)


class CharacterCreate(BaseModel):
    """Schema for creating a new character — all inputs validated."""

    name: str = Field(..., min_length=1, max_length=100)
    archetype: CharacterArchetype = CharacterArchetype.WIZARD
    personality_prompt: str = Field(..., min_length=10, max_length=2000)
    backstory: str | None = Field(default=None, max_length=1000)
    catchphrase: str | None = Field(default=None, max_length=200)
    voice_style: str = Field(default="en-US-Neural2-D", max_length=50)
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0)
    assigned_actor: str | None = Field(default=None, max_length=100)


class CharacterUpdate(BaseModel):
    """Schema for updating a character — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    archetype: CharacterArchetype | None = None
    personality_prompt: str | None = Field(default=None, min_length=10, max_length=2000)
    backstory: str | None = Field(default=None, max_length=1000)
    catchphrase: str | None = Field(default=None, max_length=200)
    active: bool | None = None
    assigned_actor: str | None = Field(default=None, max_length=100)
