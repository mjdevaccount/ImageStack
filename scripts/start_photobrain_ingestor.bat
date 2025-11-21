@echo off
setlocal

REM Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo [PhotoBrain] Starting daemon...
python -m photobrain.ingestor run

endlocal

