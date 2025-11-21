# python_server/routers/photobrain.py

from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from loguru import logger
from qdrant_client import QdrantClient

from ..config import settings  # existing config
from ..models.photobrain_models import PhotoBrainIngestResponse
from ..services.photobrain_embedding import PhotoBrainEmbedder
from ..services.photobrain_store import PhotoBrainStore, PhotoBrainStoreConfig
from ..services.photobrain_ingest_service import PhotoBrainIngestService
from ..services.photobrain_autotag import PhotoBrainAutoTagger


router = APIRouter()

# --- Singletons / globals ----------------------------------------------------

# Qdrant config: prefer settings, fall back to env, then localhost
QDRANT_URL = getattr(settings, "qdrant_url", None) or os.getenv(
    "QDRANT_URL", "http://localhost:6333"
)
QDRANT_API_KEY = getattr(settings, "qdrant_api_key", None) or os.getenv(
    "QDRANT_API_KEY", None
)

logger.info(f"[PhotoBrain] Qdrant URL: {QDRANT_URL}")

_qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

_embedder = PhotoBrainEmbedder()
_store_config = PhotoBrainStoreConfig(
    collection_name="photobrain",
    vector_size=_embedder.dim,
)
_store = PhotoBrainStore(_qdrant_client, _store_config)
_auto_tagger = PhotoBrainAutoTagger()
_ingest_service = PhotoBrainIngestService(_embedder, _store, auto_tagger=_auto_tagger)


# --- Routes ------------------------------------------------------------------


@router.post("/ingest", response_model=PhotoBrainIngestResponse)
async def photobrain_ingest(
    file: UploadFile = File(...),
    ocr: bool = Query(True, description="Run OCR via EasyOCR"),
    vision: bool = Query(
        False,
        description="Hint that this is for vision/VQA; may control preprocessing choices",
    ),
    preprocess: bool = Query(
        True,
        description="Run preprocessing (orientation, resize, contrast, etc.)",
    ),
    embed: bool = Query(True, description="Store CLIP embedding in Qdrant"),
    auto_tag: bool = Query(
        True,
        description="Enable automatic tagging/category classification",
    ),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    return await _ingest_service.ingest_image(
        file=file,
        ocr=ocr,
        vision=vision,
        preprocess=preprocess,
        embed=embed,
        auto_tag=auto_tag,
    )

