"""
Pydantic data models for the NPC Actor System.
Defines schemas for Attendees, Characters, Events, Interactions, and API payloads.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


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
    badge_id: str = Field(..., description="Unique NFC/RFID badge identifier")
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    sessions_attended: list[str] = Field(default_factory=list)
    quests_completed: list[str] = Field(default_factory=list)
    xp_points: int = 0
    last_scanned: Optional[datetime] = None
    interaction_count: int = 0
    notes: Optional[str] = None


class Character(BaseModel):
    """Represents an NPC character that an actor will portray."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    archetype: CharacterArchetype = CharacterArchetype.WIZARD
    personality_prompt: str = Field(
        ...,
        description="System prompt defining the character's personality and behavior"
    )
    backstory: Optional[str] = None
    catchphrase: Optional[str] = None
    voice_style: str = "en-US-Neural2-D"  # Google TTS voice name
    speaking_rate: float = 1.0
    pitch: float = 0.0
    active: bool = True
    assigned_actor: Optional[str] = None


class EventSession(BaseModel):
    """Represents a session/talk at the event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    speaker: str
    track: str = "General"
    time_slot: str = ""
    room: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class EventConfig(BaseModel):
    """Top-level event configuration."""
    event_name: str = "TechCon 3000"
    event_theme: str = "The Future of Technology"
    event_date: str = "2026-04-15"
    venue: str = "Innovation Center"
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
    quest_given: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    badge_id: str = ""


# ──────────────────────────────────────────────
#  API Request / Response Models
# ──────────────────────────────────────────────

class BadgeScanRequest(BaseModel):
    """Payload when an NFC badge is scanned."""
    badge_id: str
    character_id: str
    interaction_type: InteractionType = InteractionType.GREETING
    custom_context: Optional[str] = None


class DialogueResponse(BaseModel):
    """Response containing generated NPC dialogue."""
    character_name: str
    attendee_name: str
    dialogue: str
    interaction_type: InteractionType
    quest: Optional[str] = None
    stage_direction: Optional[str] = None
    audio_base64: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ActorCueMessage(BaseModel):
    """WebSocket message sent to the actor's earpiece."""
    type: str = "cue"  # "cue", "system", "alert", "clear"
    character_name: str = ""
    attendee_name: str = ""
    dialogue: str = ""
    stage_direction: Optional[str] = None
    interaction_type: str = "greeting"
    quest: Optional[str] = None
    audio_base64: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MoreLinesRequest(BaseModel):
    """Request from actor for additional dialogue lines."""
    character_id: str
    attendee_badge_id: str
    context: str = "continue the conversation"


class AttendeeCreate(BaseModel):
    """Schema for creating a new attendee."""
    badge_id: str
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    sessions_attended: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CharacterCreate(BaseModel):
    """Schema for creating a new character."""
    name: str
    archetype: CharacterArchetype = CharacterArchetype.WIZARD
    personality_prompt: str
    backstory: Optional[str] = None
    catchphrase: Optional[str] = None
    voice_style: str = "en-US-Neural2-D"
    speaking_rate: float = 1.0
    pitch: float = 0.0
    assigned_actor: Optional[str] = None
