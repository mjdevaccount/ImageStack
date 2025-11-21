# python_server/rag/image_ingest_service.py

import uuid
import hashlib
import base64
from pathlib import Path
from io import BytesIO
from datetime import datetime
from loguru import logger
from PIL import Image

from ..utils.image_io import save_temp_image
from .image_embedder import ImageEmbedder
from .image_store import ImageVectorStore


class ImageIngestService:
    """
    Ingest images into the RAG system:
    - Save image to storage
    - Generate embeddings
    - Extract OCR text (optional)
    - Store in vector DB
    """

    def __init__(self, store: ImageVectorStore, embedder: ImageEmbedder):
        self.store = store
        self.embedder = embedder
        self._ocr_reader = None

    def _get_ocr_reader(self):
        """Lazy-load OCR reader to avoid startup penalty."""
        if self._ocr_reader is None:
            import easyocr
            logger.info("Initializing EasyOCR reader for RAG ingestion...")
            self._ocr_reader = easyocr.Reader(["en"], gpu=True)
        return self._ocr_reader

    def _make_thumb(self, path: str, width=256) -> str:
        """Generate thumbnail base64."""
        img = Image.open(path).convert("RGB")
        img.thumbnail((width, width))
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    async def ingest(self, file, extract_ocr: bool = True, tags: list = None):
        """
        Ingest an image into the RAG system.
        
        Args:
            file: UploadFile from FastAPI
            extract_ocr: Whether to run OCR text extraction
            tags: Optional user-supplied tags
            
        Returns:
            dict with id, hash, ocr_text, tags
        """
        # Save image
        file_path = await save_temp_image(file)
        img_path = Path(file_path)

        # Compute hash
        digest = hashlib.sha256(img_path.read_bytes()).hexdigest()

        # OCR extract (optional)
        ocr_text = ""
        if extract_ocr:
            try:
                reader = self._get_ocr_reader()
                ocr = reader.readtext(str(img_path), detail=0)
                ocr_text = "\n".join(ocr)
                logger.info(f"[ImageRAG] OCR extracted {len(ocr)} segments")
            except Exception as ex:
                logger.warning(f"[ImageRAG] OCR failed: {ex}")
                ocr_text = ""

        # Embed
        logger.info(f"[ImageRAG] Generating embedding for {img_path.name}")
        embedding = self.embedder.embed_image(str(img_path))

        # Generate thumbnail
        thumb_b64 = self._make_thumb(str(img_path))

        # Build metadata
        image_id = uuid.uuid4().hex
        meta = {
            "filename": img_path.name,
            "hash": digest,
            "ocr_text": ocr_text,
            "tags": tags or [],
            "created": datetime.utcnow().isoformat(),
            "thumb": thumb_b64,
            "path": str(img_path),
        }

        # Store in Qdrant
        self.store.add_image(image_id=image_id, embedding=embedding, meta=meta)

        logger.info(f"[ImageRAG] Ingested {img_path} → id={image_id}")

        return {
            "id": image_id,
            "hash": digest,
            "ocr_text": ocr_text,
            "tags": tags or [],
            "filename": img_path.name,
        }

