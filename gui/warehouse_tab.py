"""Primary Warehouse tab: editing, Human (manual) mode, AI mode, Challenge mode."""
import json
import os
import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QScrollArea

from warehouse.grid import WarehouseGrid
from warehouse.scenario import Scenario
from warehouse.obstacle import generate_valid_obstacles, validate_reachability
from warehouse.robot import RobotState
from simulation.robot_controller import attempt_move
from simulation.timer_manager import TimerManager
from simulation.animation import PathAnimator
from evaluation.metrics import RunMetrics
from evaluation.scoring import compute_score, priority_violations
from gui.warehouse_view import (WarehouseScene, WarehouseView, MODE_SELECT, MODE_PLACE_PACKAGE,
                                MODE_PLACE_ROBOT, MODE_PLACE_DELIVERY, MODE_PLACE_OBSTACLE)
from gui.control_panel import ControlPanel
from gui.metrics_panel import MetricsPanel
from gui.ai_worker import AIPlanWorker
from gui.dialogs import show_error, show_warning, show_info, ReasoningDialog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIO_DIR = os.path.join(BASE_DIR, "scenarios")

KEY_MOVES = {
    Qt.Key_Up: (-1, 0), Qt.Key_W: (-1, 0),
    Qt.Key_Down: (1, 0), Qt.Key_S: (1, 0),
    Qt.Key_Left: (0, -1), Qt.Key_A: (0, -1),
    Qt.Key_Right: (0, 1), Qt.Key_D: (0, 1),
}
ROBOT_KEYS = {Qt.Key_1: 0, Qt.Key_2: 1, Qt.Key_3: 2}
AI_STEP_MS = 110


