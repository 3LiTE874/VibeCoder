"""Closable offline explanation panel."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class WikiPanel(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.heading = QLabel("Deep Wiki")
        self.heading.setStyleSheet("font-weight: bold; font-size: 13px; color: #39ff14;")

        close = QPushButton("Close")
        close.clicked.connect(self.close_requested.emit)

        header = QHBoxLayout()
        header.addWidget(self.heading, stretch=1)
        header.addWidget(close)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setPlaceholderText("Hover a known name, or highlight a block and choose Explain selection.")

        note = QLabel("Offline glossary. It does not search the internet.")
        note.setStyleSheet("color: #969696; font-size: 11px;")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(header)
        layout.addWidget(self.body, stretch=1)
        layout.addWidget(note)

    def show_explanation(self, title: str, body: str) -> None:
        self.heading.setText(title)
        self.body.setPlainText(body)
