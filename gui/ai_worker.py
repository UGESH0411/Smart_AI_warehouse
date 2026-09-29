"""Background worker so AI planning never freezes the GUI."""
from PySide6.QtCore import QThread, Signal


class AIPlanWorker(QThread):
    plan_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, grid, seed, parent=None):
        super().__init__(parent)
        self.grid = grid
        self.seed = seed

    def run(self):
        try:
            from simulation.engine import build_ai_plan
            self.plan_ready.emit(build_ai_plan(self.grid, use_hill_climbing=True, seed=self.seed))
        except Exception as exc:   # report any planning failure to the GUI
            self.failed.emit(str(exc))
