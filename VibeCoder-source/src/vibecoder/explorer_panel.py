"""Folder tree that opens files already on disk."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QTreeView, QVBoxLayout, QWidget


class ExplorerTitleBar(QWidget):
    """Explorer label and Open Folder on one line above the folder tree."""

    open_folder = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("explorerTitle")
        self.setStyleSheet(
            "QWidget#explorerTitle { background-color: #2d2d30; }"
            "QLabel#explorerTitleName { background: transparent; color: #d4d4d4; font-weight: 600; }"
        )

        name = QLabel("Explorer")
        name.setObjectName("explorerTitleName")

        self.open_button = QPushButton("Open Folder")
        self.open_button.setStyleSheet(
            "background-color: #0e639c; color: #ffffff; border: none; "
            "padding: 2px 10px; font-size: 11px;"
        )
        self.open_button.clicked.connect(self.open_folder.emit)

        close = QPushButton("×")
        close.setFixedSize(22, 22)
        close.setStyleSheet(
            "background-color: transparent; color: #d4d4d4; border: none; font-size: 14px;"
        )
        close.clicked.connect(self.close_requested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 4, 2)
        layout.setSpacing(8)
        layout.addWidget(name)
        layout.addStretch(1)
        layout.addWidget(self.open_button)
        layout.addWidget(close)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        event.ignore()

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        event.ignore()


class ExplorerPanel(QWidget):
    file_activated = pyqtSignal(str)
    root_changed = pyqtSignal(str)

    def __init__(self, root: str, parent=None) -> None:
        super().__init__(parent)
        self._model = QFileSystemModel(self)
        self._model.setRootPath(root)

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        for column in range(1, 4):
            self._tree.hideColumn(column)
        self._tree.setRootIndex(self._model.index(root))
        self._tree.doubleClicked.connect(self._activate)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        self._model.directoryLoaded.connect(self._show_root_when_ready)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)
        self._root = root

    @property
    def root_path(self) -> str:
        return self._root

    def set_root(self, path: str) -> None:
        folder = str(Path(path))
        self._root = folder
        self._model.setRootPath(folder)
        self._tree.setRootIndex(self._model.index(folder))
        self.root_changed.emit(folder)

    def _show_root_when_ready(self, loaded: str) -> None:
        if Path(loaded) == Path(self._root):
            self._tree.setRootIndex(self._model.index(self._root))

    def _context_menu(self, pos) -> None:
        index = self._tree.indexAt(pos)
        if not index.isValid() or self._model.isDir(index):
            return
        path = self._model.filePath(index)
        if not path:
            return
        menu = QMenu(self)
        action = menu.addAction("Open")
        action.triggered.connect(lambda checked=False, file_path=path: self.file_activated.emit(file_path))
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _activate(self, index: QModelIndex) -> None:
        path = self._model.filePath(index)
        if not path or self._model.isDir(index):
            return
        self.file_activated.emit(path)
