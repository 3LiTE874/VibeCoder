"""Whole-word references for the name under the caret.

Scintilla positions are UTF-8 bytes when the editor is in UTF-8 mode,
so the spans below are byte offsets into the same encoding.
"""

from __future__ import annotations

import re

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


def reference_hits(text: str, word: str) -> list[tuple[int, int, int]]:
    """Return (byte_start, byte_length, zero_based_line) for every whole-word hit."""
    if not word or _IDENT.fullmatch(word) is None:
        return []
    raw = text.encode("utf-8")
    needle = word.encode("ascii")
    pattern = re.compile(rb"(?<![A-Za-z0-9_])" + re.escape(needle) + rb"(?![A-Za-z0-9_])")
    line_starts = [0]
    for index, byte in enumerate(raw):
        if byte == 10:
            line_starts.append(index + 1)

    def line_of(pos: int) -> int:
        lo = 0
        hi = len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo

    return [
        (match.start(), match.end() - match.start(), line_of(match.start()))
        for match in pattern.finditer(raw)
    ]
