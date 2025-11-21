# python_server/services/photobrain_filters.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from loguru import logger

from ..models.photobrain_filters import PhotoBrainFilterRequest
from ..models.photobrain_query_models import PhotoBrainSearchMatch


def apply_filters(
    matches: List[PhotoBrainSearchMatch],
    filters: Optional[PhotoBrainFilterRequest]
) -> List[PhotoBrainSearchMatch]:
    """
    Apply server-side filters to search results.
    All filters are AND-ed together.
    
    Args:
        matches: Raw search results from Qdrant
        filters: Filter criteria (optional)
        
    Returns:
        Filtered list of matches
    """
    if filters is None:
        return matches

    logger.info(f"[PhotoBrain/Filters] Applying filters to {len(matches)} results")
    
    out = []
    now = datetime.now(timezone.utc)

    for m in matches:
        meta = m.metadata or {}
        exif = meta.get("exif", {})
        ocr = m.ocr_text or ""
        tags = meta.get("tags") or []

        ok = True

        # Last N days (relative filter)
        if filters.days is not None:
            if m.ingested_at is None:
                ok = False
            else:
                # Handle both aware and naive datetimes
                ing_at = m.ingested_at
                if ing_at.tzinfo is None:
                    ing_at = ing_at.replace(tzinfo=timezone.utc)
                cutoff = now - timedelta(days=filters.days)
                if ing_at < cutoff:
                    ok = False

        # Date range filters
        if filters.date_min and m.ingested_at:
            ing_at = m.ingested_at
            if ing_at.tzinfo is None:
                ing_at = ing_at.replace(tzinfo=timezone.utc)
            if ing_at < filters.date_min:
                ok = False
                
        if filters.date_max and m.ingested_at:
            ing_at = m.ingested_at
            if ing_at.tzinfo is None:
                ing_at = ing_at.replace(tzinfo=timezone.utc)
            if ing_at > filters.date_max:
                ok = False

        # Tag substring match (case-insensitive)
        if filters.tag:
            t = filters.tag.lower()
            if not any(t in x.lower() for x in tags):
                ok = False

        # AND match all tags in list
        if filters.tags:
            required = [t.lower() for t in filters.tags]
            lower_tags = [t.lower() for t in tags]
            if not all(t in lower_tags for t in required):
                ok = False

        # OCR text substring match (case-insensitive)
        if filters.contains_text:
            if filters.contains_text.lower() not in ocr.lower():
                ok = False

        # OCR confidence minimum threshold
        if filters.confidence_min is not None:
            if m.ocr_confidence is None or m.ocr_confidence < filters.confidence_min:
                ok = False

        # Device model substring match (case-insensitive)
        if filters.device:
            dev = (exif.get("device_model") or exif.get("Model") or "").lower()
            if filters.device.lower() not in dev:
                ok = False

        # Category exact match (case-insensitive)
        if filters.category:
            cat = meta.get("category")
            if not cat or filters.category.lower() != cat.lower():
                ok = False

        if ok:
            out.append(m)

    logger.info(f"[PhotoBrain/Filters] Filtered {len(matches)} → {len(out)} results")
    return out

