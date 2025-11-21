from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    vision_model: str = "llama3.2-vision:11b"  # ✅ Updated
    ocr_model: str = "moondream"               # ✅ Optional dedicated OCR
    storage_dir: str = "../storage"

    class Config:
        env_prefix = "IMAGESTACK_"

settings = Settings()

