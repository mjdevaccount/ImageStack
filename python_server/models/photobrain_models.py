# python_server/models/photobrain_models.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PhotoBrainIngestResponse(BaseModel):
    id: str = Field(..., description="Stable PhotoBrain ID for this image")
    filename: str
    path_raw: str
    path_processed: Optional[str] = None
    hash: str = Field(..., description="SHA-256 digest of the raw image bytes")
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    embedded: bool = Field(..., description="Whether an embedding was stored")
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

