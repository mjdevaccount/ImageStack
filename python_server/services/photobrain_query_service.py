# python_server/services/photobrain_query_service.py

from __future__ import annotations

from typing import List

import httpx
from loguru import logger
from qdrant_client import QdrantClient

from ..config import settings
from ..models.photobrain_query_models import (
    PhotoBrainQaResponse,
    PhotoBrainSearchMatch,
)
from .photobrain_embedding import PhotoBrainEmbedder


class PhotoBrainQueryService:
    """
    LLM-powered Q&A over images stored in the PhotoBrain collection.
    Uses CLIP text embedding for retrieval and Ollama for synthesis.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: PhotoBrainEmbedder,
        qa_model: str | None = None,
        ollama_base_url: str | None = None,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder
        self.qa_model = qa_model or getattr(settings, "photobrain_qa_model", None) or "phi4:14b"
        self.ollama_base_url = ollama_base_url or settings.ollama_base_url.rstrip("/")

    async def answer_question(self, question: str, top_k: int = 8) -> PhotoBrainQaResponse:
        logger.info(f"[PhotoBrain/QA] Question: {question!r}, top_k={top_k}")

        # 1) Retrieve relevant images (using text embedding)
        vec = self.embedder.embed_text(question).astype("float32").tolist()

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

        # 2) Build context for LLM
        if not matches:
            logger.info("[PhotoBrain/QA] No matches found; returning fallback answer")
            return PhotoBrainQaResponse(
                answer="I couldn't find any images that appear to answer that question.",
                matches=[],
                raw_answer="",
            )

        context_blocks: list[str] = []
        for m in matches:
            ctx = []
            ctx.append(f"ID: {m.id}")
            ctx.append(f"Filename: {m.filename}")
            if m.ocr_text:
                ctx.append("OCR text:")
                ctx.append(m.ocr_text)
            if m.metadata:
                # keep metadata small-ish
                exif = m.metadata.get("exif") or {}
                device = exif.get("device_model") or exif.get("Model")
                if device:
                    ctx.append(f"Device: {device}")
                if "datetime_original" in exif:
                    ctx.append(f"Captured: {exif['datetime_original']}")
            context_blocks.append("\n".join(ctx))

        context_str = "\n\n---\n\n".join(context_blocks)

        prompt = f"""You are PhotoBrain, an assistant that answers questions based on text extracted from the user's images.

User question:
{question}

You have the following image records (ID, filename, OCR text, and metadata):

{context_str}

Instructions:
- Answer the user's question ONLY using the information in these records.
- If you are not sure, say you cannot find the answer.
- If a specific ID clearly contains the answer, mention its ID in your explanation.
- Be concise and direct.

Answer:
"""

        logger.info(f"[PhotoBrain/QA] Calling Ollama model={self.qa_model}")

        async with httpx.AsyncClient(base_url=self.ollama_base_url, timeout=120.0) as client:
            resp = await client.post(
                "/api/generate",
                json={
                    "model": self.qa_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw_answer = (data.get("response") or "").strip()
        answer = raw_answer  # For now, we return as-is

        return PhotoBrainQaResponse(
            answer=answer,
            matches=matches,
            raw_answer=raw_answer,
        )

