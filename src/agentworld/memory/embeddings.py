"""Embedding generation for memory retrieval."""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation.

    Attributes:
        model: Embedding model identifier (e.g., "text-embedding-3-small")
        dimensions: Output vector dimensions
        provider: Provider for embeddings (openai, etc.)
    """
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    provider: str = "openai"

    def validate_compatibility(self, other: "EmbeddingConfig") -> bool:
        """Check if embeddings from two configs are comparable.

        Embedding similarity is only valid when both vectors use the same model.
        """
        return self.model == other.model and self.dimensions == other.dimensions


class EmbeddingGenerator:
    """Generates embeddings for text content using LLM providers.

    Uses LiteLLM for multi-provider embedding support.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedding generator.

        Args:
            config: Embedding configuration. Uses defaults if not provided.
        """
        self.config = config or EmbeddingConfig()
        self._cache: dict[str, np.ndarray] = {}

    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Numpy array of embedding values
        """
        # Check cache first
        if text in self._cache:
            return self._cache[text]

        if not HAS_LITELLM:
            # Fallback to random embedding for testing
            embedding = np.random.randn(self.config.dimensions).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            self._cache[text] = embedding
            return embedding

        try:
            response = await litellm.aembedding(
                model=self.config.model,
                input=[text],
            )
            embedding = np.array(response.data[0]["embedding"], dtype=np.float32)
            self._cache[text] = embedding
            return embedding
        except Exception:
            # Fallback to random embedding on error
            embedding = np.random.randn(self.config.dimensions).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            self._cache[text] = embedding
            return embedding

    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts.

        More efficient than calling embed() multiple times.

        Args:
            texts: List of texts to embed

        Returns:
            List of numpy arrays
        """
        if not texts:
            return []

        # Check which texts need embedding
        results = []
        texts_to_embed = []
        indices_to_embed = []

        for i, text in enumerate(texts):
            if text in self._cache:
                results.append((i, self._cache[text]))
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        # Embed remaining texts
        if texts_to_embed:
            if not HAS_LITELLM:
                for idx, text in zip(indices_to_embed, texts_to_embed):
                    embedding = np.random.randn(self.config.dimensions).astype(np.float32)
                    embedding = embedding / np.linalg.norm(embedding)
                    self._cache[text] = embedding
                    results.append((idx, embedding))
            else:
                try:
                    response = await litellm.aembedding(
                        model=self.config.model,
                        input=texts_to_embed,
                    )
                    for idx, text, data in zip(
                        indices_to_embed, texts_to_embed, response.data
                    ):
                        embedding = np.array(data["embedding"], dtype=np.float32)
                        self._cache[text] = embedding
                        results.append((idx, embedding))
                except Exception:
                    # Fallback to random embeddings on error
                    for idx, text in zip(indices_to_embed, texts_to_embed):
                        embedding = np.random.randn(self.config.dimensions).astype(np.float32)
                        embedding = embedding / np.linalg.norm(embedding)
                        self._cache[text] = embedding
                        results.append((idx, embedding))

        # Sort by original index and return
        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First embedding vector
            b: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        if a is None or b is None:
            return 0.0
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
