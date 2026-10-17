"""VibeCoder application entry point."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from vibecoder.main_window import MainWindow
from vibecoder.themes import apply_app_dark_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("VibeCoder")
    app.setOrganizationName("VibeCoder")
    apply_app_dark_theme(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
