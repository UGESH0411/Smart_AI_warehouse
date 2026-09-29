"""Human vs AI comparison table widget."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel


class ComparisonView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title_label = QLabel(
            "Human vs AI\n\nWorkflow: build a scenario -> Start Manual Mode and play it -> "
            "press Stop (or finish) -> Reset Run -> Run AI. The table fills from the REAL runs "
            "(nothing is hard-coded).")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Metric", "Human", "AI"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.verdict = QLabel("")
        self.verdict.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self.verdict)

    def set_rows(self, rows, verdict=""):
        self.table.setRowCount(len(rows))
        for i, (metric, hv, av) in enumerate(rows):
            for j, t in enumerate((metric, hv, av)):
                self.table.setItem(i, j, QTableWidgetItem(t))
        self.verdict.setText(verdict)

    def set_message(self, text):
        self.table.setRowCount(0)
        self.verdict.setText(text)
