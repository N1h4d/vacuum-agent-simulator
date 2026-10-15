"""Agent registry: maps the `kind` string used by the UI/API to an agent class."""
from __future__ import annotations

from .base_agent import BaseAgent
from .goal_agent import GoalBasedAgent
from .learning_agent import LearningAgent
from .reflex_agent import SimpleReflexAgent
from .utility_agent import UtilityBasedAgent

AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    cls.kind: cls for cls in (SimpleReflexAgent, GoalBasedAgent, UtilityBasedAgent, LearningAgent)
}


def create_agent(kind: str, seed: int = 0) -> BaseAgent:
    if kind not in AGENT_CLASSES:
        raise ValueError(f"Unknown agent kind {kind!r}. Choose from {sorted(AGENT_CLASSES)}.")
    return AGENT_CLASSES[kind](seed=seed)
