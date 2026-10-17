# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the VibeCoder folder build that Inno.iss installs.

Run from anywhere:
    .venv\\Scripts\\pyinstaller.exe --noconfirm installer\\VibeCoder.spec

UPX is off on purpose. Packing Qt DLLs is a common source of
"application failed to start" errors that only show up on other PCs.
"""

import shutil
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).resolve().parent
src = root / "src"
sys.path.insert(0, str(src))

hidden = collect_submodules("vibecoder")
hidden += collect_submodules("llama_cpp")
hidden += [
    "PyQt6.Qsci",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
]

# llama-cpp looks beside its package for ggml/llama DLLs. PyInstaller does not
# pick those up from a normal import, so stage them next to the frozen package.
# Both ggml-base.dll and libggml-base.dll are included; Windows builds ask for either name.
lib_dir = root / ".venv" / "Lib" / "site-packages" / "llama_cpp" / "lib"
stage = root / "build" / "llama_lib"
stage.mkdir(parents=True, exist_ok=True)
for dll in lib_dir.glob("*.dll"):
    shutil.copyfile(dll, stage / dll.name)
    alias = stage / f"lib{dll.name}"
    if not alias.exists():
        shutil.copyfile(dll, alias)
llama_datas = [(str(file), "llama_cpp/lib") for file in stage.iterdir() if file.is_file()]

a = Analysis(
    [str(src / "vibecoder" / "app.py")],
    pathex=[str(src)],
    binaries=[],
    datas=llama_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pydoc",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VibeCoder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VibeCoder",
)
