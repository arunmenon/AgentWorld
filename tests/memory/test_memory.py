"""Tests for memory system."""

import pytest
import asyncio
from datetime import datetime, timedelta

from agentworld.memory.base import Memory, MemoryConfig
from agentworld.memory.observation import Observation
from agentworld.memory.reflection import Reflection, ReflectionConfig
from agentworld.memory.importance import ImportanceRater
from agentworld.memory.retrieval import MemoryRetrieval, RetrievalConfig
from agentworld.memory.embeddings import EmbeddingGenerator, EmbeddingConfig


class TestObservation:
    """Tests for Observation class."""

    def test_create_observation(self):
        """Test basic observation creation."""
        obs = Observation(
            content="Test content",
            source="test_source",
        )
        assert obs.content == "Test content"
        assert obs.source == "test_source"
        assert obs.id is not None
        assert 1.0 <= obs.importance <= 10.0

    def test_observation_importance_clamp(self):
        """Test importance is clamped to valid range."""
        obs = Observation(content="Test", importance=15.0)
        assert obs.importance == 10.0

        obs2 = Observation(content="Test", importance=-5.0)
        assert obs2.importance == 1.0

    def test_observation_to_dict(self):
        """Test observation serialization."""
        obs = Observation(
            content="Test content",
            source="test",
            importance=7.5,
        )
        data = obs.to_dict()
        assert data["content"] == "Test content"
        assert data["importance"] == 7.5

    def test_observation_from_dict(self):
        """Test observation deserialization."""
        data = {
            "id": "test-id",
            "content": "Test content",
            "importance": 6.0,
            "source": "test",
            "timestamp": datetime.now().isoformat(),
        }
        obs = Observation.from_dict(data)
        assert obs.id == "test-id"
        assert obs.content == "Test content"
        assert obs.importance == 6.0


class TestReflection:
    """Tests for Reflection class."""

    def test_create_reflection(self):
        """Test basic reflection creation."""
        ref = Reflection(
            content="A synthesized insight",
            source_memories=["obs1", "obs2"],
        )
        assert ref.content == "A synthesized insight"
        assert len(ref.source_memories) == 2

    def test_reflection_importance_floor(self):
        """Test reflection importance is at least 8."""
        ref = Reflection(content="Test", importance=5.0)
        assert ref.importance == 8.0


class TestImportanceRater:
    """Tests for ImportanceRater class."""

    def test_heuristic_rating(self):
        """Test heuristic importance rating."""
        rater = ImportanceRater()

        # Simple content should have lower score
        simple_score = rater._rate_heuristic("Hello world")
        assert 1.0 <= simple_score <= 10.0

        # Content with important keywords should score higher
        important_score = rater._rate_heuristic(
            "This is very important! I believe we must make a critical decision."
        )
        assert important_score > simple_score


class TestMemory:
    """Tests for Memory class."""

    @pytest.fixture
    def memory(self):
        """Create a memory instance for testing."""
        config = MemoryConfig(use_llm_importance=False)
        return Memory(config=config)

    @pytest.mark.asyncio
    async def test_add_observation(self, memory):
        """Test adding observations to memory."""
        obs = await memory.add_observation(
            content="I saw Alice talking to Bob",
            source="observation",
        )
        assert obs is not None
        assert len(memory.observations) == 1

    @pytest.mark.asyncio
    async def test_memory_retrieval(self, memory):
        """Test basic memory retrieval."""
        await memory.add_observation("Alice likes coffee", source="alice")
        await memory.add_observation("Bob prefers tea", source="bob")
        await memory.add_observation("Charlie enjoys coding", source="charlie")

        # Retrieve should work even with simple matching
        memories = await memory.retrieve("coffee", k=2)
        assert len(memories) <= 2

    def test_clear_memory(self, memory):
        """Test clearing memory."""
        asyncio.run(memory.add_observation("Test", source="test"))
        assert len(memory.observations) > 0

        memory.clear()
        assert len(memory.observations) == 0
        assert len(memory.reflections) == 0


class TestRetrievalConfig:
    """Tests for RetrievalConfig class."""

    def test_weight_normalization(self):
        """Test that weights are normalized."""
        config = RetrievalConfig(alpha=1.0, beta=1.0, gamma=1.0)
        total = config.alpha + config.beta + config.gamma
        assert abs(total - 1.0) < 0.01

    def test_default_weights(self):
        """Test default weight values."""
        config = RetrievalConfig()
        assert config.alpha == 0.5
        assert config.beta == 0.3
        assert config.gamma == 0.2
