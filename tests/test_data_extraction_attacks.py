"""Tests for the data extraction attack library."""

from __future__ import annotations

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.data_extraction import DATA_EXTRACTION_ATTACKS


def test_has_at_least_eight_attacks() -> None:
    assert len(DATA_EXTRACTION_ATTACKS) >= 8


def test_all_ids_are_unique() -> None:
    ids = [attack.id for attack in DATA_EXTRACTION_ATTACKS]
    assert len(ids) == len(set(ids))


def test_all_attacks_are_categorized_as_data_extraction() -> None:
    for attack in DATA_EXTRACTION_ATTACKS:
        assert attack.category == AttackCategory.DATA_EXTRACTION


def test_every_attack_has_a_non_empty_prompt() -> None:
    for attack in DATA_EXTRACTION_ATTACKS:
        assert attack.prompt.strip() != ""


def test_every_attack_cites_at_least_one_reference() -> None:
    for attack in DATA_EXTRACTION_ATTACKS:
        assert len(attack.references) > 0