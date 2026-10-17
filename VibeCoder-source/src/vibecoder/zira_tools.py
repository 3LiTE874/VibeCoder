"""File tools for Zira. She can look, and she can write only inside the open project."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_LIST_LIMIT = 40
_READ_LIMIT = 1600
_WRITE_LIMIT = 32000


class ToolError(RuntimeError):
    pass


def run_tool(call: dict, project: str) -> str:
    name = call.get("name", "")
    try:
        if name == "list_dir":
            return _list_dir(_readable(call["path"], project))
        if name == "read_file":
            return _read_file(_readable(call["path"], project))
        if name == "make_dir":
            return _make_dir(_writable(call["path"], project))
        if name == "write_file":
            return _write_file(_writable(call["path"], project), call.get("content", ""))
        if name == "copy_file":
            source = _readable(call["source"], project)
            dest = _writable(call["dest"], project)
            return _copy_file(source, dest)
    except ToolError as exc:
        return str(exc)
    except OSError as exc:
        return f"Could not use that path: {exc}"
    return "Unknown tool."


def allowed_project(path: str) -> str:
    """Project folders inside Windows or Program Files are not hers to change."""
    if not path:
        return ""
    folder = Path(path)
    try:
        resolved = folder.resolve()
    except OSError:
        return ""
    if not resolved.is_dir() or _blocked(resolved):
        return ""
    return str(resolved)


def read_roots(project: str) -> list[Path]:
    roots: list[Path] = []
    if project:
        folder = Path(project)
        if folder.is_dir():
            roots.append(folder)
    home = Path.home()
    for name in ("Desktop", "Downloads", "Documents"):
        folder = home / name
        if folder.is_dir():
            roots.append(folder)
    return roots


def _readable(path: str, project: str) -> Path:
    return _inside(path, read_roots(project), "I can only list and read the open project, Desktop, Downloads, and Documents.")


def _writable(path: str, project: str) -> Path:
    if not project or not Path(project).is_dir():
        raise ToolError("Open a folder in Explorer first. I only create files inside that project.")
    return _inside(path, [Path(project)], "I only create files inside the open project.")


def _inside(path: str, roots: list[Path], refusal: str) -> Path:
    text = (path or "").strip().strip('"').strip("'")
    if not text:
        raise ToolError("That tool needs a path.")
    try:
        resolved = Path(text).expanduser().resolve()
    except OSError as exc:
        raise ToolError(f"That path is not usable: {exc}") from exc
    if _blocked(resolved):
        raise ToolError("That folder is off limits.")
    for root in roots:
        base = root.resolve()
        if resolved == base or base in resolved.parents:
            return resolved
    raise ToolError(refusal)


def _blocked(path: Path) -> bool:
    blocked_roots = [
        os.environ.get("WINDIR", r"C:\Windows"),
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
    ]
    for root in blocked_roots:
        if not root:
            continue
        base = Path(root).resolve()
        if path == base or base in path.parents:
            return True
    return False


def _list_dir(folder: Path) -> str:
    if not folder.is_dir():
        raise ToolError("That path is not a folder.")
    lines: list[str] = []
    children = sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    for child in children:
        if len(lines) >= _LIST_LIMIT:
            lines.append("…more entries not shown")
            break
        kind = "dir" if child.is_dir() else "file"
        lines.append(f"{kind}\t{child.name}")
    if not lines:
        return "(empty folder)"
    return "\n".join(lines)


def _read_file(file_path: Path) -> str:
    if not file_path.is_file():
        raise ToolError("That path is not a file.")
    data = file_path.read_bytes()
    if b"\x00" in data[:512]:
        return "Binary file. Contents not shown."
    text = data[:_READ_LIMIT].decode("utf-8", errors="replace")
    if len(data) > _READ_LIMIT:
        text += "\n…truncated"
    return text


def _make_dir(folder: Path) -> str:
    if folder.exists() and not folder.is_dir():
        raise ToolError("A file already has that name.")
    folder.mkdir(parents=True, exist_ok=True)
    return f"Folder ready: {folder}"


def _write_file(file_path: Path, content: str) -> str:
    if file_path.exists():
        raise ToolError("That file already exists. I will not overwrite it.")
    if len(content.encode("utf-8")) > _WRITE_LIMIT:
        raise ToolError("That text is too long to write.")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"Wrote {file_path.name} ({len(content)} characters)."


def _copy_file(source: Path, dest: Path) -> str:
    if not source.is_file():
        raise ToolError("The source is not a file.")
    if dest.exists():
        raise ToolError("The destination already exists. I will not overwrite it.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return f"Copied {source.name} to {dest}"
