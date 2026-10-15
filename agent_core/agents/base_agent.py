"""BaseAgent: the Agent Program interface.

AI concepts:
  * Agent Function  - the abstract mapping  percept sequence -> action.
  * Agent Program   - a concrete implementation of that mapping: `decide`.
An agent is constructed WITHOUT an environment, so it cannot cheat.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import ClassVar, Sequence

from ..domain import MOVE_ACTIONS, Action, ActionResult, CellType, Decision, Percept

BLOCKED = (CellType.OBSTACLE, CellType.WALL)


class BaseAgent(ABC):
    kind: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def start_episode(self) -> None:
        """Clear per-episode memory (learned knowledge, if any, is kept)."""

    @abstractmethod
    def decide(self, percept: Percept, history: Sequence[Percept]) -> Decision:
        """Agent program: choose an action from the current percept (and history)."""

    def observe_outcome(self, percept: Percept, decision: Decision, result: ActionResult,
                        reward: float, next_percept: Percept, done: bool) -> None:
        """Feedback hook; only learning agents use it."""

    @staticmethod
    def available_actions(percept: Percept) -> tuple[Action, ...]:
        moves = tuple(a for a in MOVE_ACTIONS if percept.neighbors[a] not in BLOCKED)
        return moves + (Action.SUCK, Action.STOP)
