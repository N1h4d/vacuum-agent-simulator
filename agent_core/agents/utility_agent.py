"""Utility-Based Agent.

For every candidate action it computes an explicit utility and picks the maximum:

  U(a) = immediate_reward(a)          reward/penalty from the performance measure
       + w_progress * (d_before - d_after)   getting closer to the current target
       - w_revisit  * visits(next cell)      discourages pointless backtracking
       + w_explore  * [next cell unvisited]  small curiosity bonus

d = BFS distance (on the agent's own map) to the nearest known dirt, or - if no
dirt is known - to the nearest unvisited free cell. This is a one-step lookahead
with a heuristic, so it is NOT guaranteed to be globally optimal.
"""
from __future__ import annotations

from typing import Optional, Sequence

from ..settings import ScoringConfig, UtilityWeights
from ..domain import MOVE_ACTIONS, Action, Candidate, CellType, Decision, Outcome, Percept, Position
from .base_agent import BLOCKED, BaseAgent
from .pathfinding import bfs_path, distance_to_goal
from .world_model import WorldModel


class UtilityBasedAgent(BaseAgent):
    kind = "utility"
    display_name = "Utility-Based Agent"
    description = "Scores every action with an explicit utility function (reward, progress, revisit cost) and picks the best."

    def __init__(self, seed: int = 0, scoring: ScoringConfig = ScoringConfig(),
                 weights: UtilityWeights = UtilityWeights()) -> None:
        super().__init__(seed)
        self.scoring = scoring
        self.weights = weights
        self.model = WorldModel()

    def start_episode(self) -> None:
        self.model = WorldModel()

    def decide(self, percept: Percept, history: Sequence[Percept]) -> Decision:
        self.model.update(percept)
        here = percept.position
        goal = self._goal_test()
        d_before = distance_to_goal(here, self.model.is_free, goal)

        candidates = [self._score_move(percept, a, d_before, goal) for a in MOVE_ACTIONS]
        candidates.append(self._score_suck(percept))
        candidates.append(self._score_stop(d_before))

        best = max(candidates, key=lambda c: c.utility)  # first max wins => deterministic
        runner_up = sorted((c for c in candidates if c is not best), key=lambda c: -c.utility)[0]
        parts = ", ".join(f"{name} {value:+.1f}" for name, value in best.components.items() if value)
        reason = (f"{best.action.value} has the highest utility U={best.utility:+.1f} ({parts or 'all terms zero'}). "
                  f"Runner-up: {runner_up.action.value} U={runner_up.utility:+.1f}.")
        return Decision(best.action, reason, self.available_actions(percept), tuple(candidates), self._plan(here, goal))

    # -- utility terms ------------------------------------------------------
    def _goal_test(self):
        if self.model.known_dirt_count() > 0:
            return self.model.is_known_dirty
        if not self.model.fully_observed:
            return self.model.is_unvisited_free
        return lambda pos: False

    def _score_move(self, percept: Percept, action: Action, d_before: Optional[int], goal) -> Candidate:
        neighbor = percept.neighbors[action]
        if neighbor in BLOCKED:
            outcome = Outcome.BUMPED_WALL if neighbor is CellType.WALL else Outcome.BUMPED_OBSTACLE
            reward = self.scoring.reward_for(outcome)
            return Candidate(action, reward, {"immediate_reward": reward}, "blocked: would collide")
        target = percept.position.shifted(action)
        d_after = distance_to_goal(target, self.model.is_free, goal)
        progress = 0.0
        if d_before is not None and d_after is not None:
            progress = self.weights.progress * (d_before - d_after)
        visits = min(self.model.visit_counts[target], self.weights.max_revisits_counted)
        components = {
            "immediate_reward": self.scoring.reward_for(Outcome.MOVED),
            "progress": progress,
            "revisit_penalty": -self.weights.revisit_penalty * visits,
            "explore_bonus": self.weights.explore_bonus if self.model.visit_counts[target] == 0 else 0.0,
        }
        return Candidate(action, sum(components.values()), components)

    def _score_suck(self, percept: Percept) -> Candidate:
        outcome = Outcome.CLEANED if percept.current_cell is CellType.DIRTY else Outcome.WASTED_SUCK
        reward = self.scoring.reward_for(outcome)
        return Candidate(Action.SUCK, reward, {"immediate_reward": reward})

    def _score_stop(self, d_before: Optional[int]) -> Candidate:
        penalty = -self.weights.stop_unfinished_penalty if d_before is not None else 0.0
        return Candidate(Action.STOP, penalty, {"unfinished_penalty": penalty})

    def _plan(self, here: Position, goal) -> tuple[Position, ...]:
        path = bfs_path(here, self.model.is_free, goal)
        return tuple(path) if path else ()
