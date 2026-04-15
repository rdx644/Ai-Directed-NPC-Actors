"""
Tests for the in-memory database operations.

Tests CRUD operations, demo data loading, and edge cases.
"""

from __future__ import annotations

import pytest

from backend.database import DEMO_ATTENDEES, DEMO_CHARACTERS, DEMO_EVENT, InMemoryDatabase
from backend.models import Attendee, Character, Interaction, InteractionType


@pytest.fixture
def fresh_db() -> InMemoryDatabase:
    """Create a fresh database instance with demo data."""
    return InMemoryDatabase()


class TestDemoDataLoading:
    """Tests for demo data initialization."""

    def test_demo_attendees_loaded(self, fresh_db: InMemoryDatabase) -> None:
        attendees = fresh_db.list_attendees()
        assert len(attendees) == len(DEMO_ATTENDEES)

    def test_demo_characters_loaded(self, fresh_db: InMemoryDatabase) -> None:
        characters = fresh_db.list_characters()
        assert len(characters) == len(DEMO_CHARACTERS)

    def test_demo_event_loaded(self, fresh_db: InMemoryDatabase) -> None:
        event = fresh_db.get_event()
        assert event.event_name == DEMO_EVENT.event_name
        assert len(event.sessions) > 0

    def test_demo_attendees_have_interests(self, fresh_db: InMemoryDatabase) -> None:
        """All demo attendees should have at least one interest."""
        for attendee in fresh_db.list_attendees():
            assert len(attendee.interests) > 0, f"{attendee.name} has no interests"

    def test_demo_characters_have_prompts(self, fresh_db: InMemoryDatabase) -> None:
        """All demo characters should have personality prompts."""
        for char in fresh_db.list_characters():
            assert len(char.personality_prompt) >= 10, f"{char.name} has too short a prompt"


class TestAttendeeCRUD:
    """Tests for attendee database operations."""

    def test_get_attendee_by_id(self, fresh_db: InMemoryDatabase) -> None:
        attendees = fresh_db.list_attendees()
        first = attendees[0]
        found = fresh_db.get_attendee(first.id)
        assert found is not None
        assert found.name == first.name

    def test_get_attendee_by_badge(self, fresh_db: InMemoryDatabase) -> None:
        found = fresh_db.get_attendee_by_badge("NFC-1001")
        assert found is not None
        assert found.name == "Priya Sharma"

    def test_get_attendee_by_badge_not_found(self, fresh_db: InMemoryDatabase) -> None:
        assert fresh_db.get_attendee_by_badge("NONEXISTENT") is None

    def test_get_attendee_not_found(self, fresh_db: InMemoryDatabase) -> None:
        assert fresh_db.get_attendee("nonexistent-id") is None

    def test_create_attendee(self, fresh_db: InMemoryDatabase) -> None:
        new = Attendee(badge_id="NFC-NEW", name="New User")
        created = fresh_db.create_attendee(new)
        assert created.name == "New User"
        assert fresh_db.get_attendee(created.id) is not None

    def test_update_attendee(self, fresh_db: InMemoryDatabase) -> None:
        attendees = fresh_db.list_attendees()
        att_id = attendees[0].id
        updated = fresh_db.update_attendee(att_id, {"name": "Updated"})
        assert updated is not None
        assert updated.name == "Updated"

    def test_update_nonexistent(self, fresh_db: InMemoryDatabase) -> None:
        assert fresh_db.update_attendee("nonexistent", {"name": "X"}) is None

    def test_delete_attendee(self, fresh_db: InMemoryDatabase) -> None:
        attendees = fresh_db.list_attendees()
        att_id = attendees[0].id
        initial_count = len(attendees)
        assert fresh_db.delete_attendee(att_id) is True
        assert len(fresh_db.list_attendees()) == initial_count - 1

    def test_delete_nonexistent(self, fresh_db: InMemoryDatabase) -> None:
        assert fresh_db.delete_attendee("nonexistent") is False


class TestCharacterCRUD:
    """Tests for character database operations."""

    def test_get_character(self, fresh_db: InMemoryDatabase) -> None:
        chars = fresh_db.list_characters()
        found = fresh_db.get_character(chars[0].id)
        assert found is not None

    def test_create_character(self, fresh_db: InMemoryDatabase) -> None:
        new = Character(
            name="Test Char",
            personality_prompt="A test character for unit testing purposes.",
        )
        created = fresh_db.create_character(new)
        assert created.name == "Test Char"

    def test_update_character(self, fresh_db: InMemoryDatabase) -> None:
        chars = fresh_db.list_characters()
        updated = fresh_db.update_character(chars[0].id, {"active": False})
        assert updated is not None
        assert updated.active is False

    def test_delete_character(self, fresh_db: InMemoryDatabase) -> None:
        chars = fresh_db.list_characters()
        assert fresh_db.delete_character(chars[0].id) is True
        assert fresh_db.get_character(chars[0].id) is None


class TestInteractions:
    """Tests for interaction logging."""

    def test_add_interaction(self, fresh_db: InMemoryDatabase) -> None:
        interaction = Interaction(
            attendee_id="a1",
            attendee_name="Alice",
            character_id="c1",
            character_name="Zephyr",
            interaction_type=InteractionType.GREETING,
            dialogue_generated="Hello!",
        )
        result = fresh_db.add_interaction(interaction)
        assert result.attendee_name == "Alice"

    def test_list_interactions_sorted(self, fresh_db: InMemoryDatabase) -> None:
        """Interactions should be sorted newest first."""
        for i in range(5):
            fresh_db.add_interaction(
                Interaction(
                    attendee_id=f"a{i}",
                    attendee_name=f"User {i}",
                    character_id="c1",
                    character_name="Zephyr",
                    dialogue_generated=f"Dialogue {i}",
                )
            )
        interactions = fresh_db.list_interactions(limit=3)
        assert len(interactions) == 3

    def test_list_interactions_limit(self, fresh_db: InMemoryDatabase) -> None:
        for i in range(10):
            fresh_db.add_interaction(
                Interaction(
                    attendee_id=f"a{i}",
                    attendee_name=f"User {i}",
                    character_id="c1",
                    character_name="Zephyr",
                    dialogue_generated=f"Dialogue {i}",
                )
            )
        assert len(fresh_db.list_interactions(limit=5)) == 5

    def test_empty_interactions(self, fresh_db: InMemoryDatabase) -> None:
        assert fresh_db.list_interactions() == []
