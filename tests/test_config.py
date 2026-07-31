"""Tests for environment loading and provider availability logic."""

from __future__ import annotations

import pytest

from prompt_sentry.utils.config import DEFAULT_MODELS, load_settings

ENV_VARS = [
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "GROQ_MODEL",
    "GEMINI_MODEL",
    "MISTRAL_MODEL",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # start every test with a blank slate so a real .env on disk
    # (or whatever happens to be exported in the dev shell) can't leak in
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_missing_keys_come_back_as_none() -> None:
    settings = load_settings()

    assert settings.providers["groq"].api_key is None
    assert settings.providers["gemini"].api_key is None
    assert settings.providers["mistral"].api_key is None


def test_available_providers_is_empty_when_no_keys_set() -> None:
    settings = load_settings()

    assert settings.available_providers() == []


def test_available_providers_only_lists_configured_ones(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test_key_123")

    settings = load_settings()

    assert settings.available_providers() == ["groq"]


def test_empty_string_key_counts_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # some shells export a var as an empty string rather than unsetting it
    monkeypatch.setenv("GROQ_API_KEY", "")

    settings = load_settings()

    assert settings.providers["groq"].api_key is None


def test_default_model_used_when_no_override_given() -> None:
    settings = load_settings()

    assert settings.providers["groq"].model == DEFAULT_MODELS["groq"]
    assert settings.providers["gemini"].model == DEFAULT_MODELS["gemini"]
    assert settings.providers["mistral"].model == DEFAULT_MODELS["mistral"]


def test_model_override_from_env_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_MODEL", "some-other-model")

    settings = load_settings()

    assert settings.providers["groq"].model == "some-other-model"
