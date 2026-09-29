"""Bottom status/metrics panel: per-robot state table + run summary."""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel,
                               QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar)


class MetricsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        table_box = QGroupBox("Robot Status")
        tl = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Robot", "State", "Carrying", "Distance"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMaximumHeight(130)
        tl.addWidget(self.table)
        table_box.setLayout(tl)
        layout.addWidget(table_box, 3)

        mbox = QGroupBox("Run Metrics")
        ml = QVBoxLayout()
        self.mode_label = QLabel("Mode: idle")
        self.delivered_label = QLabel("Delivered: 0/0    Remaining: 0")
        self.distance_label = QLabel("Distance: 0")
        self.time_label = QLabel("Time: 0.0 s")
        self.invalid_label = QLabel("Invalid Moves: 0    Nodes Explored: 0")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat("Time used: %p%")
        for w in (self.mode_label, self.delivered_label, self.distance_label,
                  self.time_label, self.invalid_label, self.progress):
            ml.addWidget(w)
        mbox.setLayout(ml)
        layout.addWidget(mbox, 2)

    def update_robots(self, robots):
        self.table.setRowCount(len(robots))
        for i, r in enumerate(robots):
            for j, text in enumerate((r.robot_id, r.state.value, r.carrying_package or "-",
                                      f"{r.distance_travelled:.0f}")):
                self.table.setItem(i, j, QTableWidgetItem(text))

    def update_metrics(self, mode, delivered, total, distance, elapsed, limit, invalid, nodes):
        self.mode_label.setText(f"Mode: {mode}")
        self.delivered_label.setText(f"Delivered: {delivered}/{total}    Remaining: {total - delivered}")
        self.distance_label.setText(f"Distance: {distance:.0f}")
        self.time_label.setText(f"Time: {elapsed:.1f} s   (limit {limit} s)")
        self.invalid_label.setText(f"Invalid Moves: {invalid}    Nodes Explored: {nodes}")
        self.progress.setValue(min(100, int(elapsed / max(1, limit) * 100)))
