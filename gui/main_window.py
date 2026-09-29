from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QTabWidget, QLabel

from gui.warehouse_tab import WarehouseTab
from gui.knowledge_tab import KnowledgeBaseTab
from gui.results_tab import ResultsTab
from gui.ai_assistant_view import AIAssistantView
from gui.dialogs import show_about


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Warehouse Simulator")
        self.resize(1320, 860)

        self.tabs = QTabWidget()

        self.warehouse_tab = WarehouseTab()
        self.knowledge_tab = KnowledgeBaseTab()
        self.results_tab = ResultsTab()
        self.ai_assistant_tab = AIAssistantView(self.warehouse_tab)

        self.tabs.addTab(self.warehouse_tab, "Warehouse")
        self.tabs.addTab(self.knowledge_tab, "Knowledge Base")
        self.tabs.addTab(self.results_tab, "Results")
        self.tabs.addTab(self.ai_assistant_tab, "AI Assistant")

        self.setCentralWidget(self.tabs)

        self.status_label = QLabel(
            "Ready. Tip: use 'Auto-Populate' then 'Generate Obstacles', or click the grid."
        )
        self.statusBar().addWidget(self.status_label, 1)

        self.warehouse_tab.status_message.connect(
            self.status_label.setText
        )

        self.warehouse_tab.run_completed.connect(
            self.results_tab.append_entry
        )

        menu = self.menuBar().addMenu("&File")

        save_a = QAction("Save Scenario...", self)
        save_a.triggered.connect(
            self.warehouse_tab.save_scenario
        )

        load_a = QAction("Load Scenario...", self)
        load_a.triggered.connect(
            self.warehouse_tab.load_scenario
        )

        quit_a = QAction("Exit", self)
        quit_a.triggered.connect(self.close)

        menu.addAction(save_a)
        menu.addAction(load_a)
        menu.addSeparator()
        menu.addAction(quit_a)

        help_menu = self.menuBar().addMenu("&Help")

        about = QAction("About", self)
        about.triggered.connect(
            lambda: show_about(self)
        )

        help_menu.addAction(about)