from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models.image_models import OcrTextResponse
from ..services.ocr_service import ocr_image

router = APIRouter()

@router.post("/text", response_model=OcrTextResponse)
async def ocr_text(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    return await ocr_image(file)

