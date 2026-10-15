# Vacuum Agent Simulator

An interactive **Vacuum Cleaner Agent** simulator built to demonstrate the core ideas of the
*Intelligent Agents* topic of an Artificial Intelligence course: percepts, actions, agent function vs.
agent program, performance measures, PEAS, and the four agent types (simple reflex, goal-based,
utility-based, learning).

Stack: **Python 3.10+**, **Django** (thin UI/HTTP layer only), HTML/CSS/vanilla JavaScript.
The AI code (`agent_core/`) does **not** import Django and is unit-tested without it.

---

## 1. Project overview

The user sees a **grid world** (3x3 up to 20x20) containing dirty cells, clean cells, obstacles and a
vacuum robot. One of four agents is plugged into the robot. The agent senses its surroundings,
decides, and acts. A performance measure scores what actually happened. The UI shows the agent's
"brain" (what it perceived, which options it had, why it chose one), the percept history, a live
dashboard, and a **comparison mode** that runs several agents on the *same* environment.

## 2. What is an AI agent?

An **agent** is anything that perceives its **environment** through **sensors** and acts on it
through **actuators**. A **rational agent** chooses, for every percept sequence, the action that is
expected to maximise its **performance measure**, given what it knows.

```
        percepts                       actions
Environment ─────► Sensors ─► Agent ─► Actuators ─────► Environment
```

## 3. What is the Vacuum Cleaner Agent?

The classic textbook toy problem (Russell & Norvig): a robot must clean a dirty world. It is small
enough to be fully understood, yet rich enough to show why different agent designs behave very
differently. Here the two-room version is generalised to a grid with obstacles and partial observability.

## 4. Environment (`agent_core/environment/`)

| Class | Responsibility |
|---|---|
| `Cell` | one square: `CLEAN`, `DIRTY` or `OBSTACLE` |
| `Grid` | storage + geometry (bounds, obstacles, reachability) |
| `Environment` | ground truth, vacuum position, step count, **the rules of the world** (`apply(action)`) |
| `EnvironmentGenerator` | random generation (size, dirt %, obstacle %, start, **seed**) and validation |

Properties (Russell & Norvig classification): **discrete, single-agent, deterministic, sequential,
static** (only the agent changes it). **Observability depends on the sensor mode**: `LOCAL` is
partially observable, `FULL` is fully observable.

Dirt that is walled off by obstacles is *unreachable*. It is ignored for completion and metrics, which
is why the goal is stated as "clean all **reachable** dirt".

Manual creation: choose a tool (Dirt / Obstacle / Clean / Start) and click or drag on the grid.
Seeds make environments reproducible, which is essential for a fair comparison.

## 5. Sensors (`agents/sensors.py`)

`Sensors` is the **only** component that reads the environment. In `LOCAL` mode it reports the
current position, the current cell and the 4 neighbours (`CLEAN`, `DIRTY`, `OBSTACLE`, or `WALL` at
the border). In `FULL` mode it additionally reports the whole grid. Agents are constructed *without*
an environment reference, so they cannot cheat.

## 6. Actuators (`agents/actuators.py`)

`Actuators` is the **only** component that changes the environment. It accepts only members of the
`Action` enum: `MOVE_UP`, `MOVE_DOWN`, `MOVE_LEFT`, `MOVE_RIGHT`, `SUCK`, `STOP`.
The *environment* decides what happens (e.g. walking into an obstacle is a collision, not a move).

## 7. Percepts (`domain.Percept`)

An immutable snapshot: step, position, current cell, the four neighbours (and the global view in
`FULL` mode). The simulator stores every percept in the **percept history**, which is passed to the
agent program and shown in the UI.

## 8. Actions and outcomes (`domain.Action`, `domain.Outcome`)

After each action the environment reports an outcome: `MOVED`, `CLEANED`, `BUMPED_OBSTACLE`,
`BUMPED_WALL`, `WASTED_SUCK` (suck on a clean cell) or `STOPPED`. Outcomes feed the performance measure.

