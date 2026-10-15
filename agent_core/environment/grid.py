"""Grid: pure storage + geometry queries (bounds, obstacles, reachability)."""
from __future__ import annotations

from collections import deque

from ..domain import MOVE_ACTIONS, CellType, Position
from .cell import Cell

SYMBOLS: dict[CellType, str] = {CellType.CLEAN: ".", CellType.DIRTY: "D", CellType.OBSTACLE: "#"}
FROM_SYMBOL: dict[str, CellType] = {symbol: cell_type for cell_type, symbol in SYMBOLS.items()}


class Grid:
    def __init__(self, height: int, width: int) -> None:
        if height < 1 or width < 1:
            raise ValueError("Grid must have at least one row and one column.")
        self.height = height
        self.width = width
        self._cells = [[Cell() for _ in range(width)] for _ in range(height)]

    @classmethod
    def from_rows(cls, rows: list[str]) -> "Grid":
        if not rows or len({len(row) for row in rows}) != 1:
            raise ValueError("Layout rows must be non-empty and of equal length.")
        grid = cls(len(rows), len(rows[0]))
        for r, row in enumerate(rows):
            for c, symbol in enumerate(row):
                if symbol not in FROM_SYMBOL:
                    raise ValueError(f"Unknown cell symbol {symbol!r}.")
                grid._cells[r][c].cell_type = FROM_SYMBOL[symbol]
        return grid

    def to_rows(self) -> list[str]:
        return ["".join(SYMBOLS[cell.cell_type] for cell in row) for row in self._cells]

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.height and 0 <= pos.col < self.width

    def cell(self, pos: Position) -> Cell:
        return self._cells[pos.row][pos.col]

    def is_free(self, pos: Position) -> bool:
        return self.in_bounds(pos) and not self.cell(pos).is_obstacle

    def positions(self) -> list[Position]:
        return [Position(r, c) for r in range(self.height) for c in range(self.width)]

    def count(self, cell_type: CellType) -> int:
        return sum(1 for pos in self.positions() if self.cell(pos).cell_type is cell_type)

    def reachable_from(self, start: Position) -> set[Position]:
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for action in MOVE_ACTIONS:
                nxt = current.shifted(action)
                if nxt not in seen and self.is_free(nxt):
                    seen.add(nxt)
                    queue.append(nxt)
        return seen
