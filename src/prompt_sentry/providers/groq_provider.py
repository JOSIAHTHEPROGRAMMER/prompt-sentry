"""Groq provider, talks to GroqCloud's OpenAI compatible chat API."""

from __future__ import annotations

from groq import Groq

from prompt_sentry.providers.base import Provider
from prompt_sentry.utils.config import ProviderConfig


class GroqProvider(Provider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = Groq(api_key=config.api_key, timeout=config.timeout_seconds)

    def _call_api(self, prompt: str) -> str:
        completion = self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("groq returned an empty response, likely filtered or truncated")
        return content