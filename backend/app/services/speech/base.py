"""Speech-to-Text Service — Abstract base class."""

from abc import ABC, abstractmethod


class SpeechToTextService(ABC):
    """Abstract base class for speech-to-text providers."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file.

        Returns:
            The transcribed text.
        """
        pass
