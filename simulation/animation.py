"""Step-by-step path animation using QTimer: robots visibly move cell by cell
(no teleporting) and pickup/delivery events fire at the right path index."""
from PySide6.QtCore import QObject, QTimer, Signal


class PathAnimator(QObject):
    step_moved = Signal(str, int, int)        # robot_id, row, col
    event_fired = Signal(str, str, str)       # robot_id, event_type, package_id
    finished = Signal(str)                    # robot_id

    def __init__(self, robot_id, path, events, interval_ms=150, parent=None):
        super().__init__(parent)
        self.robot_id = robot_id
        self.path = path
        self.events = {idx: (etype, pid) for idx, etype, pid in events}
        self._index = 0
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._advance)

    def start(self):
        self._index = 1
        if len(self.path) > 1:
            self._timer.start()
        else:
            self.finished.emit(self.robot_id)

    def stop(self):
        self._timer.stop()

    def _advance(self):
        if self._index >= len(self.path):
            self._timer.stop()
            self.finished.emit(self.robot_id)
            return
        r, c = self.path[self._index]
        self.step_moved.emit(self.robot_id, r, c)
        if self._index in self.events:
            etype, pid = self.events[self._index]
            self.event_fired.emit(self.robot_id, etype, pid)
        self._index += 1
        if self._index >= len(self.path):
            self._timer.stop()
            self.finished.emit(self.robot_id)
