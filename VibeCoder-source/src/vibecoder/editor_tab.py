"""One editor tab with file metadata."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QHBoxLayout, QWidget

from vibecoder.editor_widget import EditorWidget, OverviewRuler
from vibecoder.languages import language_for_path


class EditorTab(QWidget):
    def __init__(self, file_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._file_path: str | None = file_path
        self._modified = False
        self.editor = EditorWidget(self)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.diagnostics_changed.connect(self._sync_ruler)
        self.editor.refs_changed.connect(self._sync_ruler)
        self.editor.textChanged.connect(self._sync_source)
        self.editor.verticalScrollBar().valueChanged.connect(self._sync_viewport)
        self.ruler = OverviewRuler(self)
        self.ruler.line_chosen.connect(self._go_to_mark)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.editor, stretch=1)
        layout.addWidget(self.ruler)

        if file_path:
            self.editor.set_language(language_for_path(file_path))

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @property
    def modified(self) -> bool:
        return self._modified

    def set_file_path(self, path: str | None) -> None:
        self._file_path = path
        if path:
            self.editor.set_language(language_for_path(path))

    def mark_saved(self) -> None:
        self._modified = False

    def mark_modified(self) -> None:
        self._modified = True

    def display_name(self) -> str:
        if self._file_path:
            name = Path(self._file_path).name
        else:
            name = "Untitled"
        return f"{name}*" if self._modified else name

    def _on_text_changed(self) -> None:
        self._modified = True

    def _sync_source(self) -> None:
        self.ruler.set_source(self.editor.text())
        self._sync_viewport()

    def _sync_viewport(self, _value: int = 0) -> None:
        visible = int(self.editor.SendScintilla(self.editor.SCI_LINESONSCREEN))
        self.ruler.set_viewport(self.editor.firstVisibleLine(), max(1, visible))

    def _sync_ruler(self) -> None:
        marks = [(line, "ref") for line in self.editor.reference_lines]
        marks.extend(
            (item.line, "warning" if item.replacement_line else "error")
            for item in self.editor.diagnostics
        )
        self.ruler.set_source(self.editor.text())
        self.ruler.set_marks(max(1, self.editor.lines()), marks)
        self._sync_viewport()

    def _go_to_mark(self, line: int) -> None:
        self.editor.setCursorPosition(line, 0)
        self.editor.ensureLineVisible(line)
        self.editor.setFocus()
