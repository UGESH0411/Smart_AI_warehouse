"""Metric data structures shared by Human and AI runs (HumanResult / AIResult)."""
from dataclasses import dataclass


@dataclass
class RunMetrics:
    mode: str = "AI"                 # "Human" or "AI"
    distance: float = 0.0
    time_seconds: float = 0.0
    packages_delivered: int = 0
    packages_total: int = 0
    invalid_moves: int = 0
    nodes_explored: int = 0
    path_length: float = 0.0
    robot_utilization: float = 0.0
    score: float = 0.0
    initial_cost: float = 0.0
    final_cost: float = 0.0


# Named aliases matching the project specification
HumanResult = RunMetrics
AIResult = RunMetrics
