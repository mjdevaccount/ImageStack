@echo off
REM Start PhotoBrain watcher (auto-ingest & auto-tag)

setlocal

REM Adjust these to match your setup
set PHOTOBRAIN_API_BASE=http://localhost:8090
set PHOTOBRAIN_WATCH_DIRS=C:\PhotoBrain\Inbox

REM Change to repo root if needed
cd /d %~dp0..
call .venv\Scripts\activate.bat

echo Starting PhotoBrain watcher...
python -m python_server.services.photobrain_watcher

endlocal

