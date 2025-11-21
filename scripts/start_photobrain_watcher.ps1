# Start PhotoBrain watcher (auto-ingest & auto-tag)

$env:PHOTOBRAIN_API_BASE = "http://localhost:8090"
$env:PHOTOBRAIN_WATCH_DIRS = "C:\PhotoBrain\Inbox"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "Starting PhotoBrain watcher..." -ForegroundColor Green
python -m python_server.services.photobrain_watcher

