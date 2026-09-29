"""Minimax (with alpha-beta pruning) adversarial search for Competitive Mode.

Two teams, A (MAX) and B (MIN), move on a shared grid trying to claim the most
valuable packages. State: both team positions, the remaining packages and
whose turn it is. Actions: move one cell in one of 4 directions, or stay.
Utility: scoreA - scoreB. This is intentionally kept separate from the normal
warehouse routing pipeline (Rule: do not force Minimax into routing).
"""
import math

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]  # 4 moves, then "stay"


class CompetitiveState:
    __slots__ = ("posA", "posB", "packages", "scoreA", "scoreB", "turn")

    def __init__(self, posA, posB, packages, scoreA=0, scoreB=0, turn="A"):
        self.posA = posA
        self.posB = posB
        self.packages = packages   # dict (r, c) -> value, remaining packages only
        self.scoreA = scoreA
        self.scoreB = scoreB
        self.turn = turn           # "A" (MAX) or "B" (MIN)


def apply_move(state, mover, dr, dc, rows, cols, obstacles):
    """Returns the resulting CompetitiveState after `mover` attempts move (dr, dc)."""
    pos = state.posA if mover == "A" else state.posB
    nr, nc = pos[0] + dr, pos[1] + dc
    if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in obstacles:
        nr, nc = pos  # invalid move resolves to staying in place

    packages = dict(state.packages)
    scoreA, scoreB = state.scoreA, state.scoreB
    if (nr, nc) in packages:
        value = packages.pop((nr, nc))
        if mover == "A":
            scoreA += value
        else:
            scoreB += value

    posA = (nr, nc) if mover == "A" else state.posA
    posB = (nr, nc) if mover == "B" else state.posB
    next_turn = "B" if mover == "A" else "A"
    return CompetitiveState(posA, posB, packages, scoreA, scoreB, next_turn)


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _utility(state):
    """Score difference (exact when the game is over). At the search horizon a
    proximity heuristic is added: each remaining package contributes
    value/(1+distance) to the team that is closer to it, so agents are drawn
    toward valuable packages instead of standing still."""
    utility = state.scoreA - state.scoreB
    for pos, value in state.packages.items():
        da, db = _dist(state.posA, pos), _dist(state.posB, pos)
        utility += 0.5 * value * (1.0 / (1 + da) - 1.0 / (1 + db))
    return utility


def _terminal(state, depth):
    return depth == 0 or not state.packages


def minimax(state, depth, rows, cols, obstacles, alpha=-math.inf, beta=math.inf):
    """Returns (value, best_move) for the player whose turn it is (state.turn)."""
    if _terminal(state, depth):
        return _utility(state), None

    mover = state.turn
    best_move = None

    if mover == "A":
        value = -math.inf
        for dr, dc in DIRECTIONS:
            child = apply_move(state, "A", dr, dc, rows, cols, obstacles)
            child_value, _ = minimax(child, depth - 1, rows, cols, obstacles, alpha, beta)
            if child_value > value:
                value = child_value
                best_move = (dr, dc)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for dr, dc in DIRECTIONS:
            child = apply_move(state, "B", dr, dc, rows, cols, obstacles)
            child_value, _ = minimax(child, depth - 1, rows, cols, obstacles, alpha, beta)
            if child_value < value:
                value = child_value
                best_move = (dr, dc)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def best_move_for(state, depth, rows, cols, obstacles):
    _, move = minimax(state, depth, rows, cols, obstacles)
    return move
