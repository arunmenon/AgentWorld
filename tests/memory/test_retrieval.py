"""Tests for memory retrieval system."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from agentworld.memory.retrieval import MemoryRetrieval, RetrievalConfig
from agentworld.memory.observation import Observation
from agentworld.memory.reflection import Reflection


class TestRetrievalConfig:
    """Tests for RetrievalConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RetrievalConfig()

        assert config.alpha == 0.5  # relevance weight
        assert config.beta == 0.3   # recency weight
        assert config.gamma == 0.2  # importance weight
        assert config.recency_decay_hours == 24.0

    def test_weights_sum_to_one(self):
        """Test that weights are normalized to sum to 1."""
        config = RetrievalConfig(alpha=1.0, beta=1.0, gamma=1.0)

        total = config.alpha + config.beta + config.gamma
        assert 0.99 <= total <= 1.01

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetrievalConfig(
            alpha=0.6,
            beta=0.2,
            gamma=0.2,
            recency_decay_hours=48.0,
        )

        assert config.alpha == 0.6
        assert config.recency_decay_hours == 48.0


class TestMemoryRetrieval:
    """Tests for MemoryRetrieval class."""

    @pytest.fixture
    def retrieval(self):
        """Create retrieval system with mocked embedding generator."""
        mock_embeddings = MagicMock()
        mock_embeddings.embed = AsyncMock(return_value=np.array([0.1, 0.2, 0.3]))
        return MemoryRetrieval(embedding_generator=mock_embeddings)

    @pytest.fixture
    def sample_memories(self):
        """Create sample memories for testing."""
        now = datetime.now()
        return [
            Observation(
                content="Recent important event",
                timestamp=now - timedelta(hours=1),
                importance=9.0,
                embedding=np.array([0.1, 0.2, 0.3]),
            ),
            Observation(
                content="Old mundane event",
                timestamp=now - timedelta(hours=48),
                importance=2.0,
                embedding=np.array([0.9, 0.8, 0.7]),
            ),
            Observation(
                content="Recent mundane event",
                timestamp=now - timedelta(hours=2),
                importance=3.0,
                embedding=np.array([0.5, 0.5, 0.5]),
            ),
        ]

    @pytest.mark.asyncio
    async def test_retrieve_empty_memories(self, retrieval):
        """Test retrieving from empty memory list."""
        result = await retrieval.retrieve("query", [], k=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_returns_top_k(self, retrieval, sample_memories):
        """Test that retrieve returns at most k memories."""
        result = await retrieval.retrieve("test query", sample_memories, k=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_retrieve_respects_k_limit(self, retrieval, sample_memories):
        """Test that k limits the results."""
        result = await retrieval.retrieve("query", sample_memories, k=1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_retrieve_by_recency(self, retrieval, sample_memories):
        """Test retrieving by recency only."""
        result = await retrieval.retrieve_by_recency(sample_memories, k=2)

        assert len(result) == 2
        # Most recent should be first
        assert "Recent" in result[0].content

    @pytest.mark.asyncio
    async def test_retrieve_by_recency_empty(self, retrieval):
        """Test retrieve_by_recency with empty list."""
        result = await retrieval.retrieve_by_recency([], k=5)
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_by_importance(self, retrieval, sample_memories):
        """Test retrieving by importance only."""
        result = await retrieval.retrieve_by_importance(sample_memories, k=2)

        assert len(result) == 2
        # Most important should be first
        assert result[0].importance >= result[1].importance

    @pytest.mark.asyncio
    async def test_retrieve_by_importance_empty(self, retrieval):
        """Test retrieve_by_importance with empty list."""
        result = await retrieval.retrieve_by_importance([], k=5)
        assert result == []


class TestRetrievalScoring:
    """Tests for retrieval scoring methods."""

    @pytest.fixture
    def retrieval(self):
        """Create retrieval system."""
        mock_embeddings = MagicMock()
        return MemoryRetrieval(embedding_generator=mock_embeddings)

    def test_compute_relevance_no_embedding(self, retrieval):
        """Test relevance with no embedding returns 0."""
        obs = Observation(content="No embedding")
        query_embedding = np.array([0.1, 0.2, 0.3])

        relevance = retrieval._compute_relevance(obs, query_embedding)
        assert relevance == 0.0

    def test_compute_relevance_with_embedding(self, retrieval):
        """Test relevance computation with embedding."""
        obs = Observation(
            content="Has embedding",
            embedding=np.array([0.1, 0.2, 0.3]),
        )
        query_embedding = np.array([0.1, 0.2, 0.3])

        relevance = retrieval._compute_relevance(obs, query_embedding)
        assert 0.0 <= relevance <= 1.0

    def test_compute_recency_recent(self, retrieval):
        """Test recency for recent memory."""
        now = datetime.now()
        obs = Observation(
            content="Recent",
            timestamp=now - timedelta(minutes=10),
        )

        recency = retrieval._compute_recency(obs, now)
        assert recency > 0.9  # Very recent should have high score

    def test_compute_recency_old(self, retrieval):
        """Test recency for old memory."""
        now = datetime.now()
        obs = Observation(
            content="Old",
            timestamp=now - timedelta(days=7),
        )

        recency = retrieval._compute_recency(obs, now)
        assert recency < 0.1  # Old memory should have low score

    def test_compute_importance_normalized(self, retrieval):
        """Test importance normalization."""
        high_importance = Observation(content="High", importance=10.0)
        low_importance = Observation(content="Low", importance=1.0)

        high_score = retrieval._compute_importance(high_importance)
        low_score = retrieval._compute_importance(low_importance)

        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= low_score <= 1.0
        assert high_score > low_score


class TestRetrievalWithReflections:
    """Tests for retrieval with mixed memory types."""

    @pytest.fixture
    def mixed_memories(self):
        """Create mix of observations and reflections."""
        now = datetime.now()
        return [
            Observation(
                content="Observation 1",
                timestamp=now - timedelta(hours=1),
                importance=5.0,
                embedding=np.array([0.1, 0.2, 0.3]),
            ),
            Reflection(
                content="Reflection 1",
                timestamp=now - timedelta(hours=2),
                importance=9.0,  # Reflections are always high importance
                embedding=np.array([0.2, 0.3, 0.4]),
            ),
        ]

    @pytest.mark.asyncio
    async def test_retrieve_mixed_types(self, mixed_memories):
        """Test retrieving from mixed memory types."""
        mock_embeddings = MagicMock()
        mock_embeddings.embed = AsyncMock(return_value=np.array([0.15, 0.25, 0.35]))
        retrieval = MemoryRetrieval(embedding_generator=mock_embeddings)

        result = await retrieval.retrieve("query", mixed_memories, k=2)

        assert len(result) == 2
        # Should contain both types
        types = {type(m).__name__ for m in result}
        assert "Observation" in types or "Reflection" in types
