"""Breadth-first search on the grid.

Why BFS: every move costs the same (unweighted graph), so BFS returns a
shortest path and is complete. DFS is not shortest; A* adds nothing here
because with uniform costs it expands the same shortest path.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Optional

from ..domain import MOVE_ACTIONS, Position


def bfs_path(start: Position, is_passable: Callable[[Position], bool],
             is_goal: Callable[[Position], bool]) -> Optional[list[Position]]:
    """Shortest path from `start` (excluded) to the nearest goal cell, or None."""
    parents: dict[Position, Optional[Position]] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current != start and is_goal(current):
            path = []
            node: Optional[Position] = current
            while node is not None and node != start:
                path.append(node)
                node = parents[node]
            return path[::-1]
        for action in MOVE_ACTIONS:
            nxt = current.shifted(action)
            if nxt not in parents and is_passable(nxt):
                parents[nxt] = current
                queue.append(nxt)
    return None


def distance_to_goal(start: Position, is_passable: Callable[[Position], bool],
                     is_goal: Callable[[Position], bool]) -> Optional[int]:
    if is_goal(start):
        return 0
    path = bfs_path(start, is_passable, is_goal)
    return None if path is None else len(path)
