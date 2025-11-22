import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Compute absolute path to storage directory
_CONFIG_DIR = Path(__file__).parent
_PROJECT_ROOT = _CONFIG_DIR.parent
_DEFAULT_STORAGE = str(_PROJECT_ROOT / "storage")

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    vision_model: str = "llama3.2-vision:11b"  # ✅ Updated
    ocr_model: str = "moondream"               # ✅ Optional dedicated OCR
    storage_dir: str = _DEFAULT_STORAGE
    
    # RAG / Vector Store settings
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # Empty for local instance
    clip_model: str = "ViT-L-14"
    clip_pretrained: str = "openai"
    embedding_dim: int = 768  # ViT-L-14 dimension
    
    # PhotoBrain QA settings
    photobrain_qa_model: str = "phi4:14b"  # Ollama model for RAG Q&A

    class Config:
        env_prefix = "IMAGESTACK_"

settings = Settings()

