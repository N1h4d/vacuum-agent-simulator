"""Training loop for the Learning Agent (kept outside the agent on purpose)."""
from __future__ import annotations

from dataclasses import replace

from ..agents.learning_agent import LearningAgent
from ..environment.generator import EnvironmentGenerator, GenerationParams
from ..settings import LearningConfig, SimulationConfig
from .simulator import Simulator


def train_learning_agent(agent: LearningAgent, params: GenerationParams, config: SimulationConfig,
                         learning: LearningConfig = LearningConfig()) -> list[float]:
    """Run `episodes` random worlds with exploration; return the score of each episode."""
    generator = EnvironmentGenerator()
    base_seed = params.seed or 0
    scores: list[float] = []
    agent.set_training(True)
    for episode in range(learning.episodes):
        progress = episode / max(1, learning.episodes - 1)
        agent.epsilon = learning.epsilon_start + progress * (learning.epsilon_end - learning.epsilon_start)
        env = generator.generate(replace(params, seed=base_seed * 1000 + episode, random_start=True))
        trace = Simulator(env, agent, config).run()
        scores.append(trace.summary.score)
    agent.set_training(False)
    return scores
