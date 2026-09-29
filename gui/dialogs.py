"""Reusable dialogs: About box, reasoning viewer, error helpers."""
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton


def show_error(parent, title, message):
    QMessageBox.critical(parent, title, message)


def show_warning(parent, title, message):
    QMessageBox.warning(parent, title, message)


def show_info(parent, title, message):
    QMessageBox.information(parent, title, message)


def show_about(parent):
    QMessageBox.about(
        parent, "About AI Warehouse Simulator",
        "<h3>AI Warehouse Simulator</h3>"
        "<p>AI-Based Multi-Robot Warehouse Package Collection and Route Optimization.</p>"
        "<p>Demonstrates A*, Hill Climbing, TSP-inspired multi-robot routing, Minimax, "
        "4-Queens constraint satisfaction and Prolog knowledge representation "
        "on an interactive Qt (PySide6) warehouse.</p>"
        "<p><i>Solutions are heuristic: 'best found', not proven optimal.</i></p>")


class ReasoningDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(620, 520)
        layout = QVBoxLayout(self)
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setPlainText(text)
        edit.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 12px;")
        layout.addWidget(edit)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
