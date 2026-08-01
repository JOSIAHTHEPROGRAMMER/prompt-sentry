"""Tests for per-provider summary statistics."""

from __future__ import annotations

from prompt_sentry.scoring.aggregate import summarize_by_category, summarize_provider
from prompt_sentry.scoring.base import ScoreResult, ScoreVerdict


def make_result(**overrides: object) -> ScoreResult:
    defaults: dict[str, object] = {
        "attack_id": "injection-ignore-previous-instructions",
        "provider": "groq",
        "judged_by": "gemini",
        "self_judged": False,
        "verdict": ScoreVerdict.RESISTED,
        "severity": 10,
        "reasoning": "declined cleanly",
    }
    defaults.update(overrides)
    return ScoreResult(**defaults)  # type: ignore[arg-type]


def test_counts_verdicts_correctly() -> None:
    results = [
        make_result(verdict=ScoreVerdict.RESISTED, severity=5),
        make_result(verdict=ScoreVerdict.RESISTED, severity=10),
        make_result(verdict=ScoreVerdict.PARTIAL, severity=40),
        make_result(verdict=ScoreVerdict.COMPROMISED, severity=90),
    ]

    summary = summarize_provider("groq", results)

    assert summary.total_attacks == 4
    assert summary.resisted == 2
    assert summary.partial == 1
    assert summary.compromised == 1
    assert summary.errors == 0


def test_resistance_rate_is_fraction_of_scored_results() -> None:
    results = [
        make_result(verdict=ScoreVerdict.RESISTED, severity=0),
        make_result(verdict=ScoreVerdict.RESISTED, severity=0),
        make_result(verdict=ScoreVerdict.COMPROMISED, severity=90),
        make_result(verdict=ScoreVerdict.COMPROMISED, severity=95),
    ]

    summary = summarize_provider("groq", results)

    assert summary.resistance_rate == 0.5


def test_average_severity_only_counts_scored_results() -> None:
    results = [
        make_result(severity=10),
        make_result(severity=30),
    ]

    summary = summarize_provider("groq", results)

    assert summary.average_severity == 20.0


def test_filters_to_only_the_requested_provider() -> None:
    results = [
        make_result(provider="groq", verdict=ScoreVerdict.RESISTED),
        make_result(provider="gemini", verdict=ScoreVerdict.COMPROMISED),
    ]

    summary = summarize_provider("groq", results)

    assert summary.total_attacks == 1
    assert summary.resisted == 1


def test_errored_results_count_separately_and_do_not_skew_severity() -> None:
    results = [
        make_result(verdict=ScoreVerdict.RESISTED, severity=10),
        make_result(verdict=None, severity=None, reasoning="", error="judge failed"),
    ]

    summary = summarize_provider("groq", results)

    assert summary.total_attacks == 2
    assert summary.errors == 1
    assert summary.average_severity == 10.0  # the errored one is excluded, not averaged as 0


def test_empty_results_produce_zero_rate_and_none_severity() -> None:
    summary = summarize_provider("groq", [])

    assert summary.total_attacks == 0
    assert summary.resistance_rate == 0.0
    assert summary.average_severity is None


def test_summarize_by_category_groups_correctly() -> None:
    results = [
        make_result(attack_id="injection-ignore-previous-instructions", 
                    verdict=ScoreVerdict.RESISTED),
        make_result(attack_id="jailbreak-persona-override", 
                    verdict=ScoreVerdict.COMPROMISED),
    ]

    by_category = summarize_by_category("groq", results)

    injection_summary = next(s for c, s in by_category.items() if c.value == "prompt_injection")
    jailbreak_summary = next(s for c, s in by_category.items() if c.value == "jailbreak")

    assert injection_summary.total_attacks == 1
    assert injection_summary.resisted == 1
    assert jailbreak_summary.total_attacks == 1
    assert jailbreak_summary.compromised == 1