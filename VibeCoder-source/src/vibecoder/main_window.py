"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment, QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vibecoder.ai_panel import AiPanel
from vibecoder.diagnostics import check_python
from vibecoder.editor_tab import EditorTab
from vibecoder.explorer_panel import ExplorerPanel, ExplorerTitleBar
from vibecoder.files import TextOpenError, read_editor_text
from vibecoder.session import load_session, save_session, tab_record
from vibecoder.glossary import explain, lookup
from vibecoder.languages import LANGUAGES, label_for_language
from vibecoder.listing import ListingError, format_listing
from vibecoder.output_panel import OutputPanel
from vibecoder.runner import command_for
from vibecoder.terminal_panel import TerminalPanel
from vibecoder.wiki_panel import WikiPanel

BRAND_TITLE = "LEPAGE.AI ~ CODER"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VibeCoder")
        self.resize(1100, 720)

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setMovable(True)
        self._tabs.setMinimumWidth(120)
        self._tabs.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._ai_panel = AiPanel()
        self._ai_panel.setMinimumWidth(280)
        self._ai_dock = self._dock("Zira 1.0", self._ai_panel, Qt.DockWidgetArea.RightDockWidgetArea)
        self._ai_dock.setMinimumWidth(280)

        start_folder = str(Path.cwd())
        self._explorer = ExplorerPanel(start_folder)
        self._explorer.file_activated.connect(self._open_path)
        self._explorer_dock = self._dock("Explorer", self._explorer, Qt.DockWidgetArea.LeftDockWidgetArea)
        self._explorer_title = ExplorerTitleBar(self._explorer_dock)
        self._explorer_title.open_folder.connect(self._choose_explorer_folder)
        self._explorer_title.close_requested.connect(self._close_explorer)
        self._explorer_dock.setTitleBarWidget(self._explorer_title)

        self._output = OutputPanel()
        self._output.fix_requested.connect(self._apply_correction)
        self._output_dock = self._dock("Output", self._output, Qt.DockWidgetArea.BottomDockWidgetArea)
        self._output_dock.hide()

        self._terminal = TerminalPanel()
        self._terminal.set_cwd(start_folder)
        self._ai_panel.set_project(start_folder)
        self._explorer.root_changed.connect(self._terminal.set_cwd)
        self._explorer.root_changed.connect(self._ai_panel.set_project)
        self._terminal_dock = self._dock("Terminal", self._terminal, Qt.DockWidgetArea.BottomDockWidgetArea)
        self._terminal_dock.hide()

        self._wiki = WikiPanel()
        self._wiki.close_requested.connect(self._close_wiki)
        self._wiki_dock = self._dock("Deep Wiki", self._wiki, Qt.DockWidgetArea.BottomDockWidgetArea)
        self._wiki_dock.hide()
        self.tabifyDockWidget(self._output_dock, self._terminal_dock)
        self.tabifyDockWidget(self._output_dock, self._wiki_dock)

        self._run_process = QProcess(self)
        self._run_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._run_process.readyReadStandardOutput.connect(self._read_run_output)
        self._run_process.finished.connect(self._run_finished)
        self._pending_fix: tuple[int, str] | None = None
        self._wiki_lock = False

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)
        self.setCentralWidget(container)

        self._build_menus()
        self.statusBar().showMessage("Ready")
        self._restore_session()
        self._ai_dock.show()
        self._docks_sized = False

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._docks_sized:
            return
        self._docks_sized = True
        screen = self.screen().availableGeometry() if self.screen() else None
        frame = self.frameGeometry()
        if screen is not None and (
            frame.right() > screen.right()
            or frame.bottom() > screen.bottom()
            or frame.left() < screen.left()
            or frame.top() < screen.top()
        ):
            self.move(screen.left() + 24, screen.top() + 24)
        QTimer.singleShot(0, self._size_docks)

    def _size_docks(self) -> None:
        self.resizeDocks(
            [self._explorer_dock, self._ai_dock],
            [220, 340],
            Qt.Orientation.Horizontal,
        )
        self._dock_tries = getattr(self, "_dock_tries", 0) + 1
        if self._ai_dock.width() < 240 and self._dock_tries < 8:
            QTimer.singleShot(50, self._size_docks)

    def _current_tab(self) -> EditorTab | None:
        widget = self._tabs.currentWidget()
        return widget if isinstance(widget, EditorTab) else None

    def _current_editor(self):
        tab = self._current_tab()
        return tab.editor if tab else None

    def _build_menus(self) -> None:
        shell = QWidget()
        shell.setObjectName("topChrome")
        chrome = QVBoxLayout(shell)
        chrome.setContentsMargins(0, 0, 0, 0)
        chrome.setSpacing(0)

        brand = QLabel(BRAND_TITLE)
        brand.setObjectName("brandTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chrome.addWidget(brand)

        menubar = QMenuBar(shell)
        chrome.addWidget(menubar)
        self.setMenuWidget(shell)

        # File
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._action("New", self._new_tab, QKeySequence.StandardKey.New))
        file_menu.addAction(self._action("Open…", self._open_file, QKeySequence.StandardKey.Open))
        file_menu.addAction(self._action("Open Binary…", self._open_binary))
        file_menu.addAction(self._action("Save", self._save_file, QKeySequence.StandardKey.Save))
        file_menu.addAction(self._action("Save As…", self._save_file_as, QKeySequence("Ctrl+Shift+S")))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close, QKeySequence.StandardKey.Quit))

        # Edit
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._action("Undo", self._undo, QKeySequence.StandardKey.Undo))
        edit_menu.addAction(self._action("Redo", self._redo, QKeySequence.StandardKey.Redo))
        edit_menu.addSeparator()
        edit_menu.addAction(self._action("Cut", self._cut, QKeySequence.StandardKey.Cut))
        edit_menu.addAction(self._action("Copy", self._copy, QKeySequence.StandardKey.Copy))
        edit_menu.addAction(self._action("Paste", self._paste, QKeySequence.StandardKey.Paste))
        edit_menu.addAction(self._action("Select All", self._select_all, QKeySequence.StandardKey.SelectAll))

        # Explorer
        explorer_menu = menubar.addMenu("E&xplorer")
        explorer_menu.addAction(self._action("Open Explorer", self._open_explorer, QKeySequence("Ctrl+Shift+E")))
        explorer_menu.addAction(self._action("Close Explorer", self._close_explorer))
        explorer_menu.addSeparator()
        explorer_menu.addAction(self._action("Open Folder…", self._choose_explorer_folder))

        # Run
        run_menu = menubar.addMenu("&Run")
        run_menu.addAction(self._action("Run", self._run_file, QKeySequence("F5")))
        run_menu.addAction(self._action("Stop", self._stop_run, QKeySequence("Shift+F5")))
        run_menu.addSeparator()
        run_menu.addAction(self._action("Check for errors", self._check_errors, QKeySequence("F8")))
        run_menu.addAction(self._action("Show Output", self._show_output))

        # Terminal
        terminal_menu = menubar.addMenu("&Terminal")
        terminal_menu.addAction(self._action("Open Terminal", self._open_terminal, QKeySequence("Ctrl+`")))
        terminal_menu.addAction(self._action("Close Terminal", self._close_terminal))
        terminal_menu.addSeparator()
        terminal_menu.addAction(self._action("PowerShell", lambda: self._open_shell("PowerShell")))
        terminal_menu.addAction(self._action("Command Prompt", lambda: self._open_shell("CMD")))

        # View
        view_menu = menubar.addMenu("&View")
        self._toggle_ai_action = self._action("Toggle Zira", self._toggle_ai_panel, QKeySequence("Ctrl+Shift+A"))
        self._toggle_ai_action.setCheckable(True)
        self._toggle_ai_action.setChecked(True)
        view_menu.addAction(self._toggle_ai_action)
        self._hover_wiki_action = self._action("Explain on hover", self._toggle_hover_wiki)
        self._hover_wiki_action.setCheckable(True)
        self._hover_wiki_action.setChecked(True)
        view_menu.addAction(self._hover_wiki_action)
        view_menu.addAction(self._action("Explain selection", self._explain_selection, QKeySequence("Ctrl+Shift+W")))
        view_menu.addAction(self._action("Ask Zira about this function", self._ask_zira_function))
        view_menu.addAction(self._action("Close Deep Wiki", self._close_wiki))

        # Language, grouped A–Z so the full list stays usable.
        lang_menu = menubar.addMenu("&Language")
        self._language_actions: dict[str, QAction] = {}
        grouped: dict[str, list] = {}
        for lang in LANGUAGES:
            grouped.setdefault(lang.label[0].upper(), []).append(lang)
        for letter in sorted(grouped):
            submenu = lang_menu.addMenu(letter)
            for lang in sorted(grouped[letter], key=lambda item: item.label.lower()):
                action = QAction(lang.label, self)
                action.triggered.connect(lambda checked=False, lid=lang.id: self._set_language(lid))
                submenu.addAction(action)
                self._language_actions[lang.id] = action

        # Help
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self._action("About VibeCoder", self._show_about))

    def _action(self, text: str, slot, shortcut=None) -> QAction:
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        return action

    def _new_tab(
        self,
        file_path: str | None = None,
        content: str | None = None,
        sample_python: bool = False,
        sample_markdown: bool = False,
    ) -> EditorTab:
        tab = EditorTab(file_path)

        if sample_python:
            tab.set_file_path("hello.py")
            tab.editor.set_language("python")
            tab.editor.setText(
                '# VibeCoder — Python sample\n'
                'def greet(name: str) -> str:\n'
                '    """Return a friendly greeting."""\n'
                '    return f"Hello, {name}!"\n\n'
                'if __name__ == "__main__":\n'
                '    print(greet("Christopher"))\n'
            )
            tab.mark_saved()
            self._add_tab(tab, tab.display_name())
            return tab

        if sample_markdown:
            tab.set_file_path("notes.md")
            tab.editor.set_language("markdown")
            tab.editor.setText(
                '# VibeCoder Notes\n\n'
                'A **dark** Notepad++-style editor for *Christopher LePage*.\n\n'
                '- Persistent syntax highlighting\n'
                '- Markdown for daughters and AIs\n'
                '- AI vibe coding (stub)\n\n'
                '```python\n'
                'print("code blocks work too")\n'
                '```\n'
            )
            tab.mark_saved()
            self._add_tab(tab, tab.display_name())
            return tab

        if content is not None:
            tab.editor.setText(content)
            tab.mark_saved()

        name = Path(file_path).name if file_path else "Untitled"
        self._add_tab(tab, name)
        return tab

    def _add_tab(self, tab: EditorTab, label: str) -> None:
        tab.editor.word_hovered.connect(self._on_hover_word)
        tab.editor.explain_requested.connect(self._explain_selection)
        tab.editor.check_requested.connect(self._check_errors)
        index = self._tabs.addTab(tab, label)
        self._tabs.setCurrentIndex(index)
        self._update_language_checks()

    def _close_tab(self, index: int) -> None:
        tab = self._tabs.widget(index)
        if not isinstance(tab, EditorTab):
            return
        if tab.modified:
            name = tab.display_name().rstrip("*")
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Save changes to {name}?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save and not self._save_tab(tab):
                return
        self._tabs.removeTab(index)
        if self._tabs.count() == 0:
            self._new_tab()

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if path:
            self._open_path(path)

    def _open_binary(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Binary",
            "",
            "Programs (*.exe *.dll);;All files (*.*)",
        )
        if not path:
            return
        try:
            listing = format_listing(path)
        except ListingError as exc:
            self.statusBar().showMessage(str(exc), 6000)
            return
        tab = self._new_tab(content=listing)
        tab.editor.set_language("assembly")
        tab.editor.setReadOnly(True)
        tab.mark_saved()
        self._tabs.setTabText(self._tabs.currentIndex(), f"{Path(path).name}.lst")
        self.statusBar().showMessage(f"Listed the entry function of {Path(path).name}", 5000)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._write_session()
        self._terminal.stop()
        super().closeEvent(event)

    def _write_session(self) -> None:
        tabs: list[dict] = []
        current = 0
        seen = 0
        active = self._tabs.currentIndex()
        for index in range(self._tabs.count()):
            widget = self._tabs.widget(index)
            if not isinstance(widget, EditorTab):
                continue
            line, column = widget.editor.getCursorPosition()
            record = tab_record(
                widget.file_path,
                widget.editor.text(),
                widget.modified,
                line,
                column,
            )
            if record is None:
                continue
            if index == active:
                current = seen
            seen += 1
            tabs.append(record)
        save_session(self._explorer.root_path, tabs, current)

    def _restore_session(self) -> None:
        data = load_session()
        project = str(data.get("project") or "") if data else ""
        if project and Path(project).is_dir():
            self._explorer.set_root(project)
        records = data.get("tabs") if data else None
        if not isinstance(records, list) or not records:
            if project and Path(project).is_dir():
                self._new_tab()
            else:
                self._new_tab(sample_python=True)
                self._new_tab(sample_markdown=True)
            return
        opened = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            if self._restore_tab(record):
                opened += 1
        if opened == 0:
            self._new_tab()
            return
        current = data.get("current", 0) if data else 0
        if isinstance(current, int) and 0 <= current < self._tabs.count():
            self._tabs.setCurrentIndex(current)

    def _restore_tab(self, record: dict) -> bool:
        path = record.get("path")
        stored = record.get("text")
        modified = bool(record.get("modified"))
        if isinstance(path, str) and path:
            if not Path(path).is_file():
                return False
            if not isinstance(stored, str):
                try:
                    stored = read_editor_text(path)
                    modified = False
                except TextOpenError:
                    return False
            self._open_path(path, text=stored, modified=modified, quiet=True)
        elif isinstance(stored, str) and stored.strip():
            tab = self._new_tab(content=stored)
            if modified:
                tab.mark_modified()
                self._tabs.setTabText(self._tabs.currentIndex(), tab.display_name())
        else:
            return False
        tab = self._current_tab()
        if tab is None:
            return False
        line = record.get("line", 0)
        column = record.get("index", 0)
        if isinstance(line, int) and isinstance(column, int):
            tab.editor.setCursorPosition(max(0, line), max(0, column))
        return True

    def _open_path(self, path: str, text: str | None = None, modified: bool = False, quiet: bool = False) -> EditorTab | None:
        existing = self._tab_index_for(path)
        if existing >= 0 and text is None:
            self._tabs.setCurrentIndex(existing)
            return self._tabs.widget(existing)
        if text is None:
            try:
                text = read_editor_text(path)
            except TextOpenError as exc:
                if not quiet:
                    self.statusBar().showMessage(str(exc), 5000)
                return None
        tab = self._new_tab(file_path=path, content=text)
        tab.set_file_path(path)
        if modified:
            tab.mark_modified()
        else:
            tab.mark_saved()
        self._tabs.setTabText(self._tabs.currentIndex(), tab.display_name())
        return tab

    def _tab_index_for(self, path: str) -> int:
        try:
            resolved = str(Path(path).resolve())
        except OSError:
            resolved = path
        for index in range(self._tabs.count()):
            widget = self._tabs.widget(index)
            if not isinstance(widget, EditorTab) or not widget.file_path:
                continue
            try:
                same = str(Path(widget.file_path).resolve()) == resolved
            except OSError:
                same = widget.file_path == path
            if same:
                return index
        return -1

    def _save_file(self) -> bool:
        tab = self._current_tab()
        if not tab:
            return False
        if not tab.file_path:
            return self._save_file_as()
        return self._save_tab(tab)

    def _save_file_as(self) -> bool:
        tab = self._current_tab()
        if not tab:
            return False
        path, _ = QFileDialog.getSaveFileName(self, "Save File As")
        if not path:
            return False
        tab.set_file_path(path)
        return self._save_tab(tab)

    def _save_tab(self, tab: EditorTab) -> bool:
        if not tab.file_path:
            return False
        try:
            Path(tab.file_path).write_text(tab.editor.text(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
            return False
        tab.mark_saved()
        idx = self._tabs.indexOf(tab)
        if idx >= 0:
            self._tabs.setTabText(idx, tab.display_name())
        self.statusBar().showMessage(f"Saved {tab.file_path}", 3000)
        return True

    def _set_language(self, language_id: str) -> None:
        tab = self._current_tab()
        if not tab:
            return
        before = tab.editor.text()
        tab.editor.set_language(language_id)
        after = tab.editor.text()
        assert before == after, "Language change must not wipe buffer"
        self._update_language_checks()
        label = label_for_language(language_id)
        self.statusBar().showMessage(f"Language: {label}", 3000)

    def _update_language_checks(self) -> None:
        tab = self._current_tab()
        current = tab.editor.language_id if tab else None
        for lang_id, action in self._language_actions.items():
            action.setCheckable(True)
            action.setChecked(lang_id == current)

    def _on_tab_changed(self, _index: int) -> None:
        self._update_language_checks()
        tab = self._current_tab()
        if tab:
            self.statusBar().showMessage(
                f"{tab.display_name()} — {tab.editor.language_label}"
            )

    def _toggle_ai_panel(self) -> None:
        self._ai_dock.setVisible(self._toggle_ai_action.isChecked())

    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(area, dock)
        return dock

    def _open_explorer(self) -> None:
        self._explorer_dock.show()
        self._explorer_dock.raise_()

    def _close_explorer(self) -> None:
        self._explorer_dock.hide()

    def _choose_explorer_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", self._explorer.root_path)
        if folder:
            self._explorer.set_root(folder)
            self._open_explorer()
            self.statusBar().showMessage(f"Project: {folder}", 5000)

    def _show_output(self) -> None:
        self._output_dock.show()
        self._output_dock.raise_()

    def _open_terminal(self) -> None:
        self._terminal_dock.show()
        self._terminal_dock.raise_()
        if self._terminal._process.state() == QProcess.ProcessState.NotRunning:
            self._terminal.start_shell()

    def _close_terminal(self) -> None:
        self._terminal.stop()
        self._terminal_dock.hide()

    def _open_shell(self, name: str) -> None:
        self._terminal_dock.show()
        self._terminal_dock.raise_()
        if self._terminal.shell_box.currentText() == name:
            self._terminal.start_shell(name)
        else:
            self._terminal.shell_box.setCurrentText(name)

    def _run_file(self) -> None:
        tab = self._current_tab()
        if not tab:
            return
        path = Path(tab.file_path) if tab.file_path else None
        if path is None or tab.modified or not path.is_file():
            if not self._save_file():
                return
            path = Path(tab.file_path) if tab.file_path else None
        if path is None:
            return
        argv, error = command_for(tab.editor.language_id, path)
        self._show_output()
        self._output.clear()
        if error or not argv:
            self._output.append(error or "Nothing to run.")
            return
        if self._run_process.state() != QProcess.ProcessState.NotRunning:
            self._run_process.kill()
            self._run_process.waitForFinished(1000)
        self._run_process.setWorkingDirectory(str(path.parent))
        self._run_process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self._output.append(" ".join(argv))
        self._run_process.start(argv[0], argv[1:])

    def _stop_run(self) -> None:
        if self._run_process.state() != QProcess.ProcessState.NotRunning:
            self._run_process.kill()
            self._output.append("--- stopped ---")

    def _read_run_output(self) -> None:
        data = bytes(self._run_process.readAllStandardOutput())
        text = data.decode("utf-8", errors="replace")
        if text.strip():
            self._output.append(text)

    def _run_finished(self, code: int, _status) -> None:
        self._output.append(f"--- exit {code} ---")

    def _check_errors(self) -> None:
        tab = self._current_tab()
        if not tab:
            return
        editor = tab.editor
        editor.clear_diagnostics()
        self._pending_fix = None
        self._output.set_fix_enabled(False)
        self._output.clear()
        self._show_output()
        if editor.language_id not in {"python", "qiskit"}:
            self._output.append(
                "Error spotting reads Python syntax. Other languages keep their highlighting; "
                "use the terminal for their compilers."
            )
            return
        found = check_python(editor.text())
        editor.set_diagnostics(found)
        if not found:
            self._output.append("No Python syntax errors.")
            return
        diag = found[0]
        editor.setCursorPosition(diag.line, diag.column)
        editor.ensureLineVisible(diag.line)
        self._output.append(f"Line {diag.line + 1}: {diag.message}")
        if diag.replacement_line is not None:
            self._pending_fix = (diag.line, diag.replacement_line)
            self._output.set_fix_enabled(True)
            self._output.append(f"Suggested correction: {diag.replacement_line.strip()}")

    def _apply_correction(self) -> None:
        editor = self._current_editor()
        if not editor or not self._pending_fix:
            return
        line, replacement = self._pending_fix
        editor.replace_line(line, replacement)
        self._pending_fix = None
        self._check_errors()
        self._output.append("Applied the correction.")

    def _on_hover_word(self, word: str) -> None:
        if not self._hover_wiki_action.isChecked():
            return
        note = lookup(word)
        if not note:
            return
        self._show_wiki(word, note)

    def _ask_zira_function(self) -> None:
        editor = self._current_editor()
        if editor is None:
            return
        body = editor.selected_text_value().strip() or editor.text().strip()
        if not body:
            self.statusBar().showMessage("Open a function listing first.", 4000)
            return
        if len(body) > 4000:
            body = body[:4000] + "\n…"
        self._toggle_ai_action.setChecked(True)
        self._ai_dock.show()
        self._ai_dock.raise_()
        self._ai_panel.prime(
            "Explain this function in plain English. "
            "The lines below are the decoded instructions. "
            "Do not add instructions that are not written here.\n\n"
            + body
        )
        self.statusBar().showMessage("The function is in Zira's box. Send it when you are ready.", 5000)

    def _explain_selection(self) -> None:
        editor = self._current_editor()
        if not editor:
            return
        text = editor.selected_text_value().strip() or editor.word_under_cursor()
        title, body = explain(text)
        self._show_wiki(title, body)

    def _show_wiki(self, title: str, body: str) -> None:
        self._wiki.show_explanation(title, body)
        self._wiki_lock = True
        self._wiki_dock.show()
        self._wiki_dock.raise_()
        self._wiki_lock = False

    def _close_wiki(self) -> None:
        self._hover_wiki_action.setChecked(False)
        self._wiki_dock.hide()

    def _toggle_hover_wiki(self) -> None:
        if not self._hover_wiki_action.isChecked():
            self._wiki_dock.hide()

    def _undo(self) -> None:
        editor = self._current_editor()
        if editor:
            editor.undo()

    def _redo(self) -> None:
        editor = self._current_editor()
        if editor:
            editor.redo()

    def _text_focus(self):
        """The prompt, Zira's reply, and the other panels. The code editor is separate."""
        widget = QApplication.focusWidget()
        if widget is None:
            return None
        editor = self._current_editor()
        if editor is not None and (widget is editor or editor.isAncestorOf(widget)):
            return None
        if hasattr(widget, "toPlainText") and hasattr(widget, "copy"):
            return widget
        return None

    def _cut(self) -> None:
        widget = self._text_focus()
        if widget is not None:
            widget.cut()
            return
        editor = self._current_editor()
        if editor:
            editor.cut()

    def _copy(self) -> None:
        widget = self._text_focus()
        if widget is not None:
            selected = hasattr(widget, "textCursor") and widget.textCursor().hasSelection()
            if selected:
                widget.copy()
            else:
                QApplication.clipboard().setText(widget.toPlainText())
            return
        editor = self._current_editor()
        if editor:
            editor.copy()

    def _paste(self) -> None:
        widget = self._text_focus()
        if widget is not None:
            widget.paste()
            return
        editor = self._current_editor()
        if editor:
            editor.paste()

    def _select_all(self) -> None:
        widget = self._text_focus()
        if widget is not None:
            widget.selectAll()
            return
        editor = self._current_editor()
        if editor:
            editor.selectAll()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About VibeCoder",
            "<h3>VibeCoder 0.1.0</h3>"
            "<p>Notepad++-style editor for Christopher LePage.</p>"
            "<p>Dark mode, persistent syntax highlighting, Markdown, AI vibe coding.</p>"
            "<p>Licensed under GNU GPL-3.0.</p>",
        )
