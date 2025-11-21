from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    vision_model: str = "llama3.2-vision:11b"  # ✅ Updated
    ocr_model: str = "moondream"               # ✅ Optional dedicated OCR
    storage_dir: str = "../storage"
    
    # RAG / Vector Store settings
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # Empty for local instance
    clip_model: str = "ViT-L-14"
    clip_pretrained: str = "openai"
    embedding_dim: int = 768  # ViT-L-14 dimension

    class Config:
        env_prefix = "IMAGESTACK_"

settings = Settings()

