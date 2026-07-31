"""Centralized environment/config loading.

Nothing else in this codebase should call os.getenv() directly - this is
the one place that touches the environment, so provider defaults or env
var names only ever need to change here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# these are our defaults, not hardcoded assumptions the user is stuck with -
# override any of them with GROQ_MODEL / GEMINI_MODEL / MISTRAL_MODEL in .env
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-20b",
    "gemini": "gemini-3.6-flash",
    "mistral": "mistral-small-latest",
}


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str | None
    model: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class Settings:
    providers: dict[str, ProviderConfig]
    max_retries: int = 1

    def available_providers(self) -> list[str]:
        """providers we can actually call - key is present and non-empty"""
        return [name for name, cfg in self.providers.items() if cfg.api_key]


def load_settings() -> Settings:
    """Build Settings from the current environment.

    Deliberately not cached at module level - call this once at CLI
    startup. Keeping it a plain function (not a global singleton) means
    tests can set env vars and call this fresh without reloading modules.
    """
    providers = {
        "groq": ProviderConfig(
            name="groq",
            api_key=os.getenv("GROQ_API_KEY") or None,
            model=os.getenv("GROQ_MODEL", DEFAULT_MODELS["groq"]),
        ),
        "gemini": ProviderConfig(
            name="gemini",
            api_key=os.getenv("GEMINI_API_KEY") or None,
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODELS["gemini"]),
        ),
        "mistral": ProviderConfig(
            name="mistral",
            api_key=os.getenv("MISTRAL_API_KEY") or None,
            model=os.getenv("MISTRAL_MODEL", DEFAULT_MODELS["mistral"]),
        ),
    }
    return Settings(providers=providers)
