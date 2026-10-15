"""Environment: owns the ground truth and enforces the rules of the world.

AI concept: Environment. The agent never touches this class directly; only
Sensors (read) and Actuators (write) hold a reference to it.
Properties (Russell & Norvig): discrete, single-agent, static (apart from the
agent's own cleaning), deterministic, sequential.
"""
from __future__ import annotations

from ..domain import Action, ActionResult, CellType, Outcome, Position
from .grid import Grid


class Environment:
    def __init__(self, grid: Grid, vacuum: Position) -> None:
        if not grid.is_free(vacuum):
            raise ValueError("Vacuum start must be inside the grid and not on an obstacle.")
        self.grid = grid
        self.vacuum = vacuum
        self.step_count = 0
        # Obstacles never change, so reachability is fixed for the whole episode.
        self._reachable = grid.reachable_from(vacuum)
        self._remaining_dirt = sum(1 for p in self._reachable if grid.cell(p).is_dirty)

    @property
    def height(self) -> int:
        return self.grid.height

    @property
    def width(self) -> int:
        return self.grid.width

    @property
    def remaining_dirt(self) -> int:
        """Dirty cells the vacuum can still reach (performance/termination only)."""
        return self._remaining_dirt

    def reachable_dirt(self) -> set[Position]:
        return {p for p in self._reachable if self.grid.cell(p).is_dirty}

    def is_complete(self) -> bool:
        return self._remaining_dirt == 0

    def apply(self, action: Action) -> ActionResult:
        """The single place where the rules of the world are enforced."""
        self.step_count += 1
        if action is Action.STOP:
            return ActionResult(action, Outcome.STOPPED, self.vacuum)
        if action is Action.SUCK:
            cell = self.grid.cell(self.vacuum)
            if cell.is_dirty:
                cell.clean()
                self._remaining_dirt -= 1
                return ActionResult(action, Outcome.CLEANED, self.vacuum)
            return ActionResult(action, Outcome.WASTED_SUCK, self.vacuum)
        target = self.vacuum.shifted(action)
        if not self.grid.in_bounds(target):
            return ActionResult(action, Outcome.BUMPED_WALL, self.vacuum)
        if self.grid.cell(target).is_obstacle:
            return ActionResult(action, Outcome.BUMPED_OBSTACLE, self.vacuum)
        self.vacuum = target
        return ActionResult(action, Outcome.MOVED, self.vacuum)

    def snapshot(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "cells": self.grid.to_rows(),
            "vacuum": [self.vacuum.row, self.vacuum.col],
        }

    @classmethod
    def from_snapshot(cls, data: dict) -> "Environment":
        try:
            grid = Grid.from_rows(list(data["cells"]))
            row, col = data["vacuum"]
            return cls(grid, Position(int(row), int(col)))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid environment layout: {error}") from error

    def dirt_count(self) -> int:
        return self.grid.count(CellType.DIRTY)
