"""Results tab: session log of every Human / AI run."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Session run log (real measured results):"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 12px;")
        layout.addWidget(self.log)

    def append_entry(self, text):
        self.log.append(text + "\n")
