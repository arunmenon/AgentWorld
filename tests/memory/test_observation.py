"""Tests for Observation class."""

import pytest
import numpy as np
from datetime import datetime

from agentworld.memory.observation import Observation


class TestObservationCreation:
    """Tests for Observation creation."""

    def test_creation_minimal(self):
        """Test creating observation with minimal fields."""
        obs = Observation(content="I saw something")

        assert obs.content == "I saw something"
        assert obs.id is not None
        assert obs.importance == 5.0  # default
        assert obs.embedding is None

    def test_creation_full(self):
        """Test creating observation with all fields."""
        embedding = np.array([0.1, 0.2, 0.3])
        obs = Observation(
            content="Detailed observation",
            timestamp=datetime(2024, 1, 15, 10, 30),
            importance=8.0,
            embedding=embedding,
            embedding_model="text-embedding-ada-002",
            source="alice",
            location="meeting room",
        )

        assert obs.content == "Detailed observation"
        assert obs.importance == 8.0
        assert obs.source == "alice"
        assert obs.location == "meeting room"
        assert obs.embedding_model == "text-embedding-ada-002"

    def test_importance_clamped_high(self):
        """Test that importance above 10 is clamped."""
        obs = Observation(content="Test", importance=15.0)
        assert obs.importance <= 10.0

    def test_importance_clamped_low(self):
        """Test that importance below 1 is clamped."""
        obs = Observation(content="Test", importance=-5.0)
        assert obs.importance >= 1.0


class TestObservationSerialization:
    """Tests for Observation serialization."""

    def test_to_dict(self):
        """Test converting observation to dictionary."""
        obs = Observation(
            content="Test observation",
            importance=7.0,
            source="bob",
        )
        data = obs.to_dict()

        assert data["content"] == "Test observation"
        assert data["importance"] == 7.0
        assert data["source"] == "bob"
        assert "id" in data
        assert "timestamp" in data

    def test_to_dict_with_embedding(self):
        """Test to_dict includes embedding as list."""
        embedding = np.array([0.1, 0.2, 0.3])
        obs = Observation(content="Test", embedding=embedding)
        data = obs.to_dict()

        assert data["embedding"] == [0.1, 0.2, 0.3]

    def test_from_dict(self):
        """Test creating observation from dictionary."""
        data = {
            "id": "obs123",
            "content": "From dict",
            "importance": 6.0,
            "source": "charlie",
            "timestamp": "2024-01-15T12:00:00",
        }
        obs = Observation.from_dict(data)

        assert obs.id == "obs123"
        assert obs.content == "From dict"
        assert obs.importance == 6.0
        assert obs.source == "charlie"

    def test_from_dict_with_embedding(self):
        """Test from_dict restores embedding."""
        data = {
            "content": "With embedding",
            "embedding": [0.1, 0.2, 0.3, 0.4],
        }
        obs = Observation.from_dict(data)

        assert obs.embedding is not None
        assert len(obs.embedding) == 4
        assert isinstance(obs.embedding, np.ndarray)

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = Observation(
            content="Roundtrip test",
            importance=8.5,
            source="test",
            embedding=np.array([1.0, 2.0, 3.0]),
            embedding_model="test-model",
        )

        data = original.to_dict()
        restored = Observation.from_dict(data)

        assert restored.content == original.content
        assert restored.importance == original.importance
        assert restored.source == original.source
        assert np.allclose(restored.embedding, original.embedding)


class TestObservationEmbedding:
    """Tests for embedding compatibility checking."""

    def test_has_compatible_embedding_true(self):
        """Test compatible embedding check returns True."""
        obs = Observation(
            content="Test",
            embedding=np.array([0.1, 0.2]),
            embedding_model="model-a",
        )
        assert obs.has_compatible_embedding("model-a") is True

    def test_has_compatible_embedding_false_different_model(self):
        """Test incompatible model returns False."""
        obs = Observation(
            content="Test",
            embedding=np.array([0.1, 0.2]),
            embedding_model="model-a",
        )
        assert obs.has_compatible_embedding("model-b") is False

    def test_has_compatible_embedding_false_no_embedding(self):
        """Test no embedding returns False."""
        obs = Observation(content="Test")
        assert obs.has_compatible_embedding("any-model") is False
