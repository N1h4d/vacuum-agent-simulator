import unittest

from agent_core.domain import Action, CellType, Outcome, Position
from agent_core.environment.environment import Environment
from agent_core.environment.generator import EnvironmentGenerator, GenerationParams
from tests.helpers import make_env


class EnvironmentRulesTests(unittest.TestCase):
    def test_suck_cleans_dirty_cell(self):
        env = make_env(["D."])
        result = env.apply(Action.SUCK)
        self.assertEqual(result.outcome, Outcome.CLEANED)
        self.assertEqual(env.grid.cell(Position(0, 0)).cell_type, CellType.CLEAN)
        self.assertEqual(env.remaining_dirt, 0)

    def test_suck_on_clean_cell_is_wasted_and_changes_nothing(self):
        env = make_env([".D"])
        result = env.apply(Action.SUCK)
        self.assertEqual(result.outcome, Outcome.WASTED_SUCK)
        self.assertFalse(result.success)
        self.assertEqual(env.remaining_dirt, 1)

    def test_cannot_walk_through_obstacle(self):
        env = make_env([".#."])
        result = env.apply(Action.MOVE_RIGHT)
        self.assertEqual(result.outcome, Outcome.BUMPED_OBSTACLE)
        self.assertEqual(env.vacuum, Position(0, 0))

    def test_cannot_leave_the_grid(self):
        env = make_env(["..", ".."])
        for action in (Action.MOVE_UP, Action.MOVE_LEFT):
            self.assertEqual(env.apply(action).outcome, Outcome.BUMPED_WALL)
        self.assertEqual(env.vacuum, Position(0, 0))

    def test_valid_move_updates_position_and_step_count(self):
        env = make_env(["..", ".."])
        env.apply(Action.MOVE_RIGHT)
        env.apply(Action.MOVE_DOWN)
        self.assertEqual(env.vacuum, Position(1, 1))
        self.assertEqual(env.step_count, 2)

    def test_unreachable_dirt_is_not_counted(self):
        env = make_env([".#D"])
        self.assertEqual(env.remaining_dirt, 0)
        self.assertTrue(env.is_complete())

    def test_snapshot_roundtrip(self):
        env = make_env(["D#.", "..D"], start=(1, 0))
        copy = Environment.from_snapshot(env.snapshot())
        self.assertEqual(copy.snapshot(), env.snapshot())

    def test_start_on_obstacle_is_rejected(self):
        with self.assertRaises(ValueError):
            make_env(["#."], start=(0, 0))


class GeneratorTests(unittest.TestCase):
    def test_counts_match_percentages(self):
        params = GenerationParams(width=10, height=10, dirt_percent=30, obstacle_percent=10, seed=7)
        env = EnvironmentGenerator().generate(params)
        self.assertEqual(env.grid.count(CellType.DIRTY), 30)
        self.assertEqual(env.grid.count(CellType.OBSTACLE), 10)
        self.assertEqual((env.width, env.height), (10, 10))

    def test_same_seed_gives_same_environment(self):
        params = GenerationParams(seed=123)
        gen = EnvironmentGenerator()
        self.assertEqual(gen.generate(params).snapshot(), gen.generate(params).snapshot())

    def test_start_is_free_and_clean(self):
        for seed in range(20):
            env = EnvironmentGenerator().generate(GenerationParams(seed=seed))
            self.assertEqual(env.grid.cell(env.vacuum).cell_type, CellType.CLEAN)

    def test_fixed_start_is_top_left(self):
        env = EnvironmentGenerator().generate(GenerationParams(random_start=False, seed=1))
        self.assertEqual(env.vacuum, Position(0, 0))

    def test_invalid_parameters_rejected(self):
        for bad in (GenerationParams(width=1), GenerationParams(dirt_percent=-1),
                    GenerationParams(dirt_percent=70, obstacle_percent=40)):
            with self.assertRaises(ValueError):
                EnvironmentGenerator().generate(bad)


if __name__ == "__main__":
    unittest.main()
