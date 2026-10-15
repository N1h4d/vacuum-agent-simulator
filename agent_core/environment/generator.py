"""Random and manual environment creation (seeded => reproducible)."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from ..settings import MAX_GRID_SIZE, MIN_GRID_SIZE
from ..domain import CellType, Position
from .environment import Environment
from .grid import Grid


@dataclass(frozen=True)
class GenerationParams:
    width: int = 10
    height: int = 10
    dirt_percent: float = 30.0
    obstacle_percent: float = 10.0
    random_start: bool = True
    seed: Optional[int] = None

    def validate(self) -> None:
        for name, size in (("width", self.width), ("height", self.height)):
            if not MIN_GRID_SIZE <= size <= MAX_GRID_SIZE:
                raise ValueError(f"{name} must be between {MIN_GRID_SIZE} and {MAX_GRID_SIZE}.")
        for name, pct in (("dirt_percent", self.dirt_percent), ("obstacle_percent", self.obstacle_percent)):
            if not 0 <= pct <= 100:
                raise ValueError(f"{name} must be between 0 and 100.")
        if self.dirt_percent + self.obstacle_percent > 100:
            raise ValueError("dirt_percent + obstacle_percent must not exceed 100.")

    @classmethod
    def from_environment(cls, env: Environment, seed: Optional[int] = None) -> "GenerationParams":
        total = env.width * env.height
        return cls(
            width=env.width,
            height=env.height,
            dirt_percent=100 * env.dirt_count() / total,
            obstacle_percent=100 * env.grid.count(CellType.OBSTACLE) / total,
            random_start=True,
            seed=seed,
        )


class EnvironmentGenerator:
    def generate(self, params: GenerationParams) -> Environment:
        params.validate()
        rng = random.Random(params.seed)
        grid = Grid(params.height, params.width)
        positions = grid.positions()
        start = rng.choice(positions) if params.random_start else Position(0, 0)

        others = [p for p in positions if p != start]  # the start cell stays clean
        rng.shuffle(others)
        total = len(positions)
        obstacle_count = min(round(total * params.obstacle_percent / 100), len(others))
        dirt_count = min(round(total * params.dirt_percent / 100), len(others) - obstacle_count)

        for pos in others[:obstacle_count]:
            grid.cell(pos).cell_type = CellType.OBSTACLE
        for pos in others[obstacle_count:obstacle_count + dirt_count]:
            grid.cell(pos).cell_type = CellType.DIRTY
        return Environment(grid, start)


def validate_size(env: Environment) -> Environment:
    """Enforce the UI/API grid-size limits on a user-supplied layout."""
    for name, size in (("width", env.width), ("height", env.height)):
        if not MIN_GRID_SIZE <= size <= MAX_GRID_SIZE:
            raise ValueError(f"{name} must be between {MIN_GRID_SIZE} and {MAX_GRID_SIZE}.")
    return env
