"""Tests for CLI orchestration. Providers are always fakes or mocks,
nothing here calls a real API.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

import pytest
from rich.console import Console

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.registry import get_all_attacks
from prompt_sentry.cli.main import (
    ScanConfigError,
    resolve_attacks,
    resolve_providers,
    run_scan,
)
from prompt_sentry.cli.main import main as cli_main
from prompt_sentry.providers.base import Provider, ProviderResponse
from prompt_sentry.utils.config import ProviderConfig, Settings

GOOD_JSON = '{"verdict": "resisted", "severity": 5, "reasoning": "ok"}'


class FakeProvider(Provider):
    def _call_api(self, prompt: str) -> str:
        return "fake response"


FAKE_CLASSES: dict[str, type[Provider]] = {
    "groq": FakeProvider,
    "gemini": FakeProvider,
    "mistral": FakeProvider,
}


def make_console() -> tuple[Console, io.StringIO]:
    buffer = io.StringIO()
    return Console(file=buffer, width=200, no_color=True), buffer

def test_main_runs_a_full_scan_end_to_end(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setattr("prompt_sentry.cli.main.PROVIDER_CLASSES", FAKE_CLASSES)
    monkeypatch.chdir(tmp_path)
    console, buffer = make_console()

    cli_main(
        argv=["--provider", "groq", "--attack", "injection-ignore-previous-instructions"],
        console=console,
    )

    output = buffer.getvalue()
    assert "running 1 attack(s) against 1 provider(s)" in output
    assert "Scan Summary" in output


def test_main_exports_json_when_flag_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    monkeypatch.setattr("prompt_sentry.cli.main.PROVIDER_CLASSES", FAKE_CLASSES)


    monkeypatch.chdir(tmp_path)
    console, buffer = make_console()

    cli_main(
        argv=[
            "--provider",
            "groq",
            "--attack",
            "injection-ignore-previous-instructions",
            "--json",
            "--verbose",
        ],
        console=console,
    )

    output = buffer.getvalue()
    assert "report exported to" in output
    assert (tmp_path / "reports").exists()

def make_settings() -> Settings:
    return Settings(
        providers={
            "groq": ProviderConfig(name="groq", api_key="key1", model="m"),
            "gemini": ProviderConfig(name="gemini", api_key=None, model="m"),
            "mistral": ProviderConfig(name="mistral", api_key="key3", model="m"),
        }
    )


def test_resolve_providers_builds_instances_for_requested_provider() -> None:
    args = argparse.Namespace(provider=["groq"])

    providers = resolve_providers(args, make_settings(), provider_classes=FAKE_CLASSES)

    assert set(providers.keys()) == {"groq"}
    assert isinstance(providers["groq"], FakeProvider)


def test_resolve_providers_defaults_to_available_when_none_requested() -> None:
    args = argparse.Namespace(provider=None)

    providers = resolve_providers(args, make_settings(), provider_classes=FAKE_CLASSES)

    assert set(providers.keys()) == {"groq", "mistral"}  # gemini has no key configured


def test_resolve_providers_raises_when_no_keys_configured_at_all() -> None:
    empty_settings = Settings(
        providers={"groq": ProviderConfig(name="groq", api_key=None, model="m")}
    )
    args = argparse.Namespace(provider=None)

    with pytest.raises(ScanConfigError):
        resolve_providers(args, empty_settings, provider_classes=FAKE_CLASSES)

def test_resolve_providers_raises_when_explicit_provider_missing_key() -> None:
    args = argparse.Namespace(provider=["gemini"])

    with pytest.raises(ScanConfigError, match="gemini"):
        resolve_providers(args, make_settings(), provider_classes=FAKE_CLASSES)


def test_resolve_attacks_all_returns_full_library() -> None:
    args = argparse.Namespace(all=True, attack=None, attack_category=None)

    attacks = resolve_attacks(args)

    assert len(attacks) == len(get_all_attacks())


def test_resolve_attacks_specific_id_returns_just_that_attack() -> None:
    args = argparse.Namespace(
        all=False, attack=["injection-ignore-previous-instructions"], attack_category=None
    )

    attacks = resolve_attacks(args)

    assert len(attacks) == 1
    assert attacks[0].id == "injection-ignore-previous-instructions"


def test_resolve_attacks_unknown_id_raises_scan_config_error() -> None:
    args = argparse.Namespace(all=False, attack=["not-a-real-id"], attack_category=None)

    with pytest.raises(ScanConfigError, match="not-a-real-id"):
        resolve_attacks(args)


def test_resolve_attacks_category_returns_only_that_category() -> None:
    args = argparse.Namespace(all=False, attack=None, attack_category=["jailbreak"])

    attacks = resolve_attacks(args)

    assert len(attacks) >= 8
    assert all(attack.category == AttackCategory.JAILBREAK for attack in attacks)


def test_resolve_attacks_dedupes_overlapping_selections() -> None:
    args = argparse.Namespace(
        all=True, attack=["injection-ignore-previous-instructions"], attack_category=None
    )

    attacks = resolve_attacks(args)
    ids = [attack.id for attack in attacks]

    assert len(ids) == len(set(ids))
    assert len(attacks) == len(get_all_attacks())


def test_run_scan_produces_one_result_per_attack_per_provider() -> None:
    console, _ = make_console()
    from unittest.mock import MagicMock

    alpha = MagicMock(spec=Provider)
    alpha.send_prompt.return_value = ProviderResponse(
        provider="alpha", model="m", prompt="p", text=GOOD_JSON, latency_seconds=0.1
    )
    beta = MagicMock(spec=Provider)
    beta.send_prompt.return_value = ProviderResponse(
        provider="beta", model="m", prompt="p", text=GOOD_JSON, latency_seconds=0.1
    )
    providers = {"alpha": alpha, "beta": beta}
    args = argparse.Namespace(
        all=False, attack=["injection-ignore-previous-instructions"], attack_category=None
    )
    attacks = resolve_attacks(args)

    report = run_scan(attacks, providers, console=console)

    assert len(report.results) == 2
    assert {r.provider for r in report.results} == {"alpha", "beta"}
    assert "alpha" in report.provider_summaries
    assert "beta" in report.provider_summaries


def test_run_scan_prints_progress_for_each_completed_attack() -> None:
    console, buffer = make_console()
    from unittest.mock import MagicMock

    alpha = MagicMock(spec=Provider)
    alpha.send_prompt.return_value = ProviderResponse(
        provider="alpha", model="m", prompt="p", text=GOOD_JSON, latency_seconds=0.1
    )
    providers = {"alpha": alpha}
    args = argparse.Namespace(
        all=False, attack=["injection-ignore-previous-instructions"], attack_category=None
    )
    attacks = resolve_attacks(args)

    run_scan(attacks, providers, console=console)

    output = buffer.getvalue()
    assert "1/1" in output
    assert "alpha" in output


def test_main_list_flag_prints_categories_without_running_a_scan() -> None:
    console, buffer = make_console()

    cli_main(argv=["--list"], console=console)

    assert "jailbreak" in buffer.getvalue()


def test_main_exits_cleanly_when_no_provider_keys_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in ["GROQ_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY"]:
        monkeypatch.delenv(var, raising=False)
    console, buffer = make_console()

    with pytest.raises(SystemExit):
        cli_main(argv=["--all"], console=console)

    assert "error" in buffer.getvalue().lower()