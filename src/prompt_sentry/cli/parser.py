"""Argparse setup for the prompt-sentry CLI.

Only handles flag definitions and validating flag combinations. Turning
a parsed --attack id into an actual Attack object, or a --provider name
into a live Provider instance, is main.py's job, not this file's.
"""

from __future__ import annotations

import argparse

from prompt_sentry.attacks.base import AttackCategory

PROVIDER_NAMES = ("groq", "gemini", "mistral")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-sentry",
        description=(
            "Red teams multiple LLM APIs against a library of prompt injection, "
            "jailbreak, and other adversarial attacks, then compares how each "
            "model handled them."
        ),
    )

    parser.add_argument(
        "--provider",
        action="append",
        choices=PROVIDER_NAMES,
        help="Limit the scan to this provider. Repeatable. Defaults to every "
        "provider with an api key configured.",
    )
    parser.add_argument(
        "--attack",
        action="append",
        metavar="ATTACK_ID",
        help="Run this specific attack by id. Repeatable. See --list for ids.",
    )
    parser.add_argument(
        "--attack-category",
        action="append",
        choices=[category.value for category in AttackCategory],
        metavar="CATEGORY",
        help="Run every attack in this category. Repeatable.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the entire attack library.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available attacks and categories, then exit without scanning.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export the scan report as json under reports/.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a detailed per-attack table in addition to the summary.",
    )
    parser.add_argument(
        "--judge",
        choices=PROVIDER_NAMES,
        help="Force this provider to judge every response, bypassing random "
        "non-self judge selection.",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Wait this many seconds between each attack, useful for staying under "
        "free tier rate limits during --all runs.",
    )

    return parser


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Cross flag checks argparse's own choices/action rules can't express."""
    if args.list:
        return  # --list ignores every scan related flag, always valid alone

    has_attack_selection = args.all or args.attack or args.attack_category
    if not has_attack_selection:
        parser.error("specify --all, --attack, --attack-category, or --list")