## 9. Agent function vs. agent program

* **Agent function**: the abstract mapping *percept sequence → action*.
* **Agent program**: a concrete implementation running on an architecture.
  Here: `BaseAgent.decide(percept, history) -> Decision`. Each strategy is a different agent program
  implementing (an approximation of) a different agent function.

A `Decision` contains the action **and** its explanation (reason, available actions, scored
candidates, plan), which powers the Agent Brain panel.

## 10. Simple Reflex Agent (`agents/reflex_agent.py`)

Condition-action rules on the **current percept only** (no memory, no map, no plan):

```
IF current cell is DIRTY            -> SUCK
ELIF a neighbour is DIRTY           -> MOVE towards it
ELSE                                -> MOVE to a random free neighbour (seeded)
```
Deliberate weakness: it wanders and can revisit the same area; it has no guarantee of finding all
dirt before the step limit. This is exactly what the comparison mode makes visible.

## 11. Goal-Based Agent (`goal_agent.py`, `world_model.py`, `pathfinding.py`)

Goal: **clean all reachable dirt.** It keeps an internal **world model** (a map built only from
percepts) and re-plans every step:

1. known dirt → shortest path (BFS) to the nearest dirt, then `SUCK`
2. no known dirt, unexplored cells exist → BFS to the nearest unvisited cell (exploration)
3. nothing left → `STOP`

**Why BFS?** Every move costs the same (unweighted graph), so BFS returns a *shortest* path and is
complete. DFS is not shortest. A\* needs a heuristic and gives the same result under uniform cost, so
it only adds complexity. **Limitation:** "nearest dirt first" is greedy. The full tour is a
travelling-salesman-like problem, so the agent reaches the goal but not necessarily with the globally
minimal number of steps.

## 12. Utility-Based Agent (`utility_agent.py`)

Instead of a yes/no goal, every candidate action receives an explicit **utility**:

```
U(a) = immediate_reward(a)                      reward/penalty from the performance measure
     + w_progress * (d_before - d_after)        getting closer to the nearest target
     - w_revisit  * visits(next cell)           discourages pointless backtracking
     + w_explore  * [next cell never visited]   small curiosity bonus
```
`d` = BFS distance on the agent's own map to the nearest known dirt (or, if none is known, to the
nearest unvisited cell). The Agent Brain panel prints this table for **every** action, including
`STOP` and blocked moves (collision penalty), so the computation is fully transparent.
Weights live in `UtilityWeights` (`settings.py`).

**Honest note:** this is a one-step lookahead with a heuristic. In this uniform-cost world it often
behaves like the goal-based agent; the difference is conceptual (explicit trade-offs, graded
preferences, tunable weights) and shows up in small step-count differences.

## 12b. Learning Agent (`learning_agent.py`, `simulation/training.py`)

Tabular **Q-learning**, mapped to the four components of a learning agent:

| Component | Implementation |
|---|---|
| Performance element | epsilon-greedy policy over the Q-table |
| Critic | the performance measure (reward) |
| Learning element | `Q(s,a) += alpha * (r + gamma * max Q(s',a') - Q(s,a))` |
| Problem generator | exploration (epsilon, decaying during training) |

* **State** (abstract, so the table stays small): on-dirt flag, a code for each neighbour
  (blocked / visited / unvisited / dirty), and a *direction hint* from its own memory. It is not
  told what to do with the hint; it must learn that following it pays off.
* **Action masking:** moves the sensors show as blocked and `SUCK` on a clean cell are not offered.
  Otherwise an untried action has Q=0 and looks better than a learned negative value, and the agent
  keeps bumping.
* **Reward shaping:** a small novelty bonus for entering a new cell (otherwise there is no signal for exploring).
* **Training:** 80 episodes on random worlds with the same size/densities as yours; the UI then runs the
  frozen policy (no exploration) on your environment. The learning curve is shown in Compare.