class WarehouseTab(QWidget):
    status_message = Signal(str)
    run_completed = Signal(str)
    results_changed = Signal(object, object, bool)   # human, ai, same_scenario

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = WarehouseGrid(20, 20)
        self.time_limit = 30
        self.seed = 48291

        # run state
        self.run_mode = None            # None / "Human" / "AI"
        self.invalid_moves = 0
        self.active_robot_index = 0
        self.delivery_log = []
        self.plan = None
        self.animators = []
        self.finished_robots = set()
        self.worker = None
        self.human_metrics = None
        self.ai_metrics = None
        self.human_sig = None
        self.ai_sig = None

        # widgets
        self.scene = WarehouseScene()
        self.view = WarehouseView(self.scene)
        self.scene.set_grid(self.grid)
        self.control = ControlPanel()
        self.metrics = MetricsPanel()
        self.timer = TimerManager(100, self)

        left = QVBoxLayout()
        left.addWidget(self.view, 1)
        left.addWidget(self.metrics)
        scroll = QScrollArea()
        scroll.setWidget(self.control)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(330)
        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addWidget(scroll)

        # wiring
        self.scene.cell_clicked.connect(self.on_cell_clicked)
        self.view.key_pressed.connect(self.on_key)
        self.timer.tick.connect(self.on_tick)
        self.timer.time_up.connect(self.on_time_up)
        c = self.control
        c.mode_changed.connect(self.scene.set_mode)
        c.resize_grid.connect(self.apply_grid_size)
        c.populate.connect(self.populate)
        c.generate_obstacles.connect(self.generate_obstacles)
        c.clear_obstacles.connect(self.clear_obstacles)
        c.clear_all.connect(self.clear_all)
        c.challenge.connect(self.generate_challenge)
        c.reset_run.connect(self.reset_run)
        c.manual_mode_toggled.connect(self.on_manual_toggled)
        c.run_ai_clicked.connect(self.run_ai)
        c.show_reasoning_clicked.connect(self.show_reasoning)
        c.save_scenario_clicked.connect(self.save_scenario)
        c.load_scenario_clicked.connect(self.load_scenario)
        self.refresh_metrics(0.0)

    # ------------------------------------------------------------------ helpers
    def msg(self, text):
        self.status_message.emit(text)

    def signature(self):
        return json.dumps(self.grid.to_dict(), sort_keys=True)

    def is_running(self):
        return self.run_mode is not None

    def redraw(self):
        self.scene.redraw()
        self.metrics.update_robots(self.grid.robots)

    def layout_changed(self):
        """Any edit to the layout invalidates stored Human/AI results."""
        self.human_metrics = self.ai_metrics = None
        self.human_sig = self.ai_sig = None
        self.plan = None
        self.results_changed.emit(None, None, False)
        self.redraw()
        self.refresh_metrics(0.0)

    def validate_for_run(self):
        if not self.grid.robots:
            show_error(self, "No robots", "Place at least one robot first (or use Auto-Populate).")
            return False
        if self.grid.delivery is None:
            show_error(self, "No delivery point", "Set a delivery point first.")
            return False
        if not self.grid.packages:
            show_error(self, "No packages", "Add at least one package first.")
            return False
        ok, unreachable = validate_reachability(self.grid.rows, self.grid.cols, self.grid.obstacles,
                                                self.grid.robots, self.grid.packages, self.grid.delivery)
        # check every robot separately for reachability
        from warehouse.obstacle import bfs_reachable
        bad = set()
        for r in self.grid.robots:
            reach = bfs_reachable(self.grid.rows, self.grid.cols, self.grid.obstacles, (r.row, r.col))
            if (self.grid.delivery.row, self.grid.delivery.col) not in reach:
                show_error(self, "Unreachable delivery point",
                           f"Robot {r.robot_id} cannot reach the delivery point. Remove some obstacles.")
                return False
            for p in self.grid.packages:
                if (p.row, p.col) not in reach:
                    bad.add(p.package_id)
        if bad:
            show_warning(self, "Unreachable packages",
                         "Some packages cannot be reached by every robot: " + ", ".join(sorted(bad)) +
                         ".\nThe AI will skip packages it cannot reach.")
        return True

    # ------------------------------------------------------------------ editing
    def on_cell_clicked(self, row, col):
        if self.is_running():
            return
        g = self.grid
        mode = self.scene.mode
        if mode == MODE_SELECT:
            what = "empty"
            if (row, col) in g.obstacles:
                what = "obstacle"
            for r in g.robots:
                if (r.row, r.col) == (row, col):
                    what = f"robot {r.robot_id}"
            for p in g.packages:
                if (p.row, p.col) == (row, col):
                    what = f"package {p.package_id} (priority {p.priority})"
            if g.delivery and (g.delivery.row, g.delivery.col) == (row, col):
                what = "delivery point"
            self.msg(f"Cell ({row}, {col}): {what}")
            return
        if mode == MODE_PLACE_ROBOT:
            if len(g.robots) >= 3:
                self.msg("Maximum of 3 robots supported.")
                return
            if g.add_robot(row, col) is None:
                self.msg("Invalid position: cell is blocked or occupied.")
                return
        elif mode == MODE_PLACE_PACKAGE:
            if g.add_package(row, col, self.control.current_priority()) is None:
                self.msg("Invalid position: cell is blocked or occupied.")
                return
        elif mode == MODE_PLACE_DELIVERY:
            old = g.delivery
            g.delivery = None
            if not g.set_delivery(row, col):
                g.delivery = old
                self.msg("Invalid position: cell is blocked or occupied.")
                return
        elif mode == MODE_PLACE_OBSTACLE:
            if (row, col) in g.obstacles:
                g.remove_obstacle(row, col)
            elif not g.add_obstacle(row, col):
                self.msg("Cannot place an obstacle on a robot, package or delivery point.")
                return
        self.layout_changed()

    def apply_grid_size(self, rows, cols):
        self.grid = WarehouseGrid(rows, cols)
        self.scene.set_grid(self.grid)
        self.layout_changed()
        self.msg(f"New empty {rows}x{cols} warehouse.")

    def clear_all(self):
        self.grid.clear_all()
        self.layout_changed()
        self.msg("Warehouse cleared.")

    def clear_obstacles(self):
        self.grid.clear_obstacles()
        self.layout_changed()
        self.msg("Obstacles cleared.")

    def populate(self, n_robots, n_packages, seed=None):
        """Randomly place robots, delivery point and packages (reproducible by seed)."""
        seed = self.control.seed_spin.value() if seed is None else seed
        rng = random.Random(seed)
        rows, cols = self.grid.rows, self.grid.cols
        if n_robots + n_packages + 1 > rows * cols // 2:
            show_error(self, "Grid too small", "Too many objects for this grid size.")
            return False
        self.grid.clear_all()
        cells = [(r, c) for r in range(rows) for c in range(cols)]
        rng.shuffle(cells)
        it = iter(cells)
        for _ in range(n_robots):
            self.grid.add_robot(*next(it))
        dr, dc = next(it)
        self.grid.set_delivery(dr, dc)
        priorities = ["normal", "normal", "high", "low"]
        for _ in range(n_packages):
            self.grid.add_package(*next(it), priority=rng.choice(priorities))
        self.layout_changed()
        self.msg(f"Placed {n_robots} robots, {n_packages} packages and a delivery point (seed {seed}).")
        return True

    def generate_obstacles(self, silent=False):
        density = self.control.density_spin.value() / 100.0
        seed = self.control.seed_spin.value()
        obstacles, used_seed = generate_valid_obstacles(
            self.grid.rows, self.grid.cols, density, seed,
            self.grid.robots, self.grid.packages, self.grid.delivery)
        self.grid.obstacles = obstacles
        self.layout_changed()
        if not silent:
            note = "" if used_seed == seed else f" (seed adjusted to {used_seed} to keep everything reachable)"
            self.msg(f"Generated {len(obstacles)} obstacles at {self.control.density_spin.value()}% density{note}.")

    def generate_challenge(self):
        if self.is_running():
            return
        seed = self.control.seed_spin.value()
        if not self.populate(self.control.robots_spin.value(), self.control.packages_spin.value(), seed):
            return
        self.generate_obstacles(silent=True)
        self.time_limit = self.control.time_limit_spin.value()
        path = os.path.join(SCENARIO_DIR, f"challenge_seed{seed}.json")
        try:
            Scenario(self.grid, self.time_limit, seed, f"challenge_{seed}").save(path)
            saved = f"Saved to scenarios/challenge_seed{seed}.json."
        except OSError as exc:
            saved = f"(Could not auto-save: {exc})"
        show_info(self, "Challenge generated",
                  f"Challenge scenario ready (seed {seed}). {saved}\n\n"
                  "1) Click 'Start Manual Mode' and collect the packages yourself.\n"
                  "2) Click 'Reset Run', then 'Run AI' on the exact same scenario.\n"
                  "3) Open the 'Human vs AI' tab for the comparison.")

    # ------------------------------------------------------------------ run control
    def begin_run(self, mode):
        self.run_mode = mode
        self.control.set_running(True)
        self.grid.reset_run_state()
        self.delivery_log = []
        self.invalid_moves = 0
        self.scene.clear_path_overlay()
        self.redraw()
        self.time_limit = self.control.time_limit_spin.value()

    def end_run_controls(self):
        self.run_mode = None
        self.view.capture_keys = False
        self.control.set_running(False)
        self.control.set_manual_checked(False)

    def reset_run(self):
        if self.is_running():
            self.abort_run()
        self.grid.reset_run_state()
        self.redraw()
        self.refresh_metrics(0.0)
        self.msg("Run reset: robots and packages restored to the exact scenario start.")

    def abort_run(self):
        self.timer.stop()
        for a in self.animators:
            a.stop()
        self.animators = []
        self.end_run_controls()

    # ------------------------------------------------------------------ manual mode
    def on_manual_toggled(self, checked):
        if checked:
            if self.is_running() or not self.validate_for_run():
                self.control.set_manual_checked(False)
                return
            self.begin_run("Human")
            self.active_robot_index = 0
            self.view.capture_keys = True
            self.control.set_manual_checked(True)
            self.control.set_running(True)
            self.control.manual_mode_btn.setEnabled(True)
            self.timer.start(self.time_limit)
            self.view.setFocus()
            self.msg("Manual mode: Arrow keys / WASD move the active robot. Keys 1-3 switch robot. "
                     "Walk onto a package to pick it up, then onto the delivery point.")
        elif self.run_mode == "Human":
            self.finish_human("Stopped by user")

    def on_key(self, key):
        if self.run_mode != "Human":
            return
        if key in ROBOT_KEYS:
            idx = ROBOT_KEYS[key]
            if idx < len(self.grid.robots):
                self.active_robot_index = idx
                self.msg(f"Now controlling {self.grid.robots[idx].robot_id}.")
            return
        drdc = KEY_MOVES.get(key)
        if drdc is None:
            return
        robot = self.grid.robots[self.active_robot_index]
        result = attempt_move(self.grid, robot, *drdc)
        if not result.valid:
            self.invalid_moves += 1
            self.msg("Invalid move: blocked by an obstacle or the warehouse boundary.")
        else:
            self.scene.move_robot_visual(robot.robot_id, robot.row, robot.col)
            if result.event == "pickup":
                self.msg(f"{robot.robot_id} picked up {result.package_id}. Now go to the delivery point.")
                self.redraw()
            elif result.event == "deliver":
                self.delivery_log.append(result.package_id)
                self.msg(f"{robot.robot_id} delivered {result.package_id}.")
                self.redraw()
        self.metrics.update_robots(self.grid.robots)
        self.refresh_metrics(self.timer.elapsed_seconds())
        if self.grid.all_delivered():
            self.finish_human("All packages delivered")

    def finish_human(self, reason):
        elapsed = self.timer.elapsed_seconds()
        self.timer.stop()
        m = self.collect_metrics("Human", elapsed)
        self.human_metrics, self.human_sig = m, self.signature()
        self.end_run_controls()
        self.refresh_metrics(elapsed)
        self.after_run(m, reason)

    # ------------------------------------------------------------------ AI mode
    def run_ai(self):
        if self.is_running() or not self.validate_for_run():
            return
        self.begin_run("AI")
        self.msg("Computing AI plan in a background thread...")
        self.worker = AIPlanWorker(self.grid, self.control.seed_spin.value(), self)
        self.worker.plan_ready.connect(self.on_plan_ready)
        self.worker.failed.connect(self.on_plan_failed)
        self.worker.start()

    def on_plan_failed(self, message):
        self.abort_run()
        show_error(self, "AI planning failed", message)

    def on_plan_ready(self, plan):
        if self.run_mode != "AI":
            return
        self.plan = plan
        if plan.unreachable_packages:
            show_warning(self, "Unreachable packages",
                         "These packages cannot be reached and will be skipped: " +
                         ", ".join(sorted(set(plan.unreachable_packages))))
        for robot in self.grid.robots:
            rp = plan.robot_plans[robot.robot_id]
            robot.assigned_packages = list(rp.package_order)
            robot.state = RobotState.MOVING_TO_PACKAGE if rp.package_order else RobotState.FINISHED
            if self.control.show_paths_check.isChecked():
                self.scene.show_path_overlay(rp.full_path, robot.color)
        self.finished_robots = set()
        self.animators = []
        for robot in self.grid.robots:
            rp = plan.robot_plans[robot.robot_id]
            anim = PathAnimator(robot.robot_id, rp.full_path, rp.events, AI_STEP_MS, self)
            anim.step_moved.connect(self.on_ai_step)
            anim.event_fired.connect(self.on_ai_event)
            anim.finished.connect(self.on_ai_robot_finished)
            self.animators.append(anim)
        self.metrics.update_robots(self.grid.robots)
        self.timer.start(self.time_limit)
        self.msg("Robots executing the plan. Use 'Show AI Reasoning' for details.")
        for anim in list(self.animators):
            anim.start()

    def on_ai_step(self, robot_id, row, col):
        robot = self.grid.get_robot(robot_id)
        robot.row, robot.col = row, col
        robot.distance_travelled += 1
        robot.state = RobotState.MOVING_TO_DELIVERY if robot.carrying_package else RobotState.MOVING_TO_PACKAGE
        self.scene.move_robot_visual(robot_id, row, col)
        self.metrics.update_robots(self.grid.robots)

    def on_ai_event(self, robot_id, etype, package_id):
        robot = self.grid.get_robot(robot_id)
        pkg = self.grid.get_package(package_id)
        if etype == "pickup":
            if robot.carrying_package is not None:      # Rule 3 safeguard
                return
            pkg.picked = True
            robot.carrying_package = package_id
            robot.state = RobotState.CARRYING
        else:
            pkg.delivered = True
            robot.carrying_package = None
            robot.delivered_count += 1
            robot.state = RobotState.DELIVERING
            self.delivery_log.append(package_id)
        overlay = self.control.show_paths_check.isChecked()
        self.redraw()
        if overlay and self.plan:
            for r in self.grid.robots:
                self.scene.show_path_overlay(self.plan.robot_plans[r.robot_id].full_path, r.color)

    def on_ai_robot_finished(self, robot_id):
        robot = self.grid.get_robot(robot_id)
        robot.state = RobotState.FINISHED
        self.finished_robots.add(robot_id)
        self.metrics.update_robots(self.grid.robots)
        if len(self.finished_robots) == len(self.animators) and self.run_mode == "AI":
            self.finish_ai("Plan completed")

    def finish_ai(self, reason):
        elapsed = self.timer.elapsed_seconds()
        self.timer.stop()
        for a in self.animators:
            a.stop()
        m = self.collect_metrics("AI", elapsed)
        if self.plan:
            m.nodes_explored = self.plan.total_nodes_explored
            m.path_length = self.plan.total_distance
            m.initial_cost = self.plan.initial_cost
            m.final_cost = self.plan.final_cost
        self.ai_metrics, self.ai_sig = m, self.signature()
        self.animators = []
        self.end_run_controls()
        self.refresh_metrics(elapsed)
        self.after_run(m, reason)

    def show_reasoning(self):
        if self.plan is None:
            show_info(self, "AI reasoning", "Run the AI first to see its reasoning.")
            return
        extra = ("\n\nPipeline: greedy assignment (high-priority packages first, cf. Prolog rule "
                 "high_priority_package/1) -> Hill Climbing over assignment/order -> TSP-inspired "
                 "nearest-neighbour ordering -> A* for every leg. Each robot carries ONE package at a time.")
        ReasoningDialog("AI Reasoning", self.plan.describe() + extra, self).exec()

    # ------------------------------------------------------------------ metrics
    def collect_metrics(self, mode, elapsed):
        delivered = sum(1 for p in self.grid.packages if p.delivered)
        distance = sum(r.distance_travelled for r in self.grid.robots)
        used = sum(1 for r in self.grid.robots if r.delivered_count > 0)
        prios = {p.package_id: p.priority for p in self.grid.packages}
        viol = priority_violations(self.delivery_log, prios)
        m = RunMetrics(mode=mode, distance=distance, time_seconds=elapsed, packages_delivered=delivered,
                       packages_total=len(self.grid.packages), invalid_moves=self.invalid_moves,
                       robot_utilization=100.0 * used / max(1, len(self.grid.robots)))
        m.score = compute_score(delivered, distance, elapsed, self.invalid_moves, viol)
        return m

    def refresh_metrics(self, elapsed):
        delivered = sum(1 for p in self.grid.packages if p.delivered)
        distance = sum(r.distance_travelled for r in self.grid.robots)
        nodes = self.plan.total_nodes_explored if (self.plan and self.run_mode == "AI") else 0
        self.metrics.update_metrics(self.run_mode or "idle", delivered, len(self.grid.packages), distance,
                                    elapsed, self.control.time_limit_spin.value(), self.invalid_moves, nodes)
        self.metrics.update_robots(self.grid.robots)

    def on_tick(self, elapsed, remaining):
        self.refresh_metrics(elapsed)

    def on_time_up(self):
        if self.run_mode == "Human":
            self.finish_human("Time limit reached")
        elif self.run_mode == "AI":
            self.finish_ai("Time limit reached")

    def after_run(self, m, reason):
        same = (self.human_sig is not None and self.human_sig == self.ai_sig)
        self.results_changed.emit(self.human_metrics, self.ai_metrics, same)
        text = (f"[{m.mode}] {reason}: delivered {m.packages_delivered}/{m.packages_total}, "
                f"distance {m.distance:.0f}, time {m.time_seconds:.1f}s, invalid moves {m.invalid_moves}, "
                f"utilization {m.robot_utilization:.0f}%, score {m.score:.1f}")
        self.run_completed.emit(text)
        self.msg(text)
        show_info(self, f"{m.mode} run finished", text)

    # ------------------------------------------------------------------ files
    def save_scenario(self):
        if self.is_running():
            return
        os.makedirs(SCENARIO_DIR, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, "Save Scenario", os.path.join(SCENARIO_DIR, "scenario.json"),
                                              "JSON files (*.json)")
        if not path:
            return
        try:
            Scenario(self.grid, self.control.time_limit_spin.value(),
                     self.control.seed_spin.value(), os.path.basename(path)).save(path)
            self.msg(f"Scenario saved: {path}")
        except OSError as exc:
            show_error(self, "Save failed", str(exc))

    def load_scenario(self):
        if self.is_running():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load Scenario", SCENARIO_DIR, "JSON files (*.json)")
        if not path:
            return
        try:
            sc = Scenario.load(path)
            g = sc.grid
            for r in g.robots:
                if not g.in_bounds(r.row, r.col) or (r.row, r.col) in g.obstacles:
                    raise ValueError(f"Invalid robot position for {r.robot_id}")
            for p in g.packages:
                if not g.in_bounds(p.row, p.col) or (p.row, p.col) in g.obstacles:
                    raise ValueError(f"Invalid package position for {p.package_id}")
            if g.delivery and (not g.in_bounds(g.delivery.row, g.delivery.col)
                               or (g.delivery.row, g.delivery.col) in g.obstacles):
                raise ValueError("Invalid delivery point position")
        except (json.JSONDecodeError, KeyError, TypeError, IndexError, ValueError, OSError) as exc:
            show_error(self, "Invalid scenario file", f"Could not load scenario:\n{exc}")
            return
        self.grid = sc.grid
        self.scene.set_grid(self.grid)
        self.control.rows_spin.setValue(self.grid.rows)
        self.control.cols_spin.setValue(self.grid.cols)
        self.control.time_limit_spin.setValue(int(sc.time_limit))
        self.control.seed_spin.setValue(int(sc.random_seed))
        self.layout_changed()
        self.msg(f"Scenario loaded: {path}")
