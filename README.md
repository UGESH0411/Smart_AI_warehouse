# AI Warehouse Simulator
**AI-Based Multi-Robot Warehouse Package Collection and Route Optimization**
PySide6 (Qt 6) desktop app: A*, Hill Climbing, TSP-inspired routing, multi-robot assignment, Minimax, 4-Queens, Prolog.

## 1. Install & run
Requirements: **Python 3.10+ (3.12 recommended)**.

**Windows (PowerShell / CMD)**
```
cd warehouse_ai_project
python -m venv venv
venv\Scripts\activate
pip install PySide6 matplotlib
python main.py
```
(or just double-click `run_windows.bat`)

**Linux / macOS**
```
cd warehouse_ai_project
python3 -m venv venv
source venv/bin/activate
pip install PySide6 matplotlib
python main.py
```
(or `./run_linux_mac.sh`)

Run tests: `pip install pytest` then `python -m pytest`

### Optional: real SWI-Prolog
The app works without it (a built-in Python rule engine mirrors `prolog/warehouse_rules.pl`; the
Knowledge Base tab tells you which mode is active). To use real Prolog: install SWI-Prolog
(https://www.swi-prolog.org/Download.html, add it to PATH), then `pip install pyswip`.
Check with `swipl --version`.

## 2. How to use (demo script)
1. **Warehouse** tab -> set Robots=3, Packages=8, Density=20%, Time Limit=30s, Seed=48291.
2. Click **Challenge Mode: Generate From Seed** (creates robots, packages, delivery point, reachable
   obstacles, and auto-saves `scenarios/challenge_seed48291.json`). Same seed = same scenario.
   Or build manually: *Place Robot / Add Package / Set Delivery Point / Toggle Obstacle*, then click the grid.
3. **Human**: click **Start Manual Mode**. Arrow keys or WASD move the active robot; keys **1/2/3** switch
   robot. Walk onto a package to pick it up (max ONE at a time), then onto the green **D** to deliver.
   Click **Stop Manual Mode** (or finish/time out) to record your result.
4. Click **Reset Run** (restores the exact same scenario), then **Run AI**. Robots move in parallel.
5. **Show AI Reasoning** shows Hill Climbing cost history, assignment and TSP-inspired order.
6. **Human vs AI** tab shows the comparison table (real measured values) and **Results** logs every run.
7. **Competitive Mode** (Minimax), **Constraint Solver** (4-Queens), **Knowledge Base** (Prolog queries).

## 3. Warehouse rules (always enforced)
Robots stay in bounds and never enter obstacles; each robot carries **one** package at a time
(Robot -> Package -> Pick up -> Delivery -> Deliver -> available); 1-3 robots run simultaneously;
obstacle generator avoids robots/packages/delivery and re-validates reachability; unreachable packages are
detected and reported. Results are described as *heuristic / best found*, never "globally optimal".

## 4. Scoring (evaluation/scoring.py)
```
Score = 100*delivered - 0.5*distance - 1.0*time_seconds - 5*invalid_moves - 20*priority_violations
```
(floored at 0). A priority violation = a lower-priority package delivered before a higher-priority one.

## 5. Project layout
```
main.py            entry point + stylesheet
gui/               main_window, warehouse_tab (main logic), warehouse_view (QGraphicsScene/View),
                   control_panel, metrics_panel, comparison_view, dialogs, ai_worker (QThread),
                   competitive_tab, constraint_tab, knowledge_tab, results_tab
warehouse/         grid, grid_cell, robot, package, delivery, obstacle (generation+reachability), scenario (JSON)
ai/                astar, hill_climbing, tsp_optimizer, multi_robot_optimizer, minimax, four_queens
simulation/        engine (AI planner), robot_controller (manual rules), animation, timer_manager
evaluation/        metrics, scoring, comparison
prolog/            warehouse_rules.pl, prolog_interface.py (single point of Prolog access)
tests/             pytest suite (A*, rules, scenario, optimisation, Prolog, minimax, 4-queens)
```
Data flow: UI -> WarehouseGrid -> (Human: robot_controller | AI: engine = greedy assignment ->
Hill Climbing -> TSP-inspired order -> A*) -> animation -> metrics -> comparison.
AI planning runs in a `QThread` so the GUI never freezes; AI modules contain no GUI code.

## 6. Algorithms
| Algorithm | Problem | State | Evaluation | Time / Space |
|---|---|---|---|---|
| **A*** | shortest path on 4-connected grid | cell (r,c); f=g+h, h=Manhattan (admissible) | f cost | O(b^d) worst, ~O(N log N) on grid; O(N) |
| **Greedy assignment** | initial robot->package split | dict robot -> package list | nearest chain end, high priority first | O(R*P) |
| **TSP-inspired ordering** | order pickups per robot (pickup->delivery round trips) | permutation of a robot's packages | route cost, nearest neighbour | O(P^2) |
| **Hill Climbing** | improve assignment + order | assignment dict | total distance + 2*(max-min route) imbalance | O(iter * neighbours * P); local optimum only |
| **Minimax + alpha-beta** | 2-team competitive package claiming | both positions, packages, turn | score diff + proximity heuristic | O(b^d), pruning ~O(b^(d/2)) |
| **Backtracking (4-Queens)** | non-conflicting charging stations | partial column list | constraint check | O(n!) worst |
| **Prolog rules** | robot/package compatibility & priority | facts/rules | logical inference | - |

The multi-robot problem is a **pickup-and-delivery** problem (not a plain single-salesman TSP); Hill Climbing
is a heuristic and may stop at a local optimum, so results are "best found", not proven optimal.

## 7. Viva quick answers
- *Why A*?* Optimal for unit-cost grids with an admissible heuristic, far fewer nodes than BFS.
- *Why Hill Climbing not exact search?* Assignment+ordering is NP-hard; exact search explodes; HC gives good solutions fast (but no optimality guarantee).
- *Where is Prolog used?* `warehouse_rules.pl` defines capability/priority rules queried only via `prolog_interface.py`; the planner schedules `high` priority packages first (mirrors `high_priority_package/1`).
- *How is fairness ensured in Human vs AI?* Both runs use the identical grid; `Reset Run` restores start positions; results are compared only if the layout signature matches.
- *Why does AI not collide?* Robots may share cells (no inter-robot collision rule in the spec); every path is obstacle-free and one cell per step.

## Warehouse AI Assistant

The **AI Assistant** is a natural-language monitoring and explainability layer on top of the existing warehouse simulator. It does not replace the deterministic algorithms or create a second warehouse state.

### Architecture

```text
User -> PySide6 AI Assistant -> OpenRouter (optional)
                              -> approved tool calls
                              -> live WarehouseTab/grid/AI plan
```

The approved tools expose only warehouse queries and safe application actions. The assistant cannot execute arbitrary Python, shell commands, or filesystem operations.

The existing algorithms remain the source of truth:

- **A*** performs grid pathfinding.
- **Hill Climbing** optimizes the multi-robot assignment and ordering.
- **TSP-inspired nearest-neighbour ordering** determines pickup order.

### Free API configuration

The assistant supports OpenRouter's free-model routing configuration. No API key is stored in Python source code.

1. Copy `.env.example` to `.env`.
2. Put your OpenRouter key in `OPENROUTER_API_KEY`.
3. Keep `OPENROUTER_MODEL=openrouter/free` or choose another model available to your account.
4. Run the application normally.
5. Open the **AI Assistant** tab.

`.env` is ignored by Git. Never commit a real key.

### Offline mode

Without an API key, the warehouse application remains fully usable. The assistant provides deterministic local answers for common status questions such as robot count, pending packages, completion count, simulation state, robot position, and inventory availability. If the API becomes unavailable or rate-limited, the application does not crash and falls back where a local answer is possible.

### Example questions

- How many robots are active?
- Which packages are pending?
- Where is R2?
- What is the current simulation status?
- What did Hill Climbing improve?
- What A* statistics are available for R1?
- How are the tasks currently assigned?
- Why is a battery value unavailable?

The current project model does not contain battery, stock quantity, order completion time, or charging-state fields, so the assistant reports those values as unavailable instead of inventing them.

### Testing

The assistant tests do not require a real API key. API integration is isolated from the deterministic warehouse tests.
