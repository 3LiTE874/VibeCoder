"""Zira's output window keeps every line until Clear."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class OutputWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        previous = os.environ.get("VIBECODER_APPDATA")
        os.environ["VIBECODER_APPDATA"] = str(Path(self._tmp.name) / "appdata")

        def restore() -> None:
            if previous is None:
                os.environ.pop("VIBECODER_APPDATA", None)
            else:
                os.environ["VIBECODER_APPDATA"] = previous

        self.addCleanup(restore)

    def test_text_is_kept_across_a_new_window_until_clear(self) -> None:
        from PyQt6.QtWidgets import QApplication

        from vibecoder.ai_panel import AiPanel
        from vibecoder.zira_memory import load_output

        app = QApplication.instance() or QApplication([])
        first = AiPanel()
        first._append_output("Zira:\nFirst answer.")
        first._append_output("Zira:\nSecond answer, still here.")
        self.assertIn("First answer.", first.response.toPlainText())
        self.assertIn("Second answer, still here.", first.response.toPlainText())
        self.assertIn("First answer.", load_output())
        first.deleteLater()

        second = AiPanel()
        held = second.response.toPlainText()
        self.assertIn("First answer.", held)
        self.assertIn("Second answer, still here.", held)
        second._clear_output()
        self.assertEqual(second.response.toPlainText(), "")
        self.assertEqual(load_output(), "")
        second.deleteLater()

        third = AiPanel()
        self.assertEqual(third.response.toPlainText(), "")
        third.deleteLater()
        del app


if __name__ == "__main__":
    unittest.main()
