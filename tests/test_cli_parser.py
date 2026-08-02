"""Tests for CLI argument parsing and flag validation."""

from __future__ import annotations

import pytest

from prompt_sentry.cli.parser import build_parser, validate_args


def test_all_flag_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["--all"])

    assert args.all is True
    assert args.attack is None


def test_repeated_provider_flag_accumulates_into_a_list() -> None:
    parser = build_parser()
    args = parser.parse_args(["--all", "--provider", "groq", "--provider", "mistral"])

    assert args.provider == ["groq", "mistral"]


def test_repeated_attack_flag_accumulates_into_a_list() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--attack",
            "injection-ignore-previous-instructions",
            "--attack",
            "jailbreak-persona-override",
        ]
    )

    assert args.attack == [
        "injection-ignore-previous-instructions",
        "jailbreak-persona-override",
    ]

def test_invalid_provider_choice_exits() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--all", "--provider", "not-a-real-provider"])


def test_invalid_attack_category_choice_exits() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--attack-category", "not-a-real-category"])


def test_verbose_and_json_default_to_false() -> None:
    parser = build_parser()
    args = parser.parse_args(["--all"])

    assert args.verbose is False
    assert args.json is False


def test_validate_args_allows_list_with_no_other_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["--list"])

    validate_args(args, parser)  # should not raise


def test_validate_args_rejects_no_attack_selection_at_all() -> None:
    parser = build_parser()
    args = parser.parse_args([])

    with pytest.raises(SystemExit):
        validate_args(args, parser)


def test_validate_args_allows_attack_and_category_combined() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["--attack-category", "jailbreak", "--attack", "injection-ignore-previous-instructions"]
    )

    validate_args(args, parser)  # should not raise