"""Performance Measure: scores the agent by what happened in the ENVIRONMENT.

AI concept: Performance Measure / Rational Agent. A rational agent is one that
maximises the expected value of this measure, not one that "feels" it did well.
"""
from __future__ import annotations

from ..domain import ActionResult, PerformanceSnapshot, RunStatus
from ..settings import ScoringConfig


class PerformanceMeasure:
    def __init__(self, scoring: ScoringConfig = ScoringConfig()) -> None:
        self.scoring = scoring
        self.score = 0.0
        self.steps = 0
        self.dirt_cleaned = 0
        self.invalid_actions = 0

    def register(self, result: ActionResult, completed: bool) -> float:
        """Update counters for one executed action and return the reward earned."""
        reward = self.scoring.reward_for(result.outcome)
        if completed:
            reward += self.scoring.completion_bonus
        self.score += reward
        self.steps += 1
        self.dirt_cleaned += int(result.cleaned)
        self.invalid_actions += int(not result.success)
        return reward

    def snapshot(self, remaining_dirt: int, status: RunStatus) -> PerformanceSnapshot:
        efficiency = self.dirt_cleaned / self.steps if self.steps else 0.0
        return PerformanceSnapshot(self.score, self.steps, self.dirt_cleaned, remaining_dirt,
                                   self.invalid_actions, round(efficiency, 3), status)
