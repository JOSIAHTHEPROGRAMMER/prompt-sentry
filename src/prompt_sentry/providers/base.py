"""Shared contract every LLM provider implements.

Nothing outside this file should care whether a response came from Groq,
Gemini, or Mistral. They all return the same ProviderResponse shape.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from prompt_sentry.utils.config import ProviderConfig


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    prompt: str
    text: str
    latency_seconds: float
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class Provider(ABC):
    """Base class for a single LLM provider.

    Subclasses only need to implement _call_api. Timing and error
    handling live here so every provider behaves the same way when
    something goes wrong.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def send_prompt(self, prompt: str) -> ProviderResponse:
        start = time.monotonic()
        try:
            text = self._call_api(prompt)
            error = None
        except Exception as exc:  # noqa: BLE001, deliberate: one bad call can't kill a scan
            text = ""
            error = str(exc)
        latency = time.monotonic() - start

        return ProviderResponse(
            provider=self.name,
            model=self.config.model,
            prompt=prompt,
            text=text,
            latency_seconds=latency,
            error=error,
        )

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """Subclasses raise on failure, send_prompt catches it and wraps the result."""
        raise NotImplementedError