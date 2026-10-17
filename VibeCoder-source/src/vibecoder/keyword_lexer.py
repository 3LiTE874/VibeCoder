"""Keyword lexer for languages QScintilla does not ship a native lexer for."""

from __future__ import annotations

from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont

_WS = {9, 10, 13, 32}
_DIGITS = set(b"0123456789")
_IDENT_START = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_")
_IDENT_BODY = _IDENT_START | _DIGITS


class KeywordLexer(QsciLexerCustom):
    """Highlight keywords, comments, strings, numbers, and operators."""

    def __init__(
        self,
        parent,
        *,
        name: str,
        keywords: tuple[str, ...],
        line_comments: tuple[str, ...] = (),
        block_comments: tuple[tuple[str, str], ...] = (),
        case_insensitive: bool = False,
        ident_extra: str = "",
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._case_insensitive = case_insensitive
        words = (word.casefold() if case_insensitive else word for word in keywords)
        self._keywords = set(words)
        self._line_comments = tuple(sorted(line_comments, key=len, reverse=True))
        self._block_comments = tuple(sorted(block_comments, key=lambda pair: len(pair[0]), reverse=True))
        extra = ident_extra.encode("utf-8")
        self._ident_start = _IDENT_START | set(extra)
        self._ident_body = _IDENT_BODY | set(extra)
        self._styling = False

        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setDefaultFont(font)
        self.setDefaultColor(QColor("#d4d4d4"))
        self.setDefaultPaper(QColor("#1e1e1e"))

    def language(self) -> str:
        return self._name

    def description(self, style: int) -> str:
        return {
            0: "Default",
            1: "Keyword",
            2: "String",
            3: "Comment",
            4: "Number",
            5: "Operator",
        }.get(style, "")

    def styleText(self, start: int, end: int) -> None:
        if self._styling or end <= start:
            return
        editor = self.editor()
        if editor is None:
            return

        self._styling = True
        try:
            raw = editor.text().encode("utf-8")
            if start >= len(raw):
                return
            end = min(end, len(raw))
            data = raw[start:end]
            self.startStyling(start)
            index = 0
            limit = len(data)
            while index < limit:
                length, style = self._token_at(data, index)
                if length <= 0 or index + length > limit:
                    length = 1
                    style = 0
                self.setStyling(length, style)
                index += length
        finally:
            self._styling = False

    def _token_at(self, data: bytes, index: int) -> tuple[int, int]:
        for opener, closer in self._block_comments:
            if self._starts(data, index, opener):
                return self._until(data, index, closer.encode("utf-8"), len(opener)), 3

        for prefix in self._line_comments:
            if self._starts(data, index, prefix):
                return self._until_eol(data, index), 3

        byte = data[index]
        if byte in (34, 39, 96):  # " ' `
            return self._string(data, index, byte), 2

        if byte in _DIGITS or (byte == 46 and index + 1 < len(data) and data[index + 1] in _DIGITS):
            return self._number(data, index), 4

        if byte in self._ident_start:
            cursor = index + 1
            while cursor < len(data) and data[cursor] in self._ident_body:
                cursor += 1
            word = data[index:cursor].decode("utf-8", errors="ignore")
            if self._case_insensitive:
                word = word.casefold()
            return cursor - index, (1 if word in self._keywords else 0)

        if byte in _WS:
            cursor = index + 1
            while cursor < len(data) and data[cursor] in _WS:
                cursor += 1
            return cursor - index, 0

        if byte in b"()[]{}.,;:+-*/%=<>!&|^~?@\\":
            return 1, 5

        return 1, 0

    def _starts(self, data: bytes, index: int, text: str) -> bool:
        token = text.encode("utf-8")
        return data[index : index + len(token)] == token

    def _until(self, data: bytes, index: int, closer: bytes, opener_len: int) -> int:
        found = data.find(closer, index + opener_len)
        if found < 0:
            return len(data) - index
        return found + len(closer) - index

    def _until_eol(self, data: bytes, index: int) -> int:
        found = data.find(b"\n", index)
        if found < 0:
            return len(data) - index
        return found - index

    def _string(self, data: bytes, index: int, quote: int) -> int:
        cursor = index + 1
        while cursor < len(data):
            current = data[cursor]
            if current == 10:
                return cursor - index
            if current == 92 and cursor + 1 < len(data):
                cursor += 2
                continue
            cursor += 1
            if current == quote:
                return cursor - index
        return len(data) - index

    def _number(self, data: bytes, index: int) -> int:
        cursor = index + 1
        while cursor < len(data) and data[cursor] in _DIGITS | {46, 95, 120, 88, 98, 66, 97, 102, 65, 70}:
            cursor += 1
        return cursor - index
