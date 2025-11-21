Param(
    [int]$Port = 8090
)

Set-Location -Path "$PSScriptRoot\..\python_server"
$env:PYTHONPATH = "$PSScriptRoot\.."

python -m uvicorn main:app --host 0.0.0.0 --port $Port --reload

