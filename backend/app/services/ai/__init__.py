"""AI Service factory — returns the configured AI provider."""

from app.core.config import get_settings
from app.services.ai.base import AIService


def get_ai_service() -> AIService:
    """Return the AI service based on the configured provider."""
    settings = get_settings()
    provider = settings.AI_PROVIDER.lower()

    if provider == "mock":
        from app.services.ai.mock_provider import MockAIService
        return MockAIService()
    elif provider == "openai":
        from app.services.ai.openai_provider import OpenAIService
        return OpenAIService()
    elif provider == "anthropic":
        from app.services.ai.anthropic_provider import AnthropicService
        return AnthropicService()
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Use 'mock', 'openai', or 'anthropic'.")
