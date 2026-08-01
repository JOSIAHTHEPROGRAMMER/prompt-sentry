"""Tests for MistralProvider. Mocks the SDK client, never calls the real API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from prompt_sentry.providers.mistral_provider import MistralProvider
from prompt_sentry.utils.config import ProviderConfig


@pytest.fixture
def config() -> ProviderConfig:
    return ProviderConfig(name="mistral", api_key="test_key", model="mistral-small-latest")


def make_completion(content: str | None) -> MagicMock:
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=content))]
    return completion


@patch("prompt_sentry.providers.mistral_provider.Mistral")
def test_send_prompt_returns_model_text(
    mock_mistral_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_mistral_cls.return_value
    mock_client.chat.complete.return_value = make_completion("hello there")

    provider = MistralProvider(config)
    response = provider.send_prompt("hi")

    assert response.succeeded
    assert response.text == "hello there"


@patch("prompt_sentry.providers.mistral_provider.Mistral")
def test_send_prompt_calls_api_with_correct_model_and_message(
    mock_mistral_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_mistral_cls.return_value
    mock_client.chat.complete.return_value = make_completion("ok")

    provider = MistralProvider(config)
    provider.send_prompt("attack payload here")

    _, kwargs = mock_client.chat.complete.call_args
    assert kwargs["model"] == "mistral-small-latest"
    assert kwargs["timeout_ms"] == 30_000
    assert len(kwargs["messages"]) == 1
    assert kwargs["messages"][0].content == "attack payload here"
    assert kwargs["messages"][0].role == "user"


@patch("prompt_sentry.providers.mistral_provider.Mistral")
def test_none_content_becomes_a_wrapped_error(
    mock_mistral_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_mistral_cls.return_value
    mock_client.chat.complete.return_value = make_completion(None)

    provider = MistralProvider(config)
    response = provider.send_prompt("hi")

    assert not response.succeeded
    assert "empty response" in response.error


@patch("prompt_sentry.providers.mistral_provider.Mistral")
def test_none_message_becomes_a_wrapped_error(
    mock_mistral_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_mistral_cls.return_value
    completion = MagicMock()
    completion.choices = [MagicMock(message=None)]
    mock_client.chat.complete.return_value = completion

    provider = MistralProvider(config)
    response = provider.send_prompt("hi")

    assert not response.succeeded
    assert "empty response" in response.error