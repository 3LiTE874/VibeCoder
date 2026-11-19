"""AI sidebar. Suggestions stay in this panel and never touch the editor."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vibecoder.gguf_backend import GgufError, generate, validate_gguf
from vibecoder.zira_memory import choose_database_folder, database_path
from vibecoder.zira_tools import allowed_project

_SETTINGS_KEY = "gguf/model_path"
_MODE_KEY = "ai/connection"
_OFFLINE = "offline"
_ONLINE = "online"


class _GenerateThread(QThread):
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, path: str, prompt: str, project: str, online: bool) -> None:
        super().__init__()
        self._path = path
        self._prompt = prompt
        self._project = project
        self._online = online

    def run(self) -> None:
        try:
            self.succeeded.emit(generate(self._path, self._prompt, self._project, online=self._online))
        except Exception as exc:
            self.failed.emit(str(exc))


class _SendButton(QPushButton):
    """Right-pointing arrow inside a circle."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#5a5a5a")
        if self.isEnabled() and self.underMouse():
            color = QColor("#39ff14")
        elif self.isEnabled():
            color = QColor("#d4d4d4")
        pen = QPen(color)
        pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(2, 2, 23, 23)
        painter.drawLine(8, 14, 18, 14)
        painter.drawLine(14, 9, 19, 14)
        painter.drawLine(14, 19, 19, 14)
        painter.end()


class _PromptBox(QPlainTextEdit):
    submit = pyqtSignal()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if enter and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submit.emit()
            return
        super().keyPressEvent(event)


class AiPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("aiPanel")
        self._model_path = ""
        self._project = ""
        self._worker: _GenerateThread | None = None
        saved_mode = QSettings().value(_MODE_KEY, _OFFLINE, type=str)
        self._mode = _ONLINE if saved_mode == _ONLINE else _OFFLINE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("Zira 1.0")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.add_model_btn = QPushButton("Get Model")
        self.add_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_model_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.add_model_btn.setStyleSheet(
            "QPushButton { font-size: 10px; padding: 1px 8px; min-height: 16px; "
            "background-color: #0e639c; color: #ffffff; border: none; }"
            "QPushButton:hover { background-color: #1177bb; }"
        )
        self.add_model_btn.clicked.connect(self._add_model)
        header.addWidget(title)
        header.addWidget(self.add_model_btn)
        header.addStretch(1)
        layout.addLayout(header)

        hint = QLabel(
            "She can look through the open project, Desktop, Downloads, and Documents, and search them. "
            "She creates and edits files only in the open project. If she cannot do something, she says so."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #969696; font-size: 11px;")
        layout.addWidget(hint)

        self.mode_btn = QPushButton()
        self.mode_btn.clicked.connect(self._toggle_mode)
        layout.addWidget(self.mode_btn)
        self._paint_mode()

        self.db_label = QLabel()
        self.db_label.setWordWrap(True)
        self.db_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.db_label.setStyleSheet("color: #969696; font-size: 10px;")
        layout.addWidget(self.db_label)
        self.db_btn = QPushButton("Choose backup folder")
        self.db_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.db_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 1px 8px; min-height: 16px; }")
        self.db_btn.clicked.connect(self._choose_database)
        layout.addWidget(self.db_btn)
        self._show_database()

        self.response = QTextEdit()
        self.response.setReadOnly(True)
        self.response.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.response.setPlaceholderText("Zira's replies appear here.")
        layout.addWidget(self.response, stretch=1)

        self.copy_btn = QPushButton("Copy reply")
        self.copy_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.copy_btn.setStyleSheet(
            "QPushButton { font-size: 10px; padding: 1px 8px; min-height: 16px; }"
        )
        self.copy_btn.clicked.connect(self._copy_reply)
        copy_row = QHBoxLayout()
        copy_row.addStretch(1)
        copy_row.addWidget(self.copy_btn)
        layout.addLayout(copy_row)

        self.model_note = QLabel("No GGUF model loaded")
        self.model_note.setWordWrap(True)
        self.model_note.setStyleSheet("color: #6a9955; font-size: 10px;")
        self.model_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.model_note)

        self.prompt = _PromptBox()
        self.prompt.setPlaceholderText("Message Zira…")
        self.prompt.setFixedHeight(52)
        self.prompt.setMinimumWidth(220)
        self.prompt.submit.connect(self._on_generate)
        self.send_btn = _SendButton()
        self.send_btn.clicked.connect(self._on_generate)
        composer = QHBoxLayout()
        composer.setSpacing(8)
        composer.addWidget(self.prompt, stretch=1)
        composer.addWidget(self.send_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(composer)

        saved = QSettings().value(_SETTINGS_KEY, "", type=str)
        if saved:
            self._remember_model(saved, quiet=True)
        else:
            self._show_model_note()

    def _toggle_mode(self) -> None:
        self._mode = _ONLINE if self._mode == _OFFLINE else _OFFLINE
        QSettings().setValue(_MODE_KEY, self._mode)
        self._paint_mode()
        self._show_model_note()
        if self._mode == _OFFLINE:
            self.response.setPlainText(
                "OFFLINE. Nothing is sent off this PC. Her notes stay in the database file below."
            )
        else:
            self.response.setPlainText(
                "ONLINE. She still answers from the model on this PC. "
                "She may read one public web page when a reference is not in your PDFs, and that note is saved in the database file below. "
                "The open file is not uploaded."
            )

    def _paint_mode(self) -> None:
        if self._mode == _OFFLINE:
            self.mode_btn.setText("OFFLINE")
            self.mode_btn.setStyleSheet(
                "background-color: #3c1414; color: #ff4d4d; font-weight: 700; "
                "font-size: 14px; padding: 8px 14px; border: 1px solid #ff4d4d;"
            )
        else:
            self.mode_btn.setText("ONLINE")
            self.mode_btn.setStyleSheet(
                "background-color: #17361c; color: #39ff14; font-weight: 700; "
                "font-size: 14px; padding: 8px 14px; border: 1px solid #39ff14;"
            )

    def _add_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Get Model",
            _dialog_start(),
            "GGUF model (*.gguf)",
        )
        if path:
            self._remember_model(path, quiet=False)

    def _remember_model(self, path: str, quiet: bool) -> None:
        try:
            file_path = validate_gguf(path)
        except GgufError as exc:
            self._model_path = ""
            self._show_model_note()
            if not quiet:
                self.response.setPlainText(str(exc))
            return
        self._model_path = str(file_path)
        QSettings().setValue(_SETTINGS_KEY, self._model_path)
        self._show_model_note()
        if not quiet:
            self.response.setPlainText(f"Loaded {file_path.name}. Ask for a suggestion when you are ready.")

    def _on_generate(self) -> None:
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            self.response.setPlainText("Enter a prompt first.")
            return
        if not self._model_path:
            self.response.setPlainText("Use Get Model and choose a .gguf file first.")
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self.send_btn.setEnabled(False)
        self.prompt.setEnabled(False)
        self.add_model_btn.setEnabled(False)
        self.mode_btn.setEnabled(False)
        self.model_note.setText("Zira is working…")
        self._worker = _GenerateThread(self._model_path, prompt, self._project, self._mode == _ONLINE)
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, text: str) -> None:
        self.response.setPlainText(text or "The model returned an empty reply.")
        self._restore_buttons()

    def _on_failure(self, message: str) -> None:
        self.response.setPlainText(message)
        self._restore_buttons()

    def _restore_buttons(self) -> None:
        self.send_btn.setEnabled(True)
        self.prompt.setEnabled(True)
        self.add_model_btn.setEnabled(True)
        self.mode_btn.setEnabled(True)
        self._show_model_note()

    def _copy_reply(self) -> None:
        text = self.response.toPlainText()
        if not text.strip():
            return
        QGuiApplication.clipboard().setText(text)
        self.model_note.setText("Reply copied.")

    def _choose_database(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Zira's backup folder", str(database_path().parent))
        if not folder:
            return
        path = choose_database_folder(folder)
        self._show_database()
        self.response.setPlainText(
            "Her database is now this file. Copy it when you move to another computer:\n" + str(path)
        )

    def _show_database(self) -> None:
        self.db_label.setText("Database:\n" + str(database_path()))

    def prime(self, text: str) -> None:
        """Put a prompt in the box. The person still chooses when to send it."""
        self.prompt.setPlainText(text)
        self.prompt.setFocus()

    def set_project(self, path: str) -> None:
        self._project = allowed_project(path)

    def _show_model_note(self) -> None:
        mode = "OFFLINE" if self._mode == _OFFLINE else "ONLINE"
        if self._model_path:
            self.model_note.setText(f"{mode} · GGUF: {Path(self._model_path).name}")
        else:
            self.model_note.setText(f"{mode} · No GGUF model loaded")


def _dialog_start() -> str:
    desktop = Path.home() / "Desktop"
    if desktop.is_dir():
        return str(desktop)
    return str(Path.home())
