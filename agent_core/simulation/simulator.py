"""Simulator: the perceive -> decide -> act loop.

AI concept: the agent-environment interaction cycle. The simulator is the only
component that connects Sensors, Agent, Actuators and the Performance Measure.
"""
from __future__ import annotations

from typing import Optional

from ..agents.actuators import Actuators
from ..agents.base_agent import BaseAgent
from ..agents.sensors import Sensors
from ..domain import Action, Percept, RunStatus, StepRecord
from ..environment.environment import Environment
from ..settings import ScoringConfig, SimulationConfig
from .logger import SimulationTrace
from .performance import PerformanceMeasure


class Simulator:
    def __init__(self, environment: Environment, agent: BaseAgent,
                 config: SimulationConfig = SimulationConfig(),
                 scoring: ScoringConfig = ScoringConfig()) -> None:
        self.environment = environment
        self.agent = agent
        self.config = config
        self.sensors = Sensors(environment, config.sensor_mode)
        self.actuators = Actuators(environment)
        self.performance = PerformanceMeasure(scoring)
        self.max_steps = config.max_steps(environment.height, environment.width)
        self.history: list[Percept] = []
        self.status = RunStatus.COMPLETED if environment.is_complete() else RunStatus.RUNNING
        agent.start_episode()
        self.trace = SimulationTrace(
            agent_kind=agent.kind, agent_name=agent.display_name, sensor_mode=config.sensor_mode,
            initial_environment=environment.snapshot(),
            initial_performance=self.performance.snapshot(environment.remaining_dirt, self.status),
        )

    @property
    def finished(self) -> bool:
        return self.status is not RunStatus.RUNNING

    def step(self) -> Optional[StepRecord]:
        """Execute exactly one perceive-decide-act cycle."""
        if self.finished:
            return None
        percept = self.sensors.perceive()
        self.history.append(percept)
        decision = self.agent.decide(percept, self.history)
        result = self.actuators.execute(decision.action)
        completed = self.environment.is_complete()
        reward = self.performance.register(result, completed and result.cleaned)

        if completed:
            self.status = RunStatus.COMPLETED
        elif decision.action is Action.STOP:
            self.status = RunStatus.STOPPED_EARLY
        elif self.performance.steps >= self.max_steps:
            self.status = RunStatus.MAX_STEPS_REACHED

        self.agent.observe_outcome(percept, decision, result, reward, self.sensors.perceive(), self.finished)
        record = StepRecord(percept.step + 1, percept, decision, result, reward,
                            self.performance.snapshot(self.environment.remaining_dirt, self.status))
        self.trace.records.append(record)
        return record

    def run(self) -> SimulationTrace:
        while not self.finished:
            self.step()
        self.trace.summary = self.performance.snapshot(self.environment.remaining_dirt, self.status)
        return self.trace
