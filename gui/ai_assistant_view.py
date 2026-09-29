from datetime import datetime

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
                               QPushButton, QScrollArea, QMessageBox, QFrame)

from ai_assistant.assistant import WarehouseAssistant


class AskWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, assistant, question):
        super().__init__()
        self.assistant = assistant
        self.question = question

    @Slot()
    def run(self):
        try:
            self.finished.emit(self.assistant.ask(self.question))
        except Exception as exc:
            self.failed.emit(str(exc))


class AIAssistantView(QWidget):
    def __init__(self, warehouse_tab, parent=None):
        super().__init__(parent)
        self.warehouse_tab = warehouse_tab
        self.assistant = WarehouseAssistant(warehouse_tab)
        self.thread = None
        self.worker = None

        root = QVBoxLayout(self)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Warehouse AI Assistant")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Ask questions about your warehouse, robots, orders and AI decisions.")
        subtitle.setStyleSheet("color: #64748b;")
        title_box.addWidget(title); title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.status = QLabel("● Online" if self.assistant.online else "● Offline")
        self.status.setStyleSheet("font-weight: bold; color: #16a34a;" if self.assistant.online else "font-weight: bold; color: #dc2626;")
        header.addWidget(self.status, 0, Qt.AlignTop)
        root.addLayout(header)

        quick = QHBoxLayout()
        for label, question in [
            ("Warehouse Status", "What is the current warehouse status?"),
            ("Robot Status", "Give me the current status of all robots."),
            ("Pending Orders", "How many orders/packages are pending?"),
            ("Inventory", "Show me the current inventory/package information."),
            ("AI Decisions", "Explain the latest AI task assignment decisions."),
            ("Simulation Statistics", "What are the current simulation statistics?"),
        ]:
            b = QPushButton(label); b.clicked.connect(lambda _=False, q=question: self.send_question(q)); quick.addWidget(b)
        root.addLayout(quick)

        self.chat = QTextEdit(); self.chat.setReadOnly(True)
        self.chat.setStyleSheet("QTextEdit { background: white; border: 1px solid #cbd5e1; padding: 10px; }")
        root.addWidget(self.chat, 1)

        bottom = QHBoxLayout()
        self.input = QLineEdit(); self.input.setPlaceholderText("Ask about your warehouse...")
        self.send = QPushButton("Send"); self.send.setObjectName("accent")
        self.clear = QPushButton("Clear Chat")
        self.stop = QPushButton("Stop")
        self.stop.setEnabled(False)
        bottom.addWidget(self.input, 1); bottom.addWidget(self.send); bottom.addWidget(self.stop); bottom.addWidget(self.clear)
        root.addLayout(bottom)

        self.input.returnPressed.connect(self.send_question)
        self.send.clicked.connect(self.send_question)
        self.clear.clicked.connect(self.clear_chat)
        self.stop.clicked.connect(self.cancel_request)
        self.append_message("assistant", "Warehouse AI Assistant is ready. Ask me about the current warehouse state or the AI algorithms.")

    def append_message(self, role, text):
        stamp = datetime.now().strftime("%H:%M:%S")
        if role == "user":
            label, align = "You", "right"
            style = "background:#dbeafe; border-radius:8px; padding:8px;"
        else:
            label, align = "Assistant", "left"
            style = "background:#f1f5f9; border-radius:8px; padding:8px;"
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self.chat.append(f'<div align="{align}"><b>{label}</b> <span style="color:#64748b;">{stamp}</span><br>'
                          f'<span style="{style}">{safe}</span></div><br>')
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    def send_question(self, question=None):
        question = (question or self.input.text()).strip()
        if not question or self.thread:
            return
        lowered = question.lower()
        if any(x in lowered for x in ("reset simulation", "reset the warehouse", "reset warehouse")):
            self.append_message("user", question)
            answer = QMessageBox.question(self, "Confirm Reset", "This will reset the current simulation state to the scenario start.\n\nDo you want to continue?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer == QMessageBox.Yes:
                self.warehouse_tab.reset_run()
                self.append_message("assistant", "The simulation has been reset to the current scenario start state.")
            else:
                self.append_message("assistant", "Reset cancelled. The current simulation state was not changed.")
            self.input.clear()
            return
        self.input.clear()
        self.append_message("user", question)
        self.send.setEnabled(False); self.stop.setEnabled(True)
        self.status.setText("● Thinking...")
        self.thread = QThread()
        self.worker = AskWorker(self.assistant, question)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup_thread)
        self.thread.start()

    def on_finished(self, answer):
        self.append_message("assistant", answer)
        self.status.setText("● Online" if self.assistant.online else "● Offline")

    def on_failed(self, message):
        self.append_message("assistant", "The AI Assistant is temporarily unavailable. The warehouse simulation is still running normally.\n\n" + message)
        self.status.setText("● Error / Offline")

    def cleanup_thread(self):
        self.send.setEnabled(True); self.stop.setEnabled(False)
        if self.thread:
            self.thread.deleteLater()
        self.worker = None; self.thread = None
        self.status.setText("● Online" if self.assistant.online else "● Offline")

    def cancel_request(self):
        if self.thread:
            self.thread.requestInterruption()
        self.stop.setEnabled(False)
        self.status.setText("● Cancelling...")

    def clear_chat(self):
        self.assistant.clear()
        self.chat.clear()
        self.append_message("assistant", "Conversation cleared. I am ready for a new warehouse question.")
