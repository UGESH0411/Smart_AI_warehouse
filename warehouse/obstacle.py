"""Random, reproducible obstacle generation plus reachability validation.

Rule 8: Obstacles can be randomly generated.
Rule 9: The obstacle generator avoids robots, packages, and the delivery point.
Rule 10: The system detects unreachable packages after generation.
"""
import random
from collections import deque


def generate_obstacles(rows, cols, density, seed, forbidden_cells):
    """Generate obstacle cells with the given density (0.0-1.0), reproducible via seed.

    forbidden_cells: set of (r, c) that must never become obstacles
    (robot positions, package positions, delivery point).
    """
    rng = random.Random(seed)
    all_cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in forbidden_cells]
    target_count = int(len(all_cells) * density)
    rng.shuffle(all_cells)
    return set(all_cells[:target_count])


def bfs_reachable(rows, cols, obstacles, start):
    """Flood-fill from `start`, respecting obstacles. Returns the set of reachable cells."""
    visited = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in obstacles and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return visited


def validate_reachability(rows, cols, obstacles, robots, packages, delivery):
    """Returns (is_valid, list_of_unreachable_package_ids)."""
    if not robots or delivery is None:
        return True, []
    reachable = bfs_reachable(rows, cols, obstacles, (robots[0].row, robots[0].col))
    if (delivery.row, delivery.col) not in reachable:
        return False, [p.package_id for p in packages]
    unreachable = [p.package_id for p in packages if (p.row, p.col) not in reachable]
    return len(unreachable) == 0, unreachable


def generate_valid_obstacles(rows, cols, density, seed, robots, packages, delivery, max_attempts=25):
    """Generate obstacles that keep every package and the delivery point reachable
    from the first robot. If a generated layout blocks the warehouse, the seed is
    perturbed deterministically and generation is retried."""
    forbidden = set((r.row, r.col) for r in robots)
    forbidden |= set((p.row, p.col) for p in packages)
    if delivery is not None:
        forbidden.add((delivery.row, delivery.col))

    attempt_seed = seed
    for attempt in range(max_attempts):
        obstacles = generate_obstacles(rows, cols, density, attempt_seed, forbidden)
        valid, unreachable = validate_reachability(rows, cols, obstacles, robots, packages, delivery)
        if valid:
            return obstacles, attempt_seed
        attempt_seed = (attempt_seed or 0) + 1000003
    return set(), seed  # fallback: no obstacles rather than an unsolvable warehouse
