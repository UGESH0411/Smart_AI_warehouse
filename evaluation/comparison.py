"""Builds the Human vs AI comparison table from two RunMetrics objects."""


def build_comparison_rows(h, a):
    return [
        ("Packages Delivered", f"{h.packages_delivered}/{h.packages_total}", f"{a.packages_delivered}/{a.packages_total}"),
        ("Distance", f"{h.distance:.1f}", f"{a.distance:.1f}"),
        ("Time (s)", f"{h.time_seconds:.1f}", f"{a.time_seconds:.1f}"),
        ("Invalid Moves", str(h.invalid_moves), str(a.invalid_moves)),
        ("Nodes Explored", str(h.nodes_explored), str(a.nodes_explored)),
        ("Robot Utilization", f"{h.robot_utilization:.0f}%", f"{a.robot_utilization:.0f}%"),
        ("Score", f"{h.score:.1f}", f"{a.score:.1f}"),
    ]


def winner(h, a):
    if h.score > a.score:
        return "Human"
    if a.score > h.score:
        return "AI"
    return "Tie"
