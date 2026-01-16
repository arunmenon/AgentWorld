"""Observation (episodic memory) implementation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
import numpy as np


@dataclass
class Observation:
    """Episodic memory entry representing a specific event or experience.

    Observations are the raw experiences that agents record during simulation.
    They include conversations, observations about others, and events.

    Attributes:
        id: Unique identifier
        content: Natural language description of the observation
        timestamp: When the observation occurred
        importance: LLM-rated importance score (1-10)
        embedding: Vector embedding for semantic similarity
        embedding_model: Model used to generate embedding (for compatibility checking)
        source: Who/what caused this observation (agent name, "self", etc.)
        location: Optional spatial context
    """
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 5.0
    embedding: Optional[np.ndarray] = None
    embedding_model: Optional[str] = None
    source: str = ""
    location: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate observation fields."""
        if not 1.0 <= self.importance <= 10.0:
            self.importance = max(1.0, min(10.0, self.importance))

    def to_dict(self) -> dict:
        """Convert observation to dictionary for persistence."""
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "embedding_model": self.embedding_model,
            "source": self.source,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        """Create observation from dictionary."""
        embedding = None
        if data.get("embedding") is not None:
            embedding = np.array(data["embedding"])

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            timestamp=timestamp,
            importance=data.get("importance", 5.0),
            embedding=embedding,
            embedding_model=data.get("embedding_model"),
            source=data.get("source", ""),
            location=data.get("location", ""),
        )

    def has_compatible_embedding(self, model: str) -> bool:
        """Check if this observation's embedding is compatible with the given model."""
        if self.embedding is None:
            return False
        return self.embedding_model == model
