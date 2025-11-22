# python_server/services/photobrain_ingest_service.py

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile
from loguru import logger
from PIL import Image, ExifTags

from ..models.photobrain_models import PhotoBrainIngestResponse
from ..utils.image_io import save_temp_image
from .image_preprocess import (
    preprocess_image_for_ocr,
    preprocess_image_for_vision,
)
from .photobrain_embedding import PhotoBrainEmbedder
from .photobrain_store import PhotoBrainStore
from .photobrain_autotag import PhotoBrainAutoTagger


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _extract_exif_metadata(path: Path) -> dict:
    """Extract EXIF metadata and convert all values to JSON-serializable types."""
    meta: dict = {}
    try:
        img = Image.open(path)
        exif = img.getexif()
        if not exif:
            return meta

        # Map numeric tags → human-readable and convert to JSON-serializable types
        tagged = {}
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            # Convert PIL types to standard Python types
            if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                # IFDRational type - convert to float
                tagged[tag] = float(value)
            elif isinstance(value, bytes):
                # Bytes - try to decode or represent as hex
                try:
                    tagged[tag] = value.decode('utf-8', errors='ignore')
                except:
                    tagged[tag] = value.hex()
            elif isinstance(value, (list, tuple)):
                # Recursively convert sequences
                tagged[tag] = [float(v) if hasattr(v, 'numerator') else v for v in value]
            else:
                tagged[tag] = value

        # Extract some common fields
        if "DateTimeOriginal" in tagged:
            meta["datetime_original"] = str(tagged["DateTimeOriginal"])
        if "Model" in tagged:
            meta["device_model"] = str(tagged["Model"])
        if "Make" in tagged:
            meta["device_make"] = str(tagged["Make"])
        if "Orientation" in tagged:
            meta["orientation"] = tagged["Orientation"]

        meta["raw_exif"] = tagged
    except Exception as ex:
        logger.warning(f"[PhotoBrain] EXIF extraction failed for {path}: {ex}")
    return meta


def _run_easyocr(path: Path) -> Tuple[Optional[str], Optional[float]]:
    try:
        # Reuse global EasyOCR reader from ocr_service to avoid re-init cost
        from .ocr_service import _reader as easyocr_reader  # type: ignore

        logger.info(f"[PhotoBrain] Running EasyOCR on {path}")
        result = easyocr_reader.readtext(str(path), detail=1)

        texts = []
        confs = []
        for _, text, conf in result:
            texts.append(text)
            confs.append(float(conf))

        if not texts:
            return None, None

        joined = "\n".join(texts).strip()
        avg_conf = sum(confs) / len(confs) if confs else None
        return joined, avg_conf
    except Exception as ex:
        logger.error(f"[PhotoBrain] OCR failed for {path}: {ex}")
        return None, None


class PhotoBrainIngestService:
    """
    High-level pipeline for PhotoBrain ingestion.
    """

    def __init__(
        self,
        embedder: PhotoBrainEmbedder,
        store: PhotoBrainStore,
        auto_tagger: Optional[PhotoBrainAutoTagger] = None,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.auto_tagger = auto_tagger or PhotoBrainAutoTagger()

    async def ingest_image(
        self,
        file: UploadFile,
        ocr: bool = True,
        vision: bool = False,
        preprocess: bool = True,
        embed: bool = True,
        auto_tag: bool = True,
    ) -> PhotoBrainIngestResponse:
        """
        Full ingestion pipeline:
        - Save raw image
        - Optional preprocessing
        - Optional OCR
        - Optional auto-tagging (category + tags)
        - Optional embedding (image+text)
        - Store in Qdrant
        - Return rich metadata response
        """
        # 1. Save raw
        raw_path_str = await save_temp_image(file)
        raw_path = Path(raw_path_str)
        logger.info(f"[PhotoBrain] Saved raw image at {raw_path}")

        # 2. Preprocess
        processed_path: Optional[Path] = None
        if preprocess:
            # If OCR is requested, bias toward OCR pipeline; otherwise vision.
            if ocr:
                proc_str = preprocess_image_for_ocr(str(raw_path))
            elif vision:
                proc_str = preprocess_image_for_vision(str(raw_path))
            else:
                proc_str = preprocess_image_for_vision(str(raw_path))
            processed_path = Path(proc_str)
            logger.info(f"[PhotoBrain] Processed image at {processed_path}")

        # Use processed image for embedding / OCR if available, else raw
        work_path = processed_path or raw_path

        # 3. Hash
        digest = _compute_sha256(raw_path)
        logger.info(f"[PhotoBrain] SHA256={digest} for {raw_path}")

        # 4. EXIF metadata
        exif_meta = _extract_exif_metadata(raw_path)

        # 5. OCR
        ocr_text: Optional[str] = None
        ocr_conf: Optional[float] = None
        if ocr:
            ocr_text, ocr_conf = _run_easyocr(work_path)

        # 6. Auto-tagging / categorization
        autotag_result = None
        if auto_tag and self.auto_tagger is not None:
            try:
                autotag_result = await self.auto_tagger.auto_tag(
                    str(work_path),
                    ocr_text=ocr_text,
                )
            except Exception as ex:
                logger.error(f"[PhotoBrain] Auto-tagging failed: {ex}")
                autotag_result = None

        # 7. Embedding
        vector = None
        if embed:
            try:
                unified = self.embedder.embed_image_and_text(
                    str(work_path),
                    ocr_text or "",
                )
                vector = unified.tolist()
            except Exception as ex:
                logger.error(f"[PhotoBrain] Embedding failed: {ex}")
                vector = None

        # 8. Build metadata & store
        now = datetime.now(timezone.utc)
        image_id = uuid.uuid4().hex

        payload = {
            "filename": raw_path.name,
            "path_raw": str(raw_path),
            "path_processed": str(processed_path) if processed_path else None,
            "hash": digest,
            "ingested_at": now.isoformat(),
            "ocr_text": ocr_text,
            "ocr_confidence": ocr_conf,
            "exif": exif_meta,
        }

        # Add auto-tagging results to payload
        if autotag_result is not None:
            payload["category"] = autotag_result.category
            payload["tags"] = autotag_result.tags
            payload["autotag"] = {
                "model": self.auto_tagger.model,
                "confidence": autotag_result.confidence,
                "raw": autotag_result.raw_json,
            }

        if vector is not None:
            self.store.upsert_image(image_id, vector=vector, payload=payload)
            embedded_flag = True
        else:
            embedded_flag = False

        return PhotoBrainIngestResponse(
            id=image_id,
            filename=raw_path.name,
            path_raw=str(raw_path),
            path_processed=str(processed_path) if processed_path else None,
            hash=digest,
            ocr_text=ocr_text,
            ocr_confidence=ocr_conf,
            embedded=embedded_flag,
            timestamp=now,
            metadata=payload,
        )

