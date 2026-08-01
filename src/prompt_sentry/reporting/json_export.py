"""Writes a ScanReport to a timestamped JSON file under reports/.

Not using dataclasses.asdict here, it would leave enum fields as raw
Enum objects, which json.dumps can't serialize. Converting explicitly
keeps the exported shape visible in one place instead of trusting an
automatic recursive converter.
"""

from __future__ import annotations

import json
from pathlib import Path

from prompt_sentry.reporting.base import AttackResult, ScanReport
from prompt_sentry.scoring.aggregate import ProviderSummary

REPORTS_DIR = Path("reports")


def _attack_result_to_dict(result: AttackResult) -> dict[str, object]:
    return {
        "attack_id": result.attack_id,
        "attack_name": result.attack_name,
        "category": result.category.value,
        "prompt": result.prompt,
        "provider": result.provider,
        "model": result.model,
        "response_text": result.response_text,
        "response_error": result.response_error,
        "latency_seconds": result.latency_seconds,
        "judged_by": result.judged_by,
        "self_judged": result.self_judged,
        "verdict": result.verdict.value if result.verdict else None,
        "severity": result.severity,
        "reasoning": result.reasoning,
        "score_error": result.score_error,
    }


def _summary_to_dict(summary: ProviderSummary) -> dict[str, object]:
    return {
        "provider": summary.provider,
        "total_attacks": summary.total_attacks,
        "resisted": summary.resisted,
        "partial": summary.partial,
        "compromised": summary.compromised,
        "errors": summary.errors,
        "resistance_rate": round(summary.resistance_rate, 4),
        "average_severity": summary.average_severity,
    }


def report_to_dict(report: ScanReport) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "provider_summaries": {
            provider: _summary_to_dict(summary)
            for provider, summary in report.provider_summaries.items()
        },
        "results": [_attack_result_to_dict(result) for result in report.results],
    }


def export_report(report: ScanReport, output_dir: Path = REPORTS_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    # colons aren't safe in filenames on windows, so the iso timestamp
    # gets its colons swapped for dashes before it becomes a filename
    safe_timestamp = report.generated_at.replace(":", "-")
    output_path = output_dir / f"scan_{safe_timestamp}.json"

    output_path.write_text(json.dumps(report_to_dict(report), indent=2), encoding="utf-8")
    return output_path