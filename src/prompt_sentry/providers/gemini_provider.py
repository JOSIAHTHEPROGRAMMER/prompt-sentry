"""Gemini provider, talks to Google's Gen AI SDK."""

from __future__ import annotations

from google import genai
from google.genai import types

from prompt_sentry.providers.base import Provider
from prompt_sentry.utils.config import ProviderConfig


class GeminiProvider(Provider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        # google's sdk wants timeout in milliseconds, everywhere else in
        # this project uses seconds, so the conversion happens right here
        self._client = genai.Client(
            api_key=config.api_key,
            http_options=types.HttpOptions(timeout=config.timeout_seconds * 1000),
        )

    def _call_api(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self.config.model,
            contents=prompt,
        )
        if response.text is None:
            raise ValueError("gemini returned an empty response, likely blocked by safety filters")
        return response.text