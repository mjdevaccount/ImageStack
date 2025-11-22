# Stop PhotoBrain API Server

Write-Host "Stopping PhotoBrain API Server..." -ForegroundColor Cyan

# Find process listening on port 8090
$port = 8090
$connections = netstat -ano | Select-String ":$port"

if ($connections) {
    Write-Host "Found server running on port $port" -ForegroundColor Yellow
    
    # Extract PIDs
    $processIds = @()
    foreach ($line in $connections) {
        if ($line -match '\s+(\d+)\s*$') {
            $procId = $matches[1]
            if ($procId -and $procId -ne "0" -and $processIds -notcontains $procId) {
                $processIds += $procId
            }
        }
    }
    
    if ($processIds.Count -gt 0) {
        foreach ($procId in $processIds) {
            try {
                $process = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "  Stopping process: $($process.ProcessName) (PID: $procId)" -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "  [OK] Stopped PID $procId" -ForegroundColor Green
            } catch {
                Write-Host "  [FAIL] Could not stop PID $procId" -ForegroundColor Red
            }
        }
        
        # Verify it stopped
        Start-Sleep -Seconds 2
        $stillRunning = netstat -ano | Select-String ":$port"
        if (-not $stillRunning) {
            Write-Host ""
            Write-Host "[OK] Server stopped successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "[WARN] Server may still be running. Check manually." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Could not identify process PID" -ForegroundColor Red
    }
} else {
    Write-Host "No server found running on port $port" -ForegroundColor Yellow
}

# Also stop any stray Python processes running uvicorn
Write-Host ""
Write-Host "Checking for Python processes..." -ForegroundColor Cyan
try {
    $pythonProcs = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -eq "python"
    }

    if ($pythonProcs) {
        $stopped = $false
        foreach ($proc in $pythonProcs) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                Write-Host "  [OK] Stopped Python process (PID: $($proc.Id))" -ForegroundColor Green
                $stopped = $true
            } catch {
                # Ignore - process may already be gone
            }
        }
        if (-not $stopped) {
            Write-Host "  No active Python processes found" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No Python processes found" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Could not check Python processes" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
