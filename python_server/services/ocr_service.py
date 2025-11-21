# python_server/services/ocr_service.py

from fastapi import UploadFile
from loguru import logger
from PIL import Image  # not strictly needed anymore but fine if kept
import easyocr

from ..models.image_models import OcrTextResponse
from ..utils.image_io import save_temp_image
from .image_preprocess import preprocess_image_for_ocr, OcrPreprocessConfig

# Initialize once (can use GPU; you already have torch)
_reader = easyocr.Reader(["en"], gpu=True)


async def ocr_image(file: UploadFile, preprocess: bool = False) -> OcrTextResponse:
    saved_path = await save_temp_image(file)
    logger.info(f"OCR input saved at {saved_path}")

    processed_path = saved_path
    if preprocess:
        cfg = OcrPreprocessConfig()
        processed_path = preprocess_image_for_ocr(saved_path, cfg)
        logger.info(f"OCR preprocessing applied: {processed_path}")

    logger.info(f"Running OCR on {processed_path}")

    result = _reader.readtext(processed_path, detail=1)

    # result is list of [bbox, text, confidence]
    texts = []
    confidences = []
    for _, text, conf in result:
        texts.append(text)
        confidences.append(conf)

    joined = "\n".join(texts).strip()
    avg_conf = float(sum(confidences) / len(confidences)) if confidences else None

    logger.info(f"OCR extracted {len(texts)} segments from {processed_path}")

    return OcrTextResponse(
        text=joined,
        language="en",
        confidence=avg_conf,
    )

