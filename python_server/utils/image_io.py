import os
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile

from ..config import settings

async def save_temp_image(file: UploadFile) -> str:
    storage_root = Path(settings.storage_dir).resolve()
    images_dir = storage_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    ext = os.path.splitext(file.filename or "upload.png")[1] or ".png"
    name = f"img_{ts}{ext}"
    full_path = images_dir / name
    
    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)
    
    # Reset file pointer so other consumers could re-read if needed
    await file.seek(0)
    
    return str(full_path)

