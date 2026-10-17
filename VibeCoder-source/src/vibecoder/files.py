"""Decide which files the editor can show."""

from __future__ import annotations

from pathlib import Path

_MAX_BYTES = 2_000_000

# Binary and archive types. Opening these in the text editor crashes or shows garbage.
_BINARY_SUFFIXES = frozenset(
    {
        ".pyc",
        ".pyo",
        ".pyd",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".zip",
        ".7z",
        ".rar",
        ".gz",
        ".tgz",
        ".tar",
        ".bz2",
        ".xz",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".bmp",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".mp3",
        ".mp4",
        ".wav",
        ".ogg",
        ".avi",
        ".mkv",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".bin",
        ".obj",
        ".o",
        ".a",
        ".lib",
        ".class",
        ".jar",
        ".gguf",
        ".onnx",
        ".pt",
        ".pth",
        ".safetensors",
        ".sqlite",
        ".db",
        ".whl",
        ".egg",
    }
)


class TextOpenError(Exception):
    pass


def read_editor_text(path: str) -> str:
    """Read a text file. Refuse folders, binaries, and files that are too large."""
    file_path = Path(path)
    if file_path.is_dir():
        raise TextOpenError(f"{file_path.name} is a folder.")
    if not file_path.is_file():
        raise TextOpenError("That file is not there anymore.")
    if file_path.suffix.lower() in _BINARY_SUFFIXES:
        raise TextOpenError(f"{file_path.name} is not a text file.")
    try:
        size = file_path.stat().st_size
    except OSError as exc:
        raise TextOpenError(str(exc)) from exc
    if size > _MAX_BYTES:
        raise TextOpenError(f"{file_path.name} is too large to open in the editor.")
    try:
        data = file_path.read_bytes()
    except OSError as exc:
        raise TextOpenError(str(exc)) from exc
    if b"\x00" in data[:8192]:
        raise TextOpenError(f"{file_path.name} is not a text file.")
    try:
        return data.decode("utf-8")
    except UnicodeError as exc:
        raise TextOpenError(f"{file_path.name} is not a text file.") from exc