**Honest note:** learning is stochastic and the abstraction is crude. The learner sometimes matches the
planning agents and sometimes gets stuck in a loop and hits the step limit. That is expected and is
itself a good discussion point (limited state abstraction, no long-term memory in the state).

## 13. Performance measure (`simulation/performance.py`, `ScoringConfig`)

| Event | Reward |
|---|---|
| Dirt cleaned | +10 |
| Successful move (time/energy cost) | −1 |
| Collision with obstacle or wall | −5 |
| `SUCK` on a clean cell | −2 |
| All reachable dirt cleaned (once) | +20 |

The measure judges **environment outcomes**, not what the agent believes. "Unnecessary movement" is
not a separate penalty: judging whether a move was necessary would mean judging the agent's internal
strategy. Wasteful movement simply accumulates the −1 cost.
Dashboard: total score, steps, dirt cleaned, remaining (reachable) dirt, invalid actions
(collisions + wasted SUCK), efficiency (= dirt cleaned / steps), completion status
(`COMPLETED`, `STOPPED_EARLY`, `MAX_STEPS_REACHED`). The step limit is `width × height × 4`.

## 14. PEAS

| | |
|---|---|
| **P**erformance | cleanliness, efficiency, movement cost, penalties (section 13) |
| **E**nvironment | grid world with dirt and obstacles (section 4) |
| **A**ctuators | move ×4, suck, stop |
| **S**ensors | position, current-cell status, 4 neighbours (+ whole grid in FULL mode) |

The same table is available in the UI (tab *PEAS & Concepts*).

## 15. Architecture

```
vacuum_agent/
├── manage.py  requirements.txt  README.md
├── config/                    Django settings, root urls (no database)
├── simulator/                 Django app, THIN: views.py (JSON in/out), urls.py
├── agent_core/                PURE PYTHON, no Django imports
│   ├── domain.py              Action, Percept, Decision, StepRecord ... (value objects)
│   ├── settings.py            ScoringConfig, UtilityWeights, LearningConfig, SimulationConfig
│   ├── environment/           cell.py, grid.py, environment.py, generator.py
│   ├── agents/                sensors, actuators, base_agent, world_model, pathfinding,
│   │                          reflex_agent, goal_agent, utility_agent, learning_agent
│   └── simulation/            simulator, performance, logger, training, comparison, serialization
├── templates/simulator/index.html
├── static/simulator/{css,js}  api, grid_view, panels, compare, main (vanilla ES modules)
└── tests/                     unittest (also runs with pytest)
```

```
Browser ── JSON ──► Django views ──► agent_core ──► JSON ──► Browser
                    (no AI logic)    (all AI logic)
```

Simulation loop (`simulation/simulator.py`):

```
percept  = sensors.perceive()                 # Environment -> Percept
decision = agent.decide(percept, history)     # agent program
result   = actuators.execute(decision.action) # Actuator -> Environment.apply()
reward   = performance.register(result)       # performance measure
agent.observe_outcome(...)                    # learning agent only
log StepRecord
```

**Trace + playback.** The backend runs the complete perceive→decide→act loop and returns every
`StepRecord`. The browser plays it back step by step (Start / Pause / Step / Reset / Replay). The
agent really does decide one step at a time on the server, but the UI animates a recorded run
(stateless server, free Replay, identical mechanism for Comparison). State this when presenting.

## 16. How to run

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
# open http://127.0.0.1:8000/
```

Run the tests (no Django needed):

```bash
python -m unittest -v            # or: pytest
```

The tests cover: cleaning dirt, no SUCK on clean cells, obstacle and border collisions, goal agent
cleaning all reachable dirt (LOCAL and FULL sensors, many random worlds), score arithmetic,
environment generation (counts, seeds, validation), identical environments in comparisons, JSON serialisation.

## 17. Example simulation

Environment `#12` (generate with seed `12`, defaults: 10×10, 30 % dirt, 10 % obstacles, random start,
LOCAL sensors). These numbers were produced by running the simulator, not typed in:

