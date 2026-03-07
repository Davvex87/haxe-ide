# Build script for producing a standalone Windows executable using PyInstaller.
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/build.ps1

$ErrorActionPreference = "Stop"

# Resolve project root
$HERE = Resolve-Path "$PSScriptRoot\.."
$VENV_DIR = Join-Path $HERE ".venv"
$DIST_DIR = Join-Path $HERE "dist"
$BUILD_DIR = Join-Path $HERE "build"
$HOOKS_DIR = Join-Path $HERE "hooks"

Write-Host "Project root: $HERE"

if (!(Test-Path $VENV_DIR)) {
    Write-Host "Creating virtualenv in $VENV_DIR..."
    python -m venv $VENV_DIR
}

Write-Host "Activating virtualenv..."
$VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
$VENV_PIP = Join-Path $VENV_DIR "Scripts\pip.exe"

Write-Host "Installing dependencies..."
& $VENV_PIP install --upgrade pip
& $VENV_PIP install -r (Join-Path $HERE "requirements.txt")

Write-Host "Cleaning previous builds..."
if (Test-Path $DIST_DIR) { Remove-Item $DIST_DIR -Recurse -Force }
if (Test-Path $BUILD_DIR) { Remove-Item $BUILD_DIR -Recurse -Force }

$ABS_EXAMPLES = Join-Path $HERE "examples"
$ABS_STYLE = Join-Path $HERE "style.tcss"

if (!(Test-Path $ABS_STYLE)) {
    Write-Host "Warning: style.tcss not found at $ABS_STYLE"
}

$PYINSTALLER_OPTS = @(
    "--onefile"
    "--name", "haxe-ide"
    "--additional-hooks-dir=$HOOKS_DIR"
    "--collect-submodules", "textual"
    "--collect-submodules", "textual.widgets"
    "--add-data", "$ABS_EXAMPLES;examples"
    "--add-data", "$ABS_STYLE;."
)

Write-Host "Running PyInstaller..."
& $VENV_DIR\Scripts\pyinstaller.exe @PYINSTALLER_OPTS (Join-Path $HERE "src\main.py")

Write-Host "Build finished. Output in $DIST_DIR"

Write-Host "You can test run: $DIST_DIR\haxe-ide.exe"
