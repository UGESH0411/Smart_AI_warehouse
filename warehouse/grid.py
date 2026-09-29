"""WarehouseGrid: the central container for robots, packages, obstacles and the
delivery point. All warehouse rules about valid placement are enforced here."""
from .robot import Robot
from .package import Package
from .delivery import DeliveryPoint
from .grid_cell import GridCell


class WarehouseGrid:
    def __init__(self, rows: int = 20, cols: int = 20):
        self.rows = rows
        self.cols = cols
        self.obstacles = set()          # set of (r, c)
        self.robots = []                # list[Robot]
        self.packages = []              # list[Package]
        self.delivery = None            # DeliveryPoint or None
        self._robot_counter = 0
        self._package_counter = 0

    # ---------- geometry helpers ----------
    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_walkable(self, r, c):
        return self.in_bounds(r, c) and (r, c) not in self.obstacles

    def is_cell_free(self, r, c):
        """True if the cell has no obstacle, robot, package or delivery point on it."""
        if not self.in_bounds(r, c) or (r, c) in self.obstacles:
            return False
        if any(r == rb.row and c == rb.col for rb in self.robots):
            return False
        if any(r == p.row and c == p.col for p in self.packages):
            return False
        if self.delivery is not None and r == self.delivery.row and c == self.delivery.col:
            return False
        return True

    def cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                yield GridCell(r, c, walkable=(r, c) not in self.obstacles)

    # ---------- mutation ----------
    def add_obstacle(self, r, c):
        if self.is_cell_free(r, c):
            self.obstacles.add((r, c))
            return True
        return False

    def remove_obstacle(self, r, c):
        self.obstacles.discard((r, c))

    def clear_obstacles(self):
        self.obstacles.clear()

    def add_robot(self, r, c):
        if not self.is_cell_free(r, c):
            return None
        self._robot_counter += 1
        robot = Robot(f"R{self._robot_counter}", r, c, index=self._robot_counter - 1)
        self.robots.append(robot)
        return robot

    def add_package(self, r, c, priority="normal", weight=1.0):
        if not self.is_cell_free(r, c):
            return None
        self._package_counter += 1
        pkg = Package(f"P{self._package_counter}", r, c, priority=priority, weight=weight)
        self.packages.append(pkg)
        return pkg

    def set_delivery(self, r, c):
        if not self.is_cell_free(r, c):
            return False
        self.delivery = DeliveryPoint(r, c)
        return True

    def remove_package(self, package_id):
        self.packages = [p for p in self.packages if p.package_id != package_id]

    def get_package(self, package_id):
        for p in self.packages:
            if p.package_id == package_id:
                return p
        return None

    def get_robot(self, robot_id):
        for r in self.robots:
            if r.robot_id == robot_id:
                return r
        return None

    def clear_all(self):
        self.obstacles.clear()
        self.robots.clear()
        self.packages.clear()
        self.delivery = None
        self._robot_counter = 0
        self._package_counter = 0

    def reset_run_state(self):
        """Reset robots/packages to their start state without touching the layout
        (used to re-run Human or AI mode on the exact same scenario)."""
        for r in self.robots:
            r.reset()
        for p in self.packages:
            p.reset()

    def pending_packages(self):
        return [p for p in self.packages if not p.delivered]

    def all_delivered(self):
        return len(self.packages) > 0 and all(p.delivered for p in self.packages)

    # ---------- serialization ----------
    def to_dict(self):
        return {
            "grid_size": [self.rows, self.cols],
            "robots": [r.to_dict() for r in self.robots],
            "packages": [p.to_dict() for p in self.packages],
            "obstacles": [list(o) for o in sorted(self.obstacles)],
            "delivery_point": self.delivery.to_dict() if self.delivery else None,
        }

    @classmethod
    def from_dict(cls, data):
        rows, cols = data["grid_size"]
        grid = cls(rows, cols)
        for o in data.get("obstacles", []):
            grid.obstacles.add((o[0], o[1]))
        for i, r in enumerate(data.get("robots", [])):
            grid._robot_counter += 1
            robot = Robot(r.get("id", f"R{grid._robot_counter}"), r["position"][0], r["position"][1], index=i)
            grid.robots.append(robot)
        for p in data.get("packages", []):
            grid._package_counter += 1
            pkg = Package(p.get("id", f"P{grid._package_counter}"), p["position"][0], p["position"][1],
                          priority=p.get("priority", "normal"), weight=p.get("weight", 1.0))
            grid.packages.append(pkg)
        dp = data.get("delivery_point")
        if dp:
            grid.delivery = DeliveryPoint(dp[0], dp[1])
        return grid
