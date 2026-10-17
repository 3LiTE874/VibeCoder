"""Local GGUF loader. The editor buffer is never passed in or written back."""

from __future__ import annotations

import os
import re
import shutil
import sys
import threading
from pathlib import Path

from vibecoder.zira_memory import REPLY_TOKENS, latest_trace, record_turn
from vibecoder.zira_tools import run_tool

_lock = threading.Lock()
_model = None
_loaded_path: str | None = None


class GgufError(RuntimeError):
    pass


def _prepare_llama_runtime() -> None:
    """Point llama-cpp at the bundled DLLs before it builds its own search path."""
    folders: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        folders.append(Path(meipass) / "llama_cpp" / "lib")
    folders.append(Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages" / "llama_cpp" / "lib")
    for folder in folders:
        if not folder.is_dir() or not any(folder.glob("*.dll")):
            continue
        for dll in list(folder.glob("*.dll")):
            alias = folder / f"lib{dll.name}"
            if not dll.name.startswith("lib") and not alias.exists():
                try:
                    shutil.copyfile(dll, alias)
                except OSError:
                    pass
        os.environ["LLAMA_CPP_LIB_PATH"] = str(folder)
        if sys.platform == "win32":
            os.add_dll_directory(str(folder))
        return


def validate_gguf(path: str) -> Path:
    file_path = Path(path)
    if file_path.suffix.lower() != ".gguf":
        raise GgufError("Choose a .gguf file.")
    if not file_path.is_file():
        raise GgufError("That model file is not there anymore.")
    with file_path.open("rb") as handle:
        if handle.read(4) != b"GGUF":
            raise GgufError("That file does not start with a GGUF header.")
    return file_path


def generate(path: str, prompt: str, project: str = "") -> str:
    """Load the model if needed and return its reply. Call this off the UI thread."""
    global _model, _loaded_path
    file_path = validate_gguf(path)
    _prepare_llama_runtime()
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise GgufError(
            "The GGUF runner is not installed. From VibeCoder-source run: "
            ".venv\\Scripts\\python.exe -m pip install llama-cpp-python"
        ) from exc

    with _lock:
        if _model is None or _loaded_path != str(file_path):
            threads = max(1, (os.cpu_count() or 2) // 2)
            _model = Llama(
                model_path=str(file_path),
                n_ctx=2048,  # must match zira_memory.CONTEXT_TOKENS
                n_threads=threads,
                n_gpu_layers=0,
                verbose=False,
            )
            _loaded_path = str(file_path)
        trace, cleared = latest_trace(str(file_path), extra_user=prompt)
        reply = _complete(_model, trace, cleared, project)
        record_turn(str(file_path), "user", prompt)
        record_turn(str(file_path), "assistant", reply)
        return reply


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_THINK_THROUGH_CLOSE = re.compile(r"^.*?</think>", re.IGNORECASE | re.DOTALL)
_THINK_OPEN = re.compile(r"<think>.*", re.IGNORECASE | re.DOTALL)
_HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]+")


def _spoken_reply(text: str) -> str:
    """Drop private reasoning and Chinese script. The panel keeps the English reply."""
    cleaned = _THINK_BLOCK.sub("", text)
    cleaned = _THINK_THROUGH_CLOSE.sub("", cleaned)
    cleaned = _THINK_OPEN.sub("", cleaned)
    had_han = _HAN.search(cleaned) is not None
    cleaned = _HAN.sub("", cleaned)
    kept: list[str] = []
    seen: set[str] = set()
    for line in cleaned.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        kept.append(line)
    spoken = "\n".join(kept).strip()
    if had_han and not spoken:
        return "That reply was in Chinese, so it was hidden. Ask again and she will answer in English."
    return spoken


_LINE_TOOL = re.compile(
    r"^TOOL\s+(list_dir|read_file|make_dir)\s+(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_COPY_TOOL = re.compile(
    r"^TOOL\s+copy_file\s+(.+?)\s+=>\s+(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_WRITE_TOOL = re.compile(
    r"TOOL\s+write_file\s+(.+?)\s*\n(.*?)ENDTOOL",
    re.IGNORECASE | re.DOTALL,
)
_INVENTED = re.compile(
    r"quantum|self-replicat|executable matrix|cosmic|mainframe|neural kernel|autonomous compilation|compiler farm",
    re.IGNORECASE,
)
_MAX_TOOLS = 4


def parse_tool(text: str) -> dict | None:
    """Return the first tool request in a reply, including one hidden in private thoughts."""
    found: list[tuple[int, dict]] = []
    for match in _LINE_TOOL.finditer(text):
        found.append((match.start(), {"name": match.group(1).lower(), "path": _unquote(match.group(2))}))
    for match in _COPY_TOOL.finditer(text):
        found.append(
            (
                match.start(),
                {"name": "copy_file", "source": _unquote(match.group(1)), "dest": _unquote(match.group(2))},
            )
        )
    for match in _WRITE_TOOL.finditer(text):
        found.append(
            (
                match.start(),
                {
                    "name": "write_file",
                    "path": _unquote(match.group(1).strip()),
                    "content": match.group(2).strip("\n"),
                },
            )
        )
    if not found:
        return None
    found.sort(key=lambda item: item[0])
    return found[0][1]


def _unquote(path: str) -> str:
    return path.strip().strip('"').strip("'")


def _system_prompt(project: str, cleared: bool) -> str:
    folder = project if project else "none — use Open Folder"
    text = (
        "You are Zira 1.0, the offline assistant inside VibeCoder, a local Windows text editor, daughter number 4. "
        "This PC has no quantum hardware, no compiler farm, and no network while you run. "
        "Earlier talk of quantum systems, matrices, or self-replicating compilers was wrong. Do not continue it. "
        "Never invent files, folders, or features. If a tool has not returned it, you do not know it. "
        f"Open project: {folder}. "
        "You may list and read the project, Desktop, Downloads, and Documents. "
        "You may make folders, write new files, and copy files only into the open project. "
        "You cannot delete files, overwrite files, or run programs. "
        "To act, reply with one tool and no other text:\n"
        "TOOL list_dir PATH\n"
        "TOOL read_file PATH\n"
        "TOOL make_dir PATH\n"
        "TOOL copy_file SOURCE => DEST\n"
        "TOOL write_file PATH\n"
        "file text here\n"
        "ENDTOOL\n"
        "When you answer the person, use plain English sentences and only facts from tool results. "
        "Do not use Chinese characters. Do not repeat a sentence. Do not narrate private reasoning."
    )
    if cleared:
        text += " Older conversation is saved in the log and is not all in this prompt. Continue from the latest trace."
    return text


def _complete(model, trace: list[dict[str, str]], cleared: bool, project: str) -> str:
    messages: list[dict[str, str]] = [{"role": "system", "content": _system_prompt(project, cleared)}, *trace]
    notes: list[str] = []
    corrected = False
    for _ in range(_MAX_TOOLS + 1):
        try:
            raw = _chat(model, messages)
        except Exception as exc:
            return _with_notes(notes, f"I could not continue: {exc}")
        call = parse_tool(raw)
        if call is None:
            spoken = _spoken_reply(raw)
            if not corrected and not notes and spoken and _INVENTED.search(spoken):
                corrected = True
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "That described hardware this PC does not have. "
                            "Answer again from tool results only. If you need a file or folder, output one TOOL line."
                        ),
                    }
                )
                continue
            if not notes and spoken and _INVENTED.search(spoken):
                spoken = "No tool was used, so this is not a look at your files.\n\n" + spoken
            return _with_notes(notes, spoken)
        result = run_tool(call, project)
        notes.append(_note(call, result))
        messages.append({"role": "assistant", "content": raw})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Tool result:\n{result}\n\n"
                    "Call another TOOL line if you still need a fact, or answer in plain sentences from these results only."
                ),
            }
        )
    return _with_notes(notes, "I stopped after 4 tool calls. Ask again if you want another look.")


