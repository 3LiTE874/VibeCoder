"""Zira's job memory. One open piece of work, stored in her own database.

This is her ASA layer: she can leave a blocked job and pick it up on the
next message. It does not share files with any other assistant.
"""

from __future__ import annotations

from pathlib import Path

from vibecoder.zira_memory import _now, connect

_NOTE_LIMIT = 800


def unfinished_note(database: Path | None = None) -> str:
    """Prompt text for the newest job that stopped before it was done."""
    conn = connect(database)
    try:
        row = conn.execute(
            "SELECT goal, note FROM asa_jobs WHERE status = 'blocked' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return ""
    goal, note = row
    text = f"Unfinished job: {goal.strip()}"
    if note.strip():
        text += f" Last note: {note.strip()}"
    if len(text) > 360:
        text = text[:360].rstrip() + "…"
    return text + " Continue that job if this message asks you to go on."


def begin_turn(goal: str, database: Path | None = None) -> int:
    """Start this message as the open job. Older open jobs are paused."""
    conn = connect(database)
    try:
        conn.execute("UPDATE asa_jobs SET status = 'paused', updated_at = ? WHERE status = 'open'", (_now(),))
        cursor = conn.execute(
            "INSERT INTO asa_jobs (goal, status, note, updated_at) VALUES (?, 'open', '', ?)",
            (goal.strip()[:500], _now()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def note_step(job_id: int, line: str, database: Path | None = None) -> None:
    """Keep the tail of what this job already did."""
    extra = " ".join(line.split())
    if not extra:
        return
    conn = connect(database)
    try:
        row = conn.execute("SELECT note FROM asa_jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return
        note = (row[0] + "\n" + extra).strip()
        if len(note) > _NOTE_LIMIT:
            note = note[-_NOTE_LIMIT:]
        conn.execute(
            "UPDATE asa_jobs SET note = ?, updated_at = ? WHERE id = ?",
            (note, _now(), job_id),
        )
        conn.commit()
    finally:
        conn.close()


def close_turn(
    job_id: int,
    status: str,
    summary: str,
    database: Path | None = None,
    worked: bool = False,
) -> None:
    """Mark this job done or blocked. A turn that used a tool clears older blocked jobs."""
    if status not in {"done", "blocked"}:
        status = "blocked"
    note_step(job_id, summary, database)
    conn = connect(database)
    try:
        conn.execute(
            "UPDATE asa_jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), job_id),
        )
        if status == "done" and worked:
            conn.execute(
                "UPDATE asa_jobs SET status = 'done', updated_at = ? WHERE status = 'blocked'",
                (_now(),),
            )
        conn.commit()
    finally:
        conn.close()
