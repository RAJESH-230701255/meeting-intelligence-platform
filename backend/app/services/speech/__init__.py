"""Speech-to-Text Service factory."""

from app.core.config import get_settings
from app.services.speech.base import SpeechToTextService


def get_speech_service() -> SpeechToTextService:
    """Return the speech-to-text service based on configuration."""
    settings = get_settings()
    provider = settings.SPEECH_PROVIDER.lower()

    if provider == "mock":
        from app.services.speech.mock_provider import MockSpeechToTextService
        return MockSpeechToTextService()
    elif provider == "whisper":
        from app.services.speech.whisper_provider import WhisperSpeechToTextService
        return WhisperSpeechToTextService()
    else:
        raise ValueError(f"Unknown speech provider: {provider}. Use 'mock' or 'whisper'.")
