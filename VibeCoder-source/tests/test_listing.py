"""Entry-function listings from a tiny PE file. Capstone decodes the bytes."""

from __future__ import annotations

import os
import struct
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _pe(code: bytes, machine: int = 0x8664) -> bytes:
    optional_size = 32
    e_lfanew = 0x40
    section = e_lfanew + 24 + optional_size
    raw = section + 40
    blob = bytearray(raw + len(code))
    blob[0:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3C, e_lfanew)
    struct.pack_into("<I", blob, e_lfanew, 0x00004550)
    struct.pack_into("<HH", blob, e_lfanew + 4, machine, 1)
    struct.pack_into("<H", blob, e_lfanew + 20, optional_size)
    optional = e_lfanew + 24
    struct.pack_into("<I", blob, optional + 16, 0x1000)
    if machine == 0x8664:
        struct.pack_into("<H", blob, optional, 0x20B)
        struct.pack_into("<Q", blob, optional + 24, 0x140000000)
    else:
        struct.pack_into("<H", blob, optional, 0x10B)
        struct.pack_into("<I", blob, optional + 28, 0x400000)
    struct.pack_into("<8sIIII", blob, section, b".text\0\0\0", len(code), 0x1000, len(code), raw)
    struct.pack_into("<I", blob, section + 36, 0x60000020)
    blob[raw:] = code
    return bytes(blob)


class ListingTests(unittest.TestCase):
    def test_entry_function_stops_at_return(self) -> None:
        from vibecoder.listing import format_listing

        code = bytes([0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3, 0x90])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.exe"
            path.write_bytes(_pe(code))
            text = format_listing(str(path))
        self.assertIn("mov", text)
        self.assertIn("ret", text)
        self.assertNotIn("nop", text)
        self.assertIn("Stopped at the return.", text)
        self.assertIn("0x140001000", text)

    def test_long_function_stops_at_the_cap(self) -> None:
        from vibecoder.listing import list_entry

        listing = list_entry(_pe(bytes([0x90]) * 80), "long.exe")
        self.assertEqual(len(listing.instructions), 48)
        self.assertIn("48", listing.stopped)

    def test_rejects_a_text_file(self) -> None:
        from vibecoder.listing import ListingError, format_listing

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "notes.txt"
            path.write_text("hello", encoding="utf-8")
            with self.assertRaises(ListingError):
                format_listing(str(path))

    def test_listing_can_sit_in_the_editor_and_zira_box(self) -> None:
        from PyQt6.QtWidgets import QApplication

        from vibecoder.ai_panel import AiPanel
        from vibecoder.editor_widget import EditorWidget
        from vibecoder.listing import format_listing

        code = bytes([0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.exe"
            path.write_bytes(_pe(code))
            text = format_listing(str(path))
        app = QApplication.instance() or QApplication([])
        editor = EditorWidget()
        editor.set_language("assembly")
        editor.setText(text)
        editor.setReadOnly(True)
        self.assertTrue(editor.isReadOnly())
        self.assertIn("ret", editor.text())
        self.assertEqual(editor.language_id, "assembly")
        panel = AiPanel()
        panel.prime("Explain this function in plain English.\n\n" + text)
        self.assertIn("ret", panel.prompt.toPlainText())
        editor.deleteLater()
        panel.deleteLater()
        del app


if __name__ == "__main__":
    unittest.main()
