# python_server/services/image_preprocess.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from loguru import logger
from PIL import Image, ImageOps


@dataclass
class OcrPreprocessConfig:
    auto_orient: bool = True
    denoise: bool = True
    enhance_contrast: bool = True
    binarize: bool = True
    deskew: bool = False  # simple heuristic, not perfect
    target_long_edge: int = 1600


def _load_and_orient(path: str, auto_orient: bool = True) -> np.ndarray:
    """Load image from disk and apply EXIF-based orientation if requested."""
    img = Image.open(path)
    if auto_orient:
        img = ImageOps.exif_transpose(img)
    # Convert PIL RGB -> OpenCV BGR
    arr = np.array(img.convert("RGB"))
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return bgr


def _resize_long_edge(img: np.ndarray, target_long_edge: int) -> np.ndarray:
    h, w = img.shape[:2]
    long_edge = max(h, w)
    if long_edge <= target_long_edge:
        return img

    scale = target_long_edge / float(long_edge)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized


def _enhance_contrast_gray(gray: np.ndarray) -> np.ndarray:
    # CLAHE for OCR-friendly contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _binarize(gray: np.ndarray) -> np.ndarray:
    # Otsu thresholding to get clean black/white text
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh


def _denoise(gray: np.ndarray) -> np.ndarray:
    # Non-local means denoising; keep text edges
    return cv2.fastNlMeansDenoising(gray, None, h=30, templateWindowSize=7, searchWindowSize=21)


def _deskew(gray: np.ndarray) -> np.ndarray:
    """
    Simple skew correction based on text-like content.
    If detection fails, returns original.
    """
    try:
        # Invert: text as white on black
        inv = cv2.bitwise_not(gray)
        coords = np.column_stack(np.where(inv > 0))
        if coords.size == 0:
            return gray

        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.5:
            return gray  # already straight enough

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            gray, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        logger.info(f"Deskew applied, angle={angle:.2f} deg")
        return rotated
    except Exception as ex:
        logger.warning(f"Deskew failed: {ex}")
        return gray


def preprocess_image_for_ocr(
    path: str,
    config: Optional[OcrPreprocessConfig] = None,
) -> str:
    """
    Full OCR-oriented pipeline:
    - load + EXIF orientation
    - resize long edge
    - grayscale
    - denoise
    - contrast enhancement
    - binarization
    - optional deskew
    Writes a new file next to the original and returns its path.
    """
    config = config or OcrPreprocessConfig()
    src_path = Path(path)
    if not src_path.exists():
        raise FileNotFoundError(path)

    logger.info(f"OCR preprocess start: {path}")

    img = _load_and_orient(str(src_path), auto_orient=config.auto_orient)
    img = _resize_long_edge(img, config.target_long_edge)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if config.denoise:
        gray = _denoise(gray)

    if config.enhance_contrast:
        gray = _enhance_contrast_gray(gray)

    if config.binarize:
        gray = _binarize(gray)

    if config.deskew:
        gray = _deskew(gray)

    out_path = src_path.with_name(src_path.stem + "_proc_ocr" + src_path.suffix)
    cv2.imwrite(str(out_path), gray)

    logger.info(f"OCR preprocess finished: {out_path}")
    return str(out_path)


def preprocess_image_for_vision(
    path: str,
    target_long_edge: int = 1600,
    auto_orient: bool = True,
    sharpen: bool = True,
) -> str:
    """
    Lighter vision/VQA preprocessing:
    - load + EXIF orientation
    - resize long edge
    - mild sharpening
    Writes a new file and returns its path.
    """
    src_path = Path(path)
    if not src_path.exists():
        raise FileNotFoundError(path)

    logger.info(f"Vision preprocess start: {path}")

    img = _load_and_orient(str(src_path), auto_orient=auto_orient)
    img = _resize_long_edge(img, target_long_edge)

    if sharpen:
        # simple unsharp mask style filter
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)

    out_path = src_path.with_name(src_path.stem + "_proc_vis" + src_path.suffix)
    cv2.imwrite(str(out_path), img)

    logger.info(f"Vision preprocess finished: {out_path}")
    return str(out_path)

