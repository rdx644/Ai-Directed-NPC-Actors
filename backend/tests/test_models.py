"""
Tests for Pydantic data models.
"""

import pytest
from backend.models import (
    Attendee, Character, CharacterArchetype, InteractionType,
    BadgeScanRequest, AttendeeCreate, CharacterCreate,
    EventSession, EventConfig, Interaction, DialogueResponse,
    ActorCueMessage, MoreLinesRequest
)


class TestAttendeeModel:
    """Tests for the Attendee model."""

    def test_create_minimal(self):
        a = Attendee(badge_id="NFC-001", name="Alice")
        assert a.name == "Alice"
        assert a.badge_id == "NFC-001"
        assert a.interests == []
        assert a.xp_points == 0
        assert a.id is not None

    def test_create_full(self):
        a = Attendee(
            badge_id="NFC-002", name="Bob",
            email="bob@test.com", company="TestCo", role="Dev",
            interests=["python", "AI"], sessions_attended=["Keynote"],
            xp_points=100, interaction_count=3
        )
        assert a.company == "TestCo"
        assert len(a.interests) == 2
        assert a.xp_points == 100

    def test_badge_id_required(self):
        with pytest.raises(Exception):
            Attendee(name="No Badge")

    def test_name_required(self):
        with pytest.raises(Exception):
            Attendee(badge_id="NFC-003")


class TestCharacterModel:
    """Tests for the Character model."""

    def test_create_character(self):
        c = Character(
            name="Test Wizard",
            personality_prompt="You are a test wizard."
        )
        assert c.name == "Test Wizard"
        assert c.archetype == CharacterArchetype.WIZARD
        assert c.active is True
        assert c.speaking_rate == 1.0

    def test_archetype_enum(self):
        for arch in CharacterArchetype:
            c = Character(
                name=f"Test {arch.value}",
                archetype=arch,
                personality_prompt="Test"
            )
            assert c.archetype == arch

    def test_voice_config(self):
        c = Character(
            name="Custom Voice",
            personality_prompt="Test",
            voice_style="en-US-Studio-M",
            speaking_rate=0.8,
            pitch=-3.0
        )
        assert c.voice_style == "en-US-Studio-M"
        assert c.speaking_rate == 0.8
        assert c.pitch == -3.0


class TestBadgeScanRequest:
    """Tests for badge scan request validation."""

    def test_valid_request(self):
        req = BadgeScanRequest(
            badge_id="NFC-001",
            character_id="chr-001",
            interaction_type=InteractionType.QUEST
        )
        assert req.badge_id == "NFC-001"
        assert req.interaction_type == InteractionType.QUEST

    def test_default_interaction_type(self):
        req = BadgeScanRequest(badge_id="NFC-001", character_id="chr-001")
        assert req.interaction_type == InteractionType.GREETING

    def test_custom_context(self):
        req = BadgeScanRequest(
            badge_id="NFC-001", character_id="chr-001",
            custom_context="attendee just won a prize"
        )
        assert req.custom_context is not None


class TestInteractionModel:
    """Tests for the Interaction model."""

    def test_create_interaction(self):
        i = Interaction(
            attendee_id="a1", attendee_name="Alice",
            character_id="c1", character_name="Zephyr",
            interaction_type=InteractionType.QUEST,
            dialogue_generated="A quest for you!",
            quest_given="Find the hidden token"
        )
        assert i.attendee_name == "Alice"
        assert i.quest_given is not None
        assert i.timestamp is not None


class TestDialogueResponse:
    """Tests for dialogue response model."""

    def test_create_response(self):
        r = DialogueResponse(
            character_name="Zephyr",
            attendee_name="Alice",
            dialogue="Greetings, Alice!",
            interaction_type=InteractionType.GREETING
        )
        assert r.dialogue == "Greetings, Alice!"
        assert r.quest is None
        assert r.audio_base64 is None


class TestEventModels:
    """Tests for event configuration models."""

    def test_event_session(self):
        s = EventSession(title="Test Talk", speaker="Dr. Test")
        assert s.title == "Test Talk"
        assert s.track == "General"

    def test_event_config(self):
        e = EventConfig()
        assert e.event_name == "TechCon 3000"
        assert len(e.sessions) == 0

    def test_event_with_sessions(self):
        e = EventConfig(sessions=[
            EventSession(title="Talk 1", speaker="Speaker 1"),
            EventSession(title="Talk 2", speaker="Speaker 2"),
        ])
        assert len(e.sessions) == 2


class TestActorCueMessage:
    """Tests for WebSocket cue messages."""

    def test_cue_message(self):
        msg = ActorCueMessage(
            type="cue",
            character_name="Nova",
            attendee_name="Bob",
            dialogue="Your aura shimmers, Bob...",
            interaction_type="greeting"
        )
        assert msg.type == "cue"
        assert msg.character_name == "Nova"


class TestMoreLinesRequest:
    """Tests for the more-lines request model."""

    def test_create_request(self):
        req = MoreLinesRequest(
            character_id="chr-001",
            attendee_badge_id="NFC-001"
        )
        assert req.context == "continue the conversation"
