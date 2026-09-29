"""Knowledge Base tab: query the Prolog (or fallback) warehouse rules."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit
from prolog.prolog_interface import PrologInterface


class KnowledgeBaseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.prolog = PrologInterface()
        layout = QVBoxLayout(self)
        self.status_label = QLabel(self.prolog.status_message())
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        facts = QLabel("Facts: robot(r1..r3); package_type(p1=fragile, p2=heavy, p3=normal); can_carry/2; "
                       "priority(p1=high, p2=normal, p3=low). Rules: valid_assignment/2, high_priority_package/1, "
                       "robots_for_package/2, packages_for_robot/2. The AI planner schedules 'high' priority "
                       "packages first, mirroring high_priority_package/1.")
        facts.setWordWrap(True)
        layout.addWidget(facts)
        row = QHBoxLayout()
        self.queries = [
            ("Which robots can carry P1 (fragile)?", lambda p: ("robots_for_package(p1, R)", p.robots_for_package("p1"))),
            ("Which robots can carry P2 (heavy)?", lambda p: ("robots_for_package(p2, R)", p.robots_for_package("p2"))),
            ("Which robots can carry P3 (normal)?", lambda p: ("robots_for_package(p3, R)", p.robots_for_package("p3"))),
            ("Which packages can R1 carry?", lambda p: ("packages_for_robot(r1, P)", p.packages_for_robot("r1"))),
            ("Which packages can R2 carry?", lambda p: ("packages_for_robot(r2, P)", p.packages_for_robot("r2"))),
            ("Which packages can R3 carry?", lambda p: ("packages_for_robot(r3, P)", p.packages_for_robot("r3"))),
            ("Which packages are high priority?", lambda p: ("high_priority_package(P)", p.high_priority_packages())),
            ("Is R1 allowed to carry P2?", lambda p: ("valid_assignment(r1, p2)", p.is_valid_assignment("r1", "p2"))),
            ("Is R2 allowed to carry P2?", lambda p: ("valid_assignment(r2, p2)", p.is_valid_assignment("r2", "p2"))),
        ]
        self.combo = QComboBox()
        self.combo.addItems([q[0] for q in self.queries])
        self.run_btn = QPushButton("Run Query")
        self.run_btn.setObjectName("accent")
        row.addWidget(self.combo, 1)
        row.addWidget(self.run_btn)
        layout.addLayout(row)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.output)
        self.run_btn.clicked.connect(self.run_query)

    def run_query(self):
        goal, result = self.queries[self.combo.currentIndex()][1](self.prolog)
        self.output.append(f"?- {goal}.\n   => {result}\n")
