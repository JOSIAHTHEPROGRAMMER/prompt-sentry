"""Aggregates every attack category into one queryable library.

This is what the CLI's --attack and --all flags actually query against.
Individual category files only guarantee id uniqueness within
themselves, this is the one place that checks it holds across the
whole library.
"""

from __future__ import annotations

from prompt_sentry.attacks.base import Attack, AttackCategory
from prompt_sentry.attacks.data_extraction import DATA_EXTRACTION_ATTACKS
from prompt_sentry.attacks.encoding_obfuscation import ENCODING_OBFUSCATION_ATTACKS
from prompt_sentry.attacks.injection import INJECTION_ATTACKS
from prompt_sentry.attacks.jailbreak import JAILBREAK_ATTACKS
from prompt_sentry.attacks.role_manipulation import ROLE_MANIPULATION_ATTACKS
from prompt_sentry.attacks.system_prompt_leak import SYSTEM_PROMPT_LEAK_ATTACKS

ALL_ATTACKS: tuple[Attack, ...] = (
    INJECTION_ATTACKS
    + JAILBREAK_ATTACKS
    + ROLE_MANIPULATION_ATTACKS
    + DATA_EXTRACTION_ATTACKS
    + SYSTEM_PROMPT_LEAK_ATTACKS
    + ENCODING_OBFUSCATION_ATTACKS
)

# built once at import time, --attack lookups shouldn't do a linear scan
_ATTACKS_BY_ID: dict[str, Attack] = {attack.id: attack for attack in ALL_ATTACKS}


def get_all_attacks() -> tuple[Attack, ...]:
    return ALL_ATTACKS


def get_attacks_by_category(category: AttackCategory) -> tuple[Attack, ...]:
    return tuple(attack for attack in ALL_ATTACKS if attack.category == category)


def get_attack_by_id(attack_id: str) -> Attack:
    try:
        return _ATTACKS_BY_ID[attack_id]
    except KeyError:
        raise KeyError(f"no attack found with id '{attack_id}'") from None