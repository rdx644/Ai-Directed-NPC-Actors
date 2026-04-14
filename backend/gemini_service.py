"""
Google Gemini API integration for NPC dialogue generation.

Generates contextual, in-character dialogue based on:
  - NPC character personality prompt
  - Attendee profile (name, interests, sessions attended)
  - Event schedule context
  - Interaction type (greeting, quest, advice, riddle, lore, farewell)
"""

from __future__ import annotations
import logging
from typing import Optional

from backend.config import settings
from backend.models import (
    Attendee, Character, EventConfig, InteractionType, DialogueResponse
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Gemini Client Setup
# ──────────────────────────────────────────────

_model = None


def _get_model():
    """Lazy-initialize the Gemini generative model."""
    global _model
    if _model is None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            _model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.85,
                    "top_p": 0.92,
                    "top_k": 40,
                    "max_output_tokens": 512,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ],
            )
            logger.info("Gemini model initialized (gemini-2.0-flash)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            _model = None
    return _model


# ──────────────────────────────────────────────
#  Prompt Engineering
# ──────────────────────────────────────────────

def _build_context_prompt(
    character: Character,
    attendee: Attendee,
    event: EventConfig,
    interaction_type: InteractionType,
    custom_context: Optional[str] = None,
) -> str:
    """Build the complete prompt with full context for Gemini."""

    # Compile sessions the attendee hasn't visited yet (for quest suggestions)
    attended_titles = set(attendee.sessions_attended)
    unattended = [
        s for s in event.sessions
        if s.title not in attended_titles
    ]
    unattended_info = "\n".join(
        f"  - '{s.title}' by {s.speaker} ({s.track}, {s.time_slot}, {s.room})"
        for s in unattended[:5]
    )

    attended_info = ", ".join(attendee.sessions_attended) if attendee.sessions_attended else "none yet"
    interests_info = ", ".join(attendee.interests) if attendee.interests else "general technology"

    # Interaction-specific instructions
    interaction_instructions = {
        InteractionType.GREETING: (
            "Greet the attendee warmly in character. Acknowledge something about their "
            "interests or past sessions to show you 'know' them. Be welcoming but mysterious."
        ),
        InteractionType.QUEST: (
            "Assign the attendee a personalized QUEST. The quest should connect their current "
            "interests to a session they haven't attended yet. Frame it dramatically in character. "
            "Include a specific objective and a reward (XP points). Format the quest name on its own line "
            "prefixed with 'QUEST:'"
        ),
        InteractionType.ADVICE: (
            "Give the attendee personalized career or learning advice based on their interests "
            "and sessions. Frame it as wisdom from your character's perspective. Be insightful "
            "and specific to their field."
        ),
        InteractionType.RIDDLE: (
            "Pose a clever riddle or puzzle related to the attendee's interests. The riddle "
            "should be solvable and fun. After stating the riddle, give a subtle hint."
        ),
        InteractionType.LORE: (
            "Share a piece of 'lore' — a fictional story from your character's world that "
            "metaphorically relates to the attendee's interests or the event theme. Make it "
            "entertaining and short."
        ),
        InteractionType.FAREWELL: (
            "Bid the attendee farewell in character. Reference something from your conversation "
            "or their interests. Leave them with a memorable parting line or prophecy."
        ),
    }

    instruction = interaction_instructions.get(
        interaction_type, interaction_instructions[InteractionType.GREETING]
    )

    prompt = f"""### CHARACTER IDENTITY
{character.personality_prompt}

Catchphrase: "{character.catchphrase}"

### ATTENDEE INFORMATION
- Name: {attendee.name}
- Company: {attendee.company or 'Unknown'}
- Role: {attendee.role or 'Attendee'}
- Interests: {interests_info}
- Sessions Attended: {attended_info}
- XP Points: {attendee.xp_points}
- Previous Interactions: {attendee.interaction_count}

### EVENT CONTEXT
- Event: {event.event_name}
- Theme: {event.event_theme}
- Available Sessions (not yet attended):
{unattended_info if unattended_info else '  (All sessions attended — congratulate them!)'}

### YOUR TASK
Interaction Type: {interaction_type.value.upper()}
{instruction}

### OUTPUT FORMAT
Respond with ONLY what the actor should say aloud. Do NOT include stage directions in parentheses,
action descriptions, or meta-commentary. Write 2-3 natural sentences the actor can deliver.
If this is a QUEST, put the quest name on a separate line starting with "QUEST: ".
{f"Additional context: {custom_context}" if custom_context else ""}"""

    return prompt


# ──────────────────────────────────────────────
#  Fallback Dialogue (when Gemini is unavailable)
# ──────────────────────────────────────────────

FALLBACK_DIALOGUES = {
    InteractionType.GREETING: [
        "Ah, {name}, the stars foretold your arrival! I sense great curiosity about {interest} within you.",
        "Welcome, {name}! Your journey through the realms of {interest} has brought you to me.",
    ],
    InteractionType.QUEST: [
        "Listen well, {name}! I have a quest for you. Seek the wisdom hidden in the next {interest} session. "
        "QUEST: Attend a session you haven't explored yet and return with new knowledge. Reward: 50 XP!",
    ],
    InteractionType.ADVICE: [
        "{name}, the path of {interest} is long but rewarding. Focus on the fundamentals, "
        "and the advanced patterns will reveal themselves.",
    ],
    InteractionType.RIDDLE: [
        "A riddle for you, {name}: I have keys but no locks, space but no room. What am I? "
        "Hint: You use me every day in your work with {interest}...",
    ],
    InteractionType.LORE: [
        "Long ago, in the digital realm, a great hero mastered {interest} and changed the world forever. "
        "Perhaps, {name}, that hero is you.",
    ],
    InteractionType.FAREWELL: [
        "Until we meet again, {name}. May your code compile on the first try and your {interest} "
        "knowledge grow ever deeper!",
    ],
}


def _get_fallback_dialogue(
    attendee: Attendee,
    interaction_type: InteractionType,
) -> str:
    """Generate fallback dialogue when Gemini API is unavailable."""
    import random
    templates = FALLBACK_DIALOGUES.get(
        interaction_type, FALLBACK_DIALOGUES[InteractionType.GREETING]
    )
    template = random.choice(templates)
    interest = attendee.interests[0] if attendee.interests else "technology"
    return template.format(name=attendee.name, interest=interest)


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

async def generate_dialogue(
    character: Character,
    attendee: Attendee,
    event: EventConfig,
    interaction_type: InteractionType = InteractionType.GREETING,
    custom_context: Optional[str] = None,
) -> DialogueResponse:
    """
    Generate NPC dialogue using Google Gemini API.

    Falls back to template-based dialogue if Gemini is unavailable.

    Returns:
        DialogueResponse with generated dialogue and metadata.
    """
    model = _get_model()

    dialogue_text = ""
    quest_text = None

    if model and settings.gemini_api_key:
        try:
            prompt = _build_context_prompt(
                character, attendee, event, interaction_type, custom_context
            )
            response = model.generate_content(prompt)
            dialogue_text = response.text.strip()
            logger.info(
                f"Gemini generated dialogue for {attendee.name} ↔ {character.name} "
                f"({interaction_type.value})"
            )
        except Exception as e:
            logger.warning(f"Gemini generation failed: {e}. Using fallback.")
            dialogue_text = _get_fallback_dialogue(attendee, interaction_type)
    else:
        logger.info("Gemini unavailable — using fallback dialogue")
        dialogue_text = _get_fallback_dialogue(attendee, interaction_type)

    # Extract quest if present
    if "QUEST:" in dialogue_text:
        lines = dialogue_text.split("\n")
        quest_lines = [l for l in lines if l.strip().startswith("QUEST:")]
        if quest_lines:
            quest_text = quest_lines[0].replace("QUEST:", "").strip()

    # Generate stage direction for the actor
    stage_directions = {
        InteractionType.GREETING: "Approach warmly, make eye contact, gesture grandly.",
        InteractionType.QUEST: "Speak with gravitas, lean in conspiratorially.",
        InteractionType.ADVICE: "Nod wisely, place hand on heart or chin.",
        InteractionType.RIDDLE: "Raise an eyebrow, pause dramatically after the riddle.",
        InteractionType.LORE: "Look into the distance, use sweeping hand gestures.",
        InteractionType.FAREWELL: "Bow slightly, wave mystically.",
    }

    return DialogueResponse(
        character_name=character.name,
        attendee_name=attendee.name,
        dialogue=dialogue_text,
        interaction_type=interaction_type,
        quest=quest_text,
        stage_direction=stage_directions.get(interaction_type, "Stay in character."),
    )
