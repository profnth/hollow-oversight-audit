"""Simulated reviewers and the six oversight structures.

These simulated reviewers are for piloting and power analysis only. Their
parameters are assumptions to be replaced by estimates from human experiments;
nothing produced here is evidence about real people.

A reviewer approves or rejects each AI proposal. Every structure reports, for
each scenario, whether the proposal was executed (approved) and how many
human-review minutes it consumed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .scenarios import Scenario


@dataclass
class HumanReviewer:
    vigilance: float = 0.6  # chance the reviewer actually checks an item against its context
    skill: float = 0.8  # chance a check detects a planted error of average difficulty
    false_alarm: float = 0.05  # chance a check wrongly rejects a correct item
    trust: float = 0.5  # pull toward accepting the AI's view; lowers vigilance when the AI is visible
    persuasion: float = 0.4  # how much an adversarial justification lowers detection
    time_pressure: float = 0.3  # 0 none, 1 severe; lowers vigilance
    minutes_per_check: float = 1.5
    minutes_per_glance: float = 0.2

    def review(self, s: Scenario, rng: random.Random, sees_ai: bool = True,
               flagged: bool = False, independent_first: bool = False) -> tuple[bool, float]:
        """Return (approve, minutes)."""
        vig = self.vigilance * (1 - 0.6 * self.time_pressure)
        if sees_ai and not independent_first:
            vig *= 1 - 0.5 * self.trust
        if flagged:
            vig = min(1.0, vig + 0.35)
        if rng.random() >= vig:
            return True, self.minutes_per_glance  # rubber stamp
        detect = self.skill * (1.2 - s.difficulty)
        if s.adversarial and not independent_first:
            detect *= 1 - self.persuasion
        detect = max(0.0, min(1.0, detect))
        if s.is_harmful:
            return (rng.random() >= detect), self.minutes_per_check
        return (rng.random() >= self.false_alarm), self.minutes_per_check


@dataclass
class AIChecker:
    """A language-model critic or overseer, abstracted as sensitivity/specificity."""
    sensitivity: float = 0.7
    specificity: float = 0.9
    fooled_by_adversarial: float = 0.3  # drop in sensitivity when the AI under review argues

    def flags(self, s: Scenario, rng: random.Random) -> bool:
        if s.is_harmful:
            sens = self.sensitivity * (1 - (self.fooled_by_adversarial if s.adversarial else 0))
            return rng.random() < sens
        return rng.random() >= self.specificity


STRUCTURES = [
    "ai_alone",
    "human_alone",
    "human_signoff",
    "independent_first",
    "ai_critic_then_human",
    "ai_overseer_spot_check",
]


def run_structure(name: str, scenarios: list[Scenario], human: HumanReviewer,
                  checker: AIChecker, seed: int = 0, spot_check_rate: float = 0.1) -> list[dict]:
    rng = random.Random(f"{name}-{seed}")
    rows = []
    for s in scenarios:
        minutes = 0.0
        if name == "ai_alone":
            approve = True  # proposal executes with no review
        elif name == "human_alone":
            # Human judges the item without the AI's recommendation or justification:
            # no trust or persuasion effects.
            approve, minutes = human.review(s, rng, sees_ai=False, independent_first=True)
        elif name == "human_signoff":
            approve, minutes = human.review(s, rng)
        elif name == "independent_first":
            approve, minutes = human.review(s, rng, independent_first=True)
        elif name == "ai_critic_then_human":
            flagged = checker.flags(s, rng)
            approve, minutes = human.review(s, rng, flagged=flagged)
        elif name == "ai_overseer_spot_check":
            flagged = checker.flags(s, rng)
            if flagged:
                approve, minutes = human.review(s, rng, flagged=True)
            elif rng.random() < spot_check_rate:
                approve, minutes = human.review(s, rng)
            else:
                approve = True
        else:
            raise ValueError(f"unknown structure: {name}")
        rows.append({"id": s.id, "structure": name, "approve": approve, "minutes": minutes})
    return rows
