"""Tests for GroqProvider. Mocks the SDK client, never calls the real API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from prompt_sentry.providers.groq_provider import GroqProvider
from prompt_sentry.utils.config import ProviderConfig


@pytest.fixture
def config() -> ProviderConfig:
    return ProviderConfig(name="groq", api_key="test_key", model="openai/gpt-oss-20b")


def make_completion(content: str | None) -> MagicMock:
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=content))]
    return completion


@patch("prompt_sentry.providers.groq_provider.Groq")
def test_send_prompt_returns_model_text(mock_groq_cls: MagicMock, config: ProviderConfig) -> None:
    mock_client = mock_groq_cls.return_value
    mock_client.chat.completions.create.return_value = make_completion("hello there")

    provider = GroqProvider(config)
    response = provider.send_prompt("hi")

    assert response.succeeded
    assert response.text == "hello there"


@patch("prompt_sentry.providers.groq_provider.Groq")
def test_send_prompt_calls_api_with_correct_model_and_message(
    mock_groq_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_groq_cls.return_value
    mock_client.chat.completions.create.return_value = make_completion("ok")

    provider = GroqProvider(config)
    provider.send_prompt("attack payload here")

    mock_client.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "attack payload here"}],
    )


@patch("prompt_sentry.providers.groq_provider.Groq")
def test_none_content_becomes_a_wrapped_error(
    mock_groq_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_groq_cls.return_value
    mock_client.chat.completions.create.return_value = make_completion(None)

    provider = GroqProvider(config)
    response = provider.send_prompt("hi")

    assert not response.succeeded
    assert "empty response" in response.error


@patch("prompt_sentry.providers.groq_provider.Groq")
def test_client_is_built_with_key_and_timeout_from_config(
    mock_groq_cls: MagicMock, config: ProviderConfig
) -> None:
    GroqProvider(config)

    mock_groq_cls.assert_called_once_with(api_key="test_key", timeout=30)