"""QScintilla editor widget with stable language switching."""

from __future__ import annotations

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import QEvent, QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QWidget

from vibecoder.diagnostics import Diagnostic, check_python
from vibecoder.languages import create_lexer, label_for_language
from vibecoder.themes import style_editor

_ERROR_INDICATOR = 20
_WARNING_INDICATOR = 21
_ERROR_MARKER = 8
_WARNING_MARKER = 9
_BREAKPOINT_MARKER = 10
_BREAKPOINT_MARGIN = 1
_DIAGNOSTIC_MARGIN = 2


class OverviewRuler(QWidget):
    """Minimap of the open file. Grey box tracks the scroll. Red and amber lines are problems."""

    line_chosen = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._lines: list[str] = [""]
        self._marks: list[tuple[int, str]] = []
        self._first = 0
        self._visible = 1
        self._image: QImage | None = None
        self._source = ""
        self.setFixedWidth(104)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Faint copy of the file. Grey box is what you can see. Red is an error. Amber is a warning.")

    def set_source(self, text: str) -> None:
        if text == self._source:
            return
        self._source = text
        self._lines = text.splitlines() or [""]
        self._image = None
        self.update()

    def set_viewport(self, first: int, visible: int) -> None:
        self._first = max(0, first)
        self._visible = max(1, visible)
        self.update()

    def set_marks(self, _line_count: int, marks: list[tuple[int, str]]) -> None:
        self._marks = list(marks)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        _count, line_h, used = self._layout()
        image = self._sketch()
        if image is not None and not image.isNull() and used > 0:
            painter.drawImage(QRect(0, 0, self.width(), used), image)
        top = int(self._first * line_h)
        box = max(3, int(self._visible * line_h))
        if top + box > used:
            box = max(3, used - top)
        painter.fillRect(0, top, self.width(), box, QColor(200, 200, 200, 42))
        painter.setPen(QColor(186, 186, 186, 140))
        painter.drawRect(0, top, self.width() - 1, max(1, box - 1))
        for line, kind in self._marks:
            color = QColor("#cca700") if kind == "warning" else QColor("#f14c4c")
            y = int(max(0, line) * line_h)
            painter.fillRect(0, y, self.width(), 2, color)
        painter.end()

    def _layout(self) -> tuple[int, float, int]:
        count = max(1, len(self._lines))
        height = max(1, self.height())
        natural = count * 3
        if natural <= height:
            return count, 3.0, natural
        return count, height / count, height

    def _sketch(self) -> QImage | None:
        if self._image is not None:
            return self._image
        count = max(1, len(self._lines))
        image = QImage(self.width(), max(1, count * 3), QImage.Format.Format_RGB32)
        image.fill(QColor("#1e1e1e"))
        painter = QPainter(image)
        ink = QColor("#8d8d8d")
        for index, line in enumerate(self._lines):
            y = index * 3
            x = 2
            for char in line[:48]:
                if x >= self.width() - 2:
                    break
                if not char.isspace():
                    painter.fillRect(x, y, 2, 2, ink)
                x += 3
        painter.end()
        self._image = image
        return image

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            _count, line_h, used = self._layout()
            y = event.position().y()
            if line_h > 0 and y <= used:
                line = int(y / line_h)
                self.line_chosen.emit(max(0, min(line, len(self._lines) - 1)))
        super().mousePressEvent(event)


