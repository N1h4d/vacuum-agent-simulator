from agent_core.environment.environment import Environment
from agent_core.environment.grid import Grid
from agent_core.domain import Position


def make_env(rows: list[str], start: tuple[int, int] = (0, 0)) -> Environment:
    """Build an environment from text rows: '.' clean, 'D' dirty, '#' obstacle."""
    return Environment(Grid.from_rows(rows), Position(*start))
