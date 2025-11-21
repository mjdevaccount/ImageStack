# python_server/models/photobrain_query_models.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PhotoBrainSearchMatch(BaseModel):
    id: str
    score: float
    filename: str
    path_raw: str
    path_processed: Optional[str] = None
    hash: Optional[str] = None
    ingested_at: Optional[datetime] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    metadata: dict = Field(default_factory=dict)


class PhotoBrainTextSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query over OCR + metadata")
    top_k: int = Field(8, ge=1, le=50, description="Max matches to return")


class PhotoBrainTextSearchResponse(BaseModel):
    matches: List[PhotoBrainSearchMatch]


class PhotoBrainImageSearchResponse(BaseModel):
    matches: List[PhotoBrainSearchMatch]


class PhotoBrainQaRequest(BaseModel):
    question: str = Field(..., description="Question to ask over image memory")
    top_k: int = Field(8, ge=1, le=50, description="How many images to consider")


class PhotoBrainQaResponse(BaseModel):
    answer: str
    matches: List[PhotoBrainSearchMatch]
    raw_answer: str

