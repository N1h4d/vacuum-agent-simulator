"""Run one or several agents on the SAME environment layout and tabulate results.

Every number in the comparison table comes from a real simulation trace.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from ..agents import create_agent
from ..agents.learning_agent import LearningAgent
from ..domain import SensorMode
from ..environment.environment import Environment
from ..environment.generator import GenerationParams
from ..settings import LearningConfig, SimulationConfig
from .logger import SimulationTrace
from .simulator import Simulator
from .training import train_learning_agent

_TRAINED_CACHE: dict[tuple, tuple[LearningAgent, list[float]]] = {}


def _trained_learner(snapshot: dict, config: SimulationConfig, learning: LearningConfig):
    """Train once per (world statistics, config) and reuse; the cache is only a speed-up."""
    env = Environment.from_snapshot(snapshot)
    params = GenerationParams.from_environment(env, seed=config.agent_seed)
    training_config = replace(config, sensor_mode=SensorMode.LOCAL)  # learner ignores the global view
    key = (env.width, env.height, round(params.dirt_percent), round(params.obstacle_percent),
           config.agent_seed, learning)
    if key not in _TRAINED_CACHE:
        agent = LearningAgent(seed=config.agent_seed, config=learning)
        curve = train_learning_agent(agent, params, training_config, learning)
        _TRAINED_CACHE[key] = (agent, curve)
    return _TRAINED_CACHE[key]


def run_agent(snapshot: dict, kind: str, config: SimulationConfig = SimulationConfig(),
              learning: LearningConfig = LearningConfig()) -> SimulationTrace:
    env = Environment.from_snapshot(snapshot)  # fresh copy: every agent gets identical conditions
    curve: Optional[list[float]] = None
    if kind == "learning":
        agent, curve = _trained_learner(snapshot, config, learning)
        agent.rng.seed(config.agent_seed)
    else:
        agent = create_agent(kind, config.agent_seed)
    trace = Simulator(env, agent, config).run()
    trace.training_curve = curve
    return trace


@dataclass
class ComparisonResult:
    traces: dict[str, SimulationTrace]

    def table(self) -> list[dict]:
        rows = []
        for kind, trace in self.traces.items():
            s = trace.summary
            rows.append({"agent": kind, "name": trace.agent_name, "score": s.score, "steps": s.steps,
                         "dirt_cleaned": s.dirt_cleaned, "remaining_dirt": s.remaining_dirt,
                         "invalid_actions": s.invalid_actions, "efficiency": s.efficiency,
                         "status": s.status.value})
        return rows


def compare_agents(snapshot: dict, kinds: list[str], config: SimulationConfig = SimulationConfig(),
                   learning: LearningConfig = LearningConfig()) -> ComparisonResult:
    return ComparisonResult({kind: run_agent(snapshot, kind, config, learning) for kind in kinds})
