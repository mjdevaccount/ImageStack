Write-Host "Checking Python..."
python --version

Write-Host "Checking pip packages..."
pip show fastapi | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "fastapi missing"; }

Write-Host "Checking Ollama..."
curl http://localhost:11434/api/tags

Write-Host "Done."

