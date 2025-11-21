# python_server/rag/image_embedder.py

from pathlib import Path
import numpy as np
from PIL import Image
from loguru import logger
import torch
import torchvision.transforms as T
import open_clip


class ImageEmbedder:
    """
    Embeds images into a vector space using CLIP.
    """

    def __init__(self, model_name="ViT-L-14", pretrained="openai", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Loading CLIP model {model_name} ({pretrained}) on {self.device}")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self.model.eval().to(self.device)

        # Get tokenizer for text embeddings
        self.tokenizer = open_clip.get_tokenizer(model_name)

        # CLIP requires transforms as preproc
        self.transform = self.preprocess

    def embed_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model.encode_image(tensor)

        embedding = embedding.cpu().float().numpy()[0]
        embedding /= np.linalg.norm(embedding)  # normalize
        return embedding

    def embed_text(self, text: str) -> np.ndarray:
        """Embed text using CLIP text encoder."""
        tokens = self.tokenizer([text]).to(self.device)

        with torch.no_grad():
            embedding = self.model.encode_text(tokens)

        embedding = embedding.cpu().float().numpy()[0]
        embedding /= np.linalg.norm(embedding)  # normalize
        return embedding

