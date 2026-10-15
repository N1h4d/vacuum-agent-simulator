"""Recording of the run: percept/action history and the full trace."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..domain import PerformanceSnapshot, SensorMode, StepRecord


@dataclass
class SimulationTrace:
    agent_kind: str
    agent_name: str
    sensor_mode: SensorMode
    initial_environment: dict
    initial_performance: PerformanceSnapshot
    records: list[StepRecord] = field(default_factory=list)
    summary: Optional[PerformanceSnapshot] = None
    training_curve: Optional[list[float]] = None
