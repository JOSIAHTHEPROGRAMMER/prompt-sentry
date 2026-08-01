"""Mistral provider, talks to La Plateforme's chat completions API."""

from __future__ import annotations

from mistralai.client import Mistral
from mistralai.client.models import AssistantMessage, SystemMessage, ToolMessage, UserMessage

from prompt_sentry.providers.base import Provider
from prompt_sentry.utils.config import ProviderConfig

MistralMessage = AssistantMessage | SystemMessage | ToolMessage | UserMessage


class MistralProvider(Provider):
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = Mistral(api_key=config.api_key)

    def _call_api(self, prompt: str) -> str:
        # unlike groq and gemini, mistral wants the timeout on the call
        # itself rather than at client construction, in milliseconds
        messages: list[MistralMessage] = [UserMessage(content=prompt)]
        completion = self._client.chat.complete(
            model=self.config.model,
            messages=messages,
            timeout_ms=self.config.timeout_seconds * 1000,
        )
        message = completion.choices[0].message
        if message is None or message.content is None:
            raise ValueError("mistral returned an empty response, likely filtered or truncated")
        return str(message.content)