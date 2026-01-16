"""Memory retrieval implementation.

Implements the Generative Agents retrieval function:
    score = alpha * relevance + beta * recency + gamma * importance
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Union
import math

import numpy as np

from agentworld.memory.observation import Observation
from agentworld.memory.reflection import Reflection
from agentworld.memory.embeddings import EmbeddingGenerator


@dataclass
class RetrievalConfig:
    """Configuration for memory retrieval scoring.

    Attributes:
        alpha: Weight for relevance (semantic similarity)
        beta: Weight for recency (time decay)
        gamma: Weight for importance
        recency_decay_hours: Half-life for recency decay in hours
    """
    alpha: float = 0.5  # Relevance weight
    beta: float = 0.3   # Recency weight
    gamma: float = 0.2  # Importance weight
    recency_decay_hours: float = 24.0  # Decay half-life

    def __post_init__(self):
        """Validate weights sum to approximately 1."""
        total = self.alpha + self.beta + self.gamma
        if not (0.99 <= total <= 1.01):
            # Normalize weights
            self.alpha /= total
            self.beta /= total
            self.gamma /= total


MemoryItem = Union[Observation, Reflection]


class MemoryRetrieval:
    """Retrieves memories based on relevance, recency, and importance.

    Implements the Generative Agents retrieval function for ranking memories
    when agents need to recall relevant context.
    """

    def __init__(
        self,
        config: RetrievalConfig | None = None,
        embedding_generator: EmbeddingGenerator | None = None
    ):
        """Initialize retrieval system.

        Args:
            config: Retrieval scoring configuration
            embedding_generator: Generator for query embeddings
        """
        self.config = config or RetrievalConfig()
        self.embeddings = embedding_generator or EmbeddingGenerator()

    async def retrieve(
        self,
        query: str,
        memories: List[MemoryItem],
        k: int = 10,
        current_time: datetime | None = None
    ) -> List[MemoryItem]:
        """Retrieve top-k most relevant memories for a query.

        Args:
            query: The query text to find relevant memories for
            memories: List of memories to search through
            k: Number of memories to return
            current_time: Reference time for recency calculation

        Returns:
            Top-k memories sorted by combined score (descending)
        """
        if not memories:
            return []

        current_time = current_time or datetime.now()

        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)

        # Score all memories
        scored = []
        for memory in memories:
            score = self._compute_score(memory, query_embedding, current_time)
            scored.append((memory, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        return [mem for mem, _ in scored[:k]]

    def _compute_score(
        self,
        memory: MemoryItem,
        query_embedding: np.ndarray,
        current_time: datetime
    ) -> float:
        """Compute combined retrieval score for a memory.

        score = alpha * relevance + beta * recency + gamma * importance

        Args:
            memory: The memory to score
            query_embedding: Embedding of the query
            current_time: Reference time for recency

        Returns:
            Combined score between 0 and 1
        """
        relevance = self._compute_relevance(memory, query_embedding)
        recency = self._compute_recency(memory, current_time)
        importance = self._compute_importance(memory)

        return (
            self.config.alpha * relevance +
            self.config.beta * recency +
            self.config.gamma * importance
        )

    def _compute_relevance(
        self,
        memory: MemoryItem,
        query_embedding: np.ndarray
    ) -> float:
        """Compute semantic relevance using cosine similarity.

        Returns:
            Relevance score between 0 and 1
        """
        if memory.embedding is None:
            return 0.0

        similarity = EmbeddingGenerator.cosine_similarity(
            query_embedding, memory.embedding
        )
        # Normalize from [-1, 1] to [0, 1]
        return (similarity + 1.0) / 2.0

    def _compute_recency(
        self,
        memory: MemoryItem,
        current_time: datetime
    ) -> float:
        """Compute recency score using exponential decay.

        Uses formula: e^(-delta_t / tau) where tau is based on decay_hours.

        Returns:
            Recency score between 0 and 1
        """
        delta = current_time - memory.timestamp
        hours = delta.total_seconds() / 3600.0

        # tau is set so that at decay_hours, we have ~0.5 remaining
        tau = self.config.recency_decay_hours / math.log(2)
        return math.exp(-hours / tau)

    def _compute_importance(self, memory: MemoryItem) -> float:
        """Normalize importance score to 0-1 range.

        Importance is stored as 1-10, normalize to 0-1.

        Returns:
            Normalized importance between 0 and 1
        """
        return (memory.importance - 1.0) / 9.0

    async def retrieve_by_recency(
        self,
        memories: List[MemoryItem],
        k: int = 10,
        current_time: datetime | None = None
    ) -> List[MemoryItem]:
        """Retrieve memories sorted by recency only.

        Useful for getting recent context without semantic matching.

        Args:
            memories: List of memories to search
            k: Number to return
            current_time: Reference time

        Returns:
            Top-k most recent memories
        """
        if not memories:
            return []

        current_time = current_time or datetime.now()

        scored = [
            (mem, self._compute_recency(mem, current_time))
            for mem in memories
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [mem for mem, _ in scored[:k]]

    async def retrieve_by_importance(
        self,
        memories: List[MemoryItem],
        k: int = 10
    ) -> List[MemoryItem]:
        """Retrieve memories sorted by importance only.

        Useful for getting the most significant memories.

        Args:
            memories: List of memories to search
            k: Number to return

        Returns:
            Top-k most important memories
        """
        if not memories:
            return []

        sorted_mems = sorted(memories, key=lambda m: m.importance, reverse=True)
        return sorted_mems[:k]
