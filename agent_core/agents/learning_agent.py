"""Learning Agent: tabular Q-learning.

Maps onto the four components of a learning agent (Russell & Norvig):
  performance element -> epsilon-greedy policy over the Q-table (`decide`)
  critic              -> the performance measure (reward passed to `observe_outcome`)
  learning element    -> the Q-value update rule
  problem generator   -> exploration (epsilon): occasionally try a random action

State abstraction keeps the table small: (standing on dirt?, code of each of
the 4 neighbours, direction hint) where code = blocked / clean-visited /
clean-unvisited / dirty, and the hint is the first step towards the nearest
known dirt / unvisited cell according to the agent's own memory (WorldModel).
The agent is NOT told what to do with the hint; it must learn that following it pays off.
Action masking: moves that the sensors show as blocked, and SUCK on a clean cell,
are never candidates (otherwise an untried action has Q=0 and looks better than
any learned negative value). The agent still has to LEARN which legal action is best.
Reward = performance-measure reward + a small novelty bonus (reward shaping),
otherwise the agent gets no signal for exploring clean areas.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from ..settings import LearningConfig
from ..domain import MOVE_ACTIONS, Action, ActionResult, Candidate, CellType, Decision, Outcome, Percept, Position
from .base_agent import BLOCKED, BaseAgent
from .pathfinding import bfs_path
from .world_model import WorldModel

LEARNER_ACTIONS: tuple[Action, ...] = MOVE_ACTIONS + (Action.SUCK,)
State = tuple


class LearningAgent(BaseAgent):
    kind = "learning"
    display_name = "Learning Agent (Q-learning)"
    description = "Learns from experience which action is best in each abstract situation. Trained on random worlds first."

    def __init__(self, seed: int = 0, config: LearningConfig = LearningConfig()) -> None:
        super().__init__(seed)
        self.config = config
        self.q_table: dict[State, dict[Action, float]] = defaultdict(lambda: {a: 0.0 for a in LEARNER_ACTIONS})
        self.epsilon = 0.0
        self.training = False
        self.model = WorldModel()
        self._last_state: State | None = None

    def start_episode(self) -> None:
        self.model = WorldModel()
        self._last_state = None

    def set_training(self, enabled: bool) -> None:
        self.training = enabled
        if not enabled:
            self.epsilon = 0.0

    def decide(self, percept: Percept, history: Sequence[Percept]) -> Decision:
        self.model.update(percept)  # idempotent for an already-seen percept
        state = self._encode(percept)
        self._last_state = state
        q_values = self.q_table[state]
        legal = self._legal_actions(percept)
        if not legal:
            return Decision(Action.STOP, "Boxed in: no legal action -> STOP.", self.available_actions(percept))
        candidates = tuple(Candidate(a, q_values[a], {"q_value": q_values[a]}) for a in legal)
        available = self.available_actions(percept)

        if self.training and self.rng.random() < self.epsilon:
            action = self.rng.choice(legal)
            reason = f"Exploration (epsilon={self.epsilon:.2f}): trying a random action to gather experience."
        else:
            best = max(q_values[a] for a in legal)
            action = self.rng.choice([a for a in legal if q_values[a] == best])
            reason = f"Exploitation: {action.value} has the highest learned Q-value ({best:+.2f}) in this situation."
        return Decision(action, reason, available, candidates)

    def observe_outcome(self, percept: Percept, decision: Decision, result: ActionResult,
                        reward: float, next_percept: Percept, done: bool) -> None:
        if not self.training or self._last_state is None:
            return
        shaped = reward
        if result.outcome is Outcome.MOVED and self.model.visit_counts[next_percept.position] == 0:
            shaped += self.config.novelty_bonus
        self.model.update(next_percept)
        next_state = self._encode(next_percept)
        next_q = self.q_table[next_state]
        future = 0.0 if done else max(next_q[a] for a in self._legal_actions(next_percept))
        old = self.q_table[self._last_state][decision.action]
        if decision.action in LEARNER_ACTIONS:
            self.q_table[self._last_state][decision.action] = old + self.config.alpha * (
                shaped + self.config.gamma * future - old)

    @staticmethod
    def _legal_actions(percept: Percept) -> tuple[Action, ...]:
        moves = tuple(a for a in MOVE_ACTIONS if percept.neighbors[a] not in BLOCKED)
        return moves + ((Action.SUCK,) if percept.current_cell is CellType.DIRTY else ())

    def _hint(self, percept: Percept) -> int:
        here = percept.position
        path = bfs_path(here, self.model.is_free, self.model.is_known_dirty)
        if not path and not self.model.fully_observed:
            path = bfs_path(here, self.model.is_free, self.model.is_unvisited_free)
        if not path:
            return 0
        return 1 + MOVE_ACTIONS.index(here.direction_to(path[0]))

    def _encode(self, percept: Percept) -> State:
        codes = []
        for action in MOVE_ACTIONS:
            cell = percept.neighbors[action]
            if cell in BLOCKED:
                codes.append(0)
            elif cell is CellType.DIRTY:
                codes.append(3)
            elif self.model.visit_counts[percept.position.shifted(action)] > 0:
                codes.append(1)
            else:
                codes.append(2)
        return (percept.current_cell is CellType.DIRTY, *codes, self._hint(percept))
