import pytest
from app.core.config import get_settings
from app.services.ai.mock_provider import MockAIService
from app.schemas.analysis import MeetingAnalysis


def test_mock_provider():
    provider = MockAIService()
    transcript = "Rajesh will prepare the report by Friday."
    result = provider.analyze_transcript(transcript)

    assert isinstance(result, MeetingAnalysis)
    assert len(result.action_items) > 0
    assert result.action_items[0].title != ""


def test_openai_provider_missing_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="OpenAI API key not configured"):
        from app.services.ai.openai_provider import OpenAIService
        OpenAIService()


def test_anthropic_provider_missing_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="Anthropic API key not configured"):
        from app.services.ai.anthropic_provider import AnthropicService
        AnthropicService()

