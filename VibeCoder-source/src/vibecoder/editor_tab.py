"""One editor tab with file metadata."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from vibecoder.editor_widget import EditorWidget
from vibecoder.languages import language_for_path


class EditorTab(QWidget):
    def __init__(self, file_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._file_path: str | None = file_path
        self._modified = False
        self.editor = EditorWidget(self)
        self.editor.textChanged.connect(self._on_text_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)

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
