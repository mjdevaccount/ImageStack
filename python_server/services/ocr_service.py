from fastapi import UploadFile
from loguru import logger
from PIL import Image
import easyocr

from ..models.image_models import OcrTextResponse
from ..utils.image_io import save_temp_image

# Initialize once (can use GPU; you already have torch)
_reader = easyocr.Reader(["en"], gpu=True)

async def ocr_image(file: UploadFile) -> OcrTextResponse:
    saved_path = await save_temp_image(file)
    
    logger.info(f"Running OCR on {saved_path}")
    
    result = _reader.readtext(saved_path, detail=1)
    # result is list of [bbox, text, confidence]
    
    texts = []
    confidences = []
    
    for _, text, conf in result:
        texts.append(text)
        confidences.append(conf)
    
    joined = "\n".join(texts).strip()
    avg_conf = float(sum(confidences) / len(confidences)) if confidences else None
    
    logger.info(f"OCR extracted {len(texts)} segments from {saved_path}")
    
    return OcrTextResponse(
        text=joined,
        language="en",
        confidence=avg_conf,
    )

