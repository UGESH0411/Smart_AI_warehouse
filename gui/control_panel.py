"""Right-hand control panel: scenario configuration + action buttons."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, QSpinBox,
                               QPushButton, QLabel, QHBoxLayout, QComboBox, QCheckBox)


class ControlPanel(QWidget):
    mode_changed = Signal(str)            # SELECT / PLACE_ROBOT / ...
    generate_obstacles = Signal()
    clear_obstacles = Signal()
    reset_run = Signal()
    clear_all = Signal()
    resize_grid = Signal(int, int)
    populate = Signal(int, int)           # robots, packages
    challenge = Signal()
    manual_mode_toggled = Signal(bool)
    run_ai_clicked = Signal()
    show_reasoning_clicked = Signal()
    save_scenario_clicked = Signal()
    load_scenario_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ---- configuration ----
        box = QGroupBox("Scenario Configuration")
        form = QFormLayout()
        self.rows_spin = QSpinBox(); self.rows_spin.setRange(5, 40); self.rows_spin.setValue(20)
        self.cols_spin = QSpinBox(); self.cols_spin.setRange(5, 40); self.cols_spin.setValue(20)
        size_w = QWidget(); size_l = QHBoxLayout(size_w); size_l.setContentsMargins(0, 0, 0, 0)
        size_l.addWidget(self.rows_spin); size_l.addWidget(QLabel("x")); size_l.addWidget(self.cols_spin)
        form.addRow("Grid (rows x cols)", size_w)
        self.apply_size_btn = QPushButton("Apply Grid Size (clears layout)")
        form.addRow(self.apply_size_btn)

        self.robots_spin = QSpinBox(); self.robots_spin.setRange(1, 3); self.robots_spin.setValue(3)
        self.packages_spin = QSpinBox(); self.packages_spin.setRange(1, 30); self.packages_spin.setValue(8)
        self.density_spin = QSpinBox(); self.density_spin.setRange(0, 40); self.density_spin.setValue(20)
        self.density_spin.setSuffix(" %")
        self.seed_spin = QSpinBox(); self.seed_spin.setRange(0, 999999); self.seed_spin.setValue(48291)
        self.time_limit_spin = QSpinBox(); self.time_limit_spin.setRange(5, 600); self.time_limit_spin.setValue(30)
        self.time_limit_spin.setSuffix(" s")
        form.addRow("Robots (1-3)", self.robots_spin)
        form.addRow("Packages", self.packages_spin)
        form.addRow("Obstacle Density", self.density_spin)
        form.addRow("Random Seed", self.seed_spin)
        form.addRow("Time Limit", self.time_limit_spin)
        box.setLayout(form)
        layout.addWidget(box)

        # ---- quick generation ----
        gen_box = QGroupBox("Quick Setup")
        gl = QVBoxLayout()
        self.populate_btn = QPushButton("Auto-Populate (robots, packages, delivery)")
        self.generate_obstacles_btn = QPushButton("Generate Obstacles")
        self.clear_obstacles_btn = QPushButton("Clear Obstacles")
        self.challenge_btn = QPushButton("Challenge Mode: Generate From Seed")
        self.challenge_btn.setObjectName("accent")
        for b in (self.populate_btn, self.generate_obstacles_btn, self.clear_obstacles_btn, self.challenge_btn):
            gl.addWidget(b)
        gen_box.setLayout(gl)
        layout.addWidget(gen_box)

        # ---- manual placement ----
        place_box = QGroupBox("Manual Placement (click the grid)")
        pl = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("Package priority:"))
        self.priority_combo = QComboBox(); self.priority_combo.addItems(["normal", "high", "low"])
        row.addWidget(self.priority_combo)
        pl.addLayout(row)
        self._mode_buttons = {}
        for text, mode in (("Select / Inspect", "SELECT"), ("Place Robot", "PLACE_ROBOT"),
                           ("Add Package", "PLACE_PACKAGE"), ("Set Delivery Point", "PLACE_DELIVERY"),
                           ("Toggle Obstacle", "PLACE_OBSTACLE")):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, m=mode: self._set_mode(m))
            self._mode_buttons[mode] = btn
            pl.addWidget(btn)
        self._mode_buttons["SELECT"].setChecked(True)
        self.clear_all_btn = QPushButton("Clear Everything")
        pl.addWidget(self.clear_all_btn)
        place_box.setLayout(pl)
        layout.addWidget(place_box)

        # ---- run ----
        run_box = QGroupBox("Run")
        rl = QVBoxLayout()
        self.manual_mode_btn = QPushButton("Start Manual Mode (Human)")
        self.manual_mode_btn.setCheckable(True)
        self.run_ai_btn = QPushButton("Run AI")
        self.run_ai_btn.setObjectName("accent")
        self.reasoning_btn = QPushButton("Show AI Reasoning")
        self.show_paths_check = QCheckBox("Show AI paths")
        self.show_paths_check.setChecked(True)
        self.reset_btn = QPushButton("Reset Run (same scenario)")
        for w in (self.manual_mode_btn, self.run_ai_btn, self.reasoning_btn, self.show_paths_check, self.reset_btn):
            rl.addWidget(w)
        run_box.setLayout(rl)
        layout.addWidget(run_box)

        # ---- file ----
        io_box = QGroupBox("Scenario File (JSON)")
        il = QHBoxLayout()
        self.save_btn = QPushButton("Save"); self.load_btn = QPushButton("Load")
        il.addWidget(self.save_btn); il.addWidget(self.load_btn)
        io_box.setLayout(il)
        layout.addWidget(io_box)
        layout.addStretch(1)

        # ---- wiring ----
        self.apply_size_btn.clicked.connect(lambda: self.resize_grid.emit(self.rows_spin.value(), self.cols_spin.value()))
        self.populate_btn.clicked.connect(lambda: self.populate.emit(self.robots_spin.value(), self.packages_spin.value()))
        self.generate_obstacles_btn.clicked.connect(self.generate_obstacles.emit)
        self.clear_obstacles_btn.clicked.connect(self.clear_obstacles.emit)
        self.challenge_btn.clicked.connect(self.challenge.emit)
        self.clear_all_btn.clicked.connect(self.clear_all.emit)
        self.manual_mode_btn.toggled.connect(self.manual_mode_toggled.emit)
        self.run_ai_btn.clicked.connect(self.run_ai_clicked.emit)
        self.reasoning_btn.clicked.connect(self.show_reasoning_clicked.emit)
        self.reset_btn.clicked.connect(self.reset_run.emit)
        self.save_btn.clicked.connect(self.save_scenario_clicked.emit)
        self.load_btn.clicked.connect(self.load_scenario_clicked.emit)

    def _set_mode(self, mode):
        for m, b in self._mode_buttons.items():
            b.setChecked(m == mode)
        self.mode_changed.emit(mode)

    def current_priority(self):
        return self.priority_combo.currentText()

    def set_manual_checked(self, checked):
        self.manual_mode_btn.blockSignals(True)
        self.manual_mode_btn.setChecked(checked)
        self.manual_mode_btn.setText("Stop Manual Mode" if checked else "Start Manual Mode (Human)")
        self.manual_mode_btn.blockSignals(False)

    def set_running(self, running):
        """Disable editing controls while a run is in progress."""
        for w in (self.apply_size_btn, self.populate_btn, self.generate_obstacles_btn, self.clear_obstacles_btn,
                  self.challenge_btn, self.clear_all_btn, self.run_ai_btn, self.load_btn, self.reset_btn,
                  self.rows_spin, self.cols_spin):
            w.setEnabled(not running)
        for b in self._mode_buttons.values():
            b.setEnabled(not running)
