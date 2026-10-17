"""Commands used by the Run menu. Missing tools are reported, not invented."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def command_for(language_id: str, path: Path) -> tuple[list[str] | None, str | None]:
    """Return (argv, error). error is set when this language has no local runner."""
    if language_id in {"python", "qiskit"}:
        argv = _python_prefix()
        if not argv:
            return None, "Python was not found on PATH, so the file was not started."
        return [*argv, str(path)], None

    if language_id == "javascript":
        node = shutil.which("node")
        if not node:
            return None, "Node.js was not found on PATH."
        return [node, str(path)], None

    if language_id == "powershell":
        shell = shutil.which("powershell") or shutil.which("powershell.exe")
        if not shell:
            return None, "powershell.exe was not found."
        return [shell, "-NoLogo", "-NoProfile", "-File", str(path)], None

    if language_id == "batch":
        shell = shutil.which("cmd") or shutil.which("cmd.exe")
        if not shell:
            return None, "cmd.exe was not found."
        return [shell, "/c", str(path)], None

    if language_id == "go":
        go = shutil.which("go")
        if not go:
            return None, "go was not found on PATH."
        return [go, "run", str(path)], None

    return None, f"No runner is set for {language_id}. Use the terminal to run it yourself."


def _python_prefix() -> list[str]:
    if not getattr(sys, "frozen", False):
        return [sys.executable, "-u"]
    py = shutil.which("py")
    if py:
        return [py, "-3", "-u"]
    python = shutil.which("python")
    if python:
        return [python, "-u"]
    return []
