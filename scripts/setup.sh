#!/usr/bin/env bash
set -euo pipefail

# Setup script for setting up Python virtual environment and dependencies on Linux.
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$HERE/.venv"
REQUIREMENTS="$HERE/requirements.txt"

echo "Project root: $HERE"

if [ ! -e "$REQUIREMENTS" ]; then
    echo "Error: requirements.txt not found at $REQUIREMENTS"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtualenv in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtualenv..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r "$REQUIREMENTS"

echo "Setup complete. Virtual environment is ready at $VENV_DIR"
echo "To activate manually: source $VENV_DIR/bin/activate"