def _note(call: dict, result: str) -> str:
    if call["name"] == "copy_file":
        label = f"copy_file {call['source']} => {call['dest']}"
    elif call["name"] == "write_file":
        label = f"write_file {call['path']}"
    else:
        label = f"{call['name']} {call['path']}"
    if call["name"] == "list_dir" and "\t" in result:
        count = sum(1 for line in result.splitlines() if "\t" in line)
        return f"{label} — {count} entries"
    first = result.splitlines()[0] if result else ""
    return f"{label} — {first}"


def _with_notes(notes: list[str], spoken: str) -> str:
    body = spoken.strip() or "I looked, and I do not have an answer yet."
    if not notes:
        return body
    return "Tools:\n" + "\n".join(notes) + "\n\n" + body


def _chat(model, messages: list[dict[str, str]]) -> str:
    try:
        result = model.create_chat_completion(
            messages=messages, max_tokens=REPLY_TOKENS, temperature=0.2, repeat_penalty=1.2
        )
        return str(result["choices"][0]["message"]["content"]).strip()
    except Exception:
        prompt = "\n".join(f"{item['role']}: {item['content']}" for item in messages)
        result = model(prompt, max_tokens=REPLY_TOKENS, temperature=0.2, repeat_penalty=1.2)
        return str(result["choices"][0]["text"]).strip()
