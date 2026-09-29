"""Scenario: a saveable/loadable snapshot of a warehouse layout, used both for
JSON persistence (Rule: Scenario Save/Load) and for exact Human-vs-AI restore
(Rule G: Never change the scenario when comparing Human and AI)."""
import json
import os
from .grid import WarehouseGrid


class Scenario:
    def __init__(self, grid: WarehouseGrid, time_limit: int = 30, random_seed: int = 0, name: str = "scenario"):
        self.grid = grid
        self.time_limit = time_limit
        self.random_seed = random_seed
        self.name = name

    def to_dict(self):
        data = self.grid.to_dict()
        data["time_limit"] = self.time_limit
        data["random_seed"] = self.random_seed
        data["name"] = self.name
        return data

    @classmethod
    def from_dict(cls, data):
        grid = WarehouseGrid.from_dict(data)
        return cls(grid, time_limit=data.get("time_limit", 30), random_seed=data.get("random_seed", 0),
                    name=data.get("name", "scenario"))

    def save(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def clone_grid(self):
        """Return a brand-new WarehouseGrid rebuilt from this scenario's data
        (a deep copy via JSON round-trip), used to restore the exact same
        layout for a second (Human or AI) attempt."""
        return WarehouseGrid.from_dict(self.grid.to_dict())
