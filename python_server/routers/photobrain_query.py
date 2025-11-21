# python_server/routers/photobrain_query.py

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from loguru import logger
from qdrant_client import QdrantClient

from ..config import settings
from ..models.photobrain_query_models import (
    PhotoBrainImageSearchResponse,
    PhotoBrainQaRequest,
    PhotoBrainQaResponse,
    PhotoBrainTextSearchRequest,
    PhotoBrainTextSearchResponse,
)
from ..services.photobrain_embedding import PhotoBrainEmbedder
from ..services.photobrain_image_search import PhotoBrainImageSearchService
from ..services.photobrain_query_service import PhotoBrainQueryService
from ..services.photobrain_text_search import PhotoBrainTextSearchService
from ..utils.image_io import save_temp_image


router = APIRouter()

# --- Shared clients / services ----------------------------------------------

QDRANT_URL = getattr(settings, "qdrant_url", None) or os.getenv(
    "QDRANT_URL", "http://localhost:6333"
)
QDRANT_API_KEY = getattr(settings, "qdrant_api_key", None) or os.getenv(
    "QDRANT_API_KEY", None
)

logger.info(f"[PhotoBrain/Query] Using Qdrant URL: {QDRANT_URL}")

_qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

_embedder = PhotoBrainEmbedder()
_COLLECTION = "photobrain"

_text_service = PhotoBrainTextSearchService(
    client=_qdrant_client,
    collection_name=_COLLECTION,
    embedder=_embedder,
)

_image_service = PhotoBrainImageSearchService(
    client=_qdrant_client,
    collection_name=_COLLECTION,
    embedder=_embedder,
)

_query_service = PhotoBrainQueryService(
    client=_qdrant_client,
    collection_name=_COLLECTION,
    embedder=_embedder,
)


# --- Routes ------------------------------------------------------------------


@router.post("/search/text", response_model=PhotoBrainTextSearchResponse)
async def photobrain_search_text(req: PhotoBrainTextSearchRequest) -> PhotoBrainTextSearchResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    matches = _text_service.search(req.query, top_k=req.top_k)
    return PhotoBrainTextSearchResponse(matches=matches)


@router.post("/search/image", response_model=PhotoBrainImageSearchResponse)
async def photobrain_search_image(
    file: UploadFile = File(...),
    top_k: int = Query(8, ge=1, le=50),
) -> PhotoBrainImageSearchResponse:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    saved_path = await save_temp_image(file)
    logger.info(f"[PhotoBrain/Query] Image search input saved at {saved_path}")

    matches = _image_service.search(saved_path, top_k=top_k)
    try:
        Path(saved_path).unlink(missing_ok=True)
    except Exception as ex:
        logger.warning(f"[PhotoBrain/Query] Failed to delete temp image {saved_path}: {ex}")

    return PhotoBrainImageSearchResponse(matches=matches)


@router.post("/query", response_model=PhotoBrainQaResponse)
async def photobrain_query(req: PhotoBrainQaRequest) -> PhotoBrainQaResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    return await _query_service.answer_question(req.question, top_k=req.top_k)

