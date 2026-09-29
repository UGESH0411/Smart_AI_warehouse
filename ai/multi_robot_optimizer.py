"""Initial multi-robot package assignment (greedy nearest-robot heuristic).

This is NOT a standard single-salesman TSP -- it is a multi-robot
pickup-and-delivery assignment problem, respecting the one-package-per-robot
capacity constraint (each package/delivery leg is a separate round trip)."""


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def greedy_initial_assignment(robots, packages, delivery_pos):
    """robots: list of Robot (uses .row/.col as the starting position)
    packages: list of Package
    Returns dict: robot_id -> [package_id, ...] in a plausible visiting order.
    High-priority packages are considered first (Prolog identifies these via
    high_priority_package/1 -- see the Knowledge Base tab)."""
    assignment = {r.robot_id: [] for r in robots}
    chain_end = {r.robot_id: (r.row, r.col) for r in robots}

    priority_rank = {"high": 0, "normal": 1, "low": 2}
    remaining = sorted(packages, key=lambda p: (priority_rank.get(p.priority, 1), p.package_id))

    for pkg in remaining:
        best_robot = None
        best_cost = None
        for r in robots:
            cost = manhattan(chain_end[r.robot_id], (pkg.row, pkg.col))
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_robot = r
        assignment[best_robot.robot_id].append(pkg.package_id)
        chain_end[best_robot.robot_id] = delivery_pos

    return assignment
