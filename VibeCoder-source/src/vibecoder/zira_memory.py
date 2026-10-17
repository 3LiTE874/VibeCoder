"""Zira's conversation log. The full history stays in SQLite.

The live prompt only keeps the newest turns that fit the token window.
When older turns no longer fit, they stay in the database and the next
reply continues from the latest trace that still fits.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

CONTEXT_TOKENS = 2048
REPLY_TOKENS = 512
_SYSTEM_RESERVE = 480


def app_folder() -> Path:
    override = os.environ.get("VIBECODER_APPDATA", "").strip()
    root = Path(override) if override else Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VibeCoder"
    root.mkdir(parents=True, exist_ok=True)
    return root


def database_path() -> Path:
    """SQLite file to copy when backing Zira up onto another PC."""
    pointer = app_folder() / "database.path"
    if pointer.is_file():
        chosen = pointer.read_text(encoding="utf-8").strip()
        if chosen:
            path = Path(chosen)
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
    return app_folder() / "zira_memory.sqlite"


def choose_database_folder(folder: str) -> Path:
    """Point Zira at a folder. Copy the current database if the new file is not there yet."""
    dest_dir = Path(folder)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "zira_memory.sqlite"
    current = database_path()
    if current.is_file() and current.resolve() != dest.resolve() and not dest.exists():
        shutil.copy2(current, dest)
    (app_folder() / "database.path").write_text(str(dest), encoding="utf-8")
    return dest


def save_note(query: str, summary: str, url: str, database: Path | None = None) -> None:
    with _connect(database) as conn:
        conn.execute(
            "INSERT INTO notes (query, summary, url, created_at) VALUES (?, ?, ?, ?)",
            (query, summary, url, _now()),
        )


def history_budget() -> int:
    return CONTEXT_TOKENS - REPLY_TOKENS - _SYSTEM_RESERVE


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def record_turn(model_path: str, role: str, content: str, database: Path | None = None) -> None:
    with _connect(database) as conn:
        conn.execute(
            "INSERT INTO turns (model_path, role, content, created_at) VALUES (?, ?, ?, ?)",
            (model_path, role, content, _now()),
        )


def load_turns(model_path: str, database: Path | None = None) -> list[dict[str, str]]:
    with _connect(database) as conn:
        rows = conn.execute(
            "SELECT role, content FROM turns WHERE model_path = ? ORDER BY id",
            (model_path,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def latest_trace(model_path: str, extra_user: str = "", database: Path | None = None) -> tuple[list[dict[str, str]], bool]:
    """Return the newest logged turns that fit, plus whether older turns were left out."""
    turns = load_turns(model_path, database)
    if extra_user:
        turns.append({"role": "user", "content": extra_user})
    kept: list[dict[str, str]] = []
    used = 0
    budget = history_budget()
    for turn in reversed(turns):
        cost = estimate_tokens(turn["content"]) + 4
        if kept and used + cost > budget:
            break
        kept.append(turn)
        used += cost
        if used > budget:
            break
    kept.reverse()
    cleared = len(kept) < len(turns)
    return kept, cleared


def _connect(database: Path | None) -> sqlite3.Connection:
    path = database or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_path TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS turns_model ON turns (model_path, id)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            summary TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
