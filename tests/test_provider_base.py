"""Tests for the shared Provider contract, using a fake provider.

Provider is abstract, so we test its shared behavior (timing, error
wrapping) through a minimal subclass built just for this file.
"""

from __future__ import annotations

import pytest

from prompt_sentry.providers.base import Provider
from prompt_sentry.utils.config import ProviderConfig


class FakeProvider(Provider):
    """Subclass for testing only, lets a test control success or failure."""

    def __init__(self, config: ProviderConfig, should_fail: bool = False) -> None:
        super().__init__(config)
        self.should_fail = should_fail

    def _call_api(self, prompt: str) -> str:
        if self.should_fail:
            raise RuntimeError("simulated api failure")
        return f"echo: {prompt}"


@pytest.fixture
def config() -> ProviderConfig:
    return ProviderConfig(name="fake", api_key="test_key", model="fake-model-v1")


def test_successful_call_returns_text(config: ProviderConfig) -> None:
    provider = FakeProvider(config)

    response = provider.send_prompt("hello")

    assert response.succeeded
    assert response.text == "echo: hello"
    assert response.error is None


def test_failed_call_wraps_error_instead_of_raising(config: ProviderConfig) -> None:
    provider = FakeProvider(config, should_fail=True)

    response = provider.send_prompt("hello")

    assert not response.succeeded
    assert response.text == ""
    assert "simulated api failure" in response.error


def test_response_carries_provider_and_model_metadata(config: ProviderConfig) -> None:
    provider = FakeProvider(config)

    response = provider.send_prompt("hello")

    assert response.provider == "fake"
    assert response.model == "fake-model-v1"
    assert response.prompt == "hello"


def test_latency_is_recorded(config: ProviderConfig) -> None:
    provider = FakeProvider(config)

    response = provider.send_prompt("hello")

    assert response.latency_seconds >= 0


def test_provider_cannot_be_instantiated_directly(config: ProviderConfig) -> None:
    with pytest.raises(TypeError):
        Provider(config)  # type: ignore[abstract]



def test_abstract_call_api_raises_not_implemented(config: ProviderConfig) -> None:
    # calling Provider._call_api directly, bypassing FakeProvider's own
    # override, is the only way to actually execute the abstract stub's body
    provider = FakeProvider(config)
    with pytest.raises(NotImplementedError):
        Provider._call_api(provider, "hi")