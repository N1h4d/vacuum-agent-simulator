"""Sensors: the ONLY channel through which information leaves the Environment.

AI concept: Sensors / Percepts / (partial vs full) observability.
"""
from __future__ import annotations

from ..environment.environment import Environment
from ..domain import MOVE_ACTIONS, CellType, Percept, Position, SensorMode


class Sensors:
    def __init__(self, environment: Environment, mode: SensorMode = SensorMode.LOCAL) -> None:
        self._environment = environment
        self.mode = mode

    def perceive(self) -> Percept:
        env, grid = self._environment, self._environment.grid
        here = env.vacuum
        neighbors = {}
        for action in MOVE_ACTIONS:
            nxt = here.shifted(action)
            neighbors[action] = grid.cell(nxt).cell_type if grid.in_bounds(nxt) else CellType.WALL
        global_view = None
        if self.mode is SensorMode.FULL:
            global_view = tuple(
                tuple(grid.cell(Position(r, c)).cell_type for c in range(env.width))
                for r in range(env.height)
            )
        return Percept(env.step_count, here, grid.cell(here).cell_type, neighbors, global_view)
