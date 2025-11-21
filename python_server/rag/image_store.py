# python_server/rag/image_store.py

import hashlib
from pathlib import Path
import base64
from io import BytesIO
import numpy as np
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct


class ImageVectorStore:
    COLLECTION = "imagestack_images"

    def __init__(self, client: QdrantClient, dim: int = 768):
        self.client = client
        self.dim = dim

        self._init_collection()

    def _init_collection(self):
        logger.info("Initializing ImageRAG vector store...")

        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
            logger.info(f"Created collection: {self.COLLECTION}")
        else:
            logger.info(f"Collection already exists: {self.COLLECTION}")

    def _make_thumb(self, path: str, width=256):
        from PIL import Image

        img = Image.open(path).convert("RGB")
        img.thumbnail((width, width))
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def add_image(self, image_id: str, embedding: np.ndarray, meta: dict):
        point = PointStruct(
            id=image_id,
            vector=embedding.tolist(),
            payload=meta,
        )
        self.client.upsert(collection_name=self.COLLECTION, points=[point])

    def search_by_vector(self, vector: np.ndarray, limit=5):
        return self.client.search(
            collection_name=self.COLLECTION,
            query_vector=vector.tolist(),
            limit=limit,
        )

