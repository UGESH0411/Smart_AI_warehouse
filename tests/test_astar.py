from ai.astar import astar


def test_straight_path():
    path, explored = astar(5, 5, set(), (0, 0), (0, 4))
    assert path == [(0, i) for i in range(5)]
    assert explored > 0


def test_obstacle_path_avoids_obstacles():
    obstacles = {(0, 2), (1, 2)}
    path, _ = astar(5, 5, obstacles, (0, 0), (0, 4))
    assert path is not None and not (set(path) & obstacles)
    assert path[0] == (0, 0) and path[-1] == (0, 4)


def test_unreachable_goal():
    obstacles = {(0, 1), (1, 0), (1, 1)}
    path, _ = astar(5, 5, obstacles, (0, 0), (4, 4))
    assert path is None


def test_start_equals_goal():
    path, explored = astar(5, 5, set(), (2, 2), (2, 2))
    assert path == [(2, 2)] and explored == 0
