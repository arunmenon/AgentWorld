"""Core data models for AgentWorld."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class SimulationStatus(str, Enum):
    """Status of a simulation."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """A message exchanged between agents."""

    sender_id: str
    content: str
    receiver_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    step: int = 0
    simulation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "step": self.step,
            "simulation_id": self.simulation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            content=data["content"],
            timestamp=timestamp or datetime.now(UTC),
            step=data.get("step", 0),
            simulation_id=data.get("simulation_id"),
        )


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    traits: dict[str, float] = field(default_factory=dict)
    background: str = ""
    system_prompt: str | None = None
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "traits": self.traits,
            "background": self.background,
            "system_prompt": self.system_prompt,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary."""
        return cls(
            name=data["name"],
            traits=data.get("traits", {}),
            background=data.get("background", ""),
            system_prompt=data.get("system_prompt"),
            model=data.get("model"),
        )


@dataclass
class SimulationConfig:
    """Configuration for a simulation."""

    name: str
    agents: list[AgentConfig]
    steps: int = 10
    initial_prompt: str = ""
    model: str = "openai/gpt-4o-mini"
    seed: int | None = None
    temperature: float = 0.7

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "agents": [a.to_dict() for a in self.agents],
            "steps": self.steps,
            "initial_prompt": self.initial_prompt,
            "model": self.model,
            "seed": self.seed,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationConfig":
        """Create config from dictionary."""
        agents = [
            AgentConfig.from_dict(a) if isinstance(a, dict) else a
            for a in data.get("agents", [])
        ]
        return cls(
            name=data["name"],
            agents=agents,
            steps=data.get("steps", 10),
            initial_prompt=data.get("initial_prompt", ""),
            model=data.get("model", "openai/gpt-4o-mini"),
            seed=data.get("seed"),
            temperature=data.get("temperature", 0.7),
        )


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    model: str
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "tokens_used": self.tokens_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
            "model": self.model,
            "cached": self.cached,
        }
