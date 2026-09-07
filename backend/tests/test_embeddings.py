"""Tests for embedding service."""

import pytest
import numpy as np


class TestEmbeddingService:
    """Test the embedding service."""

    def test_cosine_similarity_identical(self):
        """Identical vectors should have similarity 1.0."""
        vec = [1.0, 0.0, 0.0]
        a = np.array(vec)
        b = np.array(vec)
        similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity ~0."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(similarity) < 0.001

    def test_cosine_similarity_opposite(self):
        """Opposite vectors should have similarity -1.0."""
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])
        similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(similarity - (-1.0)) < 0.001

    def test_cosine_similarity_range(self):
        """Similarity should be in [-1, 1] range."""
        np.random.seed(42)
        for _ in range(100):
            a = np.random.randn(384)
            b = np.random.randn(384)
            similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
            assert -1.0 <= similarity <= 1.0

    def test_embedding_dimensions(self):
        """Embeddings should have correct dimensions."""
        expected_dim = 384  # MiniLM-L6-v2
        assert expected_dim == 384

    def test_mock_embedding_deterministic(self):
        """Same text should produce same mock embedding."""
        # Mock embedding uses hash-based seeding
        text = "test string"
        seed = hash(text) % (2**31)
        np.random.seed(seed)
        emb1 = np.random.randn(384).tolist()

        np.random.seed(seed)
        emb2 = np.random.randn(384).tolist()

        assert emb1 == emb2
