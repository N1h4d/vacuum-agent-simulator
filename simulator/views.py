"""Thin HTTP layer: parse JSON -> call agent_core -> return JSON. No AI logic here."""
from __future__ import annotations

import json
import random
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from agent_core.agents import AGENT_CLASSES
from agent_core.domain import SensorMode
from agent_core.environment.environment import Environment
from agent_core.environment.generator import EnvironmentGenerator, GenerationParams, validate_size
from agent_core.settings import MAX_GRID_SIZE, MIN_GRID_SIZE, ScoringConfig, SimulationConfig
from agent_core.simulation.comparison import compare_agents, run_agent
from agent_core.simulation.serialization import trace_to_dict

MAX_SEED = 2**31 - 1


def index(request: HttpRequest):
    agents = [{"kind": c.kind, "name": c.display_name, "description": c.description}
              for c in AGENT_CLASSES.values()]
    context = {"agents": agents, "scoring": vars(ScoringConfig()),
               "limits": {"min": MIN_GRID_SIZE, "max": MAX_GRID_SIZE}}
    return render(request, "simulator/index.html", context)


def _payload(request: HttpRequest) -> dict[str, Any]:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Request body is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def _simulation_config(data: dict[str, Any]) -> SimulationConfig:
    mode = SensorMode(str(data.get("sensor_mode", SensorMode.LOCAL.value)).upper())
    return SimulationConfig(sensor_mode=mode)


def _json_api(handler):
    """Turn ValueError (bad input from the browser) into a clean 400 response."""
    def wrapper(request: HttpRequest):
        try:
            return JsonResponse(handler(_payload(request)))
        except (ValueError, TypeError, KeyError) as error:
            return JsonResponse({"error": str(error)}, status=400)
    wrapper.__name__ = handler.__name__
    return wrapper


@require_POST
def generate_environment(request: HttpRequest):
    @_json_api
    def handle(data: dict[str, Any]) -> dict[str, Any]:
        raw_seed = data.get("seed")
        seed = int(raw_seed) if raw_seed not in (None, "") else random.randint(0, MAX_SEED)
        params = GenerationParams(
            width=int(data.get("width", 10)), height=int(data.get("height", 10)),
            dirt_percent=float(data.get("dirt_percent", 30)),
            obstacle_percent=float(data.get("obstacle_percent", 10)),
            random_start=bool(data.get("random_start", True)), seed=seed)
        return {"environment": EnvironmentGenerator().generate(params).snapshot(), "seed": seed}
    return handle(request)


@require_POST
def run_simulation(request: HttpRequest):
    @_json_api
    def handle(data: dict[str, Any]) -> dict[str, Any]:
        validate_size(Environment.from_snapshot(data["environment"]))  # fail early, clear message
        trace = run_agent(data["environment"], str(data["agent"]), _simulation_config(data))
        return trace_to_dict(trace)
    return handle(request)


@require_POST
def run_comparison(request: HttpRequest):
    @_json_api
    def handle(data: dict[str, Any]) -> dict[str, Any]:
        validate_size(Environment.from_snapshot(data["environment"]))
        kinds = [str(k) for k in data["agents"]]
        if not kinds:
            raise ValueError("Select at least one agent.")
        result = compare_agents(data["environment"], kinds, _simulation_config(data))
        return {"table": result.table(), "traces": {k: trace_to_dict(t) for k, t in result.traces.items()}}
    return handle(request)
