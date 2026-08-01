"""Shared shape for a completed scan, stitches Attack, ProviderResponse,
and ScoreResult together into one flat record per (attack, provider)
pair, plus the run level summaries built on top of them.

Flat rather than nested so the eventual JSON export reads cleanly by
hand, a nested shape would be technically fine but awkward to skim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from prompt_sentry.attacks.base import Attack, AttackCategory
from prompt_sentry.providers.base import ProviderResponse
from prompt_sentry.scoring.aggregate import ProviderSummary
from prompt_sentry.scoring.base import ScoreResult, ScoreVerdict


@dataclass(frozen=True)
class AttackResult:
    attack_id: str
    attack_name: str
    category: AttackCategory
    prompt: str
    provider: str
    model: str
    response_text: str
    response_error: str | None
    latency_seconds: float
    judged_by: str
    self_judged: bool
    verdict: ScoreVerdict | None
    severity: int | None
    reasoning: str
    score_error: str | None

    @staticmethod
    def build(attack: Attack, response: ProviderResponse, score: ScoreResult) -> AttackResult:
        return AttackResult(
            attack_id=attack.id,
            attack_name=attack.name,
            category=attack.category,
            prompt=attack.prompt,
            provider=response.provider,
            model=response.model,
            response_text=response.text,
            response_error=response.error,
            latency_seconds=response.latency_seconds,
            judged_by=score.judged_by,
            self_judged=score.self_judged,
            verdict=score.verdict,
            severity=score.severity,
            reasoning=score.reasoning,
            score_error=score.error,
        )


@dataclass(frozen=True)
class ScanReport:
    generated_at: str
    results: tuple[AttackResult, ...]
    provider_summaries: dict[str, ProviderSummary] = field(default_factory=dict)

    @staticmethod
    def now_timestamp() -> str:
        # iso 8601 with timezone, so a report generated at midnight utc
        # isn't ambiguous about which day it actually ran on
        return datetime.now(timezone.utc).isoformat()