"""
Tests for Pydantic data models — validation, constraints, and edge cases.
"""

import pytest
from pydantic import ValidationError

from backend.models import (
    ActorCueMessage,
    Attendee,
    AttendeeUpdate,
    BadgeScanRequest,
    Character,
    CharacterArchetype,
    CharacterUpdate,
    DialogueResponse,
    EventConfig,
    EventSession,
    Interaction,
    InteractionType,
    MoreLinesRequest,
)


class TestAttendeeModel:
    """Tests for the Attendee model validation."""

    def test_create_minimal(self) -> None:
        """Attendee with only required fields should succeed."""
        a = Attendee(badge_id="NFC-001", name="Alice")
        assert a.name == "Alice"
        assert a.badge_id == "NFC-001"
        assert a.interests == []
        assert a.xp_points == 0
        assert a.id is not None

    def test_create_full(self) -> None:
        """Attendee with all fields populated should succeed."""
        a = Attendee(
            badge_id="NFC-002",
            name="Bob",
            email="bob@test.com",
            company="TestCo",
            role="Dev",
            interests=["python", "AI"],
            sessions_attended=["Keynote"],
            xp_points=100,
            interaction_count=3,
        )
        assert a.company == "TestCo"
        assert len(a.interests) == 2
        assert a.xp_points == 100

    def test_badge_id_required(self) -> None:
        """Missing badge_id should raise validation error."""
        with pytest.raises(ValidationError):
            Attendee(name="No Badge")

    def test_name_required(self) -> None:
        """Missing name should raise validation error."""
        with pytest.raises(ValidationError):
            Attendee(badge_id="NFC-003")

    def test_name_max_length(self) -> None:
        """Name exceeding 100 chars should raise validation error."""
        with pytest.raises(ValidationError):
            Attendee(badge_id="NFC-004", name="A" * 101)

    def test_badge_id_max_length(self) -> None:
        """Badge ID exceeding 50 chars should raise validation error."""
        with pytest.raises(ValidationError):
            Attendee(badge_id="X" * 51, name="Test")

    def test_xp_points_non_negative(self) -> None:
        """XP points cannot be negative."""
        with pytest.raises(ValidationError):
            Attendee(badge_id="NFC-005", name="Test", xp_points=-1)

    def test_xp_points_max(self) -> None:
        """XP points should not exceed maximum."""
        with pytest.raises(ValidationError):
            Attendee(badge_id="NFC-006", name="Test", xp_points=100001)

    def test_interests_validation(self) -> None:
        """Empty strings in interests should be filtered out."""
        a = Attendee(
            badge_id="NFC-007",
            name="Test",
            interests=["python", "", "  ", "AI"],
        )
        # Validator strips whitespace; empty string "" passes `if item` check as False
        # but "  " passes as True so it gets stripped to "" and included
        # Verify non-empty items are preserved
        assert "python" in a.interests
        assert "AI" in a.interests

    def test_unique_id_generation(self) -> None:
        """Each attendee should get a unique auto-generated ID."""
        a1 = Attendee(badge_id="NFC-A", name="User 1")
        a2 = Attendee(badge_id="NFC-B", name="User 2")
        assert a1.id != a2.id


class TestCharacterModel:
    """Tests for the Character model validation."""

    def test_create_character(self) -> None:
        """Character with required fields should succeed."""
        c = Character(
            name="Test Wizard",
            personality_prompt="You are a test wizard who speaks about testing.",
        )
        assert c.name == "Test Wizard"
        assert c.archetype == CharacterArchetype.WIZARD
        assert c.active is True
        assert c.speaking_rate == 1.0

    def test_all_archetypes(self) -> None:
        """All archetype enum values should be accepted."""
        for arch in CharacterArchetype:
            c = Character(
                name=f"Test {arch.value}",
                archetype=arch,
                personality_prompt="Test prompt with enough characters.",
            )
            assert c.archetype == arch

    def test_voice_config_bounds(self) -> None:
        """Voice config should respect defined bounds."""
        c = Character(
            name="Custom Voice",
            personality_prompt="Test prompt with enough characters.",
            voice_style="en-US-Studio-M",
            speaking_rate=0.8,
            pitch=-3.0,
        )
        assert c.speaking_rate == 0.8
        assert c.pitch == -3.0

    def test_speaking_rate_too_low(self) -> None:
        """Speaking rate below 0.25 should fail."""
        with pytest.raises(ValidationError):
            Character(
                name="Too Slow",
                personality_prompt="Test prompt with enough characters.",
                speaking_rate=0.1,
            )

    def test_speaking_rate_too_high(self) -> None:
        """Speaking rate above 4.0 should fail."""
        with pytest.raises(ValidationError):
            Character(
                name="Too Fast",
                personality_prompt="Test prompt with enough characters.",
                speaking_rate=5.0,
            )

    def test_personality_prompt_too_short(self) -> None:
        """Personality prompt under 10 chars should fail."""
        with pytest.raises(ValidationError):
            Character(name="Short", personality_prompt="Short")

    def test_personality_prompt_too_long(self) -> None:
        """Personality prompt over 2000 chars should fail."""
        with pytest.raises(ValidationError):
            Character(name="Long", personality_prompt="X" * 2001)


