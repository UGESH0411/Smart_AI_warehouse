"""Robot data model."""
from enum import Enum


class RobotState(Enum):
    IDLE = "IDLE"
    MOVING_TO_PACKAGE = "MOVING_TO_PACKAGE"
    CARRYING = "CARRYING"
    MOVING_TO_DELIVERY = "MOVING_TO_DELIVERY"
    DELIVERING = "DELIVERING"
    FINISHED = "FINISHED"


ROBOT_COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"]


class Robot:
    def __init__(self, robot_id: str, row: int, col: int, index: int = 0):
        self.robot_id = robot_id
        self.row = row
        self.col = col
        self.start_row = row
        self.start_col = col
        self.state = RobotState.IDLE
        self.distance_travelled = 0.0
        self.carrying_package = None   # package_id or None
        self.current_path = []          # list of (r, c) remaining path
        self.assigned_packages = []     # list of package ids, in delivery order
        self.color = ROBOT_COLORS[index % len(ROBOT_COLORS)]
        self.delivered_count = 0

    def reset(self):
        """Reset to start position and idle state (used when re-running a scenario)."""
        self.row = self.start_row
        self.col = self.start_col
        self.state = RobotState.IDLE
        self.distance_travelled = 0.0
        self.carrying_package = None
        self.current_path = []
        self.assigned_packages = []
        self.delivered_count = 0

    def to_dict(self):
        return {"id": self.robot_id, "position": [self.start_row, self.start_col]}

    def __repr__(self):
        return f"Robot({self.robot_id}, pos=({self.row},{self.col}), state={self.state.value})"