class EditorWidget(QsciScintilla):
    """Single editor pane. Language changes never wipe buffer content."""

    word_hovered = pyqtSignal(str)
    explain_requested = pyqtSignal()
    check_requested = pyqtSignal()
    diagnostics_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language_id = "plain"
        self._hover_point = QPoint()
        self._diagnostics: list[Diagnostic] = []
        self._breakpoints: set[int] = set()
        self._dwell = QTimer(self)
        self._dwell.setSingleShot(True)
        self._dwell.setInterval(750)
        self._dwell.timeout.connect(self._emit_hover_word)
        self._check_timer = QTimer(self)
        self._check_timer.setSingleShot(True)
        self._check_timer.setInterval(350)
        self._check_timer.timeout.connect(self.recheck_diagnostics)
        self.textChanged.connect(self._check_timer.start)
        self.marginClicked.connect(self._margin_clicked)
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
        self.setMarginMarkerMask(0, 0)
        self.setMarginType(_BREAKPOINT_MARGIN, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(_BREAKPOINT_MARGIN, 16)
        self.setMarginSensitivity(_BREAKPOINT_MARGIN, True)
        self.setMarginMarkerMask(_BREAKPOINT_MARGIN, 1 << _BREAKPOINT_MARKER)
        self.setMarginType(_DIAGNOSTIC_MARGIN, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(_DIAGNOSTIC_MARGIN, 16)
        self.setMarginMarkerMask(_DIAGNOSTIC_MARGIN, (1 << _ERROR_MARKER) | (1 << _WARNING_MARKER))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(self.paper())
        self.markerDefine(_red_dot(), _ERROR_MARKER)
        self.markerDefine(_lightbulb(), _WARNING_MARKER)
        self.markerDefine(QsciScintilla.MarkerSymbol.Circle, _BREAKPOINT_MARKER)
        self.setMarkerBackgroundColor(QColor("#e51400"), _BREAKPOINT_MARKER)
        self.setMarkerForegroundColor(QColor("#e51400"), _BREAKPOINT_MARKER)
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, _ERROR_INDICATOR, QsciScintilla.INDIC_SQUIGGLE)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, _ERROR_INDICATOR, 0x00474CF1)
        self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, _WARNING_INDICATOR, QsciScintilla.INDIC_SQUIGGLE)
        self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, _WARNING_INDICATOR, 0x0000A7CC)

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
        self.recheck_diagnostics()

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

    @property
    def diagnostics(self) -> list[Diagnostic]:
        return list(self._diagnostics)

    @property
    def breakpoints(self) -> set[int]:
        return set(self._breakpoints)

    def clear_diagnostics(self) -> None:
        self._diagnostics = []
        self.markerDeleteAll(_ERROR_MARKER)
        self.markerDeleteAll(_WARNING_MARKER)
        length = self.SendScintilla(QsciScintilla.SCI_GETTEXTLENGTH)
        for indicator in (_ERROR_INDICATOR, _WARNING_INDICATOR):
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator)
            self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, length)
        self.diagnostics_changed.emit()

    def set_diagnostics(self, items: list[Diagnostic]) -> None:
        self.clear_diagnostics()
        self._diagnostics = list(items)
        for item in self._diagnostics:
            warning = item.replacement_line is not None
            self.markerAdd(item.line, _WARNING_MARKER if warning else _ERROR_MARKER)
            start = self.positionFromLineIndex(item.line, item.column)
            indicator = _WARNING_INDICATOR if warning else _ERROR_INDICATOR
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator)
            self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start, 1)
        self.diagnostics_changed.emit()

    def mark_error(self, line: int, column: int) -> None:
        self.set_diagnostics([Diagnostic(line, column, "Syntax error")])

    def recheck_diagnostics(self) -> None:
        """Refresh the track without moving the cursor or opening Output."""
        if self._language_id not in {"python", "qiskit"}:
            if self._diagnostics:
                self.set_diagnostics([])
            else:
                self.diagnostics_changed.emit()
            return
        self.set_diagnostics(check_python(self.text()))

    def toggle_breakpoint(self, line: int) -> None:
        if line < 0:
            return
        if line in self._breakpoints:
            self.markerDelete(line, _BREAKPOINT_MARKER)
            self._breakpoints.discard(line)
        else:
            self.markerAdd(line, _BREAKPOINT_MARKER)
            self._breakpoints.add(line)
        self.diagnostics_changed.emit()

    def clear_breakpoints(self) -> None:
        self.markerDeleteAll(_BREAKPOINT_MARKER)
        self._breakpoints.clear()
        self.diagnostics_changed.emit()

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

    def _margin_clicked(self, margin: int, line: int, _modifiers) -> None:
        if margin == _BREAKPOINT_MARGIN:
            self.toggle_breakpoint(line)

    def _line_from_point(self, point) -> int:
        pos = int(self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINT, int(point.x()), int(point.y())))
        if pos >= 0:
            line, _index = self.lineIndexFromPosition(pos)
            return line
        height = max(1, int(self.textHeight(0)))
        return self.firstVisibleLine() + int(point.y() // height)

    def _open_context_menu(self, point) -> None:
        line = self._line_from_point(point)
        menu = QMenu(self)
        toggle = menu.addAction("Remove Breakpoint" if line in self._breakpoints else "Add Breakpoint")
        clear = menu.addAction("Remove All Breakpoints")
        clear.setEnabled(bool(self._breakpoints))
        menu.addSeparator()
        explain = menu.addAction("Explain selection")
        check = menu.addAction("Check for errors")
        chosen = menu.exec(self.mapToGlobal(point))
        if chosen == toggle:
            self.toggle_breakpoint(line)
        elif chosen == clear:
            self.clear_breakpoints()
        elif chosen == explain:
            self.explain_requested.emit()
        elif chosen == check:
            self.check_requested.emit()


def _red_dot() -> QPixmap:
    pixmap = QPixmap(14, 14)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#f14c4c"))
    painter.drawEllipse(3, 3, 8, 8)
    painter.end()
    return pixmap


def _lightbulb() -> QPixmap:
    pixmap = QPixmap(14, 14)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#cca700"))
    painter.drawEllipse(3, 1, 8, 8)
    painter.setBrush(QColor("#d7ba7d"))
    painter.drawRect(5, 9, 4, 2)
    painter.drawRect(4, 11, 6, 2)
    painter.end()
    return pixmap
