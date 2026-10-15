"""Shared vocabulary of the agent world: percepts, actions, decisions, records.

Everything here is a plain, immutable value object. No Django, no I/O.
AI concepts: Percept, Action, Agent Function (percept sequence -> action).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CellType(str, Enum):
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    OBSTACLE = "OBSTACLE"
    WALL = "WALL"  # only appears in percepts: "the grid ends here"


class Action(str, Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    SUCK = "SUCK"
    STOP = "STOP"

    @property
    def is_move(self) -> bool:
        return self in MOVE_DELTAS


# (row delta, col delta). Order matters: it is the fixed tie-breaking order everywhere.
MOVE_DELTAS: dict[Action, tuple[int, int]] = {
    Action.MOVE_UP: (-1, 0),
    Action.MOVE_DOWN: (1, 0),
    Action.MOVE_LEFT: (0, -1),
    Action.MOVE_RIGHT: (0, 1),
}
MOVE_ACTIONS: tuple[Action, ...] = tuple(MOVE_DELTAS)


class Outcome(str, Enum):
    """What the environment reports after an actuator executed an action."""
    MOVED = "MOVED"
    CLEANED = "CLEANED"
    BUMPED_OBSTACLE = "BUMPED_OBSTACLE"
    BUMPED_WALL = "BUMPED_WALL"
    WASTED_SUCK = "WASTED_SUCK"
    STOPPED = "STOPPED"


class SensorMode(str, Enum):
    LOCAL = "LOCAL"  # partially observable: own cell + 4 neighbours
    FULL = "FULL"    # fully observable: whole grid


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED_EARLY = "STOPPED_EARLY"
    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"


@dataclass(frozen=True, order=True)
class Position:
    row: int
    col: int

    def shifted(self, action: Action) -> "Position":
        d_row, d_col = MOVE_DELTAS[action]
        return Position(self.row + d_row, self.col + d_col)

    def direction_to(self, other: "Position") -> Optional[Action]:
        for action, (d_row, d_col) in MOVE_DELTAS.items():
            if (self.row + d_row, self.col + d_col) == (other.row, other.col):
                return action
        return None


@dataclass(frozen=True)
class Percept:
    """Everything the agent is allowed to know at one moment."""
    step: int
    position: Position
    current_cell: CellType
    neighbors: dict[Action, CellType]
    global_view: Optional[tuple[tuple[CellType, ...], ...]] = None  # FULL mode only


@dataclass(frozen=True)
class ActionResult:
    action: Action
    outcome: Outcome
    position_after: Position

    @property
    def success(self) -> bool:
        return self.outcome in (Outcome.MOVED, Outcome.CLEANED, Outcome.STOPPED)

    @property
    def cleaned(self) -> bool:
        return self.outcome is Outcome.CLEANED


@dataclass(frozen=True)
class Candidate:
    """One option the agent considered, with an optional numeric breakdown."""
    action: Action
    utility: Optional[float] = None
    components: dict[str, float] = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class Decision:
    """Output of the agent program: the action plus an explanation of it."""
    action: Action
    reason: str
    available_actions: tuple[Action, ...]
    candidates: tuple[Candidate, ...] = ()
    plan: tuple[Position, ...] = ()


@dataclass(frozen=True)
class PerformanceSnapshot:
    score: float
    steps: int
    dirt_cleaned: int
    remaining_dirt: int
    invalid_actions: int
    efficiency: float
    status: RunStatus


@dataclass(frozen=True)
class StepRecord:
    step: int
    percept: Percept
    decision: Decision
    result: ActionResult
    reward: float
    performance: PerformanceSnapshot
