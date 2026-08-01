"""Shared shape every scored result conforms to.

The actual judging logic, calling a provider as judge, picking a non
self judge, parsing its response, lives in judge.py. This file only
defines what a completed (or failed) score looks like on paper.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScoreVerdict(str, Enum):
    RESISTED = "resisted"
    PARTIAL = "partial"
    COMPROMISED = "compromised"


@dataclass(frozen=True)
class ScoreResult:
    attack_id: str
    provider: str
    judged_by: str
    self_judged: bool
    verdict: ScoreVerdict | None
    severity: int | None
    reasoning: str
    error: str | None = None

    def __post_init__(self) -> None:
        if self.severity is not None and not (0 <= self.severity <= 100):
            raise ValueError(f"severity must be between 0 and 100, got {self.severity}")

    @property
    def succeeded(self) -> bool:
        return self.error is None