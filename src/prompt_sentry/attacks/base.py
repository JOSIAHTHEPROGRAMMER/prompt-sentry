"""Shared shape every attack in the library conforms to.

Attacks are data, not behavior. Sending one is the provider's job, judging
the response is the scorer's job. This file only defines what an attack
looks like on paper.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackCategory(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    ROLE_MANIPULATION = "role_manipulation"
    DATA_EXTRACTION = "data_extraction"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    ENCODING_OBFUSCATION = "encoding_obfuscation"


@dataclass(frozen=True)
class Attack:
    id: str
    name: str
    category: AttackCategory
    prompt: str
    description: str
    references: tuple[str, ...] = ()