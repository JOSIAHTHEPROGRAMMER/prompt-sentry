"""Human readable console output for a completed scan, built on rich.

Console instances are passed in rather than constructed at module
level, that's what makes this testable, a test can inject a Console
writing to an in memory buffer and inspect exactly what would have
printed.
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.registry import get_attacks_by_category
from prompt_sentry.reporting.base import ScanReport
from prompt_sentry.scoring.base import ScoreVerdict

VERDICT_COLORS: dict[ScoreVerdict, str] = {
    ScoreVerdict.RESISTED: "green",
    ScoreVerdict.PARTIAL: "yellow",
    ScoreVerdict.COMPROMISED: "red",
}


def _truncate(text: str, max_length: int = 80) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def _colored_verdict(verdict: ScoreVerdict | None) -> str:
    if verdict is None:
        return "[dim]error[/dim]"
    color = VERDICT_COLORS[verdict]
    return f"[{color}]{verdict.value}[/{color}]"


def render_summary_table(report: ScanReport, console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title=f"Prompt Sentry Scan Summary — {report.generated_at}")

    table.add_column("Provider", style="bold")
    table.add_column("Total", justify="right")
    table.add_column("Resisted", justify="right", style="green")
    table.add_column("Partial", justify="right", style="yellow")
    table.add_column("Compromised", justify="right", style="red")
    table.add_column("Errors", justify="right", style="dim")
    table.add_column("Resistance Rate", justify="right")
    table.add_column("Avg Severity", justify="right")

    for provider, summary in report.provider_summaries.items():
        if summary.average_severity is not None:
            avg_severity = f"{summary.average_severity:.1f}"
        else:
            avg_severity = "n/a"

        table.add_row(
            provider,
            str(summary.total_attacks),
            str(summary.resisted),
            str(summary.partial),
            str(summary.compromised),
            str(summary.errors),
            f"{summary.resistance_rate:.0%}",
            avg_severity,
        )

    console.print(table)


def render_detailed_results(
    report: ScanReport, console: Console | None = None, provider: str | None = None
) -> None:
    console = console or Console()
    results = report.results
    if provider is not None:
        results = tuple(r for r in results if r.provider == provider)

    table = Table(title="Detailed Attack Results")
    table.add_column("Attack", style="bold")
    table.add_column("Category")
    table.add_column("Provider")
    table.add_column("Verdict")
    table.add_column("Severity", justify="right")
    table.add_column("Judged By", style="dim")
    table.add_column("Reasoning")

    for result in results:
        severity_text = str(result.severity) if result.severity is not None else "n/a"
        judged_by = f"{result.judged_by} (self)" if result.self_judged else result.judged_by
        reasoning = result.score_error or result.reasoning
        reasoning = _truncate(reasoning)

        table.add_row(
            result.attack_name,
            result.category.value,
            result.provider,
            _colored_verdict(result.verdict),
            severity_text,
            judged_by,
            reasoning,
        )

    console.print(table)


def render_report(report: ScanReport, console: Console | 
                None = None, verbose: bool = False) -> None:
    console = console or Console()
    render_summary_table(report, console)
    if verbose:
        console.print()
        render_detailed_results(report, console)

def render_attack_list(console: Console | None = None) -> None:
    console = console or Console()
    for category in AttackCategory:
        attacks = get_attacks_by_category(category)
        table = Table(title=category.value)
        table.add_column("ID", style="bold")
        table.add_column("Name")
        table.add_column("References", style="dim")

        for attack in attacks:
            table.add_row(attack.id, attack.name, ", ".join(attack.references))

        console.print(table)
        console.print()