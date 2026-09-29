"""Constraint Solver tab: 4-Queens framed as charging-station placement."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsScene,
                               QGraphicsView, QGraphicsRectItem, QGraphicsEllipseItem, QComboBox)
from ai.four_queens import solve_four_queens

CELL = 70


class ConstraintSolverTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        intro = QLabel("Four charging stations must be placed on a 4x4 warehouse zone so that no two share a "
                       "row, column or diagonal (the 4-Queens constraint satisfaction problem, solved by "
                       "backtracking search).")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        controls = QHBoxLayout()
        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setObjectName("accent")
        self.solution_combo = QComboBox()
        controls.addWidget(self.solve_btn)
        controls.addWidget(QLabel("Show:"))
        controls.addWidget(self.solution_combo)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFixedSize(4 * CELL + 14, 4 * CELL + 14)
        layout.addWidget(self.view)
        self.info = QLabel("Press Solve.")
        layout.addWidget(self.info)
        layout.addStretch(1)
        self._solutions = []
        self.solve_btn.clicked.connect(self.solve)
        self.solution_combo.currentIndexChanged.connect(self._draw)
        self._draw_board()

    def solve(self):
        self._solutions, states = solve_four_queens(4)
        self.solution_combo.blockSignals(True)
        self.solution_combo.clear()
        for i in range(len(self._solutions)):
            self.solution_combo.addItem(f"Solution {i + 1}")
        self.solution_combo.blockSignals(False)
        self.info.setText(f"Found {len(self._solutions)} solutions. States explored by backtracking: {states}.")
        self._draw(0)

    def _draw_board(self):
        self.scene.clear()
        for r in range(4):
            for c in range(4):
                rect = QGraphicsRectItem(c * CELL, r * CELL, CELL, CELL)
                rect.setBrush(QBrush(QColor("#f1f5f9") if (r + c) % 2 == 0 else QColor("#cbd5e1")))
                rect.setPen(QPen(QColor("#94a3b8")))
                self.scene.addItem(rect)

    def _draw(self, index):
        self._draw_board()
        if 0 <= index < len(self._solutions):
            for row, col in enumerate(self._solutions[index]):
                s = QGraphicsEllipseItem(col * CELL + 12, row * CELL + 12, CELL - 24, CELL - 24)
                s.setBrush(QBrush(QColor("#2563eb")))
                s.setPen(QPen(Qt.NoPen))
                self.scene.addItem(s)
