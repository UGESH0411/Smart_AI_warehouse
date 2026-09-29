"""AI planning engine: turns a warehouse grid into an executable multi-robot plan.

Pipeline:
  greedy assignment -> Hill Climbing (assignment + order) -> TSP-inspired
  nearest-neighbour ordering per robot -> A* paths for every leg.

The engine never touches the GUI; it returns an AIPlan that the GUI animates.
"""
from ai.astar import astar, path_length
from ai.multi_robot_optimizer import greedy_initial_assignment
from ai.tsp_optimizer import nearest_neighbor_order, route_cost
from ai.hill_climbing import hill_climb


class RobotPlan:
    def __init__(self, robot_id):
        self.robot_id = robot_id
        self.full_path = []       # list of (r, c) including the start cell
        self.events = []          # (path_index, "pickup"/"deliver", package_id)
        self.nodes_explored = 0
        self.package_order = []


class AIPlan:
    def __init__(self):
        self.robot_plans = {}
        self.assignment = {}
        self.hill_climb_history = []
        self.total_distance = 0
        self.total_nodes_explored = 0
        self.unreachable_packages = []
        self.initial_cost = 0
        self.final_cost = 0

    def describe(self):
        lines = ["AI PLAN (heuristic solution - best found, not proven optimal)", ""]
        lines.append("Hill Climbing cost history:")
        for label, cost in self.hill_climb_history:
            lines.append(f"  {label}: {cost:.1f}")
        if self.initial_cost:
            gain = (self.initial_cost - self.final_cost) / self.initial_cost * 100
            lines.append(f"  Optimization improvement: {gain:.1f}%")
        lines.append("")
        lines.append("Assignment & TSP-inspired order (robot: package sequence):")
        for rid, rp in self.robot_plans.items():
            seq = " -> Delivery -> ".join(rp.package_order) + (" -> Delivery" if rp.package_order else "")
            lines.append(f"  {rid}: {seq if seq else '(no packages)'}")
        lines.append("")
        lines.append(f"Total planned path length: {self.total_distance}")
        lines.append(f"A* nodes explored: {self.total_nodes_explored}")
        if self.unreachable_packages:
            lines.append(f"UNREACHABLE packages: {', '.join(self.unreachable_packages)}")
        return "\n".join(lines)


def build_ai_plan(grid, use_hill_climbing=True, seed=42):
    """Build a plan for `grid`. Raises ValueError for unsolvable set-ups."""
    if not grid.robots:
        raise ValueError("No robots placed in the warehouse.")
    if grid.delivery is None:
        raise ValueError("No delivery point set.")
    packages = [p for p in grid.packages if not p.delivered]
    if not packages:
        raise ValueError("No packages to deliver.")

    delivery_pos = (grid.delivery.row, grid.delivery.col)
    robots_pos = {r.robot_id: (r.row, r.col) for r in grid.robots}
    package_pos = {p.package_id: (p.row, p.col) for p in packages}

    initial_assignment = greedy_initial_assignment(grid.robots, packages, delivery_pos)
    plan = AIPlan()

    if use_hill_climbing and len(grid.robots) > 1 and len(packages) > 1:
        best_assignment, history = hill_climb(initial_assignment, robots_pos, delivery_pos, package_pos, seed=seed)
    else:
        best_assignment = initial_assignment
        cost = sum(route_cost(robots_pos[rid], delivery_pos, [package_pos[p] for p in pkgs])
                   for rid, pkgs in best_assignment.items())
        history = [("Initial Cost", cost), ("Final Cost", cost)]

    plan.hill_climb_history = history
    plan.initial_cost = history[0][1]
    plan.final_cost = history[-1][1]
    plan.assignment = best_assignment

    for robot in grid.robots:
        pkg_ids = best_assignment.get(robot.robot_id, [])
        pos_to_id = {package_pos[pid]: pid for pid in pkg_ids}
        ordered_positions = nearest_neighbor_order(
            (robot.row, robot.col), delivery_pos, [package_pos[pid] for pid in pkg_ids])
        ordered_ids = [pos_to_id[pos] for pos in ordered_positions]

        rplan = RobotPlan(robot.robot_id)
        current = (robot.row, robot.col)
        full_path = [current]
        delivered_order = []

        for pid in ordered_ids:
            target = package_pos[pid]
            seg1, e1 = astar(grid.rows, grid.cols, grid.obstacles, current, target)
            rplan.nodes_explored += e1
            if seg1 is None:
                plan.unreachable_packages.append(pid)
                continue
            seg2, e2 = astar(grid.rows, grid.cols, grid.obstacles, target, delivery_pos)
            rplan.nodes_explored += e2
            if seg2 is None:
                plan.unreachable_packages.append(pid)
                continue
            full_path.extend(seg1[1:])
            rplan.events.append((len(full_path) - 1, "pickup", pid))
            full_path.extend(seg2[1:])
            rplan.events.append((len(full_path) - 1, "deliver", pid))
            current = delivery_pos
            delivered_order.append(pid)

        rplan.package_order = delivered_order
        rplan.full_path = full_path
        plan.robot_plans[robot.robot_id] = rplan
        plan.total_distance += path_length(full_path)
        plan.total_nodes_explored += rplan.nodes_explored

    return plan
