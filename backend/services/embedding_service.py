"""Embedding service using sentence-transformers."""

import os
import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generates text embeddings using sentence-transformers."""

    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = None
        self.dimension = 384
        self._load_model()

    def _load_model(self):
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Using mock embeddings.")
            self.model = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Mock embedding for development
            np.random.seed(hash(text) % (2**31))
            return np.random.randn(self.dimension).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if self.model is not None:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        else:
            return [self.embed_text(t) for t in texts]

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
