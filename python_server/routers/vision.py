from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models.image_models import VisionDescribeResponse
from ..services.vision_service import describe_image

router = APIRouter()

@router.post("/describe", response_model=VisionDescribeResponse)
async def vision_describe(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    return await describe_image(file)

