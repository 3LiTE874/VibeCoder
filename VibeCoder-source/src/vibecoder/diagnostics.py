"""Local syntax checks and the few corrections that are safe to apply."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    line: int
    column: int
    message: str
    replacement_line: str | None = None


_COLON_STARTS = (
    "def ",
    "class ",
    "if ",
    "elif ",
    "else",
    "for ",
    "while ",
    "try",
    "except",
    "finally",
    "with ",
    "async def ",
    "match ",
    "case ",
)


def check_python(source: str) -> list[Diagnostic]:
    """Return Python syntax errors. Line and column are 0-based."""
    try:
        compile(source, "<vibe>", "exec")
    except SyntaxError as exc:
        line = max((exc.lineno or 1) - 1, 0)
        column = max((exc.offset or 1) - 1, 0)
        message = exc.msg or "Syntax error"
        lines = source.splitlines()
        replacement = None
        if 0 <= line < len(lines):
            replacement = _colon_fix(lines[line], message)
        return [Diagnostic(line, column, message, replacement)]
    except ValueError as exc:
        return [Diagnostic(0, 0, str(exc), None)]
    return []


def _colon_fix(line_text: str, message: str) -> str | None:
    """Append a missing colon when the parser asked for one on a block header."""
    if "expected ':'" not in message and 'expected ":"' not in message:
        return None
    stripped = line_text.rstrip()
    if not stripped or stripped.endswith(":"):
        return None
    body = stripped.lstrip()
    if not any(body.startswith(prefix) or body == prefix.strip() for prefix in _COLON_STARTS):
        return None
    return stripped + ":"
