"""Simple Reflex Agent: condition-action rules on the CURRENT percept only.

It has no memory, no map and no plan, so it can wander in circles and has no
guarantee of finding all dirt. That weakness is intentional and measurable.
"""
from __future__ import annotations

from typing import Sequence

from ..domain import MOVE_ACTIONS, Action, CellType, Decision, Percept
from .base_agent import BLOCKED, BaseAgent


class SimpleReflexAgent(BaseAgent):
    kind = "reflex"
    display_name = "Simple Reflex Agent"
    description = "Condition-action rules on the current percept only. No memory, no plan."

    def decide(self, percept: Percept, history: Sequence[Percept]) -> Decision:
        available = self.available_actions(percept)

        if percept.current_cell is CellType.DIRTY:  # rule 1
            return Decision(Action.SUCK, "Rule 1: current cell is DIRTY -> SUCK.", available)

        dirty_neighbors = [a for a in MOVE_ACTIONS if percept.neighbors[a] is CellType.DIRTY]
        if dirty_neighbors:  # rule 2
            action = dirty_neighbors[0]
            return Decision(action, f"Rule 2: neighbour {action.value[5:]} is DIRTY -> move towards it.", available)

        free_moves = [a for a in MOVE_ACTIONS if percept.neighbors[a] not in BLOCKED]
        if free_moves:  # rule 3
            action = self.rng.choice(free_moves)
            return Decision(action, "Rule 3: nothing dirty nearby -> move to a random free neighbour.", available)

        return Decision(Action.STOP, "Boxed in: no free neighbour -> STOP.", available)
