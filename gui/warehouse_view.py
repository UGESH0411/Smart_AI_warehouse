"""Interactive Qt warehouse view built on QGraphicsScene / QGraphicsView."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsRectItem,
                               QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsLineItem)

CELL_SIZE = 30

MODE_SELECT = "SELECT"
MODE_PLACE_PACKAGE = "PLACE_PACKAGE"
MODE_PLACE_ROBOT = "PLACE_ROBOT"
MODE_PLACE_DELIVERY = "PLACE_DELIVERY"
MODE_PLACE_OBSTACLE = "PLACE_OBSTACLE"

COLOR_BG = QColor("#f8fafc")
COLOR_GRID_LINE = QColor("#dbe4ee")
COLOR_OBSTACLE = QColor("#334155")
COLOR_DELIVERY = QColor("#059669")
COLOR_PACKAGE = {"high": QColor("#dc2626"), "normal": QColor("#d97706"), "low": QColor("#65a30d")}

MOVE_KEYS = {Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
             Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D,
             Qt.Key_1, Qt.Key_2, Qt.Key_3}


class WarehouseScene(QGraphicsScene):
    cell_clicked = Signal(int, int)   # row, col

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = None
        self.mode = MODE_SELECT
        self._robot_items = {}
        self._robot_labels = {}
        self._path_items = []
        self._explored_items = []

    def set_grid(self, grid):
        self.grid = grid
        self.redraw()

    def set_mode(self, mode):
        self.mode = mode

    def mousePressEvent(self, event):
        if self.grid is not None and event.button() == Qt.LeftButton:
            pos = event.scenePos()
            col = int(pos.x() // CELL_SIZE)
            row = int(pos.y() // CELL_SIZE)
            if 0 <= row < self.grid.rows and 0 <= col < self.grid.cols:
                self.cell_clicked.emit(row, col)
        super().mousePressEvent(event)

    # ---------- drawing ----------
    def redraw(self):
        self.clear()
        self._robot_items.clear()
        self._robot_labels.clear()
        self._path_items = []
        self._explored_items = []
        if self.grid is None:
            return

        rows, cols = self.grid.rows, self.grid.cols
        self.setSceneRect(0, 0, cols * CELL_SIZE, rows * CELL_SIZE)
        self.setBackgroundBrush(QBrush(COLOR_BG))
        grid_pen = QPen(COLOR_GRID_LINE)

        for r in range(rows):
            for c in range(cols):
                rect = QGraphicsRectItem(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                rect.setPen(grid_pen)
                rect.setBrush(QBrush(COLOR_OBSTACLE if (r, c) in self.grid.obstacles else COLOR_BG))
                rect.setZValue(0)
                self.addItem(rect)

        if self.grid.delivery is not None:
            d = self.grid.delivery
            item = QGraphicsRectItem(d.col * CELL_SIZE + 3, d.row * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
            item.setBrush(QBrush(COLOR_DELIVERY))
            item.setPen(QPen(QColor("#065f46"), 2))
            item.setZValue(2)
            self.addItem(item)
            self._label("D", d.col, d.row, Qt.white, 10, 3, -6, -9)

        for pkg in self.grid.packages:
            if pkg.delivered:
                continue
            color = QColor(COLOR_PACKAGE.get(pkg.priority, COLOR_PACKAGE["normal"]))
            if pkg.picked:
                color.setAlpha(70)
            item = QGraphicsRectItem(pkg.col * CELL_SIZE + 7, pkg.row * CELL_SIZE + 7,
                                     CELL_SIZE - 14, CELL_SIZE - 14)
            item.setBrush(QBrush(color))
            item.setPen(QPen(QColor("#451a03")))
            item.setZValue(3)
            self.addItem(item)
            self._label(pkg.package_id, pkg.col, pkg.row, Qt.white, 7, 4, -7, -6)

        for robot in self.grid.robots:
            self._draw_robot(robot)

    def _label(self, text, col, row, color, size, z, dx, dy):
        label = QGraphicsSimpleTextItem(text)
        label.setBrush(QBrush(color))
        label.setFont(QFont("Arial", size, QFont.Bold))
        label.setPos(col * CELL_SIZE + CELL_SIZE / 2 + dx, row * CELL_SIZE + CELL_SIZE / 2 + dy)
        label.setZValue(z)
        self.addItem(label)
        return label

    def _draw_robot(self, robot):
        item = QGraphicsEllipseItem(robot.col * CELL_SIZE + 3, robot.row * CELL_SIZE + 3,
                                    CELL_SIZE - 6, CELL_SIZE - 6)
        item.setBrush(QBrush(QColor(robot.color)))
        item.setPen(QPen(QColor("#0f172a"), 2))
        item.setZValue(5)
        self.addItem(item)
        label = self._label(robot.robot_id, robot.col, robot.row, Qt.white, 8, 6, -9, -8)
        self._robot_items[robot.robot_id] = item
        self._robot_labels[robot.robot_id] = label

    def move_robot_visual(self, robot_id, row, col):
        item = self._robot_items.get(robot_id)
        label = self._robot_labels.get(robot_id)
        if item is None:
            return
        item.setRect(col * CELL_SIZE + 3, row * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6)
        if label is not None:
            label.setPos(col * CELL_SIZE + CELL_SIZE / 2 - 9, row * CELL_SIZE + CELL_SIZE / 2 - 8)

    # ---------- overlays ----------
    def clear_path_overlay(self):
        for item in self._path_items:
            self.removeItem(item)
        self._path_items = []

    def show_path_overlay(self, path, color_hex):
        color = QColor(color_hex)
        color.setAlpha(150)
        pen = QPen(color, 4)
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            line = QGraphicsLineItem(c1 * CELL_SIZE + CELL_SIZE / 2, r1 * CELL_SIZE + CELL_SIZE / 2,
                                     c2 * CELL_SIZE + CELL_SIZE / 2, r2 * CELL_SIZE + CELL_SIZE / 2)
            line.setPen(pen)
            line.setZValue(1)
            self.addItem(line)
            self._path_items.append(line)


class WarehouseView(QGraphicsView):
    key_pressed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setDragMode(QGraphicsView.NoDrag)
        self.capture_keys = False   # True while Manual Mode is active

    def keyPressEvent(self, event):
        if self.capture_keys and event.key() in MOVE_KEYS:
            self.key_pressed.emit(event.key())
            event.accept()
            return
        super().keyPressEvent(event)
