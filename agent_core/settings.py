"""All tunable numbers live here (no magic numbers in the logic)."""
from __future__ import annotations

from dataclasses import dataclass

from .domain import Outcome, SensorMode

MIN_GRID_SIZE = 3
MAX_GRID_SIZE = 20


@dataclass(frozen=True)
class ScoringConfig:
    """Performance measure (the P in PEAS). Judged on environment outcomes."""
    dirt_cleaned: float = 10.0
    move_cost: float = -1.0
    collision_penalty: float = -5.0
    wasted_suck_penalty: float = -2.0
    completion_bonus: float = 20.0

    def reward_for(self, outcome: Outcome) -> float:
        return {
            Outcome.CLEANED: self.dirt_cleaned,
            Outcome.MOVED: self.move_cost,
            Outcome.BUMPED_OBSTACLE: self.collision_penalty,
            Outcome.BUMPED_WALL: self.collision_penalty,
            Outcome.WASTED_SUCK: self.wasted_suck_penalty,
            Outcome.STOPPED: 0.0,
        }[outcome]


@dataclass(frozen=True)
class UtilityWeights:
    progress: float = 3.0               # per step closer to the current target
    revisit_penalty: float = 0.5        # per previous visit of the next cell
    max_revisits_counted: int = 4
    explore_bonus: float = 0.5          # next cell never visited before
    stop_unfinished_penalty: float = 50.0


@dataclass(frozen=True)
class LearningConfig:
    episodes: int = 80
    alpha: float = 0.1
    gamma: float = 0.9
    epsilon_start: float = 0.4
    epsilon_end: float = 0.02
    novelty_bonus: float = 1.0          # reward shaping: stepping on a new cell


@dataclass(frozen=True)
class SimulationConfig:
    max_steps_per_cell: int = 4
    sensor_mode: SensorMode = SensorMode.LOCAL
    agent_seed: int = 42

    def max_steps(self, height: int, width: int) -> int:
        return height * width * self.max_steps_per_cell
