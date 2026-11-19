"""File tools for Zira. She can look, and she can write only inside the open project."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_LIST_LIMIT = 40
_READ_LIMIT = 1600
_READ_LINES = 80
_WRITE_LIMIT = 32000
_SEARCH_MATCHES = 20
_SEARCH_FILES = 400
_SEARCH_FILE_BYTES = 512_000
_SKIP_DIRS = {".git", ".hg", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}

_CAN = (
    "I can list, read, and search the open project, Desktop, Downloads, and Documents. "
    "I can make folders, write a new file, append, copy, and replace one exact piece of text, "
    "and those changes stay inside the open project."
)

_REFUSALS = {
    "delete": "I can't do that. I don't delete files.",
    "delete_file": "I can't do that. I don't delete files.",
    "remove": "I can't do that. I don't delete files.",
    "remove_file": "I can't do that. I don't delete files.",
    "unlink": "I can't do that. I don't delete files.",
    "run": "I can't do that. I don't run programs.",
    "run_file": "I can't do that. I don't run programs.",
    "shell": "I can't do that. I don't run programs.",
    "exec": "I can't do that. I don't run programs.",
    "execute": "I can't do that. I don't run programs.",
    "command": "I can't do that. I don't run programs.",
    "overwrite": "I can't do that. I don't replace a whole file. I can replace one exact piece of text, or append.",
    "move": "I can't do that. I don't rename or move files. I can copy into the open project.",
    "move_file": "I can't do that. I don't rename or move files. I can copy into the open project.",
    "rename": "I can't do that. I don't rename or move files. I can copy into the open project.",
    "download": "I can't do that. I don't download files.",
}


class ToolError(RuntimeError):
    pass


def run_tool(call: dict, project: str, online: bool = False) -> str:
    name = str(call.get("name", "")).lower()
    try:
        if name in _REFUSALS:
            return _REFUSALS[name]
        if name == "web_lookup":
            if not online:
                return "I can't do that while OFFLINE. That lookup was not sent."
            from vibecoder.zira_online import lookup_web

            return lookup_web(call.get("path", ""))
        if name == "list_dir":
            return _list_dir(_readable(call["path"], project))
        if name == "read_file":
            return _read_file(_readable(call["path"], project), int(call.get("line") or 1))
        if name == "search_text":
            return _search_text(call.get("query", ""), call.get("path", ""), project)
        if name == "make_dir":
            return _make_dir(_writable(call["path"], project))
        if name == "write_file":
            if "content" not in call:
                return "I can't do that until the new file's text is closed with ENDTOOL."
            return _write_file(_writable(call["path"], project), call.get("content", ""))
        if name == "append_file":
            if "content" not in call:
                return "I can't do that until the text to add is closed with ENDTOOL."
            return _append_file(_writable(call["path"], project), call.get("content", ""))
        if name == "replace_text":
            if "old" not in call or "new" not in call:
                return "I can't do that until the old text is marked ENDOLD and the new text is closed with ENDTOOL."
            return _replace_text(_writable(call["path"], project), call.get("old", ""), call.get("new", ""))
        if name == "copy_file":
            source = _readable(call["source"], project)
            dest = _writable(call["dest"], project)
            return _copy_file(source, dest)
    except ToolError as exc:
        return str(exc)
    except OSError as exc:
        return f"Could not use that path: {exc}"
    except (TypeError, ValueError, KeyError):
        return "I can't do that. The tool line was missing a path or a line number."
    return f"I can't do that. I don't have a tool named {name or 'that'}. {_CAN}"


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


def _read_file(file_path: Path, start_line: int = 1) -> str:
    if not file_path.is_file():
        raise ToolError("That path is not a file.")
    data = file_path.read_bytes()
    if b"\x00" in data[:512]:
        return "Binary file. Contents not shown."
    lines = data.decode("utf-8", errors="replace").splitlines()
    start = max(1, start_line)
    if start > len(lines):
        return f"That file has {len(lines)} lines. Nothing starts at line {start}."
    chosen: list[str] = []
    used = 0
    next_line = start
    for number, line in enumerate(lines[start - 1 :], start=start):
        piece = f"{number}|{line}"
        if chosen and used + len(piece) + 1 > _READ_LIMIT:
            break
        if len(piece) > _READ_LIMIT:
            piece = piece[:_READ_LIMIT]
        chosen.append(piece)
        used += len(piece) + 1
        next_line = number + 1
        if len(chosen) >= _READ_LINES:
            break
    text = "\n".join(chosen)
    if next_line <= len(lines):
        text += f"\n…more lines. Next read starts at line {next_line}."
    return text


def _search_text(query: str, folder: str, project: str) -> str:
    needle = " ".join((query or "").split())
    if len(needle) < 2:
        raise ToolError("Tell me at least two characters to search for.")
    if str(folder).strip():
        root = _readable(folder, project)
    elif project and Path(project).is_dir():
        root = _readable(project, project)
    else:
        raise ToolError("Open a folder in Explorer first. I search inside that project.")
    if not root.is_dir():
        raise ToolError("That path is not a folder.")
    base = root.resolve()
    hits: list[str] = []
    seen_files = 0
    needle_cf = needle.casefold()
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(name for name in dirnames if name not in _SKIP_DIRS)
        for name in sorted(filenames):
            if len(hits) >= _SEARCH_MATCHES:
                break
            seen_files += 1
            if seen_files > _SEARCH_FILES:
                hits.append("…stopped after looking through 400 files")
                return "\n".join(hits)
            file_path = Path(dirpath) / name
            try:
                resolved = file_path.resolve()
            except OSError:
                continue
            if resolved != base and base not in resolved.parents:
                continue
            if not resolved.is_file():
                continue
            try:
                if resolved.stat().st_size > _SEARCH_FILE_BYTES:
                    continue
                data = resolved.read_bytes()
            except OSError:
                continue
            if b"\x00" in data[:512]:
                continue
            text = data.decode("utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                if needle_cf not in line.casefold():
                    continue
                shown = line.strip()
                if len(shown) > 180:
                    shown = shown[:180] + "…"
                hits.append(f"{resolved}:{number}: {shown}")
                if len(hits) >= _SEARCH_MATCHES:
                    break
        if len(hits) >= _SEARCH_MATCHES:
            break
    if not hits:
        return f"No matches for {needle}."
    return "\n".join(hits)


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


def _append_file(file_path: Path, content: str) -> str:
    if len(content.encode("utf-8")) > _WRITE_LIMIT:
        raise ToolError("That text is too long to add.")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return f"Added {len(content)} characters to {file_path.name}."


def _replace_text(file_path: Path, old: str, new: str) -> str:
    if not file_path.is_file():
        raise ToolError("That path is not a file.")
    if not old:
        raise ToolError("I need the exact text to replace.")
    if len(old.encode("utf-8")) > _WRITE_LIMIT or len(new.encode("utf-8")) > _WRITE_LIMIT:
        raise ToolError("That text is too long to replace.")
    data = file_path.read_bytes()
    if b"\x00" in data[:512]:
        raise ToolError("That file is binary. I will not change it.")
    if len(data) > 1_000_000:
        raise ToolError("That file is too large to edit this way.")
    text = data.decode("utf-8", errors="replace")
    count = text.count(old)
    if count == 0:
        return "That text is not in the file, so nothing was changed."
    if count > 1:
        return (
            f"That text appears {count} times. I will not guess which one. "
            "Include more of the line so it matches once."
        )
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return f"Replaced one match in {file_path.name}."


def _copy_file(source: Path, dest: Path) -> str:
    if not source.is_file():
        raise ToolError("The source is not a file.")
    if dest.exists():
        raise ToolError("The destination already exists. I will not overwrite it.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return f"Copied {source.name} to {dest}"
