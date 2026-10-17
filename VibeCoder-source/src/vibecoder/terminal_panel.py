"""Line-oriented PowerShell and CMD session."""

from __future__ import annotations

from PyQt6.QtCore import QProcess, QProcessEnvironment
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_SHELLS = {
    "PowerShell": ("powershell.exe", ["-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"]),
    "CMD": ("cmd.exe", ["/Q", "/K"]),
}


class TerminalPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._cwd = ""
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.errorOccurred.connect(self._on_error)
        self._history: list[str] = []
        self._history_index = 0

        self.shell_box = QComboBox()
        self.shell_box.addItems(list(_SHELLS))
        self.shell_box.currentTextChanged.connect(self.start_shell)

        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setFont(QFont("Consolas", 10))
        self.transcript.setPlaceholderText("Terminal output appears here.")

        self.command = QLineEdit()
        self.command.setPlaceholderText("Type a command and press Enter")
        self.command.returnPressed.connect(self.send_current)
        self.command.installEventFilter(self)

        send = QPushButton("Send")
        send.clicked.connect(self.send_current)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.transcript.clear)

        top = QHBoxLayout()
        top.addWidget(self.shell_box, stretch=1)
        top.addWidget(clear)

        bottom = QHBoxLayout()
        bottom.addWidget(self.command, stretch=1)
        bottom.addWidget(send)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(top)
        layout.addWidget(self.transcript, stretch=1)
        layout.addLayout(bottom)

    def eventFilter(self, obj, event):  # noqa: N802
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent

        if obj is self.command and event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent):
            key = event.key()
            if key == 16777235 and self._history:  # Up
                self._history_index = max(0, self._history_index - 1)
                self.command.setText(self._history[self._history_index])
                return True
            if key == 16777237 and self._history:  # Down
                self._history_index = min(len(self._history), self._history_index + 1)
                if self._history_index == len(self._history):
                    self.command.clear()
                else:
                    self.command.setText(self._history[self._history_index])
                return True
        return super().eventFilter(obj, event)

    def set_cwd(self, path: str) -> None:
        self._cwd = path
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self.start_shell(self.shell_box.currentText())

    def start_shell(self, name: str | None = None) -> None:
        shell_name = name or self.shell_box.currentText()
        program, args = _SHELLS[shell_name]
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1500)
        if self._cwd:
            self._process.setWorkingDirectory(self._cwd)
        self._process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self._process.start(program, args)
        if not self._process.waitForStarted(3000):
            self._append(f"Could not start {program}.")
            return
        self._append(f"--- {shell_name} ---")

    def send_current(self) -> None:
        text = self.command.text()
        self.command.clear()
        if text:
            self._history.append(text)
            self._history_index = len(self._history)
        self.send_line(text)

    def send_line(self, text: str) -> None:
        if self._process.state() == QProcess.ProcessState.NotRunning:
            self.start_shell()
        prompt = "PS>" if self.shell_box.currentText() == "PowerShell" else ">"
        self._append(f"{prompt} {text}")
        payload = (text + "\r\n").encode("utf-8")
        self._process.write(payload)

    def stop(self) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1500)
            self._append("--- stopped ---")

    def output_text(self) -> str:
        return self.transcript.toPlainText()

    def _read_output(self) -> None:
        data = bytes(self._process.readAllStandardOutput())
        self._append(_decode_console(data))

    def _on_error(self, _error) -> None:
        if self._process.state() == QProcess.ProcessState.NotRunning:
            return

    def _append(self, text: str) -> None:
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
        if not cleaned:
            return
        self.transcript.appendPlainText(cleaned)
        bar = self.transcript.verticalScrollBar()
        bar.setValue(bar.maximum())


def _decode_console(data: bytes) -> str:
    if not data:
        return ""
    if data.count(b"\x00") > max(len(data) // 4, 1):
        return data.decode("utf-16-le", errors="replace")
    return data.decode("utf-8", errors="replace")
