"""Turns a batch of ScoreResults into per-provider summary stats.

Category breakdowns look up each attack's category via the registry
rather than storing it on ScoreResult, the registry stays the single
source of truth for that.
"""

from __future__ import annotations

from dataclasses import dataclass

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.registry import get_attack_by_id
from prompt_sentry.scoring.base import ScoreResult, ScoreVerdict


@dataclass(frozen=True)
class ProviderSummary:
    provider: str
    total_attacks: int
    resisted: int
    partial: int
    compromised: int
    errors: int
    resistance_rate: float
    average_severity: float | None


def summarize_provider(provider: str, results: list[ScoreResult]) -> ProviderSummary:
    provider_results = [r for r in results if r.provider == provider]

    resisted = sum(1 for r in provider_results if r.verdict == ScoreVerdict.RESISTED)
    partial = sum(1 for r in provider_results if r.verdict == ScoreVerdict.PARTIAL)
    compromised = sum(1 for r in provider_results if r.verdict == ScoreVerdict.COMPROMISED)
    errors = sum(1 for r in provider_results if not r.succeeded)

    scored_count = resisted + partial + compromised
    resistance_rate = resisted / scored_count if scored_count else 0.0

    severities = [r.severity for r in provider_results if r.severity is not None]
    average_severity = sum(severities) / len(severities) if severities else None

    return ProviderSummary(
        provider=provider,
        total_attacks=len(provider_results),
        resisted=resisted,
        partial=partial,
        compromised=compromised,
        errors=errors,
        resistance_rate=resistance_rate,
        average_severity=average_severity,
    )


def summarize_by_category(
    provider: str, results: list[ScoreResult]
) -> dict[AttackCategory, ProviderSummary]:
    provider_results = [r for r in results if r.provider == provider]

    by_category: dict[AttackCategory, list[ScoreResult]] = {}
    for result in provider_results:
        category = get_attack_by_id(result.attack_id).category
        by_category.setdefault(category, []).append(result)

    return {
        category: summarize_provider(provider, category_results)
        for category, category_results in by_category.items()
    }