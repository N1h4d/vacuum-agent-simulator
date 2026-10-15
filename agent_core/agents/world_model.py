"""WorldModel: the agent's INTERNAL map, built only from percepts.

AI concept: model-based agent (internal state that tracks the part of the
world the agent cannot currently see).
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

from ..domain import MOVE_ACTIONS, CellType, Percept, Position

FREE = (CellType.CLEAN, CellType.DIRTY)


class WorldModel:
    def __init__(self) -> None:
        self.known: dict[Position, CellType] = {}
        self.visit_counts: Counter[Position] = Counter()
        self.fully_observed = False
        self._last_position: Optional[Position] = None

    def update(self, percept: Percept) -> None:
        if percept.position != self._last_position:
            self.visit_counts[percept.position] += 1
            self._last_position = percept.position
        self.known[percept.position] = percept.current_cell
        for action in MOVE_ACTIONS:
            self.known[percept.position.shifted(action)] = percept.neighbors[action]
        if percept.global_view is not None:
            self.fully_observed = True
            for r, row in enumerate(percept.global_view):
                for c, cell_type in enumerate(row):
                    self.known[Position(r, c)] = cell_type

    def is_free(self, pos: Position) -> bool:
        return self.known.get(pos) in FREE

    def is_known_dirty(self, pos: Position) -> bool:
        return self.known.get(pos) is CellType.DIRTY

    def is_unvisited_free(self, pos: Position) -> bool:
        return self.is_free(pos) and self.visit_counts[pos] == 0

    def known_dirt_count(self) -> int:
        return sum(1 for t in self.known.values() if t is CellType.DIRTY)
