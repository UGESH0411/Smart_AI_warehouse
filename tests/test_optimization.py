from warehouse.grid import WarehouseGrid
from ai.hill_climbing import assignment_cost, hill_climb
from ai.tsp_optimizer import route_cost
from simulation.engine import build_ai_plan
from prolog.prolog_interface import PrologInterface


def make_grid():
    g = WarehouseGrid(12, 12)
    g.add_robot(0, 0); g.add_robot(0, 11); g.add_robot(11, 0)
    g.set_delivery(6, 6)
    for pos in [(1, 3), (2, 9), (9, 2), (10, 10), (4, 4), (8, 7)]:
        g.add_package(*pos)
    g.add_obstacle(5, 5); g.add_obstacle(5, 6); g.add_obstacle(5, 7)
    return g


def test_route_cost():
    assert route_cost((0, 0), (0, 4), [(0, 2)]) == 2 + 2
    assert route_cost((0, 0), (0, 4), []) == 0


def test_plan_is_valid_assignment_and_paths():
    g = make_grid()
    plan = build_ai_plan(g)
    assigned = [p for rp in plan.robot_plans.values() for p in rp.package_order]
    assert sorted(assigned) == sorted(p.package_id for p in g.packages)   # each package exactly once
    for rp in plan.robot_plans.values():
        for a, b in zip(rp.full_path, rp.full_path[1:]):
            assert abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1                   # no teleporting
            assert b not in g.obstacles
        kinds = [e[1] for e in rp.events]
        assert kinds == ["pickup", "deliver"] * (len(kinds)//2)            # one package at a time


def test_hill_climb_never_worsens():
    g = make_grid()
    from ai.multi_robot_optimizer import greedy_initial_assignment
    d = (6, 6)
    rp = {r.robot_id: (r.row, r.col) for r in g.robots}
    pp = {p.package_id: (p.row, p.col) for p in g.packages}
    init = greedy_initial_assignment(g.robots, g.packages, d)
    best, hist = hill_climb(init, rp, d, pp)
    assert assignment_cost(best, rp, d, pp) <= assignment_cost(init, rp, d, pp)
    assert hist[0][0] == "Initial Cost" and hist[-1][0] == "Final Cost"


def test_prolog_queries():
    p = PrologInterface()
    assert p.is_valid_assignment("r2", "p2")
    assert not p.is_valid_assignment("r1", "p2")
    assert set(p.robots_for_package("p1")) == {"r1", "r3"}
    assert p.high_priority_packages() == ["p1"]
