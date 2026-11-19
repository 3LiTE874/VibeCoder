"""Tool allowlist, refusals, reference spans, and Zira's own job note."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class ToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_parse_known_and_refused_tools(self) -> None:
        from vibecoder.gguf_backend import _spoken_reply, bare_protocol, parse_tool

        written = parse_tool("TOOL write_file C:\\proj\\hello.py\nprint(1)\nENDTOOL")
        self.assertEqual(written["content"], "print(1)")
        replaced = parse_tool("TOOL replace_text C:\\proj\\hello.py\nold line\nENDOLD\nnew line\nENDTOOL")
        self.assertEqual(replaced["old"], "old line")
        self.assertEqual(replaced["new"], "new line")
        read = parse_tool("TOOL read_file C:\\proj\\hello.py @ 40")
        self.assertEqual(read["line"], 40)
        found = parse_tool("TOOL search_text C:\\proj :: alpha beta")
        self.assertEqual(found["query"], "alpha beta")
        self.assertEqual(parse_tool("TOOL delete_file C:\\proj\\hello.py")["name"], "delete_file")
        self.assertTrue(bare_protocol("ENDTOOL"))
        self.assertNotIn("ENDTOOL", _spoken_reply("I looked.\nENDTOOL"))

    def test_search_replace_and_refusals(self) -> None:
        from vibecoder.zira_tools import run_tool

        source = self.project / "note.py"
        source.write_text("alpha = 1\nalpha = 1\n", encoding="utf-8")
        project = str(self.project)
        found = run_tool({"name": "search_text", "query": "alpha", "path": ""}, project)
        self.assertIn("note.py", found)
        read = run_tool({"name": "read_file", "path": str(source), "line": 2}, project)
        self.assertTrue(read.startswith("2|"))
        many = run_tool(
            {"name": "replace_text", "path": str(source), "old": "alpha = 1", "new": "beta = 1"},
            project,
        )
        self.assertIn("appears 2 times", many)
        self.assertIn("alpha = 1", source.read_text(encoding="utf-8"))
        source.write_text("keep\nalpha = 1\n", encoding="utf-8")
        once = run_tool(
            {"name": "replace_text", "path": str(source), "old": "alpha = 1", "new": "beta = 2"},
            project,
        )
        self.assertIn("Replaced one match", once)
        self.assertIn("beta = 2", source.read_text(encoding="utf-8"))
        added = run_tool({"name": "append_file", "path": str(source), "content": "\n# end\n"}, project)
        self.assertIn("Added", added)
        self.assertIn("don't delete", run_tool({"name": "delete_file", "path": str(source)}, project))
        self.assertIn("don't run", run_tool({"name": "shell", "path": "cmd"}, project))
        self.assertIn("don't have a tool", run_tool({"name": "frobnicate", "path": "x"}, project))
        outside = self.project.parent / "outside-zira.txt"
        refused = run_tool(
            {"name": "write_file", "path": str(outside), "content": "nope"},
            project,
        )
        self.assertIn("open project", refused)
        self.assertFalse(outside.exists())

    def test_job_note_stays_in_her_database(self) -> None:
        from vibecoder.zira_asa import begin_turn, close_turn, note_step, unfinished_note

        appdata = self.project / "appdata"
        previous = os.environ.get("VIBECODER_APPDATA")
        os.environ["VIBECODER_APPDATA"] = str(appdata)

        def restore() -> None:
            if previous is None:
                os.environ.pop("VIBECODER_APPDATA", None)
            else:
                os.environ["VIBECODER_APPDATA"] = previous

        self.addCleanup(restore)
        self.assertEqual(unfinished_note(), "")
        job = begin_turn("color the references")
        note_step(job, "search_text alpha — note.py:1")
        close_turn(job, "blocked", "Ask to continue.")
        note = unfinished_note()
        self.assertIn("color the references", note)
        self.assertIn("Ask to continue.", note)
        chat = begin_turn("thanks")
        close_turn(chat, "done", "Finished.")
        self.assertIn("color the references", unfinished_note())
        done = begin_turn("continue the edit")
        close_turn(done, "done", "Replaced one match.", worked=True)
        self.assertEqual(unfinished_note(), "")
        self.assertTrue((appdata / "zira_memory.sqlite").is_file())

    def test_reference_hits_are_whole_words(self) -> None:
        from vibecoder.refs import reference_hits

        text = "alpha = 1\nalphabet = 2\nalpha = 3\n"
        hits = reference_hits(text, "alpha")
        self.assertEqual(len(hits), 2)
        self.assertEqual([line for _start, _size, line in hits], [0, 2])
        self.assertEqual(reference_hits(text, "a"), [])

    def test_editor_colors_repeated_names(self) -> None:
        from PyQt6.Qsci import QsciScintilla
        from PyQt6.QtWidgets import QApplication

        from vibecoder.editor_widget import EditorWidget

        app = QApplication.instance() or QApplication([])
        editor = EditorWidget()
        editor.setText("alpha = 1\nalphabet = 2\nalpha = 3\n")
        editor.setCursorPosition(0, 1)
        editor._paint_refs()
        self.assertEqual(editor.reference_lines, [0, 2])
        start = editor.positionFromLineIndex(0, 0)
        markers = int(editor.SendScintilla(QsciScintilla.SCI_INDICATORALLONFOR, start))
        self.assertTrue(markers & (1 << 22))
        editor.setText("alpha = 1\n")
        editor.setCursorPosition(0, 1)
        editor._paint_refs()
        self.assertEqual(editor.reference_lines, [])
        editor.deleteLater()


if __name__ == "__main__":
    unittest.main()
