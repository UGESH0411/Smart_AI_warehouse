"""QTimer wrapper tracking elapsed time against a time limit."""
from PySide6.QtCore import QObject, QTimer, Signal


class TimerManager(QObject):
    tick = Signal(float, float)   # elapsed_seconds, remaining_seconds
    time_up = Signal()

    def __init__(self, interval_ms=100, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._on_tick)
        self._elapsed_ms = 0
        self._time_limit_s = 30
        self._running = False

    def start(self, time_limit_s):
        self._time_limit_s = time_limit_s
        self._elapsed_ms = 0
        self._running = True
        self._timer.start()

    def stop(self):
        self._running = False
        self._timer.stop()

    def is_running(self):
        return self._running

    def elapsed_seconds(self):
        return self._elapsed_ms / 1000.0

    def _on_tick(self):
        if not self._running:
            return
        self._elapsed_ms += self._timer.interval()
        elapsed = self._elapsed_ms / 1000.0
        remaining = max(0.0, self._time_limit_s - elapsed)
        self.tick.emit(elapsed, remaining)
        if remaining <= 0:
            self.stop()
            self.time_up.emit()
