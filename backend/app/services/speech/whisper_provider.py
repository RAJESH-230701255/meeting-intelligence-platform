"""Whisper Speech-to-Text Provider — real transcription using OpenAI Whisper API."""

import logging

from app.core.config import get_settings
from app.services.speech.base import SpeechToTextService

logger = logging.getLogger(__name__)


class WhisperSpeechToTextService(SpeechToTextService):
    """Real speech-to-text using OpenAI Whisper API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.WHISPER_API_KEY or settings.OPENAI_API_KEY
        self.model = "whisper-1"

        if not self.api_key or self.api_key.startswith("YOUR_"):
            raise ValueError(
                "Whisper API key not configured. Set WHISPER_API_KEY or OPENAI_API_KEY in .env "
                "or use SPEECH_PROVIDER=mock for development."
            )

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file using OpenAI Whisper API."""
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="text",
                )

            return response

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise
