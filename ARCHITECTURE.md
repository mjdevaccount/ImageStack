# ImageStack Architecture (Phase 0–1)

## Goals

- Simple, local-first vision server:
  - `/vision/describe` → natural language description via Ollama VLM
  - `/ocr/text`       → raw text via EasyOCR

## High-Level

```
Client / CLI
   ↓
FastAPI (`python_server/main.py`)
   ↓
Routers (`routers/vision.py`, `routers/ocr.py`)
   ↓
Services (`services/vision_service.py`, `services/ocr_service.py`)
   ↓
- Ollama HTTP API (for multimodal / vision)
- EasyOCR (for OCR)
```

## Future phases

- ImageRAG with Qdrant
- Image generation & editing (SDXL / FLUX)
- Multimodal workflows

