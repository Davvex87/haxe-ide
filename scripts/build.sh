#!/usr/bin/env bash
set -euo pipefail

# Build script for producing a standalone Linux executable using PyInstaller.
# Usage:
#   chmod +x scripts/build.sh
#   ./scripts/build.sh

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$HERE/.venv"
DIST_DIR="$HERE/dist"
BUILD_DIR="$HERE/build"
HOOKS_DIR="$HERE/hooks"

echo "Project root: $HERE"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtualenv in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtualenv..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$HERE/requirements.txt"

echo "Cleaning previous builds..."
rm -rf "$DIST_DIR" "$BUILD_DIR"

ABS_EXAMPLES="$HERE/examples"
ABS_STYLE="$HERE/style.tcss"

if [ ! -e "$ABS_STYLE" ]; then
    echo "Warning: style.tcss not found at $ABS_STYLE"
fi

PYINSTALLER_OPTS=(
    --onefile
    --name haxe-ide
    --additional-hooks-dir="$HOOKS_DIR"
    --collect-submodules textual
    --collect-submodules textual.widgets
    --add-data "$ABS_EXAMPLES:examples"
    --add-data "$ABS_STYLE:."
)

echo "Running PyInstaller..."
pyinstaller "${PYINSTALLER_OPTS[@]}" "$HERE/src/main.py"

echo "Build finished. Output in $DIST_DIR"

echo "You can test run: $DIST_DIR/haxe-ide"
