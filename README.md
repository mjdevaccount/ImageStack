# PhotoBrain / ImageStack

> **Local, autonomous visual memory system with multimodal AI**  
> *Your photos label themselves while you live your life* ✨

[![Version](https://img.shields.io/badge/version-0.5.1-blue.svg)](https://github.com/mjdevaccount/ImageStack)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

### 🆕 **Latest: Phase A.5b - Real-Time Watcher**
- **Instant Ingestion**: Drop images into inbox folders → auto-processed in seconds
- **Watchdog Integration**: Real-time file system monitoring (no polling!)
- **Auto-Organization**: Processed files moved to `processed/` subfolder
- **File Stability Detection**: Waits for writes to complete before processing
- **Duplicate Prevention**: SHA256 hash-based deduplication
- **Zero Config**: Default inbox at `C:\PhotoBrain\Inbox` (configurable)

### ✨ **Phase A.5 - Auto-Tagger**
- **12 Document Categories**: Receipts, invoices, whiteboards, serial plates, screenshots, and more
- **Auto-Generated Tags**: 3-10 searchable labels per image
- **Rich Filtering**: Date ranges, tags, OCR text, confidence, device, category
- **LLM-Powered Q&A**: *"What's the total on my last Home Depot receipt?"*

## 🎯 Overview

**PhotoBrain** (formerly ImageStack) is a production-grade, local-first visual memory system that combines:

- 🤖 **Vision AI** (Ollama llama3.2-vision:11b)
- 👁️ **OCR** (EasyOCR with GPU acceleration)
- 🎨 **Image Preprocessing** (OpenCV pipelines)
- 🧠 **Vector Embeddings** (OpenCLIP ViT-L-14)
- 🔍 **Semantic Search** (Qdrant vector database)
- 📁 **Auto-Ingestion** (Watch folders, detect changes)
- 🌐 **REST API** (FastAPI with async support)

**Key Differentiators:**
- ✅ **100% Local** - No cloud dependencies, complete privacy
- ✅ **GPU Accelerated** - CUDA support for OCR, embeddings, vision
- ✅ **Production Ready** - Comprehensive error handling, logging, monitoring
- ✅ **Autonomous** - Auto-ingests new images from watched folders
- ✅ **Multimodal** - Unified embeddings from images + OCR text

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [CLI Tools](#-cli-tools)
- [Use Cases](#-use-cases)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Roadmap](#-roadmap)

---

## 🚀 Features

### Core Capabilities

#### **Vision & Understanding**
- **Ollama Integration**: llama3.2-vision:11b for natural language image descriptions
- **OCR**: EasyOCR with GPU support, 80+ languages
- **EXIF Extraction**: Camera model, datetime, GPS, orientation
- **Preprocessing**: OpenCV pipelines for optimal OCR/vision quality
- **Auto-Tagging**: 🆕 Vision-powered automatic categorization into 12 document types
- **Auto-Labeling**: 🆕 Generates 3-10 searchable tags per image automatically

#### **Vector Search & Memory**
- **CLIP Embeddings**: OpenCLIP ViT-L-14 (768D vectors)
- **Multimodal**: Unified embeddings from image + OCR text
- **Qdrant Storage**: Fast vector similarity search
- **Deduplication**: SHA256 hashing prevents duplicate ingestion
- **Rich Filtering**: 🆕 9 filter types (date ranges, tags, OCR text, confidence, device, category)
- **LLM-Powered Q&A**: 🆕 Ask natural language questions about your image collection

#### **Autonomous Ingestion**
- **Real-Time Watcher**: 🆕 Instant ingestion using watchdog (inotify-based)
- **Background Daemon**: Polling-based ingestion with configurable intervals
- **Smart Detection**: mtime + hash-based change detection
- **File Stability**: Waits for writes to complete before ingesting
- **SQLite Index**: Track processed files, prevent re-ingestion
- **Auto-Classification**: Every image automatically categorized and tagged
- **Auto-Organization**: Moves processed files to `processed/` subfolder

#### **REST API**
- **FastAPI**: Modern async Python framework
- **OpenAPI Docs**: Interactive API documentation at `/docs`
- **CORS Enabled**: Cross-origin requests supported
- **Streaming**: Efficient file upload handling

#### **Developer Tools**
- **Debug Lab**: HTML viewer for preprocessing pipeline visualization
- **CLI Tools**: Command-line interface for all operations
  - `describe` - Vision AI descriptions
  - `ocr` - Text extraction
  - `find` - Semantic search
  - `ask` - LLM-powered Q&A
  - `watch` 🆕 - Real-time file watcher
- **Comprehensive Logs**: Structured logging with loguru
- **Health Checks**: Monitor system status

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         PhotoBrain System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐      ┌──────────────┐      ┌───────────────┐  │
│  │   Watched   │ ───> │  PhotoBrain  │ ───> │   ImageStack  │  │
│  │ Directories │      │   Ingestor   │      │   API Server  │  │
│  │ (Pictures)  │      │   (Daemon)   │      │ (FastAPI:8090)│  │
│  └─────────────┘      └──────────────┘      └───────────────┘  │
│         │                     │                       │          │
│         │ New Images          │ POST /photobrain/    │          │
│         │ Detected            │      ingest          │          │
│         ▼                     ▼                       ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Ingestion Pipeline                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  1. Save Raw Image + SHA256 Hash                        │  │
│  │  2. Image Preprocessing (OpenCV)                        │  │
│  │  3. OCR Extraction (EasyOCR)                           │  │
│  │  4. EXIF Metadata Extraction                           │  │
│  │  5. Auto-Tag & Categorize (Vision Model) 🆕           │  │
│  │  6. CLIP Embedding (image + text)                      │  │
│  │  7. Store in Qdrant Vector DB                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                │                                 │
│                                ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Search & Retrieval                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  • Visual Similarity (image → image)                    │   │
│  │  • Semantic Search (text → image)                       │   │
│  │  • OCR Text Search                                      │   │
│  │  • Rich Filtering (date, tags, category, device) 🆕    │   │
│  │  • LLM-Powered Q&A (RAG over images) 🆕                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

External Dependencies:
├── Ollama (llama3.2-vision:11b) - localhost:11434
└── Qdrant Vector DB              - localhost:6333
```

### Component Architecture

```
ImageStack/
├── python_server/          # FastAPI Application
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   │
│   ├── models/            # Pydantic Models
│   │   ├── image_models.py
│   │   └── photobrain_models.py
│   │
│   ├── routers/           # API Endpoints
│   │   ├── health.py          # /health
│   │   ├── vision.py          # /vision/*
│   │   ├── ocr.py             # /ocr/*
│   │   ├── rag_image.py       # /rag/*
│   │   ├── photobrain.py      # /photobrain/*
│   │   └── debug_preprocess.py # /debug/*
│   │
│   ├── services/          # Business Logic
│   │   ├── vision_service.py          # Ollama vision
│   │   ├── ocr_service.py             # EasyOCR
│   │   ├── image_preprocess.py        # OpenCV preprocessing
│   │   ├── photobrain_embedding.py    # CLIP embeddings
│   │   ├── photobrain_store.py        # Qdrant storage
│   │   ├── photobrain_autotag.py      # Auto-tagging 🆕
│   │   ├── photobrain_filters.py      # Filter logic 🆕
│   │   ├── photobrain_text_search.py  # Text search 🆕
│   │   ├── photobrain_image_search.py # Image search 🆕
│   │   ├── photobrain_query_service.py # LLM Q&A 🆕
│   │   └── photobrain_ingest_service.py # Unified pipeline
│   │
│   ├── rag/               # ImageRAG Module
│   │   ├── image_embedder.py
│   │   ├── image_store.py
│   │   ├── image_ingest_service.py
│   │   └── image_search_service.py
│   │
│   └── utils/             # Utilities
│       ├── image_io.py
│       └── logging_config.py
│
├── photobrain/            # Auto-Ingestion Daemon
│   ├── settings.py        # Configuration
│   ├── index_store.py     # SQLite file tracking
│   └── ingestor.py        # Watch/scan/ingest logic
│
├── cli/                   # Command-Line Tools
│   └── imagestack_cli.py  # describe, ocr commands
│
├── scripts/               # Helper Scripts
│   ├── start_api.ps1
│   ├── start_photobrain_ingestor.ps1
│   └── verify_setup.ps1
│
└── storage/               # Data Storage
    ├── images/            # Uploaded images
    └── ocr/               # OCR outputs
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **CUDA-capable GPU** (recommended for OCR/embeddings)
- **Docker** (for Qdrant)
- **Ollama** (for vision models)

### 5-Minute Setup

**Important:** Follow these steps IN ORDER to avoid issues.

```powershell
# 1. Clone repository
git clone https://github.com/mjdevaccount/ImageStack.git
cd ImageStack

# 2. Create virtual environment (REQUIRED - don't skip this!)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt
# Note: First run will download ~500MB of EasyOCR models

# 4. Start Qdrant (vector database) - MUST be running before starting API
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# Verify Qdrant is running:
curl http://localhost:6333

# 5. Start Ollama and pull vision model
# Make sure Ollama is running as a service, then:
ollama pull llama3.2-vision:11b
ollama pull phi4:14b

# 6. Start ImageStack API (from project root!)
.\scripts\start_api.ps1
# OR manually:
# python -m uvicorn python_server.main:app --host 0.0.0.0 --port 8090 --reload
```

**Test the API:**
```powershell
# Health check (should return {"status":"ok"})
curl http://localhost:8090/health/

# API documentation in browser
Start http://localhost:8090/docs
```

**Common Startup Issues:**
- ❌ **"No module named..."**: Virtual environment not activated or dependencies not installed
- ❌ **Connection refused (Qdrant)**: Start Qdrant with Docker first
- ❌ **Unicode encoding error**: Fixed in start script - use `.\scripts\start_api.ps1`
- ❌ **Import error with config**: Make sure you're running from the project root directory

### First Image Ingestion

**⚠️ You MUST ingest at least one image before using query features!**

**Make sure the server is running first!** (See above)

#### Option 1: Upload Single Image via API

```powershell
# Upload any image (replace path with your image)
curl -F "file=@C:\Photos\test.jpg" http://localhost:8090/photobrain/ingest

# Expected response: JSON with image metadata, tags, and embedding confirmation
```

#### Option 2: Use Interactive API Docs

1. Open browser: http://localhost:8090/docs
2. Navigate to **POST /photobrain/ingest**
3. Click "Try it out"
4. Upload a test image
5. Click "Execute"

#### Option 3: Batch Ingest from Directory

```powershell
# Activate venv first
.\.venv\Scripts\Activate.ps1

# Set watch directory (where your images are)
$env:PHOTOBRAIN_WATCH_DIRS="C:\Users\Matt\Pictures"

# Run single scan
python -m photobrain.ingestor once

# Or start continuous watcher
python -m photobrain.ingestor run
```

#### Verify Images Were Ingested

```powershell
# Check Qdrant database
curl http://localhost:6333/collections/photobrain
# Look for: "points_count": <number greater than 0>

# Or check via API
Invoke-WebRequest -Uri "http://localhost:8090/photobrain/search/text" -Method POST -ContentType "application/json" -Body '{"query": "anything", "top_k": 5}'
```

---

## 📦 Installation

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 10 GB free space
- Python: 3.10+

**Recommended:**
- CPU: 8+ cores
- RAM: 16 GB+
- GPU: NVIDIA with 6GB+ VRAM (CUDA 11.8+)
- Disk: SSD with 50 GB+ free space
- Python: 3.11+

### Detailed Installation

#### 1. Create Virtual Environment (CRITICAL STEP!)

```powershell
# From project root (C:\ImageStack)
python -m venv .venv

# Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux/Mac
# source .venv/bin/activate
```

**⚠️ Important:** Always activate the virtual environment before running any Python commands!

#### 2. Install Python Dependencies

```powershell
# Make sure venv is activated first!
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi==0.115.0` - Web framework
- `uvicorn==0.30.6` - ASGI server
- `open_clip_torch>=2.24.0` - CLIP embeddings
- `qdrant-client>=1.7.0` - Vector database client
- `easyocr==1.7.2` - OCR engine
- `opencv-python-headless>=4.10.0.0` - Image preprocessing
- `torch>=2.2.0` - Deep learning framework
- `httpx==0.27.2` - HTTP client for Ollama

**Note:** First install will download large ML models (~2GB total)

#### 3. Install Ollama

**Windows:**
```powershell
# Download from https://ollama.com/download
# Or use winget
winget install Ollama.Ollama
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Pull Vision Models:**
```bash
ollama pull llama3.2-vision:11b  # Primary vision model
ollama pull moondream            # Optional: Faster, lighter model
```

#### 4. Install Qdrant

**Docker (Recommended):**
```powershell
# Windows/Linux/Mac
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# With persistent storage (optional):
# docker run -d -p 6333:6333 -p 6334:6334 -v ${PWD}/qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
```

**Verify Qdrant is running:**
```powershell
curl http://localhost:6333
# Should return Qdrant version info
```

**Binary Installation (Alternative):**
```bash
# Download from https://github.com/qdrant/qdrant/releases
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-pc-windows-msvc.zip
unzip qdrant-x86_64-pc-windows-msvc.zip
./qdrant
```

#### 5. Verify Installation

```powershell
# Run verification script
.\scripts\verify_setup.ps1

# Or manual checks
.\.venv\Scripts\Activate.ps1  # Activate venv first!
python --version          # Should be 3.10+
ollama list              # Should show llama3.2-vision:11b
curl http://localhost:6333  # Qdrant should respond
docker ps | Select-String "qdrant"  # Qdrant container should be running
```

---

## 🚀 How to Start the Server

### Prerequisites Checklist

Before starting, verify these are running:

```powershell
# 1. Check Qdrant is running
docker ps | Select-String "qdrant"
# If not running: docker start qdrant
# If doesn't exist: docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# 2. Check Ollama has models
ollama list
# Should show: llama3.2-vision:11b and phi4:14b
# If missing: ollama pull llama3.2-vision:11b && ollama pull phi4:14b

# 3. Check virtual environment exists
Test-Path .\.venv\Scripts\Activate.ps1
# Should return: True
# If False: python -m venv .venv
```

### Starting the Server

**Option 1: Use the Start Script (Recommended)**
```powershell
cd C:\ImageStack
.\scripts\start_api.ps1
```

**Option 2: Manual Start**
```powershell
cd C:\ImageStack
.\.venv\Scripts\Activate.ps1
python -m uvicorn python_server.main:app --host 0.0.0.0 --port 8090 --reload
```

**Verify it's running:**
```powershell
# Wait ~10 seconds for models to load, then:
curl http://localhost:8090/health/
# Should return: {"status":"ok"}
```

**⚠️ IMPORTANT: Before Using Query Features**

The server will return **500 errors** on query endpoints until you ingest at least one image:

```powershell
# Quick test with any image
curl -F "file=@C:\path\to\photo.jpg" http://localhost:8090/photobrain/ingest

# Or use the browser: http://localhost:8090/docs
# Navigate to POST /photobrain/ingest and upload a test image

# Verify it worked:
curl http://localhost:6333/collections/photobrain
# Should show: "points_count": 1 or more
```

See [First Image Ingestion](#first-image-ingestion) section below for more details.

### Stopping the Server

```powershell
# If running in terminal: Press CTRL+C

# Or kill the process:
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

### Restarting the Server

```powershell
# Stop it first
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Wait a moment
Start-Sleep -Seconds 2

# Start again
.\scripts\start_api.ps1
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# ImageStack API Configuration
IMAGESTACK_OLLAMA_BASE_URL=http://localhost:11434
IMAGESTACK_VISION_MODEL=llama3.2-vision:11b
IMAGESTACK_OCR_MODEL=moondream
IMAGESTACK_PHOTOBRAIN_QA_MODEL=phi4:14b
IMAGESTACK_PHOTOBRAIN_AUTOTAG_MODEL=llama3.2-vision:11b  # Optional, defaults to vision_model
IMAGESTACK_STORAGE_DIR=./storage
IMAGESTACK_QDRANT_URL=http://localhost:6333
IMAGESTACK_QDRANT_API_KEY=  # Empty for local
IMAGESTACK_CLIP_MODEL=ViT-L-14
IMAGESTACK_CLIP_PRETRAINED=openai
IMAGESTACK_EMBEDDING_DIM=768

# PhotoBrain Auto-Ingestor Configuration
PHOTOBRAIN_BASE_URL=http://localhost:8090
PHOTOBRAIN_API_BASE=http://localhost:8090  # For real-time watcher
PHOTOBRAIN_WATCH_DIRS=C:\Users\Matt\Pictures;C:\Users\Matt\Downloads
PHOTOBRAIN_POLL_INTERVAL=30  # seconds (for daemon mode)
PHOTOBRAIN_INDEX_DB=~/.photobrain/index.db
```

### Configuration File

Edit `python_server/config.py` for code-based configuration:

```python
class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    vision_model: str = "llama3.2-vision:11b"
    ocr_model: str = "moondream"
    storage_dir: str = "../storage"
    
    # RAG / Vector Store
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    clip_model: str = "ViT-L-14"
    clip_pretrained: str = "openai"
    embedding_dim: int = 768
    
    # PhotoBrain AI
    photobrain_qa_model: str = "phi4:14b"
    photobrain_autotag_model: str = "llama3.2-vision:11b"

    class Config:
        env_prefix = "IMAGESTACK_"
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8090
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8090/docs
- **ReDoc**: http://localhost:8090/redoc

### Core Endpoints

#### **Health & Status**

```http
GET /health/
```
Returns system health status.

**Response:**
```json
{
  "status": "ok"
}
```

---

#### **PhotoBrain Ingestion**

```http
POST /photobrain/ingest?ocr=true&preprocess=true&embed=true&auto_tag=true
Content-Type: multipart/form-data

file: <image file>
```

**Parameters:**
- `ocr` (bool): Run OCR text extraction (default: true)
- `vision` (bool): Vision-focused preprocessing (default: false)
- `preprocess` (bool): Apply image preprocessing (default: true)
- `embed` (bool): Generate and store CLIP embedding (default: true)
- `auto_tag` (bool): 🆕 Auto-categorize and generate tags (default: true)

**Response:**
```json
{
  "id": "7e3c1b7f5f1c4e0b8d44e3c1a0e4f9ff",
  "filename": "receipt.jpg",
  "path_raw": "/storage/images/img_20251121_032500.jpg",
  "path_processed": "/storage/images/img_20251121_032500_proc_ocr.jpg",
  "hash": "a7f8e9d2c3b4a5f6...",
  "ocr_text": "HOME DEPOT\nRECEIPT\nTotal: $45.99",
  "ocr_confidence": 0.87,
  "embedded": true,
  "timestamp": "2025-11-21T03:25:00.123456+00:00",
  "metadata": {
    "category": "receipt",
    "tags": ["home depot", "receipt", "hardware", "purchase", "tools"],
    "autotag": {
      "model": "llama3.2-vision:11b",
      "confidence": 0.92,
      "raw": {"category": "receipt", "tags": [...], "confidence": 0.92}
    },
    "exif": {
      "datetime_original": "2025:11:20 15:30:00",
      "device_model": "iPhone 14",
      "device_make": "Apple"
    }
  }
}
```

**Auto-Tag Categories:**
- `receipt`, `invoice`, `id_card`, `serial_plate`, `document`, `form`
- `handwritten_notes`, `whiteboard`, `screenshot`, `info_card`
- `photo_of_object`, `other`

---

#### **Vision Description**

```http
POST /vision/describe?preprocess=false
Content-Type: multipart/form-data

file: <image file>
```

**Response:**
```json
{
  "description": "A sunset over mountains with orange and purple hues...",
  "tags": ["sunset", "mountains", "landscape", "nature"],
  "model": "llama3.2-vision:11b",
  "raw": "Full model response..."
}
```

---

#### **OCR Text Extraction**

```http
POST /ocr/text?preprocess=true
Content-Type: multipart/form-data

file: <image file>
```

**Response:**
```json
{
  "text": "HOME DEPOT\nRECEIPT #12345\nDate: 11/20/2025\nTotal: $45.99",
  "language": "en",
  "confidence": 0.92
}
```

---

#### **PhotoBrain Text Search** 🆕

```http
POST /photobrain/search/text
Content-Type: application/json

{
  "query": "home depot receipt",
  "top_k": 12,
  "filters": {
    "category": "receipt",
    "days": 30,
    "contains_text": "home depot",
    "confidence_min": 0.7
  }
}
```

**Request Body:**
- `query` (string): Natural language search query
- `top_k` (int): Number of results (default: 12, max: 50)
- `filters` (object, optional): Server-side filters
  - `days` (int): Last N days (relative filter)
  - `date_min` / `date_max` (datetime): Absolute date ranges
  - `tag` (string): Single tag substring match
  - `tags` (array): AND match all tags
  - `contains_text` (string): OCR text substring
  - `confidence_min` (float): Minimum OCR confidence (0-1)
  - `device` (string): Device model substring
  - `category` (string): Document category

**Response:**
```json
{
  "matches": [
    {
      "id": "abc123",
      "score": 0.94,
      "filename": "receipt_homedepot_2025.jpg",
      "path_raw": "/storage/images/receipt.jpg",
      "hash": "sha256...",
      "ingested_at": "2025-11-21T10:30:00Z",
      "ocr_text": "HOME DEPOT\nTotal: $45.99",
      "ocr_confidence": 0.91,
      "metadata": {
        "category": "receipt",
        "tags": ["home depot", "hardware", "receipt"],
        "exif": {...}
      }
    }
  ]
}
```

---

#### **PhotoBrain Image Search** 🆕

```http
POST /photobrain/search/image?top_k=12
Content-Type: multipart/form-data

file: <query image>
```

**Parameters:**
- `top_k` (int): Number of results (default: 12, max: 50)

**Response:** Same format as text search (visual similarity)

---

#### **PhotoBrain LLM Q&A** 🆕

```http
POST /photobrain/query
Content-Type: application/json

{
  "question": "What is the total on my last Home Depot receipt?",
  "top_k": 8,
  "filters": {
    "category": "receipt",
    "days": 90
  }
}
```

**Request Body:**
- `question` (string): Natural language question
- `top_k` (int): Number of images to retrieve (default: 8)
- `filters` (object, optional): Same as text search

**Response:**
```json
{
  "answer": "The total on your Home Depot receipt from November 20, 2025 is $45.99.",
  "matches": [
    {
      "id": "abc123",
      "score": 0.94,
      "filename": "receipt_homedepot.jpg",
      "ocr_text": "HOME DEPOT\nTotal: $45.99",
      "metadata": {...}
    }
  ],
  "raw_answer": "Full LLM response..."
}
```

---

#### **Debug Preprocessing Lab**

```http
POST /debug/preprocess
Content-Type: multipart/form-data

file: <image file>
```

**Returns:** ZIP file containing:
- `original.jpg` - Raw uploaded image
- `ocr/` - OCR pipeline stages (5 images)
- `vision/` - Vision pipeline stages (2 images)
- `metadata.json` - Complete metadata
- `viewer.html` - Interactive browser viewer

---

## 🖥️ CLI Tools

### ImageStack CLI

**Describe Image:**
```powershell
python -m cli.imagestack_cli describe path/to/image.jpg
```

**OCR with Preprocessing:**
```powershell
python -m cli.imagestack_cli ocr path/to/receipt.jpg --preprocess
```

**Semantic Search** 🆕
```powershell
# Search your entire image memory
python -m cli.imagestack_cli find "home depot receipt"

# With filters
python -m cli.imagestack_cli find "serial number" --tag generator --days 30
```

**Ask Questions (LLM Q&A)** 🆕
```powershell
# Ask natural language questions
python -m cli.imagestack_cli ask "What is the total on my last Home Depot receipt?"

# With filters
python -m cli.imagestack_cli ask "Show me my generator's serial number" --top-k 5
```

**Real-Time Watcher** 🆕
```powershell
# Start real-time file watcher
python -m cli.imagestack_cli watch

# Or use launcher scripts
.\scripts\start_photobrain_watcher.ps1  # PowerShell
.\scripts\start_photobrain_watcher.bat  # CMD

# Configure watch directories
$env:PHOTOBRAIN_WATCH_DIRS="C:\PhotoBrain\Inbox,C:\Screenshots"
$env:PHOTOBRAIN_API_BASE="http://localhost:8090"
python -m cli.imagestack_cli watch
```

**CLI Filters:**
- `--days N`: Last N days
- `--tag TAG`: Filter by tag (substring match)
- `--top-k N`: Number of results (for `ask`)

### PhotoBrain Ingestor (Polling Daemon)

**Single Scan:**
```powershell
python -m photobrain.ingestor once
```

**Daemon Mode:**
```powershell
python -m photobrain.ingestor run

# Or use launcher scripts
.\scripts\start_photobrain_ingestor.ps1  # PowerShell
.\scripts\start_photobrain_ingestor.bat  # CMD
```

**Configuration:**
```powershell
# Custom watch directories
$env:PHOTOBRAIN_WATCH_DIRS="C:\Photos;D:\Screenshots"
python -m photobrain.ingestor run

# Faster polling
$env:PHOTOBRAIN_POLL_INTERVAL="10"
python -m photobrain.ingestor run
```

---

## 💡 Use Cases

### Personal Photo Library Management
- **Auto-ingest** photos from phone/camera imports
- **Auto-categorize** into document types (photos, screenshots, receipts)
- **Auto-tag** with searchable labels
- Search photos by visual similarity or text description
- Filter by date, device, tags: *"beach photos from iPhone, last 30 days"*
- **Ask questions**: *"Show me all sunset photos from my vacation"*

### Document & Receipt Organization
- **Auto-OCR** receipts dropped in Downloads
- **Auto-categorize** as receipts, invoices, or documents
- **Auto-tag** with merchant names, document types
- Search by merchant, amount, or date
- Filter by category and confidence: *"high-quality receipt scans from Home Depot"*
- **Ask questions**: *"What's the total on my last utility bill?"*

### Screenshot Archive & Search
- **Auto-capture** and index screenshots
- **Auto-categorize** as screenshots vs other image types
- OCR extracts all text automatically
- Search by content: *"error message about database connection"*
- Filter by date and text: *"screenshots from last week containing 'API'"*
- **Ask questions**: *"Show me the error I saw yesterday"*

### Technical Documentation & Diagrams
- **Auto-categorize** whiteboards, handwritten notes, diagrams
- **Auto-tag** serial plates, equipment labels
- Search: *"generator serial number plate"*
- Filter by category: *"all whiteboard photos from last month"*
- **Ask questions**: *"What's my HVAC unit's model number?"*

### Research & Image Collection
- Build searchable image databases with **automatic tagging**
- Find visually similar images
- Semantic search with rich filters
- **Ask questions** over entire collection
- Category-based organization (documents, photos, diagrams)

---

## 🛠️ Development

### Project Structure

Following **SOLID principles**:
- ✅ Single Responsibility
- ✅ Open/Closed
- ✅ Liskov Substitution
- ✅ Interface Segregation
- ✅ Dependency Injection

### Running Tests

```powershell
# Run health check test
pytest python_server/tests/test_health.py

# Run all tests (when more are added)
pytest python_server/tests/
```

### Code Style

```powershell
# Format code
black python_server/ photobrain/ cli/

# Lint
pylint python_server/ photobrain/ cli/

# Type checking
mypy python_server/ photobrain/ cli/
```

### Adding New Features

1. **New Service**: Add to `python_server/services/`
2. **New Endpoint**: Add router to `python_server/routers/`
3. **New Model**: Add Pydantic model to `python_server/models/`
4. **Register Router**: Update `python_server/main.py`
5. **Test**: Add tests to `python_server/tests/`
6. **Document**: Update this README

---

## 🔧 Troubleshooting

### Common Issues

#### **Virtual Environment Not Found**
```
Error: .venv\Scripts\python.exe not found
```

**Solution:**
```powershell
# Create the virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### **Qdrant Connection Failed**
```
Error: Connection to Qdrant failed
Error: [WinError 10061] No connection could be made
```

**Solution:**
```powershell
# Check if Qdrant is running
docker ps | Select-String "qdrant"

# If not running, start it:
docker start qdrant

# If container doesn't exist:
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# Verify it's working:
curl http://localhost:6333
```

#### **Ollama Model Not Found**
```
Error: Model llama3.2-vision:11b not found
```

**Solution:**
```powershell
ollama pull llama3.2-vision:11b
ollama pull phi4:14b
ollama list  # Verify installation
```

#### **Import Errors / Config Not Found**
```
ImportError: cannot import name 'settings' from 'python_server.config'
```

**Solution:**
```powershell
# Make sure you're running from the project root:
cd C:\ImageStack

# Use the start script (fixes paths automatically):
.\scripts\start_api.ps1
```

#### **Unicode/Encoding Errors**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution:**
```powershell
# Use the provided start script (has encoding fixes):
.\scripts\start_api.ps1

# Or set encoding manually:
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

#### **Query Endpoints Return 500 Internal Server Error**
```
POST /photobrain/query -> 500 Internal Server Error
POST /photobrain/search/text -> 500 Internal Server Error
```

**Cause:** No images have been ingested into the database yet.

**Solution:**
```powershell
# Check if database is empty
curl http://localhost:6333/collections/photobrain
# If "points_count": 0, you need to ingest images

# Upload a test image
curl -F "file=@C:\Photos\test.jpg" http://localhost:8090/photobrain/ingest

# Or use the interactive API docs
Start http://localhost:8090/docs
# Navigate to POST /photobrain/ingest and upload an image

# Verify it worked
curl http://localhost:6333/collections/photobrain
# Should now show "points_count": 1 or more

# Now queries should work
Invoke-WebRequest -Uri "http://localhost:8090/photobrain/query" -Method POST -ContentType "application/json" -Body '{"question": "What images do I have?", "top_k": 5}'
```

#### **CUDA Out of Memory**
```
RuntimeError: CUDA out of memory
```

**Solution:**
- Reduce batch size in config
- Use smaller CLIP model: `ViT-B-32` instead of `ViT-L-14`
- Process images sequentially
- Reduce image resolution in preprocessing

#### **EasyOCR Initialization Slow**
```
Taking minutes to load...
```

**Solution:**
- First run downloads models (~500MB)
- Subsequent runs are faster
- Models cached in `~/.EasyOCR/`

#### **PhotoBrain Not Finding Images**
```
Scan completed, ingested=0
```

**Solution:**
```powershell
# Check watch directories exist
$env:PHOTOBRAIN_WATCH_DIRS="C:\Users\Matt\Pictures"

# Verify permissions
# Check supported formats: .jpg, .jpeg, .png, .webp, .tif, .tiff
```

### Performance Tuning

**Slow Ingestion:**
- Enable GPU: `CUDA_VISIBLE_DEVICES=0`
- Disable preprocessing: `?preprocess=false`
- Disable OCR: `?ocr=false`
- Reduce poll interval: `PHOTOBRAIN_POLL_INTERVAL=60`

**High Memory Usage:**
- Reduce CLIP model size
- Process images sequentially
- Enable garbage collection
- Restart services periodically

**Disk Space Issues:**
- Clean old processed images
- Compress storage directory
- Use external storage for images
- Implement retention policies

---

## 📊 Performance

### Benchmarks

**Hardware**: NVIDIA RTX 3080, AMD Ryzen 9 5900X, 32GB RAM

| Operation | Time | Throughput |
|-----------|------|------------|
| OCR (EasyOCR) | ~1.5s | 40 images/min |
| CLIP Embedding | ~0.05s | 1200 images/min |
| Image Preprocessing | ~0.3s | 200 images/min |
| Vision Description | ~2s | 30 images/min |
| Full Ingestion Pipeline | ~3s | 20 images/min |
| Vector Search (1000 images) | <10ms | 100+ queries/sec |

### Optimization Tips

1. **GPU Acceleration**: Ensure CUDA is properly configured
2. **Batch Processing**: Process multiple images in parallel
3. **Model Caching**: Keep models in memory between requests
4. **Preprocessing**: Disable for already clean images
5. **Vector Indexing**: Qdrant automatically optimizes indices

---

## 🗺️ Roadmap

### ✅ Completed (v0.5.1)
- [x] **Phase 0-1**: Ollama vision integration + EasyOCR with GPU
- [x] **Phase 1.5**: OpenCV preprocessing pipelines + debug lab
- [x] **Phase A.1**: Autonomous file watching daemon (polling)
- [x] **Phase A.2**: Enhanced ingestion (CLIP + Qdrant + EXIF + OCR)
- [x] **Phase A.3**: Query API (text search, image search, LLM Q&A)
- [x] **Phase A.4**: Rich server-side filters (9 filter types)
- [x] **Phase A.5**: Auto-tagging & categorization (12 document types)
- [x] **Phase A.5b**: Real-time file watcher (watchdog/inotify)
- [x] Multimodal embeddings (image + text)
- [x] CLI tools (describe, ocr, find, ask, watch)
- [x] Deduplication (SHA256 + mtime tracking)
- [x] Auto-organization (processed/failed subfolders)

### 🚧 In Progress (v0.6.0)
- [ ] Web dashboard UI (React + real-time updates)
- [ ] Batch operations API
- [ ] Export/import collections
- [ ] Image editing & cropping in debug lab
- [ ] Windows tray icon for watcher

### 🔮 Near Future (v0.7.0 - v0.9.0)
- [ ] Face detection & clustering (OpenCV/dlib)
- [ ] Advanced deduplication (perceptual hashing with pHash)
- [ ] Custom category training (fine-tune auto-tagger)
- [ ] Audio transcription for video files (Whisper)
- [ ] Object detection & tagging (YOLO/DETR)
- [ ] Geo-tagging & interactive maps
- [ ] Collections & smart albums
- [ ] PDF ingestion & per-page indexing
- [ ] Duplicate image detection & merging

### 🔮 Long-Term (v1.0.0+)
- [ ] Mobile app (iOS/Android with photo sync)
- [ ] Distributed ingestion (multi-node Qdrant cluster)
- [ ] Video frame extraction & indexing
- [ ] Advanced privacy features (on-device encryption)
- [ ] Sharing & collaboration (secure links)
- [ ] Cloud backup integration (S3/B2 compatible)
- [ ] Plugin system for custom processors
- [ ] Multi-user support with permissions

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

---

## 📧 Support

- **Issues**: https://github.com/mjdevaccount/ImageStack/issues
- **Discussions**: https://github.com/mjdevaccount/ImageStack/discussions
- **Email**: [Your contact email]

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Ollama](https://ollama.com/) - Local LLM runtime
- [OpenCLIP](https://github.com/mlfoundations/open_clip) - CLIP embeddings
- [Qdrant](https://qdrant.tech/) - Vector database
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR engine
- [OpenCV](https://opencv.org/) - Image processing

---

## 📊 Project Stats

- **Version**: 0.5.1
- **Python**: 3.10+
- **Lines of Code**: ~5000+
- **API Endpoints**: 10+
- **Dependencies**: 15+
- **Platforms**: Windows, Linux, macOS

## 🔧 Recent Critical Fixes (v0.5.1)

**If you cloned this repo before November 22, 2025, please note these critical fixes:**

1. **Start Script Now Uses Virtual Environment**
   - `scripts/start_api.ps1` now explicitly uses `.venv\Scripts\python.exe`
   - Fixes "ModuleNotFoundError" issues

2. **Storage Path Fixed**
   - Changed from relative `"../storage"` to absolute path in `config.py`
   - Prevents images being saved to wrong location

3. **EXIF Serialization Fixed**
   - PIL `IFDRational` types now properly converted to JSON-serializable floats
   - Fixes "PydanticSerializationError" on image upload

4. **Config Import Fixed**
   - `python_server/config/__init__.py` now properly exposes `settings`
   - Resolves import conflicts between `config.py` and `config/` directory

5. **UTF-8 Encoding**
   - Start script sets `PYTHONIOENCODING=utf-8` to handle Unicode progress bars
   - Prevents crashes during EasyOCR model downloads

**To update your installation:**
```powershell
git pull
# Restart your server - the fixes are automatic
.\scripts\start_api.ps1
```

---

**Made with ❤️ for the local-first AI community**

*Keep your visual memories private, searchable, and under your control.*

