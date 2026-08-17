"""Mock Speech-to-Text Provider — returns canonical sample transcript."""

from app.services.speech.base import SpeechToTextService


class MockSpeechToTextService(SpeechToTextService):
    """Mock speech-to-text that returns deterministic sample transcript."""

    SAMPLE_TRANSCRIPT = (
        "Rajesh will prepare the project report by Friday. "
        "Priya will review the report on Monday. "
        "The team decided to complete testing before the next meeting."
    )

    def transcribe(self, audio_path: str) -> str:
        """Return the canonical sample transcript regardless of input."""
        return self.SAMPLE_TRANSCRIPT
