# python_server/routers/rag_image.py

from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Optional, List
from loguru import logger

from ..config import settings
from ..rag import (
    ImageEmbedder,
    ImageVectorStore,
    ImageIngestService,
    ImageSearchService,
)

router = APIRouter()

# Singleton instances (lazy-loaded)
_embedder = None
_store = None
_ingest_service = None
_search_service = None


def _get_embedder():
    """Lazy-load embedder to avoid startup penalty."""
    global _embedder
    if _embedder is None:
        logger.info("[RAG] Initializing CLIP embedder...")
        _embedder = ImageEmbedder(
            model_name=settings.clip_model,
            pretrained=settings.clip_pretrained,
        )
    return _embedder


def _get_store():
    """Lazy-load vector store."""
    global _store
    if _store is None:
        from qdrant_client import QdrantClient
        logger.info(f"[RAG] Connecting to Qdrant at {settings.qdrant_url}")
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )
        _store = ImageVectorStore(client=client, dim=settings.embedding_dim)
    return _store


def _get_ingest_service():
    """Get or create ingest service."""
    global _ingest_service
    if _ingest_service is None:
        _ingest_service = ImageIngestService(
            store=_get_store(),
            embedder=_get_embedder(),
        )
    return _ingest_service


def _get_search_service():
    """Get or create search service."""
    global _search_service
    if _search_service is None:
        _search_service = ImageSearchService(
            store=_get_store(),
            embedder=_get_embedder(),
        )
    return _search_service


@router.post("/image", summary="Ingest an image into RAG")
async def rag_ingest_image(
    file: UploadFile = File(...),
    extract_ocr: bool = Query(True, description="Extract OCR text"),
    tags: Optional[List[str]] = Query(None, description="User-supplied tags"),
):
    """
    Upload and ingest an image into the RAG system.
    
    Returns:
        - id: Unique image ID
        - hash: SHA256 hash
        - ocr_text: Extracted text (if enabled)
        - tags: Associated tags
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    ingest_service = _get_ingest_service()
    return await ingest_service.ingest(file, extract_ocr=extract_ocr, tags=tags or [])


@router.post("/search/image", summary="Search by visual similarity")
async def rag_search_image(
    file: UploadFile = File(...),
    limit: int = Query(5, ge=1, le=50, description="Number of results"),
):
    """
    Find visually similar images using image-to-image search.
    
    Returns:
        List of similar images with scores and metadata.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    search_service = _get_search_service()
    return await search_service.search_by_image(file, limit=limit)


@router.post("/search/text", summary="Search by text description")
async def rag_search_text(
    query: str = Query(..., description="Text query (e.g. 'sunset over mountains')"),
    limit: int = Query(5, ge=1, le=50, description="Number of results"),
):
    """
    Find images matching a text description using semantic search.
    
    Returns:
        List of matching images with scores and metadata.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    search_service = _get_search_service()
    return await search_service.search_by_text(query, limit=limit)


@router.get("/health", summary="RAG system health check")
async def rag_health():
    """Check if RAG system is initialized and operational."""
    try:
        store = _get_store()
        return {
            "status": "ok",
            "qdrant_url": settings.qdrant_url,
            "collection": store.COLLECTION,
            "embedding_dim": settings.embedding_dim,
        }
    except Exception as ex:
        logger.error(f"[RAG] Health check failed: {ex}")
        raise HTTPException(status_code=503, detail=f"RAG system unavailable: {str(ex)}")