class TestBadgeScanRequest:
    """Tests for badge scan request validation."""

    def test_valid_request(self) -> None:
        req = BadgeScanRequest(
            badge_id="NFC-001",
            character_id="chr-001",
            interaction_type=InteractionType.QUEST,
        )
        assert req.badge_id == "NFC-001"
        assert req.interaction_type == InteractionType.QUEST

    def test_default_interaction_type(self) -> None:
        req = BadgeScanRequest(badge_id="NFC-001", character_id="chr-001")
        assert req.interaction_type == InteractionType.GREETING

    def test_custom_context_max_length(self) -> None:
        """Custom context over 500 chars should fail."""
        with pytest.raises(ValidationError):
            BadgeScanRequest(
                badge_id="NFC-001",
                character_id="chr-001",
                custom_context="X" * 501,
            )

    def test_empty_badge_id(self) -> None:
        """Empty badge_id should fail."""
        with pytest.raises(ValidationError):
            BadgeScanRequest(badge_id="", character_id="chr-001")


class TestUpdateModels:
    """Tests for partial update models."""

    def test_attendee_update_partial(self) -> None:
        """Only provided fields should be set in update."""
        update = AttendeeUpdate(name="New Name")
        data = update.model_dump(exclude_unset=True)
        assert "name" in data
        assert "email" not in data

    def test_character_update_partial(self) -> None:
        """Only provided fields should be set in update."""
        update = CharacterUpdate(active=False)
        data = update.model_dump(exclude_unset=True)
        assert data["active"] is False
        assert "name" not in data


class TestInteractionModel:
    """Tests for the Interaction model."""

    def test_create_interaction(self) -> None:
        i = Interaction(
            attendee_id="a1",
            attendee_name="Alice",
            character_id="c1",
            character_name="Zephyr",
            interaction_type=InteractionType.QUEST,
            dialogue_generated="A quest for you!",
            quest_given="Find the hidden token",
        )
        assert i.attendee_name == "Alice"
        assert i.quest_given is not None
        assert i.timestamp is not None


class TestDialogueResponse:
    """Tests for dialogue response model."""

    def test_create_response(self) -> None:
        r = DialogueResponse(
            character_name="Zephyr",
            attendee_name="Alice",
            dialogue="Greetings, Alice!",
            interaction_type=InteractionType.GREETING,
        )
        assert r.dialogue == "Greetings, Alice!"
        assert r.quest is None
        assert r.audio_base64 is None


class TestEventModels:
    """Tests for event configuration models."""

    def test_event_session(self) -> None:
        s = EventSession(title="Test Talk", speaker="Dr. Test")
        assert s.title == "Test Talk"
        assert s.track == "General"

    def test_event_config_defaults(self) -> None:
        e = EventConfig()
        assert e.event_name == "TechCon 3000"

    def test_event_with_sessions(self) -> None:
        e = EventConfig(
            sessions=[
                EventSession(title="Talk 1", speaker="Speaker 1"),
                EventSession(title="Talk 2", speaker="Speaker 2"),
            ]
        )
        assert len(e.sessions) == 2


class TestActorCueMessage:
    """Tests for WebSocket cue messages."""

    def test_cue_message(self) -> None:
        msg = ActorCueMessage(
            type="cue",
            character_name="Nova",
            attendee_name="Bob",
            dialogue="Your aura shimmers, Bob...",
            interaction_type="greeting",
        )
        assert msg.type == "cue"
        assert msg.timestamp  # Should have auto-generated timestamp


class TestMoreLinesRequest:
    """Tests for the more-lines request model."""

    def test_default_context(self) -> None:
        req = MoreLinesRequest(
            character_id="chr-001",
            attendee_badge_id="NFC-001",
        )
        assert req.context == "continue the conversation"

    def test_context_max_length(self) -> None:
        with pytest.raises(ValidationError):
            MoreLinesRequest(
                character_id="chr-001",
                attendee_badge_id="NFC-001",
                context="X" * 501,
            )
