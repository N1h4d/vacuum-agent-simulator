"""Pure-Python conversion of core objects to JSON-ready dicts (used by the Django views)."""
from __future__ import annotations

from ..domain import Candidate, Decision, PerformanceSnapshot, Percept, Position, StepRecord
from .logger import SimulationTrace


def _pos(p: Position) -> list[int]:
    return [p.row, p.col]


def percept_to_dict(p: Percept) -> dict:
    return {"step": p.step, "position": _pos(p.position), "current_cell": p.current_cell.value,
            "neighbors": {a.value: t.value for a, t in p.neighbors.items()},
            "full_view": p.global_view is not None}


def candidate_to_dict(c: Candidate) -> dict:
    return {"action": c.action.value, "utility": c.utility, "components": c.components, "note": c.note}


def decision_to_dict(d: Decision) -> dict:
    return {"action": d.action.value, "reason": d.reason,
            "available_actions": [a.value for a in d.available_actions],
            "candidates": [candidate_to_dict(c) for c in d.candidates],
            "plan": [_pos(p) for p in d.plan]}


def performance_to_dict(s: PerformanceSnapshot) -> dict:
    return {"score": s.score, "steps": s.steps, "dirt_cleaned": s.dirt_cleaned,
            "remaining_dirt": s.remaining_dirt, "invalid_actions": s.invalid_actions,
            "efficiency": s.efficiency, "status": s.status.value}


def record_to_dict(r: StepRecord) -> dict:
    return {"step": r.step, "percept": percept_to_dict(r.percept), "decision": decision_to_dict(r.decision),
            "result": {"outcome": r.result.outcome.value, "success": r.result.success,
                       "position_after": _pos(r.result.position_after)},
            "reward": r.reward, "performance": performance_to_dict(r.performance)}


def trace_to_dict(t: SimulationTrace) -> dict:
    return {"agent": t.agent_kind, "name": t.agent_name, "sensor_mode": t.sensor_mode.value,
            "environment": t.initial_environment,
            "initial_performance": performance_to_dict(t.initial_performance),
            "records": [record_to_dict(r) for r in t.records],
            "summary": performance_to_dict(t.summary),
            "training_curve": t.training_curve}
