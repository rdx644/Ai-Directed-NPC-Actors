"""
Tests for the FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "npc-actor-system"
        assert "gemini_configured" in data
        assert "tts_mode" in data


class TestAttendeeEndpoints:
    """Tests for attendee CRUD endpoints."""

    def test_list_attendees(self, client):
        res = client.get("/api/attendees")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        # Should have demo data
        assert len(res.json()) > 0

    def test_get_attendee(self, client):
        # Get first attendee from list
        attendees = client.get("/api/attendees").json()
        if attendees:
            att_id = attendees[0]["id"]
            res = client.get(f"/api/attendees/{att_id}")
            assert res.status_code == 200
            assert res.json()["id"] == att_id

    def test_get_nonexistent_attendee(self, client):
        res = client.get("/api/attendees/nonexistent-id")
        assert res.status_code == 404

    def test_create_attendee(self, client):
        data = {
            "badge_id": "NFC-TEST-CREATE",
            "name": "Created User",
            "email": "created@test.com",
            "interests": ["testing"],
        }
        res = client.post("/api/attendees", json=data)
        assert res.status_code == 201
        assert res.json()["name"] == "Created User"
        assert res.json()["badge_id"] == "NFC-TEST-CREATE"

    def test_delete_attendee(self, client):
        # Create then delete
        data = {"badge_id": "NFC-DEL", "name": "Delete Me"}
        created = client.post("/api/attendees", json=data).json()
        res = client.delete(f"/api/attendees/{created['id']}")
        assert res.status_code == 200

    def test_delete_nonexistent(self, client):
        res = client.delete("/api/attendees/does-not-exist")
        assert res.status_code == 404


class TestCharacterEndpoints:
    """Tests for character CRUD endpoints."""

    def test_list_characters(self, client):
        res = client.get("/api/characters")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0

    def test_get_character(self, client):
        chars = client.get("/api/characters").json()
        if chars:
            char_id = chars[0]["id"]
            res = client.get(f"/api/characters/{char_id}")
            assert res.status_code == 200
            assert res.json()["id"] == char_id

    def test_create_character(self, client):
        data = {
            "name": "Test Oracle",
            "archetype": "oracle",
            "personality_prompt": "You are a test oracle.",
        }
        res = client.post("/api/characters", json=data)
        assert res.status_code == 201
        assert res.json()["name"] == "Test Oracle"
        assert res.json()["archetype"] == "oracle"


class TestEventEndpoints:
    """Tests for event configuration endpoints."""

    def test_get_event(self, client):
        res = client.get("/api/event")
        assert res.status_code == 200
        data = res.json()
        assert "event_name" in data
        assert "sessions" in data
        assert len(data["sessions"]) > 0


class TestScanEndpoint:
    """Tests for the badge scan endpoint."""

    def test_scan_valid(self, client):
        # Get a valid attendee badge and character
        attendees = client.get("/api/attendees").json()
        characters = client.get("/api/characters").json()

        if attendees and characters:
            res = client.post("/api/scan", json={
                "badge_id": attendees[0]["badge_id"],
                "character_id": characters[0]["id"],
                "interaction_type": "greeting",
            })
            assert res.status_code == 200
            data = res.json()
            assert "dialogue" in data
            assert "character_name" in data
            assert "attendee_name" in data
            assert data["attendee_name"] == attendees[0]["name"]

    def test_scan_invalid_badge(self, client):
        characters = client.get("/api/characters").json()
        if characters:
            res = client.post("/api/scan", json={
                "badge_id": "INVALID-BADGE",
                "character_id": characters[0]["id"],
            })
            assert res.status_code == 404

    def test_scan_invalid_character(self, client):
        attendees = client.get("/api/attendees").json()
        if attendees:
            res = client.post("/api/scan", json={
                "badge_id": attendees[0]["badge_id"],
                "character_id": "invalid-char-id",
            })
            assert res.status_code == 404

    def test_scan_quest_type(self, client):
        attendees = client.get("/api/attendees").json()
        characters = client.get("/api/characters").json()

        if attendees and characters:
            res = client.post("/api/scan", json={
                "badge_id": attendees[0]["badge_id"],
                "character_id": characters[0]["id"],
                "interaction_type": "quest",
            })
            assert res.status_code == 200
            assert res.json()["interaction_type"] == "quest"


class TestInteractionEndpoints:
    """Tests for interaction log endpoints."""

    def test_list_interactions(self, client):
        res = client.get("/api/interactions")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_interactions_after_scan(self, client):
        # Perform a scan first
        attendees = client.get("/api/attendees").json()
        characters = client.get("/api/characters").json()

        if attendees and characters:
            client.post("/api/scan", json={
                "badge_id": attendees[0]["badge_id"],
                "character_id": characters[0]["id"],
            })

            res = client.get("/api/interactions")
            assert res.status_code == 200
            assert len(res.json()) > 0


class TestWebSocket:
    """Tests for WebSocket endpoint."""

    def test_websocket_connect_valid(self, client):
        characters = client.get("/api/characters").json()
        if characters:
            with client.websocket_connect(f"/ws/actor/{characters[0]['id']}") as ws:
                data = ws.receive_json()
                assert data["type"] == "system"
                assert characters[0]["name"] in data["character_name"]

    def test_websocket_connect_invalid(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/actor/invalid-id") as ws:
                ws.receive_json()

    def test_websocket_ping(self, client):
        characters = client.get("/api/characters").json()
        if characters:
            with client.websocket_connect(f"/ws/actor/{characters[0]['id']}") as ws:
                ws.receive_json()  # welcome message
                ws.send_text('{"command": "ping"}')
                data = ws.receive_json()
                assert data["type"] == "pong"
