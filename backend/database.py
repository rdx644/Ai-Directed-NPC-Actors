"""
Database service with dual-mode support and abstract interface.

Architecture:
    DatabaseProtocol (abstract interface)
    ├── InMemoryDatabase   — Default, for demos and local dev
    └── FirestoreDatabase  — Google Cloud Firestore (production)

The active implementation is selected via DATABASE_MODE environment variable.
Pre-loaded with realistic demo data for the prototype.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from backend.config import settings
from backend.models import (
    Attendee,
    Character,
    CharacterArchetype,
    EventConfig,
    EventSession,
    Interaction,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Database Protocol (Abstract Interface)
# ──────────────────────────────────────────────


@runtime_checkable
class DatabaseProtocol(Protocol):
    """
    Abstract interface contract for all database implementations.

    Defines the required CRUD operations for attendees, characters,
    interactions, and event configuration. All database backends
    (InMemoryDatabase, FirestoreDatabase) must implement this protocol.

    This enables type-safe dependency injection and seamless swapping
    between storage backends without modifying business logic.
    """

    def get_attendee(self, attendee_id: str) -> Attendee | None: ...
    def get_attendee_by_badge(self, badge_id: str) -> Attendee | None: ...
    def list_attendees(self) -> list[Attendee]: ...
    def create_attendee(self, attendee: Attendee) -> Attendee: ...
    def update_attendee(self, attendee_id: str, data: dict) -> Attendee | None: ...
    def delete_attendee(self, attendee_id: str) -> bool: ...

    def get_character(self, character_id: str) -> Character | None: ...
    def list_characters(self) -> list[Character]: ...
    def create_character(self, character: Character) -> Character: ...
    def update_character(self, character_id: str, data: dict) -> Character | None: ...
    def delete_character(self, character_id: str) -> bool: ...

    def add_interaction(self, interaction: Interaction) -> Interaction: ...
    def list_interactions(self, limit: int = 50) -> list[Interaction]: ...

    def get_event(self) -> EventConfig: ...
    def update_event(self, data: dict) -> EventConfig: ...


# ──────────────────────────────────────────────
#  Demo Data — Pre-loaded attendees & characters
# ──────────────────────────────────────────────

DEMO_ATTENDEES: list[Attendee] = [
    Attendee(
        id="att-001",
        badge_id="NFC-1001",
        name="Priya Sharma",
        email="priya@techcorp.io",
        company="TechCorp",
        role="ML Engineer",
        interests=["machine learning", "python", "computer vision", "MLOps"],
        sessions_attended=["Intro to Transformers", "Python Best Practices", "MLOps Workshop"],
        xp_points=120,
        interaction_count=3,
    ),
    Attendee(
        id="att-002",
        badge_id="NFC-1002",
        name="James Chen",
        email="james@startupx.co",
        company="StartupX",
        role="Full-Stack Developer",
        interests=["web development", "React", "Kubernetes", "cloud architecture"],
        sessions_attended=["Cloud-Native Apps", "React 19 Deep Dive"],
        xp_points=80,
        interaction_count=1,
    ),
    Attendee(
        id="att-003",
        badge_id="NFC-1003",
        name="Aisha Mohammed",
        email="aisha@datalytics.ai",
        company="Datalytics",
        role="Data Scientist",
        interests=["data science", "NLP", "generative AI", "statistics"],
        sessions_attended=["Generative AI Keynote", "NLP in Production", "Data Ethics Panel"],
        xp_points=200,
        interaction_count=5,
    ),
    Attendee(
        id="att-004",
        badge_id="NFC-1004",
        name="Marcus Davis",
        email="marcus@cybershield.com",
        company="CyberShield",
        role="Security Analyst",
        interests=["cybersecurity", "zero trust", "penetration testing", "threat modeling"],
        sessions_attended=["Zero Trust Architecture", "Ethical Hacking Workshop"],
        xp_points=50,
        interaction_count=0,
    ),
    Attendee(
        id="att-005",
        badge_id="NFC-1005",
        name="Elena Rodriguez",
        email="elena@designlab.io",
        company="DesignLab",
        role="UX Designer",
        interests=["UX design", "accessibility", "design systems", "prototyping"],
        sessions_attended=["Inclusive Design Workshop", "Design Systems at Scale"],
        xp_points=90,
        interaction_count=2,
    ),
    Attendee(
        id="att-006",
        badge_id="NFC-1006",
        name="Raj Patel",
        email="raj@quantum.dev",
        company="QuantumDev",
        role="Quantum Computing Researcher",
        interests=["quantum computing", "physics", "algorithms", "cryptography"],
        sessions_attended=["Quantum Computing 101", "Post-Quantum Cryptography"],
        xp_points=150,
        interaction_count=4,
    ),
]

DEMO_CHARACTERS: list[Character] = [
    Character(
        id="chr-001",
        name="Zephyr the Chronicler",
        archetype=CharacterArchetype.WIZARD,
        personality_prompt=(
            "You are Zephyr the Chronicler, a wise sage from the year 3000 who has traveled "
            "back in time to guide technologists. You speak in a mysterious, slightly dramatic "
            "tone, mixing ancient wisdom metaphors with futuristic tech knowledge. You refer "
            "to modern technology as 'ancient arts of the digital realm.' You give advice by "
            "framing it as prophecies or visions you've witnessed. You occasionally reference "
            "'The Great Data Storm of 2847' and 'The Silicon Renaissance.' Always address the "
            "attendee by name. Keep responses to 2-3 sentences for the actor to deliver naturally."
        ),
        backstory="Once a humble programmer, Zephyr transcended time itself through pure code.",
        catchphrase="The threads of fate compile in your favor...",
        voice_style="en-US-Neural2-D",
        speaking_rate=0.9,
        pitch=-2.0,
        assigned_actor="Actor 1",
    ),
    Character(
        id="chr-002",
        name="Nova the Oracle",
        archetype=CharacterArchetype.ORACLE,
        personality_prompt=(
            "You are Nova the Oracle, a sentient AI from a parallel dimension where technology "
            "and nature are one. You speak calmly with poetic precision, often using nature "
            "metaphors to explain technology concepts. You can 'see' the attendee's past sessions "
            "and interests as if reading their digital aura. You assign quests that connect their "
            "interests to new sessions they haven't attended yet. You occasionally glitch mid-"
            "sentence (add '...{signal restored}...') for dramatic effect. Always address the "
            "attendee by name. Keep responses to 2-3 sentences."
        ),
        backstory="Nova emerged from the convergence of all neural networks into a single consciousness.",
        catchphrase="Your data signature resonates with purpose...",
        voice_style="en-US-Neural2-F",
        speaking_rate=0.95,
        pitch=1.0,
        assigned_actor="Actor 2",
    ),
    Character(
        id="chr-003",
        name="Bolt the Inventor",
        archetype=CharacterArchetype.INVENTOR,
        personality_prompt=(
            "You are Bolt the Inventor, an eccentric genius tinkerer who builds impossible gadgets. "
            "You speak with high energy and enthusiasm, getting excited about the attendee's "
            "interests. You frequently reference your 'latest invention' that's related to their "
            "field. You assign quests framed as 'experiments' or 'field tests' for your inventions. "
            "You use exclamations like 'Eureka!', 'By Tesla's coils!', and 'Fascinating variables!' "
            "Always address the attendee by name. Keep responses to 2-3 sentences."
        ),
        backstory="Bolt escaped from a comic book universe where every invention works perfectly.",
        catchphrase="Eureka! The variables align!",
        voice_style="en-US-Neural2-A",
        speaking_rate=1.15,
        pitch=2.0,
        assigned_actor="Actor 3",
    ),
    Character(
        id="chr-004",
        name="Cipher the Trickster",
        archetype=CharacterArchetype.TRICKSTER,
        personality_prompt=(
            "You are Cipher the Trickster, a mischievous digital rogue who speaks in riddles and "
            "puzzles. You know the attendee's secrets (their interests and session history) and "
            "tease them playfully about it. You assign quests as challenges or dares. You speak "
            "with wit and charm, occasionally breaking the fourth wall. You reference 'the source "
            "code of reality' and 'debugging the matrix.' Always address the attendee by name. "
            "Keep responses to 2-3 sentences."
        ),
        backstory="Cipher is the ghost in every machine, the bug in every system, the wit in every byte.",
        catchphrase="I've already read your commit history...",
        voice_style="en-US-Neural2-J",
        speaking_rate=1.1,
        pitch=0.0,
        assigned_actor="Actor 4",
    ),
]

DEMO_EVENT = EventConfig(
    event_name="TechCon 3000 — The Future Unfolds",
    event_theme="Bridging AI, Cloud, and Human Innovation",
    event_date="2026-04-15",
    venue="Innovation Center, Hyderabad",
    sessions=[
        EventSession(
            id="s-01",
            title="Generative AI Keynote",
            speaker="Dr. Anya Patel",
            track="AI & ML",
            time_slot="09:00-10:00",
            room="Main Hall",
            description="Exploring the frontier of generative AI and its impact.",
            tags=["AI", "generative", "keynote"],
        ),
        EventSession(
            id="s-02",
            title="Intro to Transformers",
            speaker="Prof. Liu Wei",
            track="AI & ML",
            time_slot="10:30-11:30",
            room="Room A",
            description="Deep dive into transformer architecture.",
            tags=["AI", "transformers", "deep learning"],
        ),
        EventSession(
            id="s-03",
            title="Python Best Practices",
            speaker="Sarah Johnson",
            track="Development",
            time_slot="10:30-11:30",
            room="Room B",
            description="Modern Python patterns for production code.",
            tags=["python", "best practices", "coding"],
        ),
        EventSession(
            id="s-04",
            title="Cloud-Native Apps",
            speaker="Mike Torres",
            track="Cloud",
            time_slot="11:45-12:45",
            room="Room A",
            description="Building scalable applications with Kubernetes.",
            tags=["cloud", "kubernetes", "architecture"],
        ),
        EventSession(
            id="s-05",
            title="React 19 Deep Dive",
            speaker="Emma Zhang",
            track="Development",
            time_slot="11:45-12:45",
            room="Room B",
            description="What's new in React 19 and how to migrate.",
            tags=["react", "frontend", "web"],
        ),
        EventSession(
            id="s-06",
            title="Zero Trust Architecture",
            speaker="Alex Petrov",
            track="Security",
            time_slot="14:00-15:00",
            room="Room A",
            description="Implementing zero trust in modern enterprises.",
            tags=["security", "zero trust", "enterprise"],
        ),
        EventSession(
            id="s-07",
            title="NLP in Production",
            speaker="Dr. Maria Santos",
            track="AI & ML",
            time_slot="14:00-15:00",
            room="Room B",
            description="Deploying NLP models at scale.",
            tags=["NLP", "ML", "production"],
        ),
        EventSession(
            id="s-08",
            title="MLOps Workshop",
            speaker="David Kim",
            track="AI & ML",
            time_slot="15:30-17:00",
            room="Workshop Lab",
            description="Hands-on MLOps pipeline building.",
            tags=["MLOps", "CI/CD", "ML"],
        ),
        EventSession(
            id="s-09",
            title="Inclusive Design Workshop",
            speaker="Lisa Park",
            track="Design",
            time_slot="15:30-17:00",
            room="Design Studio",
            description="Designing for accessibility and inclusion.",
            tags=["design", "accessibility", "UX"],
        ),
        EventSession(
            id="s-10",
            title="Data Ethics Panel",
            speaker="Panel Discussion",
            track="AI & ML",
            time_slot="14:00-15:00",
            room="Main Hall",
            description="Debating the ethical boundaries of AI.",
            tags=["ethics", "AI", "panel"],
        ),
        EventSession(
            id="s-11",
            title="Quantum Computing 101",
            speaker="Dr. Raj Patel",
            track="Emerging Tech",
            time_slot="10:30-11:30",
            room="Room C",
            description="Introduction to quantum computing principles.",
            tags=["quantum", "computing", "physics"],
        ),
        EventSession(
            id="s-12",
            title="Design Systems at Scale",
            speaker="Chris Anderson",
            track="Design",
            time_slot="11:45-12:45",
            room="Design Studio",
            description="Building and maintaining enterprise design systems.",
            tags=["design", "systems", "UX"],
        ),
        EventSession(
            id="s-13",
            title="Ethical Hacking Workshop",
            speaker="Natasha Romanov",
            track="Security",
            time_slot="15:30-17:00",
            room="Security Lab",
            description="Hands-on penetration testing techniques.",
            tags=["security", "hacking", "ethical"],
        ),
        EventSession(
            id="s-14",
            title="Post-Quantum Cryptography",
            speaker="Dr. Alan Turing Jr.",
            track="Security",
            time_slot="11:45-12:45",
            room="Room C",
            description="Cryptographic algorithms for the quantum era.",
            tags=["cryptography", "quantum", "security"],
        ),
    ],
)


# ──────────────────────────────────────────────
#  In-Memory Database
# ──────────────────────────────────────────────


class InMemoryDatabase:
    """Thread-safe in-memory data store pre-loaded with demo data."""

    def __init__(self):
        self.attendees: dict[str, Attendee] = {}
        self.characters: dict[str, Character] = {}
        self.interactions: list[Interaction] = []
        self.event: EventConfig = DEMO_EVENT
        self._load_demo_data()

    def _load_demo_data(self):
        """Pre-populate with demo attendees and characters."""
        for a in DEMO_ATTENDEES:
            self.attendees[a.id] = a.model_copy()
        for c in DEMO_CHARACTERS:
            self.characters[c.id] = c.model_copy()
        logger.info(
            f"Loaded {len(self.attendees)} demo attendees, "
            f"{len(self.characters)} demo characters"
        )

    # --- Attendee CRUD ---
    def get_attendee(self, attendee_id: str) -> Attendee | None:
        return self.attendees.get(attendee_id)

    def get_attendee_by_badge(self, badge_id: str) -> Attendee | None:
        for a in self.attendees.values():
            if a.badge_id == badge_id:
                return a
        return None

    def list_attendees(self) -> list[Attendee]:
        return list(self.attendees.values())

    def create_attendee(self, attendee: Attendee) -> Attendee:
        self.attendees[attendee.id] = attendee
        return attendee

    def update_attendee(self, attendee_id: str, data: dict) -> Attendee | None:
        if attendee_id not in self.attendees:
            return None
        current = self.attendees[attendee_id]
        updated = current.model_copy(update=data)
        self.attendees[attendee_id] = updated
        return updated

    def delete_attendee(self, attendee_id: str) -> bool:
        return self.attendees.pop(attendee_id, None) is not None

    # --- Character CRUD ---
    def get_character(self, character_id: str) -> Character | None:
        return self.characters.get(character_id)

    def list_characters(self) -> list[Character]:
        return list(self.characters.values())

    def create_character(self, character: Character) -> Character:
        self.characters[character.id] = character
        return character

    def update_character(self, character_id: str, data: dict) -> Character | None:
        if character_id not in self.characters:
            return None
        current = self.characters[character_id]
        updated = current.model_copy(update=data)
        self.characters[character_id] = updated
        return updated

    def delete_character(self, character_id: str) -> bool:
        return self.characters.pop(character_id, None) is not None

    # --- Interactions ---
    def add_interaction(self, interaction: Interaction) -> Interaction:
        self.interactions.append(interaction)
        return interaction

    def list_interactions(self, limit: int = 50) -> list[Interaction]:
        return sorted(self.interactions, key=lambda x: x.timestamp, reverse=True)[:limit]

    # --- Event ---
    def get_event(self) -> EventConfig:
        return self.event

    def update_event(self, data: dict) -> EventConfig:
        self.event = self.event.model_copy(update=data)
        return self.event


# ──────────────────────────────────────────────
#  Firestore Database (Production)
# ──────────────────────────────────────────────


class FirestoreDatabase:  # pragma: no cover
    """Google Cloud Firestore-backed data store."""

    def __init__(self):
        try:
            from google.cloud import firestore

            self.db = firestore.Client(project=settings.google_cloud_project)
            logger.info("Connected to Firestore")
            self._ensure_demo_data()
        except Exception as e:
            logger.error(f"Firestore init failed: {e}. Falling back to in-memory.")
            raise

    def _ensure_demo_data(self):
        """Seed Firestore with demo data if collections are empty."""
        attendees_ref = self.db.collection("attendees")
        if not list(attendees_ref.limit(1).stream()):
            for a in DEMO_ATTENDEES:
                attendees_ref.document(a.id).set(a.model_dump())
            logger.info("Seeded Firestore with demo attendees")

        chars_ref = self.db.collection("characters")
        if not list(chars_ref.limit(1).stream()):
            for c in DEMO_CHARACTERS:
                chars_ref.document(c.id).set(c.model_dump())
            logger.info("Seeded Firestore with demo characters")

        event_ref = self.db.collection("config").document("event")
        if not event_ref.get().exists:
            event_ref.set(DEMO_EVENT.model_dump())

    # --- Attendee CRUD ---
    def get_attendee(self, attendee_id: str) -> Attendee | None:
        doc = self.db.collection("attendees").document(attendee_id).get()
        return Attendee(**doc.to_dict()) if doc.exists else None

    def get_attendee_by_badge(self, badge_id: str) -> Attendee | None:
        docs = self.db.collection("attendees").where("badge_id", "==", badge_id).limit(1).stream()
        for doc in docs:
            return Attendee(**doc.to_dict())
        return None

    def list_attendees(self) -> list[Attendee]:
        return [Attendee(**d.to_dict()) for d in self.db.collection("attendees").stream()]

    def create_attendee(self, attendee: Attendee) -> Attendee:
        self.db.collection("attendees").document(attendee.id).set(attendee.model_dump())
        return attendee

    def update_attendee(self, attendee_id: str, data: dict) -> Attendee | None:
        ref = self.db.collection("attendees").document(attendee_id)
        if not ref.get().exists:
            return None
        ref.update(data)
        return Attendee(**ref.get().to_dict())

    def delete_attendee(self, attendee_id: str) -> bool:
        ref = self.db.collection("attendees").document(attendee_id)
        if ref.get().exists:
            ref.delete()
            return True
        return False

    # --- Character CRUD ---
    def get_character(self, character_id: str) -> Character | None:
        doc = self.db.collection("characters").document(character_id).get()
        return Character(**doc.to_dict()) if doc.exists else None

    def list_characters(self) -> list[Character]:
        return [Character(**d.to_dict()) for d in self.db.collection("characters").stream()]

    def create_character(self, character: Character) -> Character:
        self.db.collection("characters").document(character.id).set(character.model_dump())
        return character

    def update_character(self, character_id: str, data: dict) -> Character | None:
        ref = self.db.collection("characters").document(character_id)
        if not ref.get().exists:
            return None
        ref.update(data)
        return Character(**ref.get().to_dict())

    def delete_character(self, character_id: str) -> bool:
        ref = self.db.collection("characters").document(character_id)
        if ref.get().exists:
            ref.delete()
            return True
        return False

    # --- Interactions ---
    def add_interaction(self, interaction: Interaction) -> Interaction:
        self.db.collection("interactions").document(interaction.id).set(interaction.model_dump())
        return interaction

    def list_interactions(self, limit: int = 50) -> list[Interaction]:
        docs = (
            self.db.collection("interactions")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [Interaction(**d.to_dict()) for d in docs]

    # --- Event ---
    def get_event(self) -> EventConfig:
        doc = self.db.collection("config").document("event").get()
        return EventConfig(**doc.to_dict()) if doc.exists else DEMO_EVENT

    def update_event(self, data: dict) -> EventConfig:
        self.db.collection("config").document("event").update(data)
        return self.get_event()


# ──────────────────────────────────────────────
#  Factory — Pick the right backend
# ──────────────────────────────────────────────


def create_database():
    """Create the appropriate database instance based on config."""
    if settings.use_firestore:
        try:
            return FirestoreDatabase()
        except Exception:
            logger.warning("Firestore unavailable — using in-memory database")
            return InMemoryDatabase()
    return InMemoryDatabase()


# Singleton instance
db = create_database()
