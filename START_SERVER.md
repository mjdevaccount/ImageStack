# Quick Start Guide: PhotoBrain API Server

## Prerequisites Checklist

Before starting the server, ensure these are set up:

### 1. Virtual Environment
```powershell
# Check if venv exists
Test-Path .\.venv\Scripts\Activate.ps1

# If False, create it:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Qdrant Vector Database
```powershell
# Check if Qdrant is running
docker ps | Select-String "qdrant"

# If not running:
docker start qdrant

# If container doesn't exist:
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# Verify it's working:
curl http://localhost:6333
```

### 3. Ollama (Vision Models)
```powershell
# Check if Ollama has required models
ollama list

# Should show:
# - llama3.2-vision:11b (for vision/auto-tagging)
# - phi4:14b (for Q&A)

# If models missing:
ollama pull llama3.2-vision:11b
ollama pull phi4:14b
```

---

## Start PhotoBrain API Server

### Option 1: Using Start Script (Recommended)
```powershell
# Navigate to project root
cd C:\ImageStack

# Run the start script
.\scripts\start_api.ps1
```

This script automatically:
- Sets correct working directory
- Sets PYTHONPATH correctly
- Handles UTF-8 encoding
- Starts uvicorn with proper module path

### Option 2: Manual Start
```powershell
# 1. Navigate to project root
cd C:\ImageStack

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Start server
python -m uvicorn python_server.main:app --host 0.0.0.0 --port 8090 --reload
```

---

## Verify Server is Running

**Wait ~10-15 seconds after starting for models to load.**

### Check Health Endpoint
```powershell
curl http://localhost:8090/health/
# Should return: {"status":"ok"}
```

### Check API Documentation
Open in browser:
- **Swagger UI**: http://localhost:8090/docs
- **ReDoc**: http://localhost:8090/redoc

### Check Server Logs
Look for these messages in the terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Application startup complete.
```

---

## ⚠️ Before Using Query Features

**Important:** The server will return **500 Internal Server Error** on query endpoints if no images have been ingested yet.

### Quick Fix: Ingest a Test Image

```powershell
# Upload any image
curl -F "file=@C:\Photos\test.jpg" http://localhost:8090/photobrain/ingest

# Or use interactive docs
Start http://localhost:8090/docs
# Navigate to POST /photobrain/ingest
```

### Verify Database Has Images

```powershell
# Check Qdrant collection
curl http://localhost:6333/collections/photobrain
# Look for: "points_count": <number> should be > 0
```

See the README for detailed ingestion options.

### Test PhotoBrain Query Endpoint
```powershell
# Test with curl
curl -X POST http://localhost:8090/photobrain/query `
  -H "Content-Type: application/json" `
  -d '{
    "question": "What images do I have?",
    "top_k": 5
  }'
```

---

## Available Endpoints

Once server is running at `http://localhost:8090`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/photobrain/ingest` | POST | Ingest images with auto-tagging |
| `/photobrain/search/text` | POST | Semantic text search |
| `/photobrain/search/image` | POST | Image similarity search |
| `/photobrain/query` | POST | **LLM-powered Q&A** ✨ |
| `/vision/describe` | POST | Vision AI descriptions |
| `/ocr/text` | POST | OCR text extraction |
| `/debug/preprocess` | POST | Preprocessing debug lab |

---

## Stopping the Server

```powershell
# If running in terminal: Press CTRL+C

# Or kill the process:
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

## Restarting the Server

```powershell
# Stop it
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Wait
Start-Sleep -Seconds 2

# Start again
.\scripts\start_api.ps1
```

---

## Troubleshooting

### Virtual Environment Not Found
```
Error: .venv\Scripts\python.exe not found
```
**Solution:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Port Already in Use
```powershell
# Check what's using port 8090
netstat -ano | findstr :8090

# Kill the process if it's a stuck Python process
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Or use a different port
.\scripts\start_api.ps1 -Port 8091
```

### Import Errors / Config Not Found
```
ImportError: cannot import name 'settings'
```
**Solution:**
```powershell
# Make sure you're in the project root
cd C:\ImageStack

# Use the start script (handles paths correctly)
.\scripts\start_api.ps1
```

### Qdrant Connection Failed
```
Error: [WinError 10061] No connection could be made
```
**Solution:**
```powershell
# Check if running
docker ps | Select-String "qdrant"

# Start it
docker start qdrant

# Or create new container
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant
```

### Ollama Models Not Found
```powershell
# Verify models are downloaded
ollama list

# Pull missing models
ollama pull llama3.2-vision:11b
ollama pull phi4:14b
```

### Unicode Encoding Errors
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution:**
```powershell
# Use the start script (has encoding fixes)
.\scripts\start_api.ps1
```

### Server Starts But Doesn't Respond
**Possible causes:**
1. Models are still loading (wait 30 seconds)
2. Qdrant not running (see above)
3. Wrong working directory

**Solution:**
```powershell
# Check server process is running
Get-Process | Where-Object {$_.ProcessName -eq "python"}

# Check Qdrant
curl http://localhost:6333

# Wait for models to load (first run takes longer)
Start-Sleep -Seconds 30
curl http://localhost:8090/health/
```

---

## Example: Test Complete Workflow

```powershell
# 1. Start server (this terminal)
uvicorn python_server.main:app --port 8090

# 2. In another terminal: Ingest an image
curl -F "file=@C:\Photos\receipt.jpg" `
  "http://localhost:8090/photobrain/ingest?auto_tag=true"

# 3. Query it
curl -X POST http://localhost:8090/photobrain/query `
  -H "Content-Type: application/json" `
  -d '{"question": "What is the total on my receipt?", "top_k": 5}'

# 4. Or use CLI
python -m cli.imagestack_cli ask "What is the total on my receipt?"
```

---

## Keep Server Running

### Background (Windows)
```powershell
# Run in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\ImageStack; .\.venv\Scripts\Activate.ps1; uvicorn python_server.main:app --port 8090"
```

### As Windows Service
Use NSSM (Non-Sucking Service Manager):
1. Download NSSM
2. `nssm install PhotoBrainAPI`
3. Configure path to uvicorn command
4. Set startup type to Automatic

---

## 🎉 Server Ready!

Once you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Your PhotoBrain query endpoint is live at:
**http://localhost:8090/photobrain/query** ✅

