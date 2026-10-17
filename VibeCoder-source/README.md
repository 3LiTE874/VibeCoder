# VibeCoder

Notepad++-style open-source editor for **Christopher LePage**. Dark mode by default, tabbed editing, persistent syntax highlighting, Markdown support, and a stub AI vibe-coding panel.

Licensed under **GNU GPL-3.0**.

## Requirements

- Python 3.10+
- PyQt6 + PyQt6-QScintilla

> **Note:** QScintilla's official Python bindings target PyQt6 (not PySide6). The editor uses the same Scintilla engine family as Notepad++.

## Quick start (Windows)

```powershell
git clone https://github.com/3LiTE874/VibeCoder.git
cd VibeCoder
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m vibecoder
```

## Quick start (Linux / dev VM)

```bash
git clone https://github.com/3LiTE874/VibeCoder.git
cd VibeCoder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python3 -m vibecoder
```

Or install in editable mode:

```bash
pip install -e .
vibecoder
```

## Features (MVP)

- **Menus:** File, Edit, View, Language, Help
- **Tabs:** Multiple files, closable and movable
- **Dark theme:** Applied to chrome and every lexer after `setLexer()`
- **Languages:** Python, Markdown, JavaScript, HTML, CSS, C/C++, JSON, YAML, XML, SQL, Bash, Plain Text
- **File ops:** New, Open, Save, Save As
- **AI panel:** Stub sidebar (`Ctrl+Shift+A` to toggle) — does not touch the editor lexer

## Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| New | Ctrl+N |
| Open | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Toggle AI Panel | Ctrl+Shift+A |
| Quit | Ctrl+Q |

## Project layout

```
VibeCoder/
├── LICENSE          # GPL-3.0
├── README.md
├── requirements.txt
├── pyproject.toml
└── src/vibecoder/
    ├── app.py           # Entry point
    ├── main_window.py   # Menus, tabs, file ops
    ├── editor_widget.py # QScintilla wrapper
    ├── editor_tab.py    # Tab + file metadata
    ├── languages.py     # Lexer factory
    ├── themes.py        # Dark palette (post-lexer)
    └── ai_panel.py      # AI stub
```

## Roadmap

- File-extension auto-detect on open
- Local GGUF / AI backend
- Windows installer (Inno Setup)
- Broader language list
