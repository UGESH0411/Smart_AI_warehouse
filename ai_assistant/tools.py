import math


def _robot_dict(r):
    return {"robot_id": r.robot_id, "position": [r.row, r.col], "start_position": [r.start_row, r.start_col],
            "state": r.state.value, "distance_travelled": r.distance_travelled,
            "carrying_package": r.carrying_package, "assigned_packages": list(r.assigned_packages),
            "delivered_count": r.delivered_count}


def build_tools(adapter):
    return {
        "get_warehouse_status": adapter.get_warehouse_status,
        "get_all_robots": adapter.get_all_robots,
        "get_robot_status": adapter.get_robot_status,
        "get_pending_orders": adapter.get_pending_orders,
        "get_order_status": adapter.get_order_status,
        "get_inventory": adapter.get_inventory,
        "get_low_stock_products": adapter.get_low_stock_products,
        "get_product_location": adapter.get_product_location,
        "get_nearest_robot": adapter.get_nearest_robot,
        "get_robot_current_task": adapter.get_robot_current_task,
        "get_robot_path": adapter.get_robot_path,
        "get_astar_statistics": adapter.get_astar_statistics,
        "get_hill_climbing_statistics": adapter.get_hill_climbing_statistics,
        "get_task_assignments": adapter.get_task_assignments,
        "get_simulation_statistics": adapter.get_simulation_statistics,
        "get_current_simulation_state": adapter.get_current_simulation_state,
        "start_simulation": adapter.start_simulation,
        "reset_simulation": adapter.reset_simulation,
    }


def openai_tool_specs():
    specs = []
    definitions = [
        ("get_warehouse_status", "Get current warehouse dimensions, robots, packages, obstacles and delivery point.", {}),
        ("get_all_robots", "Get the live status of every robot.", {}),
        ("get_robot_status", "Get live status for one robot.", {"robot_id": {"type": "string"}}),
        ("get_pending_orders", "Get packages that have not been delivered.", {}),
        ("get_order_status", "Get the status of one package/order.", {"order_id": {"type": "string"}}),
        ("get_inventory", "Get inventory/package information. If product_id is omitted, return all packages.", {"product_id": {"type": "string"}}),
        ("get_low_stock_products", "Return low-stock products when inventory data defines a stock threshold; otherwise report unavailable.", {}),
        ("get_product_location", "Get the current location of a package/product.", {"product_id": {"type": "string"}}),
        ("get_nearest_robot", "Find the nearest robot to a package/order.", {"order_id": {"type": "string"}}),
        ("get_robot_current_task", "Get a robot's current assigned/carrying task.", {"robot_id": {"type": "string"}}),
        ("get_robot_path", "Get a bounded representation of the latest planned path for a robot.", {"robot_id": {"type": "string"}}),
        ("get_astar_statistics", "Get actual A* statistics for a robot's latest AI plan.", {"robot_id": {"type": "string"}}),
        ("get_hill_climbing_statistics", "Get actual Hill Climbing costs and iterations from the latest AI plan.", {}),
        ("get_task_assignments", "Get current task assignments from the latest AI plan or live robot assignments.", {}),
        ("get_simulation_statistics", "Get current run metrics and AI planning statistics.", {}),
        ("get_current_simulation_state", "Get whether the warehouse is idle, running Human mode, or running AI mode.", {}),
        ("start_simulation", "Start the existing AI simulation using the application's own AI planner.", {}),
        ("reset_simulation", "Reset robots and packages to the exact current scenario start state.", {}),
    ]
    for name, desc, props in definitions:
        required = list(props.keys())
        specs.append({"type": "function", "function": {"name": name, "description": desc,
                      "parameters": {"type": "object", "properties": props, "required": required}}})
    return specs