| | Reflex | Goal | Utility | Learning |
|---|---:|---:|---:|---:|
| Steps | 400 | 130 | 118 | 400 |
| Dirt cleaned (of 30) | 29 | 30 | 30 | 13 |
| Invalid actions | 0 | 0 | 0 | 0 |
| Score | −81 | 220 | 232 | −257 |
| Status | MAX_STEPS | COMPLETED | COMPLETED | MAX_STEPS |

Agent Brain excerpt (utility agent, step 1, robot in the left border column):

```
Position (6,0)   Cell: CLEAN   Up: OBSTACLE  Down: CLEAN  Left: WALL  Right: CLEAN
MOVE_UP    -5.0  (collision)         MOVE_DOWN   +2.5 = -1.0 move + 3.0 progress + 0.5 explore
MOVE_LEFT  -5.0  (collision)         MOVE_RIGHT  +2.5 = -1.0 move + 3.0 progress + 0.5 explore
SUCK       -2.0  (wasted)            STOP       -50.0 (dirt is still known)
Selected: MOVE_DOWN (tie broken by the fixed action order)
```

Typical findings: reflex is cheap but unreliable and wasteful; the two planning agents always finish;
utility-based is usually (not always) a bit more efficient than goal-based; learning shows
improvement over training but is not guaranteed to reach the planners' level.

## 18. Future improvements

* Stochastic environment (slippery moves, noisy sensors) to show where deterministic planning breaks.
* Dynamic dirt that re-appears over time (a *dynamic* environment).
* Battery constraint and a charging station (richer utility trade-offs).
* Two vacuums (multi-agent environment).
* Better learning state abstraction or function approximation; persist trained policies.
* Optional session-based mode so that every Step is computed live on the server.

---

## Presentation guide: how to explain each part

| Component | What it does | Concept | Why designed this way | One-sentence answer for the teacher |
|---|---|---|---|---|
| `Environment` | owns the world, applies actions, enforces rules | Environment | the agent must not be able to bypass the rules | "The environment is the ground truth; agents only interact with it through sensors and actuators." |
| `Sensors` | builds a `Percept` | Sensors, percepts, observability | information hiding is what makes partial observability real | "LOCAL vs FULL shows partially vs fully observable environments." |
| `Actuators` | executes only legal `Action`s | Actuators | the single write channel | "The agent proposes, the environment disposes." |
| `BaseAgent.decide` | percepts → `Decision` | Agent function / program | same interface for all strategies, so they are comparable | "The agent function is the abstract mapping; each class is a different program for it." |
| `SimpleReflexAgent` | rules on current percept | Simple reflex | shows what you get with no memory | "It is fast, but without state it can loop and has no completeness guarantee." |
| `WorldModel` | map built from percepts | Model-based agent (internal state) | needed to plan in a partially observable world | "It remembers what it can no longer see." |
| `GoalBasedAgent` + BFS | plans to reach the goal | Goal-based, search | BFS = shortest, complete on uniform cost | "It chooses actions by asking: does this bring me closer to my goal?" |
| `UtilityBasedAgent` | scores each action | Utility, trade-offs | makes preferences explicit and inspectable | "Goals are yes/no; utility says how good each outcome is." |
| `LearningAgent` | Q-learning | Learning agent (4 components) | small, explainable, honest about limits | "It improves its policy from rewards; the performance measure is the critic." |
| `PerformanceMeasure` | scores the run | Performance measure, rationality | evaluates outcomes, not beliefs | "Rationality is defined relative to a performance measure." |
| `Simulator` | the perceive-decide-act loop | Agent–environment cycle | one place connects all parts | "This is the textbook agent diagram as code." |
| `comparison.py` | same world, many agents | Rational agent comparison | identical copies + seeds = fair | "Every number comes from a real run on an identical environment." |
