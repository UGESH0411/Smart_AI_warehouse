"""Package data model."""


class Package:
    def __init__(self, package_id: str, row: int, col: int, priority: str = "normal", weight: float = 1.0):
        self.package_id = package_id
        self.row = row
        self.col = col
        self.priority = priority   # "low", "normal", "high"
        self.weight = weight
        self.picked = False
        self.delivered = False

    def reset(self):
        self.picked = False
        self.delivered = False

    def to_dict(self):
        return {
            "id": self.package_id,
            "position": [self.row, self.col],
            "priority": self.priority,
            "weight": self.weight,
        }

    def __repr__(self):
        return f"Package({self.package_id}, pos=({self.row},{self.col}), priority={self.priority})"
