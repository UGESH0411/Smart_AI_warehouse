"""Transparent scoring formula shared by Human and AI runs.

Score = delivered * DELIVERY_REWARD
        - distance * DISTANCE_PENALTY
        - time_seconds * TIME_PENALTY
        - invalid_moves * INVALID_MOVE_PENALTY
        - priority_violations * PRIORITY_PENALTY
(never below 0). Nothing is adjusted after the fact.
"""

DELIVERY_REWARD = 100.0
DISTANCE_PENALTY = 0.5
TIME_PENALTY = 1.0
INVALID_MOVE_PENALTY = 5.0
PRIORITY_PENALTY = 20.0


def compute_score(delivered, distance, time_seconds, invalid_moves=0, priority_violations=0):
    score = delivered * DELIVERY_REWARD
    score -= distance * DISTANCE_PENALTY
    score -= time_seconds * TIME_PENALTY
    score -= invalid_moves * INVALID_MOVE_PENALTY
    score -= priority_violations * PRIORITY_PENALTY
    return max(0.0, score)


def priority_violations(delivery_order, priorities):
    """Count high-priority packages delivered after a lower-priority one.
    delivery_order: list of package ids in delivery order; priorities: id -> str."""
    rank = {"high": 0, "normal": 1, "low": 2}
    violations = 0
    for i, a in enumerate(delivery_order):
        for b in delivery_order[i + 1:]:
            if rank.get(priorities.get(b), 1) < rank.get(priorities.get(a), 1):
                violations += 1
    return violations
