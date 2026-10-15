import unittest

from agent_core.agents import create_agent
from agent_core.domain import Action, ActionResult, Outcome, Position, RunStatus
from agent_core.environment.generator import EnvironmentGenerator, GenerationParams
from agent_core.settings import LearningConfig, ScoringConfig, SimulationConfig
from agent_core.simulation.comparison import compare_agents, run_agent
from agent_core.simulation.performance import PerformanceMeasure
from agent_core.simulation.serialization import trace_to_dict
from agent_core.simulation.simulator import Simulator
from tests.helpers import make_env

HERE = Position(0, 0)


class PerformanceTests(unittest.TestCase):
    def test_score_is_computed_from_outcomes(self):
        measure = PerformanceMeasure(ScoringConfig())
        for outcome in (Outcome.CLEANED, Outcome.MOVED, Outcome.BUMPED_OBSTACLE, Outcome.WASTED_SUCK):
            measure.register(ActionResult(Action.SUCK, outcome, HERE), completed=False)
        self.assertEqual(measure.score, 10 - 1 - 5 - 2)
        self.assertEqual((measure.steps, measure.dirt_cleaned, measure.invalid_actions), (4, 1, 2))

    def test_completion_bonus_added_once(self):
        measure = PerformanceMeasure(ScoringConfig())
        reward = measure.register(ActionResult(Action.SUCK, Outcome.CLEANED, HERE), completed=True)
        self.assertEqual(reward, 30)

    def test_efficiency_is_dirt_per_step(self):
        measure = PerformanceMeasure()
        measure.register(ActionResult(Action.MOVE_RIGHT, Outcome.MOVED, HERE), False)
        measure.register(ActionResult(Action.SUCK, Outcome.CLEANED, HERE), False)
        self.assertEqual(measure.snapshot(0, RunStatus.COMPLETED).efficiency, 0.5)

    def test_known_trace_score(self):
        env = make_env(["D.D"])
        trace = Simulator(env, create_agent("goal"), SimulationConfig()).run()
        # SUCK(+10), MOVE(-1), MOVE(-1), SUCK(+10), completion(+20)
        self.assertEqual(trace.summary.score, 38)
        self.assertEqual(trace.summary.steps, 4)


class SimulatorTests(unittest.TestCase):
    def test_step_executes_exactly_one_action(self):
        env = make_env(["...D"])
        sim = Simulator(env, create_agent("goal"), SimulationConfig())
        sim.step()
        self.assertEqual(env.step_count, 1)
        self.assertEqual(len(sim.trace.records), 1)

    def test_max_steps_stops_endless_runs(self):
        env = make_env(["....", "....", "...D"])
        config = SimulationConfig(max_steps_per_cell=1)
        trace = Simulator(env, create_agent("reflex", 99), config).run()
        self.assertLessEqual(trace.summary.steps, 12)

    def test_agent_stopping_early_is_reported(self):
        env = make_env([".#D"])  # nothing reachable -> episode already complete
        self.assertEqual(Simulator(env, create_agent("goal"), SimulationConfig()).status, RunStatus.COMPLETED)

    def test_percept_history_is_recorded(self):
        env = make_env(["..D"])
        trace = Simulator(env, create_agent("goal"), SimulationConfig()).run()
        self.assertEqual([r.step for r in trace.records], list(range(1, len(trace.records) + 1)))
        self.assertTrue(all(r.percept is not None for r in trace.records))

    def test_trace_is_json_serialisable(self):
        import json
        env = EnvironmentGenerator().generate(GenerationParams(seed=5, width=6, height=6))
        trace = Simulator(env, create_agent("utility"), SimulationConfig()).run()
        json.dumps(trace_to_dict(trace))


class ComparisonTests(unittest.TestCase):
    def test_all_agents_get_identical_environments(self):
        snapshot = EnvironmentGenerator().generate(GenerationParams(seed=11, width=7, height=7)).snapshot()
        result = compare_agents(snapshot, ["reflex", "goal", "utility"])
        initials = {t.initial_environment["cells"].__str__() for t in result.traces.values()}
        self.assertEqual(len(initials), 1)

    def test_table_comes_from_real_runs_and_is_reproducible(self):
        snapshot = EnvironmentGenerator().generate(GenerationParams(seed=3, width=6, height=6)).snapshot()
        first = compare_agents(snapshot, ["reflex", "goal"]).table()
        second = compare_agents(snapshot, ["reflex", "goal"]).table()
        self.assertEqual(first, second)
        for row, kind in zip(first, ("reflex", "goal")):
            trace = run_agent(snapshot, kind)
            self.assertEqual(row["score"], trace.summary.score)

    def test_goal_beats_reflex_on_average(self):
        goal = reflex = 0.0
        for seed in range(8):
            snapshot = EnvironmentGenerator().generate(GenerationParams(seed=seed)).snapshot()
            rows = {r["agent"]: r for r in compare_agents(snapshot, ["reflex", "goal"]).table()}
            goal += rows["goal"]["score"]
            reflex += rows["reflex"]["score"]
        self.assertGreater(goal, reflex)

    def test_learning_agent_trains_and_runs(self):
        snapshot = EnvironmentGenerator().generate(GenerationParams(seed=2, width=5, height=5)).snapshot()
        trace = run_agent(snapshot, "learning", SimulationConfig(), LearningConfig(episodes=5))
        self.assertEqual(len(trace.training_curve), 5)
        self.assertIsNotNone(trace.summary)


if __name__ == "__main__":
    unittest.main()
