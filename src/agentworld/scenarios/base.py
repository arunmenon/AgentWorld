"""Base scenario class and common types.

This module defines the base infrastructure for all scenarios
as specified in ADR-009.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class ScenarioStatus(str, Enum):
    """Status of a scenario execution."""

    PENDING = "pending"
    SETTING_UP = "setting_up"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScenarioConfig:
    """Base configuration for all scenarios."""

    name: str
    description: str = ""
    max_steps: int = 100
    seed: int | None = None  # For reproducibility
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "max_steps": self.max_steps,
            "seed": self.seed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioConfig":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            max_steps=data.get("max_steps", 100),
            seed=data.get("seed"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AgentResponse:
    """A response from an agent during a scenario."""

    agent_id: str
    content: str
    step: int
    message_type: str = "speech"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "content": self.content,
            "step": self.step,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SystemEvent:
    """A system event injected into the scenario.

    System events bypass topology constraints - they represent
    external stimuli like announcements, environment changes, etc.
    """

    content: str
    source: str = "system"
    target: str | None = None  # None = broadcast to all
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = "announcement"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_broadcast(self) -> bool:
        """Check if this event is broadcast to all agents."""
        return self.target is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "metadata": self.metadata,
        }


@dataclass
class ScenarioResult:
    """Standard result container for scenario outputs."""

    scenario_id: str
    scenario_type: str
    config: ScenarioConfig
    status: ScenarioStatus
    messages: list[Any] = field(default_factory=list)
    events: list[SystemEvent] = field(default_factory=list)
    responses: list[AgentResponse] = field(default_factory=list)
    duration_seconds: float = 0.0
    total_steps: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "messages": [m.to_dict() if hasattr(m, "to_dict") else m for m in self.messages],
            "events": [e.to_dict() for e in self.events],
            "responses": [r.to_dict() for r in self.responses],
            "duration_seconds": self.duration_seconds,
            "total_steps": self.total_steps,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "metadata": self.metadata,
        }


class Scenario(ABC):
    """Base class for simulation scenarios.

    Scenarios provide structured approaches to common simulation
    patterns like focus groups, interviews, and data generation.
    """

    def __init__(self, config: ScenarioConfig):
        """Initialize scenario.

        Args:
            config: Scenario configuration
        """
        self.config = config
        self.scenario_id = str(uuid.uuid4())[:8]
        self.status = ScenarioStatus.PENDING
        self._message_log: list[Any] = []
        self._event_log: list[SystemEvent] = []
        self._response_log: list[AgentResponse] = []
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._total_tokens = 0
        self._total_cost = 0.0

    @property
    def scenario_type(self) -> str:
        """Get the scenario type name."""
        return self.__class__.__name__.lower().replace("scenario", "")

    @property
    def messages(self) -> list[Any]:
        """Get all logged messages."""
        return self._message_log.copy()

    @property
    def events(self) -> list[SystemEvent]:
        """Get all logged events."""
        return self._event_log.copy()

    @property
    def responses(self) -> list[AgentResponse]:
        """Get all agent responses."""
        return self._response_log.copy()

    @property
    def duration_seconds(self) -> float:
        """Get scenario duration in seconds."""
        if self._start_time is None:
            return 0.0
        end = self._end_time or datetime.utcnow()
        return (end - self._start_time).total_seconds()

    @abstractmethod
    async def setup(self) -> None:
        """Configure world and agents for this scenario.

        This method should:
        - Create/configure agents
        - Set up topology
        - Initialize any scenario-specific state
        """
        pass

    @abstractmethod
    async def run(self) -> ScenarioResult:
        """Execute the scenario.

        Returns:
            ScenarioResult containing all outputs
        """
        pass

    async def teardown(self) -> None:
        """Clean up after scenario execution.

        Override this method for custom cleanup logic.
        """
        pass

    def log_message(self, message: Any) -> None:
        """Log a message.

        Args:
            message: Message to log
        """
        self._message_log.append(message)

    def log_event(self, event: SystemEvent) -> None:
        """Log a system event.

        Args:
            event: Event to log
        """
        self._event_log.append(event)

    def log_response(self, response: AgentResponse) -> None:
        """Log an agent response.

        Args:
            response: Response to log
        """
        self._response_log.append(response)

    def add_tokens(self, tokens: int) -> None:
        """Add to token count.

        Args:
            tokens: Number of tokens to add
        """
        self._total_tokens += tokens

    def add_cost(self, cost: float) -> None:
        """Add to cost.

        Args:
            cost: Cost to add
        """
        self._total_cost += cost

    def extract_responses(
        self,
        since_step: int = 0,
        filter_type: str | None = None,
        agent_ids: list[str] | None = None,
    ) -> list[AgentResponse]:
        """Extract agent responses from response log.

        Args:
            since_step: Only include responses from this step onward
            filter_type: Message type to filter (speech, thought, etc.)
            agent_ids: Filter by agent IDs

        Returns:
            List of matching AgentResponse objects
        """
        responses = self._response_log
        if since_step > 0:
            responses = [r for r in responses if r.step >= since_step]
        if filter_type:
            responses = [r for r in responses if r.message_type == filter_type]
        if agent_ids:
            responses = [r for r in responses if r.agent_id in agent_ids]
        return responses

    def build_result(
        self,
        extra_metadata: dict[str, Any] | None = None,
    ) -> ScenarioResult:
        """Build the scenario result.

        Args:
            extra_metadata: Additional metadata to include

        Returns:
            ScenarioResult instance
        """
        metadata = self.config.metadata.copy()
        if extra_metadata:
            metadata.update(extra_metadata)

        return ScenarioResult(
            scenario_id=self.scenario_id,
            scenario_type=self.scenario_type,
            config=self.config,
            status=self.status,
            messages=self._message_log,
            events=self._event_log,
            responses=self._response_log,
            duration_seconds=self.duration_seconds,
            total_steps=len(set(r.step for r in self._response_log)),
            tokens_used=self._total_tokens,
            cost=self._total_cost,
            metadata=metadata,
        )

    def _mark_started(self) -> None:
        """Mark scenario as started."""
        self.status = ScenarioStatus.RUNNING
        self._start_time = datetime.utcnow()

    def _mark_completed(self) -> None:
        """Mark scenario as completed."""
        self.status = ScenarioStatus.COMPLETED
        self._end_time = datetime.utcnow()

    def _mark_failed(self, error: str | None = None) -> None:
        """Mark scenario as failed."""
        self.status = ScenarioStatus.FAILED
        self._end_time = datetime.utcnow()
        if error:
            self.config.metadata["error"] = error

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}(id={self.scenario_id!r}, "
            f"name={self.config.name!r}, status={self.status.value})"
        )
