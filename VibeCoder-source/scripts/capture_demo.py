"""Capture a demo screenshot of VibeCoder for documentation."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from vibecoder.app import main as _unused  # noqa: F401
from vibecoder.main_window import MainWindow
from vibecoder.themes import apply_app_dark_theme


def capture(output: Path) -> int:
    app = QApplication(sys.argv)
    apply_app_dark_theme(app)
    window = MainWindow()
    window.show()
    window._tabs.setCurrentIndex(0)  # hello.py with Python highlighting

    def save_shot() -> None:
        pixmap = window.grab()
        output.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(output))
        app.quit()

    QTimer.singleShot(800, save_shot)
    return app.exec()


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo.png")
    raise SystemExit(capture(out))
