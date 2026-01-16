"""Step execution models and three-phase execution model.

This module implements the step-based synchronous execution model
from ADR-011 with three phases: PERCEIVE, ACT, COMMIT.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StepPhase(str, Enum):
    """Phases within a simulation step.

    Per ADR-011, each step has three phases:
    1. PERCEIVE: All agents receive pending messages and observations
    2. ACT: Agents generate responses (parallelizable)
    3. COMMIT: Atomic state update
    """

    PERCEIVE = "perceive"  # Agents receive pending messages and observations
    ACT = "act"  # Agents generate responses (parallelizable)
    COMMIT = "commit"  # Atomic state update


class StepStatus(str, Enum):
    """Status of a step execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Types of agent actions."""

    SPEAK = "speak"  # Agent speaks/sends message
    THINK = "think"  # Agent thinks (internal)
    OBSERVE = "observe"  # Agent observes
    IDLE = "idle"  # Agent does nothing
    ERROR = "error"  # Agent encountered error


@dataclass
class AgentAction:
    """Result of an agent's action during the ACT phase."""

    agent_id: str
    action_type: ActionType
    content: str = ""
    receiver_id: str | None = None
    step: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "action_type": self.action_type.value,
            "content": self.content,
            "receiver_id": self.receiver_id,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class StepResult:
    """Result of executing a simulation step."""

    step: int
    status: StepStatus
    actions: list[AgentAction] = field(default_factory=list)
    duration_seconds: float = 0.0
    messages_sent: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step,
            "status": self.status.value,
            "actions": [a.to_dict() for a in self.actions],
            "duration_seconds": self.duration_seconds,
            "messages_sent": self.messages_sent,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class StepContext:
    """Context passed to agents during step execution."""

    step_number: int
    simulation_id: str
    agent_ordering: list[str]  # Agent IDs in execution order
    pending_messages: list[Any] = field(default_factory=list)  # Messages to be delivered
    seed: int | None = None  # For deterministic behavior
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_agent_seed(self, agent_id: str) -> int | None:
        """Get deterministic seed for an agent at this step.

        Args:
            agent_id: Agent ID

        Returns:
            Deterministic seed or None if no seed configured
        """
        if self.seed is None:
            return None
        # Derive agent-specific seed from step seed
        return hash((self.seed, self.step_number, agent_id)) & 0xFFFFFFFF


@dataclass
class StepEvent:
    """Event emitted during step execution."""

    event_type: str
    step: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


# Step event types
class StepEventType:
    """Step event type constants."""

    STEP_STARTED = "step_started"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    STEP_COMPLETED = "step_completed"
    STEP_TIMEOUT = "step_timeout"
    STEP_CANCELLED = "step_cancelled"
