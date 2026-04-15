"""
Tests for the FastAPI REST API endpoints.

Uses mocked Gemini and TTS services for isolated, fast testing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        data = client.get("/api/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "npc-actor-system"
        assert data["version"] == "1.0.0"
        assert "gemini_configured" in data
        assert "tts_mode" in data
        assert "cache_stats" in data

    def test_health_includes_cache_stats(self, client: TestClient) -> None:
        data = client.get("/api/health").json()
        cache = data["cache_stats"]
        assert "hits" in cache
        assert "misses" in cache
        assert "hit_rate_percent" in cache


class TestAttendeeEndpoints:
    """Tests for attendee CRUD endpoints."""

    def test_list_attendees(self, client: TestClient) -> None:
        res = client.get("/api/attendees")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0  # Demo data loaded

    def test_get_attendee_by_id(self, client: TestClient) -> None:
        attendees = client.get("/api/attendees").json()
        if attendees:
            att_id = attendees[0]["id"]
            res = client.get(f"/api/attendees/{att_id}")
            assert res.status_code == 200
            assert res.json()["id"] == att_id

    def test_get_nonexistent_attendee_returns_404(self, client: TestClient) -> None:
        res = client.get("/api/attendees/nonexistent-id")
        assert res.status_code == 404

    def test_create_attendee(self, client: TestClient) -> None:
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

    def test_create_attendee_validates_name(self, client: TestClient) -> None:
        """Empty name should fail validation."""
        data = {"badge_id": "NFC-EMPTY", "name": ""}
        res = client.post("/api/attendees", json=data)
        assert res.status_code == 422

    def test_create_attendee_validates_badge_length(self, client: TestClient) -> None:
        """Overly long badge ID should fail validation."""
        data = {"badge_id": "X" * 51, "name": "Test"}
        res = client.post("/api/attendees", json=data)
        assert res.status_code == 422

    def test_update_attendee(self, client: TestClient) -> None:
        attendees = client.get("/api/attendees").json()
        if attendees:
            att_id = attendees[0]["id"]
            res = client.put(
                f"/api/attendees/{att_id}",
                json={"name": "Updated Name"},
            )
            assert res.status_code == 200
            assert res.json()["name"] == "Updated Name"

    def test_update_nonexistent_attendee(self, client: TestClient) -> None:
        res = client.put(
            "/api/attendees/does-not-exist",
            json={"name": "Nope"},
        )
        assert res.status_code == 404

    def test_delete_attendee(self, client: TestClient) -> None:
        data = {"badge_id": "NFC-DEL", "name": "Delete Me"}
        created = client.post("/api/attendees", json=data).json()
        res = client.delete(f"/api/attendees/{created['id']}")
        assert res.status_code == 200
        assert res.json()["status"] == "deleted"

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        res = client.delete("/api/attendees/does-not-exist")
        assert res.status_code == 404


class TestCharacterEndpoints:
    """Tests for character CRUD endpoints."""

    def test_list_characters(self, client: TestClient) -> None:
        res = client.get("/api/characters")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0  # Demo data loaded

    def test_get_character_by_id(self, client: TestClient) -> None:
        chars = client.get("/api/characters").json()
        if chars:
            char_id = chars[0]["id"]
            res = client.get(f"/api/characters/{char_id}")
            assert res.status_code == 200
            assert res.json()["id"] == char_id

    def test_create_character(self, client: TestClient) -> None:
        data = {
            "name": "Test Oracle",
            "archetype": "oracle",
            "personality_prompt": "You are a test oracle who predicts test outcomes.",
        }
        res = client.post("/api/characters", json=data)
        assert res.status_code == 201
        assert res.json()["name"] == "Test Oracle"
        assert res.json()["archetype"] == "oracle"

    def test_create_character_validates_prompt_length(self, client: TestClient) -> None:
        """Short personality prompt should fail validation."""
        data = {
            "name": "Too Short",
            "personality_prompt": "Short",
        }
        res = client.post("/api/characters", json=data)
        assert res.status_code == 422

    def test_update_character(self, client: TestClient) -> None:
        chars = client.get("/api/characters").json()
        if chars:
            char_id = chars[0]["id"]
            res = client.put(
                f"/api/characters/{char_id}",
                json={"active": False},
            )
            assert res.status_code == 200

    def test_delete_character(self, client: TestClient) -> None:
        data = {
            "name": "Temporary",
            "personality_prompt": "A temporary character for deletion testing.",
        }
        created = client.post("/api/characters", json=data).json()
        res = client.delete(f"/api/characters/{created['id']}")
        assert res.status_code == 200


class TestEventEndpoint:
    """Tests for event configuration."""

    def test_get_event(self, client: TestClient) -> None:
        res = client.get("/api/event")
        assert res.status_code == 200
        data = res.json()
        assert "event_name" in data
        assert "sessions" in data
        assert len(data["sessions"]) > 0

    def test_event_has_complete_sessions(self, client: TestClient) -> None:
        data = client.get("/api/event").json()
        for session in data["sessions"]:
            assert "title" in session
            assert "speaker" in session
            assert "track" in session


class TestScanEndpoint:
    """Tests for the badge scan endpoint."""

    def test_scan_valid_badge(self, client: TestClient) -> None:
        attendees = client.get("/api/attendees").json()
        characters = client.get("/api/characters").json()
        if attendees and characters:
            res = client.post(
                "/api/scan",
                json={
                    "badge_id": attendees[0]["badge_id"],
                    "character_id": characters[0]["id"],
                    "interaction_type": "greeting",
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert "dialogue" in data
            assert "character_name" in data
            assert data["attendee_name"] == attendees[0]["name"]

    def test_scan_invalid_badge_returns_404(self, client: TestClient) -> None:
        characters = client.get("/api/characters").json()
        if characters:
            res = client.post(
                "/api/scan",
                json={
                    "badge_id": "INVALID-BADGE",
                    "character_id": characters[0]["id"],
                },
            )
            assert res.status_code == 404

    def test_scan_invalid_character_returns_404(self, client: TestClient) -> None:
        attendees = client.get("/api/attendees").json()
        if attendees:
            res = client.post(
                "/api/scan",
                json={
                    "badge_id": attendees[0]["badge_id"],
                    "character_id": "invalid-char-id",
                },
            )
            assert res.status_code == 404

    def test_scan_all_interaction_types(self, client: TestClient) -> None:
        """All interaction types should produce valid responses."""
        attendees = client.get("/api/attendees").json()
        characters = client.get("/api/characters").json()
        types = ["greeting", "quest", "advice", "riddle", "lore", "farewell"]
        if attendees and characters:
            for itype in types:
                res = client.post(
                    "/api/scan",
                    json={
                        "badge_id": attendees[0]["badge_id"],
                        "character_id": characters[0]["id"],
                        "interaction_type": itype,
                    },
                )
                assert res.status_code == 200, f"Failed for type: {itype}"
                assert res.json()["interaction_type"] == itype


class TestInteractionEndpoints:
    """Tests for interaction log endpoints."""

    def test_list_interactions(self, client: TestClient) -> None:
        res = client.get("/api/interactions")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_interactions_limit_parameter(self, client: TestClient) -> None:
        """Limit should clamp to valid range."""
        res = client.get("/api/interactions?limit=5")
        assert res.status_code == 200


class TestWebSocket:
    """Tests for WebSocket actor earpiece endpoint."""

    def test_websocket_connect_valid(self, client: TestClient) -> None:
        characters = client.get("/api/characters").json()
        if characters:
            with client.websocket_connect(f"/ws/actor/{characters[0]['id']}") as ws:
                data = ws.receive_json()
                assert data["type"] == "system"
                assert characters[0]["name"] in data["character_name"]

    def test_websocket_connect_invalid_returns_close(self, client: TestClient) -> None:
        with pytest.raises(Exception), client.websocket_connect("/ws/actor/invalid-id") as ws:  # noqa: B017
            ws.receive_json()

    def test_websocket_ping_pong(self, client: TestClient) -> None:
        characters = client.get("/api/characters").json()
        if characters:
            with client.websocket_connect(f"/ws/actor/{characters[0]['id']}") as ws:
                ws.receive_json()  # welcome
                ws.send_text('{"command": "ping"}')
                data = ws.receive_json()
                assert data["type"] == "pong"

    def test_websocket_status_command(self, client: TestClient) -> None:
        characters = client.get("/api/characters").json()
        if characters:
            with client.websocket_connect(f"/ws/actor/{characters[0]['id']}") as ws:
                ws.receive_json()  # welcome
                ws.send_text('{"command": "status"}')
                data = ws.receive_json()
                assert data["type"] == "system"
                assert characters[0]["name"] in data["character_name"]


class TestSecurityHeaders:
    """Tests that security headers are properly set."""

    def test_security_headers_present(self, client: TestClient) -> None:
        res = client.get("/api/health")
        headers = res.headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "1; mode=block"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_csp_header_present(self, client: TestClient) -> None:
        res = client.get("/api/health")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src" in csp
        assert "frame-ancestors 'none'" in csp

    def test_request_id_header(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert "x-request-id" in res.headers

    def test_response_time_header(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert "x-response-time" in res.headers
