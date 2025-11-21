from pydantic import BaseModel
from typing import List, Optional

class VisionDescribeResponse(BaseModel):
    description: str
    tags: List[str] = []
    model: str
    raw: Optional[str] = None  # full response if you want

class OcrTextResponse(BaseModel):
    text: str
    language: str = "unknown"
    confidence: Optional[float] = None

