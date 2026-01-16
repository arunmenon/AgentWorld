"""Protocol definitions for AgentWorld components.

These protocols define the interfaces that components must implement,
enabling loose coupling and testability.
"""

from typing import Protocol, AsyncIterator, Any, runtime_checkable
from datetime import datetime


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Protocol for LLM provider implementations."""

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> "LLMResponseProtocol":
        """Generate a completion from the LLM."""
        ...


@runtime_checkable
class LLMResponseProtocol(Protocol):
    """Protocol for LLM response objects."""

    content: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    model: str


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol for agent implementations."""

    id: str
    name: str

    async def think(self, context: str) -> str:
        """Generate a thought based on context."""
        ...

    async def respond_to(self, message: "MessageProtocol") -> "MessageProtocol":
        """Generate a response to a message."""
        ...


@runtime_checkable
class MessageProtocol(Protocol):
    """Protocol for message objects."""

    id: str
    sender_id: str
    receiver_id: str | None
    content: str
    timestamp: datetime
    step: int


@runtime_checkable
class SimulationProtocol(Protocol):
    """Protocol for simulation implementations."""

    id: str
    name: str
    status: str

    async def step(self) -> list["MessageProtocol"]:
        """Execute one simulation step."""
        ...

    async def run(self, steps: int) -> None:
        """Run multiple simulation steps."""
        ...


@runtime_checkable
class RepositoryProtocol(Protocol):
    """Protocol for data repository implementations."""

    def save_simulation(self, simulation: Any) -> str:
        """Save a simulation and return its ID."""
        ...

    def get_simulation(self, id: str) -> Any | None:
        """Get a simulation by ID."""
        ...

    def list_simulations(self) -> list[Any]:
        """List all simulations."""
        ...

    def save_message(self, message: Any) -> str:
        """Save a message and return its ID."""
        ...

    def get_messages(self, simulation_id: str) -> list[Any]:
        """Get all messages for a simulation."""
        ...


@runtime_checkable
class TraitVectorProtocol(Protocol):
    """Protocol for trait vector implementations."""

    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

    def to_dict(self) -> dict[str, float]:
        """Convert traits to dictionary."""
        ...

    def to_prompt_description(self) -> str:
        """Generate a natural language description of traits."""
        ...
