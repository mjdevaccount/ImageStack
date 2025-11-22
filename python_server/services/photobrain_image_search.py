# python_server/services/photobrain_image_search.py

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from loguru import logger
from qdrant_client import QdrantClient

from ..models.photobrain_query_models import PhotoBrainSearchMatch
from ..models.photobrain_filters import PhotoBrainFilterRequest
from .photobrain_embedding import PhotoBrainEmbedder
from .photobrain_filters import apply_filters


class PhotoBrainImageSearchService:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: PhotoBrainEmbedder,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder

    def search(
        self,
        image_path: str,
        top_k: int = 12,
        filters: Optional[PhotoBrainFilterRequest] = None
    ) -> List[PhotoBrainSearchMatch]:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(path)

        logger.info(f"[PhotoBrain/Image] Similarity search for {path}, top_k={top_k}")

        vec = self.embedder.embed_image(str(path)).astype("float32").tolist()

        # Retrieve more results if filtering is requested
        # to compensate for filtered-out items
        retrieve_k = top_k * 3 if filters else top_k

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vec,
            limit=retrieve_k,
            with_payload=True,
        ).points

        matches: List[PhotoBrainSearchMatch] = []
        for r in results:
            payload = r.payload or {}
            matches.append(
                PhotoBrainSearchMatch(
                    id=str(r.id),
                    score=float(r.score),
                    filename=payload.get("filename") or "",
                    path_raw=payload.get("path_raw") or "",
                    path_processed=payload.get("path_processed"),
                    hash=payload.get("hash"),
                    ingested_at=payload.get("ingested_at"),
                    ocr_text=payload.get("ocr_text"),
                    ocr_confidence=payload.get("ocr_confidence"),
                    metadata=payload,
                )
            )

        # Apply filters
        filtered_matches = apply_filters(matches, filters)
        
        # Trim to requested top_k after filtering
        filtered_matches = filtered_matches[:top_k]

        logger.info(f"[PhotoBrain/Image] Found {len(filtered_matches)} matches (after filtering)")
        return filtered_matches

