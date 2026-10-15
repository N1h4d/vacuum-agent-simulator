from __future__ import annotations

from dataclasses import dataclass

from ..domain import CellType


@dataclass
class Cell:
    cell_type: CellType = CellType.CLEAN

    @property
    def is_dirty(self) -> bool:
        return self.cell_type is CellType.DIRTY

    @property
    def is_obstacle(self) -> bool:
        return self.cell_type is CellType.OBSTACLE

    def clean(self) -> None:
        self.cell_type = CellType.CLEAN
