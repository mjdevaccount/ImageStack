# python_server/services/vision_service.py

import base64
from pathlib import Path

import httpx
from fastapi import UploadFile
from loguru import logger

from ..config import settings
from ..models.image_models import VisionDescribeResponse
from ..utils.image_io import save_temp_image
from .image_preprocess import preprocess_image_for_vision


async def describe_image(file: UploadFile, preprocess: bool = False) -> VisionDescribeResponse:
    # Save a copy to storage
    saved_path = await save_temp_image(file)
    logger.info(f"Vision input saved at {saved_path}")

    processed_path = saved_path
    if preprocess:
        processed_path = preprocess_image_for_vision(saved_path)
        logger.info(f"Vision preprocessing applied: {processed_path}")

    # Reload as bytes for base64
    with open(processed_path, "rb") as f:
        image_bytes = f.read()

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = "Describe this image in a concise paragraph, then list key tags."

    payload = {
        "model": settings.vision_model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
    }

    logger.info(f"Calling Ollama vision model={settings.vision_model}")

    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
        resp = await client.post("/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = data.get("response", "")

    # Very simple tag extraction: look for 'tags:' or 'keywords:'
    tags = []
    lower = text.lower()
    for line in lower.splitlines():
        if line.startswith("tags") or line.startswith("keywords"):
            _, _, tag_part = line.partition(":")
            tags = [t.strip() for t in tag_part.split(",") if t.strip()]
            break

    logger.info(f"Vision description complete for {processed_path}")

    return VisionDescribeResponse(
        description=text.strip(),
        tags=tags,
        model=settings.vision_model,
        raw=text,
    )

