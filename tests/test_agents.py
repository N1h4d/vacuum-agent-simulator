import unittest

from agent_core.agents import create_agent
from agent_core.agents.actuators import Actuators
from agent_core.agents.sensors import Sensors
from agent_core.domain import Action, CellType, RunStatus, SensorMode
from agent_core.environment.generator import EnvironmentGenerator, GenerationParams
from agent_core.settings import SimulationConfig
from agent_core.simulation.simulator import Simulator
from tests.helpers import make_env


class SensorsActuatorsTests(unittest.TestCase):
    def test_local_percept_hides_the_rest_of_the_world(self):
        env = make_env(["..D", "...", "D#."], start=(1, 1))
        percept = Sensors(env, SensorMode.LOCAL).perceive()
        self.assertIsNone(percept.global_view)
        self.assertEqual(percept.neighbors[Action.MOVE_DOWN], CellType.OBSTACLE)
        self.assertEqual(percept.neighbors[Action.MOVE_UP], CellType.CLEAN)

    def test_wall_is_reported_at_the_border(self):
        env = make_env(["..", ".."])
        self.assertEqual(Sensors(env).perceive().neighbors[Action.MOVE_UP], CellType.WALL)

    def test_full_mode_exposes_global_view(self):
        percept = Sensors(make_env(["D.", ".."]), SensorMode.FULL).perceive()
        self.assertEqual(percept.global_view[0][0], CellType.DIRTY)

    def test_actuators_reject_non_actions(self):
        with self.assertRaises(ValueError):
            Actuators(make_env(["."])).execute("TELEPORT")


def run(kind, rows, start=(0, 0), mode=SensorMode.LOCAL):
    env = make_env(rows, start)
    return env, Simulator(env, create_agent(kind, seed=1), SimulationConfig(sensor_mode=mode)).run()


class ReflexAgentTests(unittest.TestCase):
    def test_sucks_when_standing_on_dirt(self):
        env = make_env(["D."])
        decision = create_agent("reflex").decide(Sensors(env).perceive(), [])
        self.assertEqual(decision.action, Action.SUCK)

    def test_never_sucks_on_a_clean_cell(self):
        env = make_env(["..D", ".#.", "D.."])
        trace = Simulator(env, create_agent("reflex", 3), SimulationConfig()).run()
        for record in trace.records:
            if record.percept.current_cell is CellType.CLEAN:
                self.assertNotEqual(record.decision.action, Action.SUCK)

    def test_moves_towards_dirty_neighbour(self):
        env = make_env([".D"])
        decision = create_agent("reflex").decide(Sensors(env).perceive(), [])
        self.assertEqual(decision.action, Action.MOVE_RIGHT)


class GoalAgentTests(unittest.TestCase):
    LAYOUT = ["..D.D", ".##..", "D...#", "..#.D"]

    def test_cleans_all_reachable_dirt_local(self):
        env, trace = run("goal", self.LAYOUT)
        self.assertEqual(env.remaining_dirt, 0)
        self.assertEqual(trace.summary.status, RunStatus.COMPLETED)
        self.assertEqual(trace.summary.invalid_actions, 0)

    def test_cleans_all_reachable_dirt_full(self):
        env, trace = run("goal", self.LAYOUT, mode=SensorMode.FULL)
        self.assertEqual(env.remaining_dirt, 0)

    def test_ignores_unreachable_dirt_and_does_not_loop(self):
        env, trace = run("goal", ["..#D", "..#."])
        self.assertTrue(env.is_complete())
        self.assertEqual(trace.summary.dirt_cleaned, 0)

    def test_random_worlds_always_fully_cleaned(self):
        for seed in range(15):
            env = EnvironmentGenerator().generate(GenerationParams(seed=seed, dirt_percent=35, obstacle_percent=20))
            trace = Simulator(env, create_agent("goal"), SimulationConfig()).run()
            self.assertEqual(env.remaining_dirt, 0, f"seed {seed}")
            self.assertEqual(trace.summary.invalid_actions, 0)

    def test_plan_is_exposed_for_the_ui(self):
        env = make_env(["...D"])
        decision = create_agent("goal").decide(Sensors(env, SensorMode.FULL).perceive(), [])
        self.assertEqual(len(decision.plan), 3)


class UtilityAgentTests(unittest.TestCase):
    def test_prefers_suck_on_dirt_with_explained_utilities(self):
        env = make_env(["D."])
        decision = create_agent("utility").decide(Sensors(env).perceive(), [])
        self.assertEqual(decision.action, Action.SUCK)
        suck = next(c for c in decision.candidates if c.action is Action.SUCK)
        self.assertEqual(suck.utility, 10.0)
        self.assertIn("immediate_reward", suck.components)

    def test_blocked_moves_get_penalty_utility(self):
        env = make_env([".#"])
        decision = create_agent("utility").decide(Sensors(env).perceive(), [])
        right = next(c for c in decision.candidates if c.action is Action.MOVE_RIGHT)
        self.assertEqual(right.utility, -5.0)

    def test_cleans_all_reachable_dirt(self):
        for seed in range(10):
            env = EnvironmentGenerator().generate(GenerationParams(seed=seed, obstacle_percent=15))
            trace = Simulator(env, create_agent("utility"), SimulationConfig()).run()
            self.assertEqual(env.remaining_dirt, 0, f"seed {seed}")


class LearningAgentTests(unittest.TestCase):
    def test_only_legal_actions_are_considered(self):
        env = make_env(["..", "#."])
        decision = create_agent("learning").decide(Sensors(env).perceive(), [])
        considered = [c.action for c in decision.candidates]
        self.assertNotIn(Action.SUCK, considered)       # clean cell
        self.assertNotIn(Action.MOVE_DOWN, considered)  # obstacle
        self.assertNotIn(Action.MOVE_UP, considered)    # wall

    def test_boxed_in_agent_stops(self):
        decision = create_agent("learning").decide(Sensors(make_env([".#"])).perceive(), [])
        self.assertEqual(decision.action, Action.STOP)


if __name__ == "__main__":
    unittest.main()
