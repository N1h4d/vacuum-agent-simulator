"""Goal-Based Agent (with an internal world model).

Goal: clean all reachable dirt. The agent re-plans every step with BFS:
  1. known dirt  -> shortest path to the nearest one, then SUCK
  2. no dirt but unexplored free cells -> shortest path to the nearest one
  3. nothing left -> STOP (goal achieved)
Nearest-first is a greedy strategy: it reaches the goal but is not guaranteed
to produce the globally shortest tour (that would be a travelling-salesman problem).
"""
from __future__ import annotations

from typing import Sequence

from ..domain import Action, CellType, Decision, Percept, Position
from .base_agent import BaseAgent
from .pathfinding import bfs_path
from .world_model import WorldModel


class GoalBasedAgent(BaseAgent):
    kind = "goal"
    display_name = "Goal-Based Agent"
    description = "Keeps a world model and plans shortest paths (BFS) to reach the goal: clean all reachable dirt."

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.model = WorldModel()

    def start_episode(self) -> None:
        self.model = WorldModel()

    def decide(self, percept: Percept, history: Sequence[Percept]) -> Decision:
        self.model.update(percept)
        available = self.available_actions(percept)
        here = percept.position

        if percept.current_cell is CellType.DIRTY:
            return Decision(Action.SUCK, "Goal step: standing on dirt -> SUCK.", available)

        path = bfs_path(here, self.model.is_free, self.model.is_known_dirty)
        if path:
            return self._follow(here, path, available,
                                f"Goal: clean all reachable dirt. Nearest known dirt at {_fmt(path[-1])}, {len(path)} step(s) away.")

        if not self.model.fully_observed:
            path = bfs_path(here, self.model.is_free, self.model.is_unvisited_free)
            if path:
                return self._follow(here, path, available,
                                    f"No known dirt. Exploring nearest unvisited cell {_fmt(path[-1])} ({len(path)} step(s)) to reveal more of the map.")

        return Decision(Action.STOP, "No known dirt and nothing left to explore -> goal achieved, STOP.", available)

    @staticmethod
    def _follow(here: Position, path: list[Position], available: tuple[Action, ...], reason: str) -> Decision:
        action = here.direction_to(path[0])
        assert action is not None
        return Decision(action, f"{reason} Next step: {action.value}.", available, plan=tuple(path))


def _fmt(pos: Position) -> str:
    return f"({pos.row},{pos.col})"
