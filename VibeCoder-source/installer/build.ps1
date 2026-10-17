# Build VibeCoder.exe, then compile installer\Inno.iss when Inno Setup 6 is installed.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing $python. Create the project venv and install requirements.txt first."
}

& $python -m pip install "pyinstaller>=6.11"
if ($LASTEXITCODE -ne 0) { throw "pip install pyinstaller failed." }

$pyinstaller = Join-Path $root ".venv\Scripts\pyinstaller.exe"
& $pyinstaller --noconfirm (Join-Path $PSScriptRoot "VibeCoder.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

$exe = Join-Path $root "dist\VibeCoder\VibeCoder.exe"
if (-not (Test-Path $exe)) {
    throw "Expected executable was not created: $exe"
}

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    Write-Host "Executable is ready: $exe"
    Write-Host "Inno Setup 6 is not installed, so Inno.iss was not compiled."
    Write-Host "Install it from https://jrsoftware.org/isinfo.php and run ISCC.exe installer\Inno.iss"
    exit 0
}

& $iscc (Join-Path $PSScriptRoot "Inno.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC failed." }

Write-Host "Installer written to installer\Output"
