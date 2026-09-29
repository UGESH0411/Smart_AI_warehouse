"""A* pathfinding on the warehouse grid (4-directional movement, Manhattan heuristic).

Demonstrates explicitly: open set, closed/explored set, g cost, h cost, f cost,
and parent pointers for path reconstruction.
"""
import heapq


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(rows, cols, obstacles, start, goal):
    """Returns (path, nodes_explored).

    path is a list of (r, c) tuples from start to goal inclusive, or None if
    the goal is unreachable. The caller must ensure start/goal themselves are
    not obstacles.
    """
    if start == goal:
        return [start], 0

    open_heap = []          # (f_cost, g_cost, tie_breaker, cell)
    counter = 0
    heapq.heappush(open_heap, (manhattan(start, goal), 0, counter, start))
    g_cost = {start: 0}
    parent = {}
    closed = set()           # explored set
    nodes_explored = 0

    while open_heap:
        f, g, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        nodes_explored += 1

        if current == goal:
            path = [current]
            while current in parent:
                current = parent[current]
                path.append(current)
            path.reverse()
            return path, nodes_explored

        r, c = current
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            neighbor = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if neighbor in obstacles or neighbor in closed:
                continue
            tentative_g = g + 1
            if tentative_g < g_cost.get(neighbor, float("inf")):
                g_cost[neighbor] = tentative_g
                parent[neighbor] = current
                counter += 1
                h = manhattan(neighbor, goal)
                heapq.heappush(open_heap, (tentative_g + h, tentative_g, counter, neighbor))

    return None, nodes_explored


def path_length(path):
    return 0 if not path else len(path) - 1
