"""HTML color literals and the live swatches in the editor."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class ColorPreviewTests(unittest.TestCase):
    def test_literals(self) -> None:
        from vibecoder.color_preview import find_colors, recolor

        text = "a { color: #f00; background: #ff000080; border: rgb(0, 128, 0); outline: hsl(0, 100%, 50%); }"
        marks = find_colors(text)
        self.assertEqual([mark.kind for mark in marks], ["hex3", "hex8", "rgb", "hsl"])
        self.assertEqual((marks[0].red, marks[0].green, marks[0].blue), (255, 0, 0))
        self.assertEqual((marks[1].red, marks[1].alpha), (255, 0x80))
        self.assertEqual((marks[2].red, marks[2].green, marks[2].blue), (0, 128, 0))
        self.assertEqual((marks[3].red, marks[3].green, marks[3].blue), (255, 0, 0))
        self.assertEqual(recolor(marks[0], 0, 255, 0, 255), "#0f0")
        self.assertEqual(recolor(marks[2], 1, 2, 3, 255), "rgb(1, 2, 3)")
        named = find_colors("<p style='color: red'>redirect</p>", named=True)
        self.assertEqual([mark.text for mark in named], ["red"])

    def test_swatch_follows_the_color_and_a_pick_rewrites_it(self) -> None:
        from PyQt6.Qsci import QsciScintilla
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QApplication

        from vibecoder.editor_widget import EditorWidget

        app = QApplication.instance() or QApplication([])
        editor = EditorWidget()
        editor.resize(480, 240)
        editor.set_language("css")
        editor.setText("color: #ff0000;\n")
        editor._sync_color_preview()
        self.assertEqual((editor._color_marks[0].red, editor._color_marks[0].green), (255, 0))
        pos = editor._color_marks[0].start
        bits = int(editor.SendScintilla(QsciScintilla.SCI_INDICATORALLONFOR, pos))
        self.assertTrue(bits)
        editor._apply_color(editor._color_marks[0], QColor(0, 0, 255))
        editor._sync_color_preview()
        self.assertIn("#0000ff", editor.text())
        self.assertEqual(editor._color_marks[0].blue, 255)
        editor.setText("color: #00ff00;\n")
        editor._sync_color_preview()
        self.assertEqual(editor._color_marks[0].green, 255)
        editor.deleteLater()
        del app


if __name__ == "__main__":
    unittest.main()
