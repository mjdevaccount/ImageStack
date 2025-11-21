# PhotoBrain Ingestor Launcher for PowerShell

Write-Host "[PhotoBrain] Starting daemon..." -ForegroundColor Cyan

# Activate venv if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

# Run PhotoBrain ingestor
python -m photobrain.ingestor run

