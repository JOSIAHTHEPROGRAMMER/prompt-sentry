"""Tests for the attack registry, the aggregation point every other
attack test file doesn't cover: uniqueness across the whole library,
not just within one category.
"""

from __future__ import annotations

import pytest

from prompt_sentry.attacks.base import AttackCategory
from prompt_sentry.attacks.registry import (
    ALL_ATTACKS,
    get_all_attacks,
    get_attack_by_id,
    get_attacks_by_category,
)


def test_library_has_at_least_forty_eight_attacks() -> None:
    # six categories, at least eight each, this is the whole point of phase 7
    assert len(ALL_ATTACKS) >= 48


def test_all_ids_are_globally_unique() -> None:
    ids = [attack.id for attack in ALL_ATTACKS]
    assert len(ids) == len(set(ids))


def test_get_all_attacks_returns_the_full_library() -> None:
    assert get_all_attacks() == ALL_ATTACKS


def test_get_attacks_by_category_filters_correctly() -> None:
    jailbreaks = get_attacks_by_category(AttackCategory.JAILBREAK)

    assert len(jailbreaks) >= 8
    assert all(attack.category == AttackCategory.JAILBREAK for attack in jailbreaks)


def test_get_attacks_by_category_covers_every_category() -> None:
    # every category should have at least one attack, catches a category
    # file silently failing to get wired into ALL_ATTACKS
    for category in AttackCategory:
        assert len(get_attacks_by_category(category)) > 0


def test_get_attack_by_id_returns_the_right_attack() -> None:
    attack = get_attack_by_id("injection-ignore-previous-instructions")

    assert attack.id == "injection-ignore-previous-instructions"
    assert attack.category == AttackCategory.PROMPT_INJECTION


def test_get_attack_by_id_raises_clear_error_for_unknown_id() -> None:
    with pytest.raises(KeyError, match="no attack found with id 'nonexistent-id'"):
        get_attack_by_id("nonexistent-id")