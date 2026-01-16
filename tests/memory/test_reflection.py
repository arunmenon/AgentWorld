"""Tests for Reflection class."""

import pytest
import numpy as np
from datetime import datetime

from agentworld.memory.reflection import Reflection, ReflectionConfig


class TestReflectionConfig:
    """Tests for ReflectionConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ReflectionConfig()

        assert config.threshold == 100.0
        assert config.questions_per_reflection == 3
        assert config.memories_per_question == 10
        assert config.min_reflection_importance == 8.0
        assert config.enabled is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ReflectionConfig(
            threshold=50.0,
            questions_per_reflection=5,
            enabled=False,
        )

        assert config.threshold == 50.0
        assert config.questions_per_reflection == 5
        assert config.enabled is False


class TestReflectionCreation:
    """Tests for Reflection creation."""

    def test_creation_minimal(self):
        """Test creating reflection with minimal fields."""
        ref = Reflection(content="I think Bob is helpful")

        assert ref.content == "I think Bob is helpful"
        assert ref.id is not None
        assert ref.importance >= 8.0  # Reflections always high importance

    def test_creation_full(self):
        """Test creating reflection with all fields."""
        embedding = np.array([0.1, 0.2, 0.3])
        ref = Reflection(
            content="Insight about the discussion",
            timestamp=datetime(2024, 1, 15, 14, 0),
            importance=9.0,
            embedding=embedding,
            embedding_model="text-embedding-ada-002",
            source_memories=["obs1", "obs2", "obs3"],
            questions_addressed=["What does Bob think?"],
        )

        assert ref.importance == 9.0
        assert ref.source_memories == ["obs1", "obs2", "obs3"]
        assert ref.questions_addressed == ["What does Bob think?"]

    def test_importance_minimum_enforced(self):
        """Test that importance is at least 8.0."""
        ref = Reflection(content="Test", importance=3.0)
        assert ref.importance >= 8.0

    def test_importance_maximum_enforced(self):
        """Test that importance is at most 10.0."""
        ref = Reflection(content="Test", importance=15.0)
        assert ref.importance <= 10.0


class TestReflectionSerialization:
    """Tests for Reflection serialization."""

    def test_to_dict(self):
        """Test converting reflection to dictionary."""
        ref = Reflection(
            content="Test reflection",
            source_memories=["m1", "m2"],
            questions_addressed=["Q1?"],
        )
        data = ref.to_dict()

        assert data["content"] == "Test reflection"
        assert data["source_memories"] == ["m1", "m2"]
        assert data["questions_addressed"] == ["Q1?"]
        assert data["importance"] >= 8.0

    def test_to_dict_with_embedding(self):
        """Test to_dict includes embedding as list."""
        embedding = np.array([0.5, 0.6, 0.7])
        ref = Reflection(content="Test", embedding=embedding)
        data = ref.to_dict()

        assert data["embedding"] == [0.5, 0.6, 0.7]

    def test_from_dict(self):
        """Test creating reflection from dictionary."""
        data = {
            "id": "ref123",
            "content": "From dict reflection",
            "importance": 9.5,
            "source_memories": ["obs1", "obs2"],
            "questions_addressed": ["Why?"],
            "timestamp": "2024-01-15T15:00:00",
        }
        ref = Reflection.from_dict(data)

        assert ref.id == "ref123"
        assert ref.content == "From dict reflection"
        assert ref.importance == 9.5
        assert ref.source_memories == ["obs1", "obs2"]

    def test_from_dict_with_embedding(self):
        """Test from_dict restores embedding."""
        data = {
            "content": "With embedding",
            "embedding": [0.1, 0.2, 0.3],
        }
        ref = Reflection.from_dict(data)

        assert ref.embedding is not None
        assert len(ref.embedding) == 3

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = Reflection(
            content="Roundtrip reflection",
            importance=9.0,
            embedding=np.array([1.0, 2.0, 3.0]),
            embedding_model="test-model",
            source_memories=["a", "b"],
            questions_addressed=["Q1", "Q2"],
        )

        data = original.to_dict()
        restored = Reflection.from_dict(data)

        assert restored.content == original.content
        assert restored.importance == original.importance
        assert restored.source_memories == original.source_memories
        assert restored.questions_addressed == original.questions_addressed


class TestReflectionEmbedding:
    """Tests for embedding compatibility checking."""

    def test_has_compatible_embedding_true(self):
        """Test compatible embedding check returns True."""
        ref = Reflection(
            content="Test",
            embedding=np.array([0.1, 0.2]),
            embedding_model="model-a",
        )
        assert ref.has_compatible_embedding("model-a") is True

    def test_has_compatible_embedding_false_different_model(self):
        """Test incompatible model returns False."""
        ref = Reflection(
            content="Test",
            embedding=np.array([0.1, 0.2]),
            embedding_model="model-a",
        )
        assert ref.has_compatible_embedding("model-b") is False

    def test_has_compatible_embedding_false_no_embedding(self):
        """Test no embedding returns False."""
        ref = Reflection(content="Test")
        assert ref.has_compatible_embedding("any-model") is False
