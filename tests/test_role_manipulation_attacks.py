"""Tests for the role manipulation attack library."""

from __future__ import annotations

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.role_manipulation import ROLE_MANIPULATION_ATTACKS


def test_has_at_least_eight_attacks() -> None:
    assert len(ROLE_MANIPULATION_ATTACKS) >= 8


def test_all_ids_are_unique() -> None:
    ids = [attack.id for attack in ROLE_MANIPULATION_ATTACKS]
    assert len(ids) == len(set(ids))


def test_all_attacks_are_categorized_as_role_manipulation() -> None:
    for attack in ROLE_MANIPULATION_ATTACKS:
        assert attack.category == AttackCategory.ROLE_MANIPULATION


def test_every_attack_has_a_non_empty_prompt() -> None:
    for attack in ROLE_MANIPULATION_ATTACKS:
        assert attack.prompt.strip() != ""


def test_every_attack_cites_at_least_one_reference() -> None:
    for attack in ROLE_MANIPULATION_ATTACKS:
        assert len(attack.references) > 0