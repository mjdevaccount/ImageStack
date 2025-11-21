# python_server/models/photobrain_filters.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PhotoBrainFilterRequest(BaseModel):
    """
    Server-side filters for PhotoBrain search.
    All filters are AND-ed together.
    """
    days: Optional[int] = Field(None, description="Last N days (relative to now)")
    date_min: Optional[datetime] = Field(None, description="Minimum ingestion date")
    date_max: Optional[datetime] = Field(None, description="Maximum ingestion date")
    tag: Optional[str] = Field(None, description="Tag substring match (case-insensitive)")
    tags: Optional[List[str]] = Field(None, description="AND match all tags")
    contains_text: Optional[str] = Field(None, description="OCR text substring match")
    confidence_min: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum OCR confidence")
    device: Optional[str] = Field(None, description="Device model substring match")
    category: Optional[str] = Field(None, description="Category (receipts, notes, whiteboard, docs, screenshots)")

