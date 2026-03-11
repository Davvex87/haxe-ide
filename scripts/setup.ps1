# Setup script for setting up Python virtual environment and dependencies on Windows.
# Usage:
#   .\scripts\setup.ps1

$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Here = Split-Path -Parent $Here
$VenvDir = Join-Path $Here ".venv"
$Requirements = Join-Path $Here "requirements.txt"

Write-Host "Project root: $Here"

if (-not (Test-Path $Requirements)) {
    Write-Error "requirements.txt not found at $Requirements"
}

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtualenv in $VenvDir..."
    python -m venv $VenvDir
}

Write-Host "Activating virtualenv..."
& "$VenvDir\Scripts\Activate.ps1"

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing dependencies..."
pip install -r $Requirements

Write-Host "Setup complete. Virtual environment is ready at $VenvDir"
Write-Host "To activate manually: $VenvDir\Scripts\Activate.ps1"