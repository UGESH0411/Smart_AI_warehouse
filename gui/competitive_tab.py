"""Competitive Mode tab: Minimax (alpha-beta) adversarial pickup game."""
import random
from PySide6.QtCore import QTimer
from PySide6.QtGui import QBrush, QColor, QPen, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QGraphicsScene,
                               QGraphicsView, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem)
from ai.minimax import CompetitiveState, best_move_for, apply_move
from warehouse.obstacle import bfs_reachable

CELL = 44


class CompetitiveTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        intro = QLabel("MAX = Team A (blue), MIN = Team B (red). State: both positions, remaining packages, "
                       "whose turn. Actions: move 4-way or stay. Utility: scoreA - scoreB. Both teams choose "
                       "moves by Minimax with alpha-beta pruning to the chosen depth.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Search depth:"))
        self.depth_spin = QSpinBox(); self.depth_spin.setRange(2, 6); self.depth_spin.setValue(4)
        controls.addWidget(self.depth_spin)
        self.new_btn = QPushButton("New Game")
        self.step_btn = QPushButton("Step")
        self.auto_btn = QPushButton("Auto-Play")
        self.auto_btn.setObjectName("accent")
        for b in (self.new_btn, self.step_btn, self.auto_btn):
            controls.addWidget(b)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.rows = self.cols = 8
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFixedSize(self.cols * CELL + 14, self.rows * CELL + 14)
        layout.addWidget(self.view)
        self.status = QLabel("Press New Game.")
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.obstacles = set()
        self.state = None
        self.game_over = False
        self.timer = QTimer(self)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.step)
        self.new_btn.clicked.connect(self.new_game)
        self.step_btn.clicked.connect(self.step)
        self.auto_btn.clicked.connect(self._toggle_auto)
        self.new_game()

    def new_game(self):
        self.timer.stop()
        self.auto_btn.setText("Auto-Play")
        rng = random.Random()
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        while True:
            rng.shuffle(cells)
            self.obstacles = set(cells[:8])
            free = [c for c in cells[8:]]
            reach = bfs_reachable(self.rows, self.cols, self.obstacles, free[0])
            chosen = [c for c in free if c in reach]
            if len(chosen) >= 8 and free[1] in reach:
                break
        posA, posB = free[0], free[1]
        others = [c for c in chosen if c not in (posA, posB)][:6]
        packages = {c: rng.choice([10, 20, 30]) for c in others}
        self.state = CompetitiveState(posA, posB, packages, 0, 0, "A")
        self.game_over = False
        self.status.setText("New game. Team A (blue) moves first.")
        self._draw()

    def _toggle_auto(self):
        if self.timer.isActive():
            self.timer.stop()
            self.auto_btn.setText("Auto-Play")
        elif not self.game_over:
            self.timer.start()
            self.auto_btn.setText("Pause")

    def step(self):
        if self.state is None or self.game_over:
            self.timer.stop()
            self.auto_btn.setText("Auto-Play")
            return
        mover = self.state.turn
        move = best_move_for(self.state, self.depth_spin.value(), self.rows, self.cols, self.obstacles) or (0, 0)
        self.state = apply_move(self.state, mover, move[0], move[1], self.rows, self.cols, self.obstacles)
        self._draw()
        if not self.state.packages:
            self.game_over = True
            self.timer.stop()
            self.auto_btn.setText("Auto-Play")
            a, b = self.state.scoreA, self.state.scoreB
            result = "Team A wins!" if a > b else "Team B wins!" if b > a else "Tie!"
            self.status.setText(f"Game over. A={a}  B={b}. {result}")
        else:
            self.status.setText(f"Score A={self.state.scoreA}  B={self.state.scoreB}. Next: Team {self.state.turn}")

    def _draw(self):
        self.scene.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                rect = QGraphicsRectItem(c * CELL, r * CELL, CELL, CELL)
                rect.setBrush(QBrush(QColor("#334155") if (r, c) in self.obstacles else QColor("#f8fafc")))
                rect.setPen(QPen(QColor("#dbe4ee")))
                self.scene.addItem(rect)
        if self.state is None:
            return
        for (r, c), v in self.state.packages.items():
            item = QGraphicsRectItem(c * CELL + 8, r * CELL + 8, CELL - 16, CELL - 16)
            item.setBrush(QBrush(QColor("#f59e0b")))
            self.scene.addItem(item)
            t = QGraphicsSimpleTextItem(str(v))
            t.setFont(QFont("Arial", 9, QFont.Bold))
            t.setPos(c * CELL + 12, r * CELL + 12)
            self.scene.addItem(t)
        for pos, color in ((self.state.posA, "#2563eb"), (self.state.posB, "#dc2626")):
            e = QGraphicsEllipseItem(pos[1] * CELL + 5, pos[0] * CELL + 5, CELL - 10, CELL - 10)
            e.setBrush(QBrush(QColor(color)))
            self.scene.addItem(e)
