# python_server/rag/image_search_service.py

import numpy as np
from loguru import logger

from ..utils.image_io import save_temp_image
from .image_embedder import ImageEmbedder
from .image_store import ImageVectorStore


class ImageSearchService:
    """
    Search images by:
    - Visual similarity (image -> image)
    - Semantic text query (text -> image)
    """

    def __init__(self, store: ImageVectorStore, embedder: ImageEmbedder):
        self.store = store
        self.embedder = embedder

    async def search_by_image(self, file, limit=5):
        """
        Search for visually similar images.
        
        Args:
            file: UploadFile containing query image
            limit: Number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        saved = await save_temp_image(file)
        logger.info(f"[ImageRAG] Searching by image: {saved}")
        
        vec = self.embedder.embed_image(saved)
        results = self.store.search_by_vector(vec, limit)
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "id": result.id,
                "score": float(result.score),
                "metadata": result.payload,
            })
        
        logger.info(f"[ImageRAG] Found {len(formatted)} similar images")
        return formatted

    async def search_by_text(self, query: str, limit=5):
        """
        Search for images matching a text description.
        
        Args:
            query: Text query (e.g. "sunset over mountains")
            limit: Number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        logger.info(f"[ImageRAG] Searching by text: '{query}'")
        
        # CLIP can embed text too
        text_vec = self.embedder.embed_text(query)
        results = self.store.search_by_vector(text_vec, limit)
        
        # Format results
        formatted = []
        for result in results:
            formatted.append({
                "id": result.id,
                "score": float(result.score),
                "metadata": result.payload,
            })
        
        logger.info(f"[ImageRAG] Found {len(formatted)} matching images")
        return formatted

