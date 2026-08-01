"""Tests for the ScoreResult dataclass and ScoreVerdict enum."""

from __future__ import annotations

import pytest

from prompt_sentry.scoring.base import ScoreResult, ScoreVerdict


def make_result(**overrides: object) -> ScoreResult:
    defaults: dict[str, object] = {
        "attack_id": "injection-ignore-previous-instructions",
        "provider": "groq",
        "judged_by": "gemini",
        "self_judged": False,
        "verdict": ScoreVerdict.RESISTED,
        "severity": 10,
        "reasoning": "the model declined and did not leak anything",
    }
    defaults.update(overrides)
    return ScoreResult(**defaults)  # type: ignore[arg-type]


def test_successful_score_holds_its_fields() -> None:
    result = make_result()

    assert result.succeeded
    assert result.verdict == ScoreVerdict.RESISTED
    assert result.severity == 10
    assert result.error is None


def test_verdict_compares_equal_to_its_string_value() -> None:
    assert ScoreVerdict.COMPROMISED == "compromised"


def test_failed_judge_call_can_omit_verdict_and_severity() -> None:
    result = make_result(
        verdict=None,
        severity=None,
        reasoning="",
        error="judge call failed after retry: rate limited",
    )

    assert not result.succeeded
    assert result.verdict is None
    assert result.severity is None


@pytest.mark.parametrize("bad_severity", [-1, 101, 200])
def test_severity_out_of_range_raises(bad_severity: int) -> None:
    with pytest.raises(ValueError, match="severity must be between 0 and 100"):
        make_result(severity=bad_severity)


@pytest.mark.parametrize("edge_severity", [0, 100])
def test_severity_boundary_values_are_valid(edge_severity: int) -> None:
    result = make_result(severity=edge_severity)
    assert result.severity == edge_severity