"""Actuators: the ONLY channel through which an agent changes the Environment.

AI concept: Actuators / Actions. Only members of the Action enum are accepted.
"""
from __future__ import annotations

from ..environment.environment import Environment
from ..domain import Action, ActionResult


class Actuators:
    def __init__(self, environment: Environment) -> None:
        self._environment = environment

    def execute(self, action: Action) -> ActionResult:
        if not isinstance(action, Action):
            raise ValueError(f"Illegal action: {action!r}. Allowed: {[a.value for a in Action]}")
        return self._environment.apply(action)
