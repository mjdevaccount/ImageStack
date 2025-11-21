# ImageStack

Local multimodal / vision server for your home AI setup.

## Features (Phase 0–1)

- 🖼️ Image description via Ollama vision (e.g. `llama3.2-vision:11b`)
- 📄 OCR text extraction using EasyOCR (GPU-friendly)
- 🌐 FastAPI HTTP API
- 🖥️ Tiny CLI wrapper (`imagestack`) for quick use

## Quick Start

```bash
# from repo root
python -m venv .venv
source .venv/bin/activate   # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the API:

```bash
cd python_server
uvicorn main:app --reload --port 8090
```

Describe an image:

```bash
python -m cli.imagestack_cli describe path/to/image.jpg
```

OCR an image:

```bash
python -m cli.imagestack_cli ocr path/to/image.jpg
```

The server expects Ollama running with a vision-capable model:

```bash
ollama serve
ollama pull llama3.2-vision:11b
ollama pull moondream
```