class WarehouseToolAdapter:
    def __init__(self, warehouse_tab):
        self.tab = warehouse_tab

    def get_warehouse_status(self):
        g = self.tab.grid
        return {"rows": g.rows, "cols": g.cols, "obstacle_count": len(g.obstacles),
                "robot_count": len(g.robots), "package_count": len(g.packages),
                "pending_count": len(g.pending_packages()),
                "delivery_point": [g.delivery.row, g.delivery.col] if g.delivery else None}

    def get_all_robots(self):
        return [_robot_dict(r) for r in self.tab.grid.robots]

    def get_robot_status(self, robot_id):
        r = self.tab.grid.get_robot(robot_id)
        return _robot_dict(r) if r else {"error": f"Robot {robot_id} was not found."}

    def get_pending_orders(self):
        return [{"order_id": p.package_id, "position": [p.row, p.col], "priority": p.priority,
                 "weight": p.weight, "picked": p.picked, "delivered": p.delivered}
                for p in self.tab.grid.pending_packages()]

    def get_order_status(self, order_id):
        p = self.tab.grid.get_package(order_id)
        if not p:
            return {"error": f"Order/package {order_id} was not found."}
        return {"order_id": p.package_id, "position": [p.row, p.col], "priority": p.priority,
                "weight": p.weight, "picked": p.picked, "delivered": p.delivered}

    def get_inventory(self, product_id=""):
        if product_id:
            return self.get_order_status(product_id)
        return [{"product_id": p.package_id, "position": [p.row, p.col], "priority": p.priority,
                 "weight": p.weight, "delivered": p.delivered} for p in self.tab.grid.packages]

    def get_low_stock_products(self):
        return {"available": False, "reason": "This project stores package placement and priority, but no stock quantity/reorder threshold."}

    def get_product_location(self, product_id):
        p = self.tab.grid.get_package(product_id)
        return {"product_id": product_id, "location": [p.row, p.col]} if p else {"error": f"Product/package {product_id} was not found."}

    def get_nearest_robot(self, order_id):
        p = self.tab.grid.get_package(order_id)
        if not p:
            return {"error": f"Order/package {order_id} was not found."}
        candidates = sorted(self.tab.grid.robots, key=lambda r: abs(r.row-p.row)+abs(r.col-p.col))
        if not candidates:
            return {"error": "No robots are available."}
        r = candidates[0]
        return {"order_id": order_id, "robot_id": r.robot_id, "manhattan_distance": abs(r.row-p.row)+abs(r.col-p.col), "robot_position": [r.row,r.col]}

    def get_robot_current_task(self, robot_id):
        r = self.tab.grid.get_robot(robot_id)
        if not r:
            return {"error": f"Robot {robot_id} was not found."}
        return {"robot_id": robot_id, "state": r.state.value, "carrying_package": r.carrying_package,
                "assigned_packages": list(r.assigned_packages)}

    def _plan_robot(self, robot_id):
        return self.tab.plan.robot_plans.get(robot_id) if self.tab.plan else None

    def get_robot_path(self, robot_id):
        rp = self._plan_robot(robot_id)
        if not rp:
            return {"available": False, "reason": "No completed AI plan is available for this robot."}
        path = rp.full_path
        return {"available": True, "robot_id": robot_id, "path_length": max(0, len(path)-1),
                "nodes_explored": rp.nodes_explored, "path": [list(x) for x in path[:200]],
                "truncated": len(path) > 200}

    def get_astar_statistics(self, robot_id):
        rp = self._plan_robot(robot_id)
        if not rp:
            return {"available": False, "reason": "No completed AI plan is available for this robot."}
        return {"available": True, "robot_id": robot_id, "path_length": max(0, len(rp.full_path)-1),
                "nodes_expanded": rp.nodes_explored, "package_order": list(rp.package_order)}

    def get_hill_climbing_statistics(self):
        if not self.tab.plan:
            return {"available": False, "reason": "No completed AI plan is available."}
        history = self.tab.plan.hill_climb_history
        initial = self.tab.plan.initial_cost
        final = self.tab.plan.final_cost
        improvement = ((initial-final)/initial*100) if initial else 0.0
        return {"available": True, "initial_cost": initial, "final_cost": final,
                "improvement_percent": improvement, "iterations": max(0, len(history)-2),
                "history": [{"label": l, "cost": c} for l,c in history]}

    def get_task_assignments(self):
        if self.tab.plan:
            return {rid: list(rp.package_order) for rid, rp in self.tab.plan.robot_plans.items()}
        return {r.robot_id: list(r.assigned_packages) for r in self.tab.grid.robots}

    def get_simulation_statistics(self):
        m = self.tab.ai_metrics if self.tab.ai_metrics else self.tab.human_metrics
        data = {"simulation_mode": self.tab.run_mode or "idle", "delivered": sum(p.delivered for p in self.tab.grid.packages),
                "total_packages": len(self.tab.grid.packages), "total_distance": sum(r.distance_travelled for r in self.tab.grid.robots),
                "robot_utilization_percent": 100.0 * sum(r.delivered_count > 0 for r in self.tab.grid.robots) / max(1, len(self.tab.grid.robots))}
        if m:
            data.update({"last_run_mode": m.mode, "time_seconds": m.time_seconds, "invalid_moves": m.invalid_moves,
                         "score": m.score, "nodes_explored": m.nodes_explored, "path_length": m.path_length,
                         "initial_cost": m.initial_cost, "final_cost": m.final_cost})
        return data

    def get_current_simulation_state(self):
        return {"mode": self.tab.run_mode or "idle", "running": self.tab.is_running(),
                "robots": self.get_all_robots(), "pending_orders": len(self.tab.grid.pending_packages())}

    def start_simulation(self):
        if self.tab.is_running():
            return {"success": False, "message": "A simulation is already running."}
        self.tab.run_ai()
        return {"success": True, "message": "The existing AI simulation start command was invoked."}

    def reset_simulation(self):
        self.tab.reset_run()
        return {"success": True, "message": "The simulation was reset to the current scenario start state."}


def local_answer(question, adapter):
    """Small deterministic fallback for common read-only questions."""
    import re
    q = question.lower().strip()
    if any(x in q for x in ("how many robots", "number of robots")):
        robots = adapter.get_all_robots()
        return f"There are currently {len(robots)} robots."
    if "charging" in q:
        robots = adapter.get_all_robots()
        charging = [r["robot_id"] for r in robots if r["state"] == "CHARGING"]
        return f"{len(charging)} robots are charging: {', '.join(charging)}." if charging else "No robots are currently reported as charging."
    if "pending" in q and "order" in q:
        orders = adapter.get_pending_orders()
        return f"There are currently {len(orders)} pending orders/packages."
    if "completed" in q and ("order" in q or "package" in q):
        s = adapter.get_simulation_statistics()
        return f"There are currently {s['delivered']} completed/delivered packages out of {s['total_packages']}."
    if "simulation status" in q or "simulation state" in q:
        s = adapter.get_current_simulation_state()
        return f"The simulation state is {s['mode']}. Running: {'yes' if s['running'] else 'no'}."
    m = re.search(r"\b(r\d+)\b", q)
    if m and "battery" in q:
        return "Battery level is unavailable: the current warehouse Robot model does not store battery information."
    if m and ("where" in q or "position" in q or "location" in q):
        r = adapter.get_robot_status(m.group(1).upper())
        if "error" in r: return r["error"]
        return f"{r['robot_id']} is at row {r['position'][0]}, column {r['position'][1]}."
    if "low stock" in q:
        return "Stock quantity and reorder thresholds are not part of the current project state, so low-stock products cannot be determined."
    if "inventory" in q:
        return f"The current project tracks {len(adapter.get_inventory())} package/product records, with positions, priority, weight and delivery status."
    return None
