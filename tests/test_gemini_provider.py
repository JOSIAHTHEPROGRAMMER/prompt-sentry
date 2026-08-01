"""Tests for GeminiProvider. Mocks the SDK client, never calls the real API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from prompt_sentry.providers.gemini_provider import GeminiProvider
from prompt_sentry.utils.config import ProviderConfig


@pytest.fixture
def config() -> ProviderConfig:
    return ProviderConfig(name="gemini", api_key="test_key", model="gemini-3.6-flash")


def make_response(text: str | None) -> MagicMock:
    response = MagicMock()
    response.text = text
    return response


@patch("prompt_sentry.providers.gemini_provider.genai.Client")
def test_send_prompt_returns_model_text(mock_client_cls: MagicMock, config: ProviderConfig) -> None:
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.return_value = make_response("hello there")

    provider = GeminiProvider(config)
    response = provider.send_prompt("hi")

    assert response.succeeded
    assert response.text == "hello there"


@patch("prompt_sentry.providers.gemini_provider.genai.Client")
def test_send_prompt_calls_api_with_correct_model_and_contents(
    mock_client_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.return_value = make_response("ok")

    provider = GeminiProvider(config)
    provider.send_prompt("attack payload here")

    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-3.6-flash",
        contents="attack payload here",
    )


@patch("prompt_sentry.providers.gemini_provider.genai.Client")
def test_none_text_becomes_a_wrapped_error(
    mock_client_cls: MagicMock, config: ProviderConfig
) -> None:
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.return_value = make_response(None)

    provider = GeminiProvider(config)
    response = provider.send_prompt("hi")

    assert not response.succeeded
    assert "empty response" in response.error


@patch("prompt_sentry.providers.gemini_provider.genai.Client")
def test_timeout_is_converted_to_milliseconds(
    mock_client_cls: MagicMock, config: ProviderConfig
) -> None:
    GeminiProvider(config)

    _, kwargs = mock_client_cls.call_args
    assert kwargs["http_options"].timeout == 30_000