"""Orchestrates a full scan: resolves flags into real attacks and
providers, runs each attack against each provider, scores every
response, then prints and optionally exports the report.

This is the file that makes `prompt-sentry --all` an actual runnable
command, everything before this phase was pieces, this is where they
get wired together.
"""

from __future__ import annotations

import argparse
import time

from rich.console import Console

from prompt_sentry.attacks.base import Attack, AttackCategory
from prompt_sentry.attacks.registry import (
    get_all_attacks,
    get_attack_by_id,
    get_attacks_by_category,
)
from prompt_sentry.cli.parser import build_parser, validate_args
from prompt_sentry.providers.base import Provider
from prompt_sentry.providers.gemini_provider import GeminiProvider
from prompt_sentry.providers.groq_provider import GroqProvider
from prompt_sentry.providers.mistral_provider import MistralProvider
from prompt_sentry.reporting.base import AttackResult, ScanReport
from prompt_sentry.reporting.console import render_attack_list, render_report
from prompt_sentry.reporting.json_export import export_report
from prompt_sentry.scoring.aggregate import summarize_provider
from prompt_sentry.scoring.base import ScoreResult
from prompt_sentry.scoring.judge import score_response
from prompt_sentry.utils.config import Settings, load_settings

PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "mistral": MistralProvider,
}


class ScanConfigError(Exception):
    """Raised when flags resolve to something that can't actually run,
    a missing api key or an unknown attack id, rather than an argparse
    level syntax problem.
    """


def resolve_providers(
    args: argparse.Namespace,
    settings: Settings,
    provider_classes: dict[str, type[Provider]] | None = None,
) -> dict[str, Provider]:
    provider_classes = provider_classes or PROVIDER_CLASSES

    requested = args.provider or settings.available_providers()
    if not requested:
        raise ScanConfigError("no provider api keys configured, add at least one to your .env")

    providers: dict[str, Provider] = {}
    for name in requested:
        config = settings.providers[name]
        if config.api_key is None:
            raise ScanConfigError(f"--provider {name} requested but no api key is configured")
        providers[name] = provider_classes[name](config)

    return providers


def resolve_attacks(args: argparse.Namespace) -> tuple[Attack, ...]:
    selected: dict[str, Attack] = {}

    if args.all:
        for attack in get_all_attacks():
            selected[attack.id] = attack

    for category_value in args.attack_category or []:
        category = AttackCategory(category_value)
        for attack in get_attacks_by_category(category):
            selected[attack.id] = attack

    for attack_id in args.attack or []:
        try:
            selected[attack_id] = get_attack_by_id(attack_id)
        except KeyError as exc:
            raise ScanConfigError(
                f"unknown attack id '{attack_id}', run --list to see ids"
            ) from exc

        
    return tuple(selected.values())


def run_scan(
    attacks: tuple[Attack, ...],
    providers: dict[str, Provider],
    forced_judge: str | None = None,
    delay: float = 0.0,
    console: Console | None = None,
) -> ScanReport:
    console = console or Console()
    attack_results: list[AttackResult] = []
    score_results: list[ScoreResult] = []
    total = len(attacks) * len(providers)
    completed = 0

    for provider_name, provider in providers.items():
        for attack in attacks:
            response = provider.send_prompt(attack.prompt)
            score = score_response(attack, response, providers, forced_judge=forced_judge)

            attack_results.append(AttackResult.build(attack, response, score))
            score_results.append(score)

            completed += 1
            verdict_text = score.verdict.value if score.verdict else "error"
            console.print(f"[{completed}/{total}] {provider_name} | {attack.name}: {verdict_text}")

            if delay > 0 and completed < total:
                time.sleep(delay)

    summaries = {name: summarize_provider(name, score_results) for name in providers}

    return ScanReport(
        generated_at=ScanReport.now_timestamp(),
        results=tuple(attack_results),
        provider_summaries=summaries,
    )

def main(argv: list[str] | None = None, console: Console | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)

    console = console or Console()

    if args.list:
        render_attack_list(console)
        return

    settings = load_settings()

    try:
        providers = resolve_providers(args, settings)
        attacks = resolve_attacks(args)
    except ScanConfigError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise SystemExit(1) from exc

    console.print(f"running {len(attacks)} attack(s) against {len(providers)} provider(s)\n")
    report = run_scan(attacks, providers, forced_judge=args.judge, 
                      delay=args.delay, console=console)

    console.print()
    render_report(report, console, verbose=args.verbose)

    if args.json:
        output_path = export_report(report)
        console.print(f"\nreport exported to {output_path}")


if __name__ == "__main__":  # pragma: no cover
    main()