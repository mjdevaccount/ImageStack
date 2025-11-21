# python_server/services/photobrain_store.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse


@dataclass
class PhotoBrainStoreConfig:
    collection_name: str = "photobrain"
    vector_size: int = 768
    distance: Distance = Distance.COSINE


class PhotoBrainStore:
    def __init__(
        self,
        client: QdrantClient,
        config: PhotoBrainStoreConfig,
    ) -> None:
        self.client = client
        self.config = config
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.config.collection_name)
            logger.info(
                f"[PhotoBrain] Using existing Qdrant collection={self.config.collection_name}"
            )
        except UnexpectedResponse:
            logger.info(
                f"[PhotoBrain] Creating Qdrant collection={self.config.collection_name}, "
                f"dim={self.config.vector_size}"
            )
            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=self.config.distance,
                ),
            )

    def upsert_image(
        self,
        id_str: str,
        vector: Optional[list[float]],
        payload: Dict[str, Any],
    ) -> None:
        points: list[PointStruct] = []
        if vector is not None:
            points.append(
                PointStruct(
                    id=id_str,
                    vector=vector,
                    payload=payload,
                )
            )
        else:
            # If we don't embed, we can still store a record with an empty vector
            # but better to skip for now.
            logger.warning(
                f"[PhotoBrain] upsert_image called with vector=None; payload only is not stored."
            )
            return

        self.client.upsert(
            collection_name=self.config.collection_name,
            points=points,
        )
        logger.info(
            f"[PhotoBrain] Stored image id={id_str} in collection={self.config.collection_name}"
        )

