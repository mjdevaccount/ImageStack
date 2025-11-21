# python_server/services/photobrain_embedding.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
from PIL import Image
from loguru import logger
import open_clip


class PhotoBrainEmbedder:
    """
    Embeds images and text into a shared CLIP embedding space.
    """

    def __init__(
        self,
        model_name: str = "ViT-L-14",
        pretrained: str = "openai",
        device: Optional[str] = None,
    ) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(
            f"[PhotoBrain] Loading CLIP model {model_name} ({pretrained}) on {self.device}"
        )
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self.model.eval().to(self.device)
        self.tokenizer = open_clip.get_tokenizer(model_name)

    @property
    def dim(self) -> int:
        # CLIP features are in model's embed dimension
        # We can infer it by running a dummy forward once,
        # but many ViT-L-14 models use 768 or 1024 dimensions.
        # Safer: inspect actual feature size.
        dummy = torch.zeros(1, 3, 224, 224).to(self.device)
        with torch.no_grad():
            feat = self.model.encode_image(dummy)
        return int(feat.shape[-1])

    def embed_image(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feat = self.model.encode_image(tensor)

        vec = feat.cpu().float().numpy()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_text(self, text: str) -> np.ndarray:
        if not text.strip():
            # Empty text → zero vector (will be ignored or combined with image vec)
            return np.zeros(self.dim, dtype=np.float32)

        tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            feat = self.model.encode_text(tokens)

        vec = feat.cpu().float().numpy()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_image_and_text(self, image_path: str, text: str | None) -> np.ndarray:
        """
        Produce a single unified vector from image and text embeddings.
        If text is empty, this is just the image vector.
        If text is present, we average and renormalize.
        """
        img_vec = self.embed_image(image_path)
        if not text:
            return img_vec

        txt_vec = self.embed_text(text)

        combined = img_vec + txt_vec
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        return combined.astype(np.float32)

