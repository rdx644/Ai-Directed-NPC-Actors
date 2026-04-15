"""
Attendee management routes.

Provides CRUD operations for event attendees:
  - GET    /api/attendees          — List all attendees
  - GET    /api/attendees/{id}     — Get attendee by ID
  - POST   /api/attendees          — Register new attendee
  - PUT    /api/attendees/{id}     — Update attendee
  - DELETE /api/attendees/{id}     — Delete attendee
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.database import db
from backend.models import Attendee, AttendeeCreate, AttendeeUpdate
from backend.security import sanitize_string, sanitize_list, validate_badge_id, validate_email

logger = logging.getLogger("npc-system.routes.attendees")

router = APIRouter(prefix="/api/attendees", tags=["Attendees"])


@router.get("", response_model=list[dict[str, Any]])
async def list_attendees() -> list[dict[str, Any]]:
    """List all registered attendees."""
    attendees = db.list_attendees()
    return [a.model_dump() for a in attendees]


@router.get("/{attendee_id}")
async def get_attendee(attendee_id: str) -> dict[str, Any]:
    """Get a specific attendee by ID."""
    attendee = db.get_attendee(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return attendee.model_dump()


@router.post("", status_code=201)
async def create_attendee(data: AttendeeCreate) -> dict[str, Any]:
    """
    Register a new attendee.

    Validates and sanitizes all input fields before storage.
    """
    try:
        sanitized = AttendeeCreate(
            badge_id=validate_badge_id(data.badge_id),
            name=sanitize_string(data.name, "name"),
            email=validate_email(data.email) if data.email else None,
            company=sanitize_string(data.company, "company") if data.company else None,
            role=sanitize_string(data.role, "role") if data.role else None,
            interests=sanitize_list(data.interests, "interests") if data.interests else [],
            sessions_attended=(
                sanitize_list(data.sessions_attended, "sessions")
                if data.sessions_attended else []
            ),
            notes=sanitize_string(data.notes, "notes") if data.notes else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    attendee = Attendee(**sanitized.model_dump())
    created = db.create_attendee(attendee)
    logger.info(f"Created attendee: {created.id} ({created.name})")
    return created.model_dump()


@router.put("/{attendee_id}")
async def update_attendee(attendee_id: str, data: AttendeeUpdate) -> dict[str, Any]:
    """Update an existing attendee with validated data."""
    update_data = data.model_dump(exclude_unset=True)

    # Sanitize provided fields
    if "name" in update_data and update_data["name"]:
        update_data["name"] = sanitize_string(update_data["name"], "name")
    if "email" in update_data and update_data["email"]:
        try:
            update_data["email"] = validate_email(update_data["email"])
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    updated = db.update_attendee(attendee_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Attendee not found")
    logger.info(f"Updated attendee: {attendee_id}")
    return updated.model_dump()


@router.delete("/{attendee_id}")
async def delete_attendee(attendee_id: str) -> dict[str, str]:
    """Delete an attendee."""
    if not db.delete_attendee(attendee_id):
        raise HTTPException(status_code=404, detail="Attendee not found")
    logger.info(f"Deleted attendee: {attendee_id}")
    return {"status": "deleted", "id": attendee_id}
