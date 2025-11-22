Param(
    [int]$Port = 8090
)

Set-Location -Path "$PSScriptRoot\.."
$env:PYTHONPATH = "$PSScriptRoot\.."
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Use the virtual environment's Python
& "$PSScriptRoot\..\.venv\Scripts\python.exe" -m uvicorn python_server.main:app --host 0.0.0.0 --port $Port --reload

