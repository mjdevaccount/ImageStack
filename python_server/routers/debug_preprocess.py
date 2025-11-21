# python_server/routers/debug_preprocess.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from tempfile import TemporaryDirectory
from pathlib import Path
import zipfile
from loguru import logger

from ..utils.image_io import save_temp_image
from ..services.image_preprocess import (
    preprocess_image_for_ocr,
    preprocess_image_for_vision,
)

router = APIRouter()


@router.post("/preprocess")
async def debug_preprocess(file: UploadFile = File(...)):
    """
    Returns a ZIP containing:
    - original image
    - _proc_ocr image
    - _proc_vis image
    """

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save original
    original_path = await save_temp_image(file)
    logger.info(f"[debug] Original image saved: {original_path}")

    # Generate processed versions
    ocr_path = preprocess_image_for_ocr(original_path)
    logger.info(f"[debug] OCR preprocessed image: {ocr_path}")

    vis_path = preprocess_image_for_vision(original_path)
    logger.info(f"[debug] Vision preprocessed image: {vis_path}")

    # Build ZIP in a temp directory
    with TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "preprocess_debug.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(original_path, "original" + Path(original_path).suffix)
            zf.write(ocr_path, "ocr" + Path(ocr_path).suffix)
            zf.write(vis_path, "vision" + Path(vis_path).suffix)

        logger.info(f"[debug] ZIP file ready: {zip_path}")

        # Return ZIP
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="preprocess_debug.zip",
        )

