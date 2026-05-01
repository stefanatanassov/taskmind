from __future__ import annotations

from taskmind.config import get_settings
from taskmind.providers.http import OllamaProvider, OpenAICompatibleProvider
from taskmind.providers.mock import MockProvider


def get_provider():
    settings = get_settings()
    if settings.provider == "mock":
        return MockProvider()
    if settings.provider == "ollama":
        base_url = settings.provider_base_url or "http://localhost:11434"
        return OllamaProvider(base_url=base_url, model=settings.model)
    if settings.provider == "openai_compatible":
        base_url = settings.provider_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(base_url=base_url, model=settings.model, api_key=settings.provider_api_key)
    raise ValueError(f"Unsupported provider: {settings.provider}")

