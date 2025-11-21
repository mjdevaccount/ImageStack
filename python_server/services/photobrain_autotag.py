# python_server/services/photobrain_autotag.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import base64
import httpx
from loguru import logger

from ..config import settings


# Canonical categories we want PhotoBrain to use
CANONICAL_CATEGORIES = [
    "receipt",
    "invoice",
    "id_card",
    "serial_plate",
    "document",
    "form",
    "handwritten_notes",
    "whiteboard",
    "screenshot",
    "info_card",
    "photo_of_object",
    "other",
]


@dataclass
class AutoTagResult:
    category: str
    tags: List[str]
    confidence: float
    raw_json: dict


class PhotoBrainAutoTagger:
    """
    Uses a vision-capable Ollama model to auto-tag and categorize images.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        # Try dedicated autotag model first; fall back to vision_model
        self.model = (
            model
            or getattr(settings, "photobrain_autotag_model", None)
            or getattr(settings, "vision_model", None)
            or "llava"
        )
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        logger.info(f"[PhotoBrain/AutoTag] Using model={self.model}, base_url={self.base_url}")

    async def auto_tag(
        self,
        image_path: str,
        ocr_text: Optional[str] = None,
    ) -> Optional[AutoTagResult]:
        """
        Run the vision model to classify + tag the image.

        Returns AutoTagResult or None on failure.
        """
        path = Path(image_path)
        if not path.exists():
            logger.warning(f"[PhotoBrain/AutoTag] Image not found: {path}")
            return None

        try:
            with path.open("rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as ex:
            logger.error(f"[PhotoBrain/AutoTag] Failed to read {path}: {ex}")
            return None

        examples = ", ".join(CANONICAL_CATEGORIES)

        prompt = f"""
You are PhotoBrain's AutoTagger.

Your job is to classify the given image into ONE of these categories:

{examples}

And generate 3-10 short tags that will help the user search later.

Guidelines:
- If the image clearly shows a store receipt or purchase slip → "receipt".
- If it's a bill or invoice with charges → "invoice".
- If it shows a serial number plate / label on a device → "serial_plate".
- If it's a standard document (letter, PDF printout, typed text) → "document".
- If it's a form to fill in → "form".
- If it's handwritten notes on paper → "handwritten_notes".
- If it's a whiteboard with writing → "whiteboard".
- If it's a phone or computer screenshot → "screenshot".
- If it's a small card or label with info (e.g., medication card, business card) → "info_card".
- If it's mostly an object (e.g., generator, HVAC unit, appliance, tool) → "photo_of_object".
- Use "other" if none of these obviously fit.

You MUST respond in JSON ONLY, with this structure:

{{
  "category": "<one of: {examples}>",
  "tags": ["short", "searchable", "tags"],
  "confidence": 0.0
}}

If you are unsure, pick the closest reasonable category and use low confidence.
If OCR text is provided, use it to help understand context.
"""

        if ocr_text:
            prompt += "\n\nOCR TEXT (may be noisy, but useful):\n" + ocr_text[:4000]

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=120.0) as client:
                resp = await client.post("/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as ex:
            logger.error(f"[PhotoBrain/AutoTag] Ollama call failed: {ex}")
            return None

        raw_resp = (data.get("response") or "").strip()
        logger.debug(f"[PhotoBrain/AutoTag] Raw model response: {raw_resp!r}")

        # Try to find JSON block in the response
        parsed = None
        try:
            # Some models might wrap JSON in text → extract between first { and last }
            start = raw_resp.find("{")
            end = raw_resp.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = raw_resp[start : end + 1]
            else:
                json_str = raw_resp
            parsed = json.loads(json_str)
        except Exception as ex:
            logger.error(f"[PhotoBrain/AutoTag] Failed to parse JSON: {ex}")
            return None

        category = str(parsed.get("category") or "").strip().lower()
        tags = parsed.get("tags") or []
        confidence = float(parsed.get("confidence") or 0.0)

        # normalize category to one of our canonical ones
        canonical = "other"
        for c in CANONICAL_CATEGORIES:
            if category == c:
                canonical = c
                break

        # best-effort mapping if model returns something close
        if canonical == "other":
            # simple heuristics
            if "receipt" in category:
                canonical = "receipt"
            elif "invoice" in category:
                canonical = "invoice"
            elif "serial" in category or "plate" in category:
                canonical = "serial_plate"
            elif "whiteboard" in category:
                canonical = "whiteboard"
            elif "screenshot" in category:
                canonical = "screenshot"
            elif "handwrit" in category:
                canonical = "handwritten_notes"
            elif "form" in category:
                canonical = "form"
            elif "document" in category or "doc" in category:
                canonical = "document"

        # normalize tags to short strings
        tags_out: List[str] = []
        for t in tags:
            s = str(t).strip()
            if s:
                tags_out.append(s)

        logger.info(
            f"[PhotoBrain/AutoTag] category={canonical}, "
            f"confidence={confidence:.2f}, tags={tags_out}"
        )

        return AutoTagResult(
            category=canonical,
            tags=tags_out,
            confidence=confidence,
            raw_json=parsed,
        )

