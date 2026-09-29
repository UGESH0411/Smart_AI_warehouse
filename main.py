"""AI Warehouse Simulator - entry point.  Run with:  python main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

STYLE = """
QMainWindow, QWidget { background: #f1f5f9; color: #0f172a; font-family: 'Segoe UI', Arial; font-size: 13px; }
QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 10px; padding: 8px; background: white; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #1e3a8a; }
QPushButton { background: #e2e8f0; border: 1px solid #94a3b8; border-radius: 6px; padding: 6px 10px; }
QPushButton:hover { background: #cbd5e1; }
QPushButton:checked { background: #2563eb; color: white; border-color: #1d4ed8; }
QPushButton:disabled { color: #94a3b8; background: #f1f5f9; }
QPushButton#accent { background: #2563eb; color: white; border: 1px solid #1d4ed8; font-weight: bold; }
QPushButton#accent:hover { background: #1d4ed8; }
QPushButton#accent:disabled { background: #93c5fd; }
QTabWidget::pane { border: 1px solid #cbd5e1; background: white; }
QTabBar::tab { padding: 8px 16px; background: #e2e8f0; border: 1px solid #cbd5e1; border-bottom: none; }
QTabBar::tab:selected { background: white; font-weight: bold; color: #1d4ed8; }
QTableWidget, QTextEdit { background: white; border: 1px solid #cbd5e1; }
QHeaderView::section { background: #1e3a8a; color: white; padding: 4px; border: none; }
QProgressBar { border: 1px solid #94a3b8; border-radius: 4px; text-align: center; background: white; }
QProgressBar::chunk { background: #2563eb; }
QSpinBox, QComboBox { background: white; border: 1px solid #94a3b8; border-radius: 4px; padding: 2px 4px; }
QStatusBar { background: #1e3a8a; color: white; }
QStatusBar QLabel { background: transparent; color: white; }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AI Warehouse Simulator")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
