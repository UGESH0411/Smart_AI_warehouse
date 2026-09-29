from warehouse.grid import WarehouseGrid
from warehouse.scenario import Scenario
from warehouse.obstacle import generate_valid_obstacles, validate_reachability
from simulation.robot_controller import attempt_move


def make_grid():
    g = WarehouseGrid(6, 6)
    g.add_robot(0, 0)
    g.set_delivery(5, 5)
    return g


def test_package_cannot_be_placed_on_obstacle():
    g = make_grid()
    assert g.add_obstacle(2, 2)
    assert g.add_package(2, 2) is None


def test_robot_cannot_move_through_obstacle():
    g = make_grid()
    g.add_obstacle(0, 1)
    r = g.robots[0]
    res = attempt_move(g, r, 0, 1)
    assert not res.valid and (r.row, r.col) == (0, 0)
    assert not attempt_move(g, r, -1, 0).valid   # boundary


def test_robot_carries_max_one_package():
    g = make_grid()
    g.add_package(0, 1)
    g.add_package(0, 2)
    r = g.robots[0]
    assert attempt_move(g, r, 0, 1).event == "pickup"
    assert r.carrying_package == "P1"
    assert attempt_move(g, r, 0, 1).event is None      # stepping on P2 does NOT pick it up
    assert r.carrying_package == "P1"
    assert not g.get_package("P2").picked


def test_delivery_works():
    g = WarehouseGrid(3, 3)
    g.add_robot(0, 0)
    g.add_package(0, 1)
    g.set_delivery(0, 2)
    r = g.robots[0]
    attempt_move(g, r, 0, 1)
    res = attempt_move(g, r, 0, 1)
    assert res.event == "deliver" and g.get_package("P1").delivered
    assert r.carrying_package is None and g.all_delivered()


def test_scenario_save_load(tmp_path):
    g = make_grid()
    g.add_package(3, 3, "high")
    g.add_obstacle(1, 1)
    p = tmp_path / "s.json"
    Scenario(g, 42, 123).save(str(p))
    s2 = Scenario.load(str(p))
    assert s2.grid.to_dict() == g.to_dict()
    assert s2.time_limit == 42 and s2.random_seed == 123


def test_obstacle_generation_reproducible_and_reachable():
    g = make_grid()
    g.add_package(3, 4)
    a, _ = generate_valid_obstacles(6, 6, 0.25, 7, g.robots, g.packages, g.delivery)
    b, _ = generate_valid_obstacles(6, 6, 0.25, 7, g.robots, g.packages, g.delivery)
    assert a == b
    ok, bad = validate_reachability(6, 6, a, g.robots, g.packages, g.delivery)
    assert ok and not bad
    assert (0, 0) not in a and (5, 5) not in a and (3, 4) not in a
