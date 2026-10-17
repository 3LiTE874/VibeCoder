"""Remember the open project and tabs across launches."""

from __future__ import annotations

import json
import os
from pathlib import Path

_MAX_UNSAVED = 1_000_000


def session_path() -> Path:
    override = os.environ.get("VIBECODER_SESSION", "").strip()
    if override:
        path = Path(override)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VibeCoder"
    root.mkdir(parents=True, exist_ok=True)
    return root / "session.json"


def load_session() -> dict | None:
    path = session_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def save_session(project: str, tabs: list[dict], current: int) -> None:
    payload = {
        "project": project,
        "current": current,
        "tabs": tabs,
    }
    path = session_path()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def tab_record(path: str | None, text: str, modified: bool, line: int, index: int) -> dict | None:
    """One tab for the session file. Unmodified files store the path only."""
    record: dict = {"line": line, "index": index}
    if path and Path(path).is_file():
        record["path"] = str(Path(path).resolve())
        if modified:
            if len(text) > _MAX_UNSAVED:
                record["modified"] = False
            else:
                record["text"] = text
                record["modified"] = True
        return record
    if text.strip():
        record["text"] = text[:_MAX_UNSAVED]
        record["modified"] = True
        return record
    return None
