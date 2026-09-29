"""Hill Climbing optimizer for multi-robot package assignment and ordering.

Steepest-ascent style: at every step a batch of neighbour assignments is
generated (move a package to another robot, swap two packages between robots,
swap order inside one robot). The best strictly-better neighbour is accepted;
the search stops when no neighbour improves the cost (a local optimum).

NOTE: Hill Climbing is a heuristic. It returns the best solution found, NOT a
guaranteed global optimum.
"""
import random
from .tsp_optimizer import route_cost


def assignment_cost(assignment, robots_pos, delivery_pos, package_pos, imbalance_weight=2.0):
    """Cost = total travel distance + imbalance_weight * (longest - shortest robot route)."""
    costs = []
    for robot_id, pkg_ids in assignment.items():
        positions = [package_pos[pid] for pid in pkg_ids]
        costs.append(route_cost(robots_pos[robot_id], delivery_pos, positions))
    total = sum(costs)
    imbalance = (max(costs) - min(costs)) if costs else 0
    return total + imbalance_weight * imbalance


def _copy_assignment(assignment):
    return {k: list(v) for k, v in assignment.items()}


def _neighbors(assignment, rng):
    robot_ids = list(assignment.keys())
    neighbors = []

    # move one package from robot r1 to robot r2
    for r1 in robot_ids:
        for pkg in assignment[r1]:
            for r2 in robot_ids:
                if r2 == r1:
                    continue
                new_assign = _copy_assignment(assignment)
                new_assign[r1].remove(pkg)
                new_assign[r2].append(pkg)
                neighbors.append(new_assign)

    # swap two packages between two different robots
    for i, r1 in enumerate(robot_ids):
        for r2 in robot_ids[i + 1:]:
            for p1 in assignment[r1]:
                for p2 in assignment[r2]:
                    new_assign = _copy_assignment(assignment)
                    new_assign[r1] = [p2 if x == p1 else x for x in new_assign[r1]]
                    new_assign[r2] = [p1 if x == p2 else x for x in new_assign[r2]]
                    neighbors.append(new_assign)

    # swap adjacent packages inside one robot's route
    for r1 in robot_ids:
        pkgs = assignment[r1]
        for i in range(len(pkgs) - 1):
            new_assign = _copy_assignment(assignment)
            new_assign[r1][i], new_assign[r1][i + 1] = new_assign[r1][i + 1], new_assign[r1][i]
            neighbors.append(new_assign)

    rng.shuffle(neighbors)
    return neighbors


def hill_climb(initial_assignment, robots_pos, delivery_pos, package_pos,
               max_iterations=200, max_neighbors_per_step=200, seed=42):
    """Returns (best_assignment, history).
    history is a list of (label, cost): 'Initial Cost', 'Improvement 1', ..., 'Final Cost'."""
    rng = random.Random(seed)
    current = _copy_assignment(initial_assignment)
    current_cost = assignment_cost(current, robots_pos, delivery_pos, package_pos)
    history = [("Initial Cost", current_cost)]
    improvements = 0

    for _ in range(max_iterations):
        candidates = _neighbors(current, rng)[:max_neighbors_per_step]
        best_neighbor = None
        best_cost = current_cost
        for cand in candidates:
            cost = assignment_cost(cand, robots_pos, delivery_pos, package_pos)
            if cost < best_cost:
                best_cost = cost
                best_neighbor = cand
        if best_neighbor is None:
            break  # local optimum
        current = best_neighbor
        current_cost = best_cost
        improvements += 1
        history.append((f"Improvement {improvements}", current_cost))

    history.append(("Final Cost", current_cost))
    return current, history
