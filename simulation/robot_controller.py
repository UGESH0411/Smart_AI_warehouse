"""Manual (Human mode) robot movement with warehouse-rule enforcement.

Rules enforced: bounds, obstacles, max ONE carried package, automatic pickup
when stepping on a package, automatic delivery on the delivery point.
"""
from warehouse.robot import RobotState


class MoveResult:
    def __init__(self, moved, valid, event=None, package_id=None):
        self.moved = moved
        self.valid = valid
        self.event = event          # None / "pickup" / "deliver"
        self.package_id = package_id


def attempt_move(grid, robot, drow, dcol):
    nr, nc = robot.row + drow, robot.col + dcol

    if not grid.in_bounds(nr, nc) or (nr, nc) in grid.obstacles:
        return MoveResult(moved=False, valid=False)

    robot.row, robot.col = nr, nc
    robot.distance_travelled += 1

    # Rule 3: only pick up if not already carrying
    if robot.carrying_package is None:
        for pkg in grid.packages:
            if not pkg.delivered and not pkg.picked and pkg.row == nr and pkg.col == nc:
                pkg.picked = True
                robot.carrying_package = pkg.package_id
                robot.state = RobotState.CARRYING
                return MoveResult(True, True, "pickup", pkg.package_id)
    elif grid.delivery is not None and nr == grid.delivery.row and nc == grid.delivery.col:
        pkg = grid.get_package(robot.carrying_package)
        pid = None
        if pkg is not None:
            pkg.delivered = True
            pid = pkg.package_id
        robot.carrying_package = None
        robot.state = RobotState.IDLE
        robot.delivered_count += 1
        return MoveResult(True, True, "deliver", pid)

    robot.state = RobotState.CARRYING if robot.carrying_package else RobotState.MOVING_TO_PACKAGE
    return MoveResult(True, True)
