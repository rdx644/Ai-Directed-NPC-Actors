"""
Pytest fixtures for NPC Actor System tests.

Provides reusable test fixtures:
  - FastAPI test client
  - Sample data factories
  - Mock service patches
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.models import DialogueResponse, InteractionType


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_attendee() -> dict:
    """Factory fixture for valid attendee creation data."""
    return {
        "badge_id": "NFC-TEST-001",
        "name": "Test User",
        "email": "test@example.com",
        "company": "TestCorp",
        "role": "Tester",
        "interests": ["testing", "automation", "python"],
        "sessions_attended": ["Testing 101"],
    }


@pytest.fixture
def sample_character() -> dict:
    """Factory fixture for valid character creation data."""
    return {
        "name": "Test Wizard",
        "archetype": "wizard",
        "personality_prompt": "You are a test wizard who speaks about testing and quality assurance.",
        "backstory": "Born from unit tests.",
        "catchphrase": "May your tests always pass!",
        "assigned_actor": "Test Actor",
    }


@pytest.fixture
def mock_gemini_response() -> DialogueResponse:
    """Create a mock Gemini dialogue response."""
    return DialogueResponse(
        character_name="Test Wizard",
        attendee_name="Test User",
        dialogue="Greetings, Test User! The ancient test scripts foretell great results.",
        interaction_type=InteractionType.GREETING,
        quest=None,
        stage_direction="Gesture wisely.",
    )


@pytest.fixture
def mock_generate_dialogue(mock_gemini_response: DialogueResponse):
    """Patch Gemini service to return a mock response."""
    with patch(
        "backend.routes.scanner.generate_dialogue",
        new_callable=AsyncMock,
        return_value=mock_gemini_response,
    ) as mock:
        yield mock


@pytest.fixture
def mock_synthesize_speech():
    """Patch TTS service to return None (no audio)."""
    with patch(
        "backend.routes.scanner.synthesize_speech",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock:
        yield mock
