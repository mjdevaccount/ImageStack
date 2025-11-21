# python_server/services/photobrain_text_search.py

from __future__ import annotations

from typing import List

from loguru import logger
from qdrant_client import QdrantClient

from ..models.photobrain_query_models import PhotoBrainSearchMatch
from .photobrain_embedding import PhotoBrainEmbedder


class PhotoBrainTextSearchService:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: PhotoBrainEmbedder,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder

    def search(self, query: str, top_k: int = 8) -> List[PhotoBrainSearchMatch]:
        logger.info(f"[PhotoBrain/Text] Searching for: {query!r}, top_k={top_k}")

        vec = self.embedder.embed_text(query).astype("float32").tolist()

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vec,
            limit=top_k,
            with_payload=True,
        )

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

        logger.info(f"[PhotoBrain/Text] Found {len(matches)} matches")
        return matches

