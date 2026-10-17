"""QScintilla editor widget with stable language switching."""

from __future__ import annotations

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMenu

from vibecoder.languages import create_lexer, label_for_language
from vibecoder.themes import style_editor

_ERROR_INDICATOR = 20
_ERROR_MARKER = 8


class EditorWidget(QsciScintilla):
    """Single editor pane. Language changes never wipe buffer content."""

    word_hovered = pyqtSignal(str)
    explain_requested = pyqtSignal()
    check_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language_id = "plain"
        self._hover_point = QPoint()
        self._dwell = QTimer(self)
        self._dwell.setSingleShot(True)
        self._dwell.setInterval(750)
        self._dwell.timeout.connect(self._emit_hover_word)
        style_editor(self)
        self._configure_editor()
        self.set_language("plain")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        self.viewport().installEventFilter(self)
        self.installEventFilter(self)

    def _configure_editor(self) -> None:
        self.setUtf8(True)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "00000")
        self.setMarginLineNumbers(0, True)
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(self.paper())
        self.markerDefine(QsciScintilla.MarkerSymbol.RightArrow, _ERROR_MARKER)
        self.setMarkerBackgroundColor(QColor("#f44747"), _ERROR_MARKER)
        self.setMarkerForegroundColor(QColor("#f44747"), _ERROR_MARKER)
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, _ERROR_INDICATOR, QsciScintilla.INDIC_SQUIGGLE)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, _ERROR_INDICATOR, 0x004747F4)

    @property
    def language_id(self) -> str:
        return self._language_id

    @property
    def language_label(self) -> str:
        return label_for_language(self._language_id)

    def set_language(self, language_id: str) -> None:
        """Switch lexer without modifying editor text or cursor position."""
        if language_id == self._language_id and self.lexer() is not None:
            return

        text = self.text()
        line, index = self.getCursorPosition()
        first_visible = self.firstVisibleLine()

        self._language_id = language_id
        lexer = create_lexer(language_id, self)
        self.setLexer(lexer)
        style_editor(self)

        if self.text() != text:
            self.setText(text)

        self.setCursorPosition(line, index)
        self.setFirstVisibleLine(first_visible)

    def replace_text(self, new_text: str) -> None:
        """Replace buffer content while preserving lexer and theme."""
        language_id = self._language_id
        self.setText(new_text)
        self.set_language(language_id)

    def selected_text_value(self) -> str:
        return self.selectedText().replace("\r\n", "\n").replace("\r", "\n")

    def word_under_cursor(self) -> str:
        line, index = self.getCursorPosition()
        return self._word_at(self.positionFromLineIndex(line, index))

    def clear_diagnostics(self) -> None:
        self.markerDeleteAll(_ERROR_MARKER)
        length = self.SendScintilla(QsciScintilla.SCI_GETTEXTLENGTH)
        self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, _ERROR_INDICATOR)
        self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, length)

    def mark_error(self, line: int, column: int) -> None:
        self.clear_diagnostics()
        self.markerAdd(line, _ERROR_MARKER)
        start = self.positionFromLineIndex(line, column)
        self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, _ERROR_INDICATOR)
        self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start, 1)

    def replace_line(self, line: int, new_text: str) -> None:
        current = self.text(line)
        width = len(current.replace("\r", "").replace("\n", ""))
        self.setSelection(line, 0, line, width)
        self.replaceSelectedText(new_text)

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() == QEvent.Type.MouseMove and obj is self.viewport():
            point = event.position().toPoint() if hasattr(event, "position") else event.pos()
            self._hover_point = point
            self._dwell.start()
        return super().eventFilter(obj, event)

    def _emit_hover_word(self) -> None:
        if self.selected_text_value().strip():
            return
        pos = self.SendScintilla(
            QsciScintilla.SCI_POSITIONFROMPOINTCLOSE,
            self._hover_point.x(),
            self._hover_point.y(),
        )
        if pos < 0:
            return
        word = self._word_at(pos)
        if word:
            self.word_hovered.emit(word)

    def _word_at(self, pos: int) -> str:
        if pos < 0:
            return ""
        start = self.SendScintilla(QsciScintilla.SCI_WORDSTARTPOSITION, pos, True)
        end = self.SendScintilla(QsciScintilla.SCI_WORDENDPOSITION, pos, True)
        if end <= start:
            return ""
        raw = self.text().encode("utf-8")
        return raw[start:end].decode("utf-8", errors="ignore").strip()

    def _open_context_menu(self, point) -> None:
        menu = QMenu(self)
        explain = menu.addAction("Explain selection")
        check = menu.addAction("Check for errors")
        chosen = menu.exec(self.mapToGlobal(point))
        if chosen == explain:
            self.explain_requested.emit()
        elif chosen == check:
            self.check_requested.emit()
