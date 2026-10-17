"""Run and diagnostic transcript."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class OutputPanel(QWidget):
    fix_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setFont(QFont("Consolas", 10))
        self.transcript.setPlaceholderText("Run and error output appears here.")

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.transcript.clear)
        self.fix_button = QPushButton("Apply correction")
        self.fix_button.setEnabled(False)
        self.fix_button.clicked.connect(self.fix_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.fix_button)
        buttons.addStretch(1)
        buttons.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.transcript)
        layout.addLayout(buttons)

    def clear(self) -> None:
        self.transcript.clear()

    def append(self, text: str) -> None:
        self.transcript.appendPlainText(text.rstrip("\n"))
        self.transcript.verticalScrollBar().setValue(self.transcript.verticalScrollBar().maximum())

    def set_fix_enabled(self, enabled: bool) -> None:
        self.fix_button.setEnabled(enabled)
