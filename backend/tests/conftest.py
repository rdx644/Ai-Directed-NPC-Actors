"""
Pytest fixtures for NPC Actor System tests.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_attendee():
    """Sample attendee data for testing."""
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
def sample_character():
    """Sample character data for testing."""
    return {
        "name": "Test Wizard",
        "archetype": "wizard",
        "personality_prompt": "You are a test wizard who speaks about testing and quality.",
        "backstory": "Born from unit tests.",
        "catchphrase": "May your tests always pass!",
        "assigned_actor": "Test Actor",
    }
