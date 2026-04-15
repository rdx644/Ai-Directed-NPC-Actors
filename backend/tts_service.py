"""
Google Cloud Text-to-Speech integration for NPC Actor System.

Converts generated NPC dialogue into audio that can be streamed to the
actor's earpiece. Supports both Google Cloud TTS and browser-based
Web Speech API fallback.
"""

from __future__ import annotations

import base64
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Google Cloud TTS
# ──────────────────────────────────────────────

_tts_client = None


def _get_tts_client():
    """Lazy-initialize the Google Cloud TTS client."""
    global _tts_client
    if _tts_client is None and settings.use_google_tts:
        try:
            from google.cloud import texttospeech

            _tts_client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS client initialized")
        except Exception as e:
            logger.warning(f"Google Cloud TTS init failed: {e}")
            _tts_client = None
    return _tts_client


async def synthesize_speech(
    text: str,
    voice_name: str = "en-US-Neural2-D",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
) -> str | None:
    """
    Convert text to speech using Google Cloud TTS.

    Args:
        text: The dialogue text to synthesize.
        voice_name: Google Cloud TTS voice identifier.
        speaking_rate: Speed of speech (0.25 to 4.0).
        pitch: Voice pitch in semitones (-20.0 to 20.0).

    Returns:
        Base64-encoded MP3 audio string, or None if TTS is unavailable.
    """
    if not settings.use_google_tts:
        logger.debug("Google TTS disabled — frontend will use Web Speech API")
        return None

    client = _get_tts_client()
    if not client:
        return None

    try:
        from google.cloud import texttospeech

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Parse language code from voice name (e.g., "en-US-Neural2-D" → "en-US")
        lang_code = "-".join(voice_name.split("-")[:2])

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            effects_profile_id=["headphone-class-device"],
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )

        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        logger.info(f"TTS synthesized {len(response.audio_content)} bytes of audio")
        return audio_b64

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return None


async def list_available_voices(language_code: str = "en-US") -> list[dict]:
    """
    List available TTS voices for a given language.

    Returns:
        List of voice dictionaries with name, gender, and language info.
    """
    client = _get_tts_client()
    if not client:
        # Return default set when TTS is unavailable
        return [
            {"name": "en-US-Neural2-A", "gender": "MALE", "description": "Male voice A"},
            {"name": "en-US-Neural2-D", "gender": "MALE", "description": "Male voice D (deep)"},
            {"name": "en-US-Neural2-F", "gender": "FEMALE", "description": "Female voice F"},
            {"name": "en-US-Neural2-J", "gender": "MALE", "description": "Male voice J"},
        ]

    try:
        from google.cloud import texttospeech

        response = client.list_voices(language_code=language_code)
        voices = []
        for voice in response.voices:
            if "Neural2" in voice.name or "Studio" in voice.name:
                voices.append(
                    {
                        "name": voice.name,
                        "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                        "description": f"{voice.name} ({texttospeech.SsmlVoiceGender(voice.ssml_gender).name})",
                    }
                )
        return voices
    except Exception as e:
        logger.error(f"Failed to list voices: {e}")
        return []
