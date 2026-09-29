"""TSP-inspired route ordering for a single robot's pickup-and-delivery sequence.

Important: this is NOT a classical single-salesman TSP. Because each robot can
carry only one package at a time, after every pickup the robot must first
travel to the delivery point before collecting the next package. We still use
TSP-style nearest-neighbour construction to order the deliveries efficiently.
"""


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def route_cost(start_pos, delivery_pos, package_positions):
    """package_positions: ordered list of (r, c) positions (visiting order).
    The robot travels start -> pkg1 -> delivery -> pkg2 -> delivery -> ..."""
    if not package_positions:
        return 0
    cost = 0
    pos = start_pos
    for pkg_pos in package_positions:
        cost += manhattan(pos, pkg_pos)
        cost += manhattan(pkg_pos, delivery_pos)
        pos = delivery_pos
    return cost


def nearest_neighbor_order(start_pos, delivery_pos, package_positions):
    """Greedily order packages: from the current position (start, then the
    delivery point after each drop-off) always visit the nearest remaining
    package next."""
    remaining = list(package_positions)
    order = []
    pos = start_pos
    while remaining:
        nearest = min(remaining, key=lambda p: manhattan(pos, p))
        order.append(nearest)
        remaining.remove(nearest)
        pos = delivery_pos
    return order
