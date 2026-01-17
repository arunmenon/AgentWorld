"""Stimulus injection system for scenarios.

This module provides mechanisms for injecting external stimuli
into running scenarios - like moderator questions, system
announcements, or environmental changes.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Awaitable
import uuid


class StimulusType(str, Enum):
    """Types of stimuli that can be injected."""

    QUESTION = "question"  # A question posed to participants
    ANNOUNCEMENT = "announcement"  # System-wide announcement
    PROMPT = "prompt"  # Specific prompt to one agent
    TOPIC_CHANGE = "topic_change"  # Change discussion topic
    INSTRUCTION = "instruction"  # Instruction to agents
    ENVIRONMENT = "environment"  # Environmental change


@dataclass
class Stimulus:
    """A stimulus to be injected into a scenario.

    Stimuli bypass normal topology constraints - they represent
    external influences on the simulation.
    """

    content: str
    stimulus_type: StimulusType
    target_agents: list[str] | None = None  # None = broadcast to all
    source: str = "system"  # Who/what sent it
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.utcnow)
    injected_at: datetime | None = None
    injected_at_step: int | None = None
    priority: int = 0  # Higher = more urgent
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_broadcast(self) -> bool:
        """Check if stimulus is broadcast to all agents."""
        return self.target_agents is None or len(self.target_agents) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "stimulus_type": self.stimulus_type.value,
            "target_agents": self.target_agents,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "injected_at": self.injected_at.isoformat() if self.injected_at else None,
            "injected_at_step": self.injected_at_step,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stimulus":
        """Create from dictionary."""
        stimulus_type = data.get("stimulus_type")
        if isinstance(stimulus_type, str):
            stimulus_type = StimulusType(stimulus_type)
        else:
            stimulus_type = StimulusType.PROMPT

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now(UTC)

        injected_at = data.get("injected_at")
        if isinstance(injected_at, str):
            injected_at = datetime.fromisoformat(injected_at)

        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            content=data["content"],
            stimulus_type=stimulus_type,
            target_agents=data.get("target_agents"),
            source=data.get("source", "system"),
            created_at=created_at,
            injected_at=injected_at,
            injected_at_step=data.get("injected_at_step"),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )


# Convenience factory functions


def create_question(
    content: str,
    target_agents: list[str] | None = None,
    source: str = "moderator",
) -> Stimulus:
    """Create a question stimulus.

    Args:
        content: Question text
        target_agents: Optional list of target agents
        source: Who is asking

    Returns:
        Stimulus instance
    """
    return Stimulus(
        content=content,
        stimulus_type=StimulusType.QUESTION,
        target_agents=target_agents,
        source=source,
    )


def create_announcement(
    content: str,
    source: str = "system",
) -> Stimulus:
    """Create an announcement stimulus.

    Args:
        content: Announcement text
        source: Who is announcing

    Returns:
        Stimulus instance
    """
    return Stimulus(
        content=content,
        stimulus_type=StimulusType.ANNOUNCEMENT,
        target_agents=None,  # Broadcast
        source=source,
    )


def create_topic_change(
    new_topic: str,
    source: str = "moderator",
) -> Stimulus:
    """Create a topic change stimulus.

    Args:
        new_topic: New discussion topic
        source: Who is changing the topic

    Returns:
        Stimulus instance
    """
    return Stimulus(
        content=f"Let's now discuss: {new_topic}",
        stimulus_type=StimulusType.TOPIC_CHANGE,
        target_agents=None,  # Broadcast
        source=source,
        metadata={"topic": new_topic},
    )


def create_prompt(
    content: str,
    target_agent: str,
    source: str = "system",
) -> Stimulus:
    """Create a prompt stimulus for a specific agent.

    Args:
        content: Prompt text
        target_agent: Target agent ID
        source: Who is prompting

    Returns:
        Stimulus instance
    """
    return Stimulus(
        content=content,
        stimulus_type=StimulusType.PROMPT,
        target_agents=[target_agent],
        source=source,
    )


class StimulusInjector:
    """Manages stimulus injection into scenarios.

    Provides queuing, scheduling, and delivery of stimuli
    to agents in a scenario.
    """

    def __init__(self):
        """Initialize injector."""
        self._pending: list[Stimulus] = []
        self._history: list[Stimulus] = []
        self._on_inject_callbacks: list[Callable[[Stimulus], Awaitable[None] | None]] = []

    @property
    def pending(self) -> list[Stimulus]:
        """Get pending stimuli."""
        return self._pending.copy()

    @property
    def history(self) -> list[Stimulus]:
        """Get injection history."""
        return self._history.copy()

    def on_inject(
        self, callback: Callable[[Stimulus], Awaitable[None] | None]
    ) -> None:
        """Register callback for stimulus injection.

        Args:
            callback: Function called when stimulus is injected
        """
        self._on_inject_callbacks.append(callback)

    def queue(self, stimulus: Stimulus) -> None:
        """Queue a stimulus for injection.

        Args:
            stimulus: Stimulus to queue
        """
        self._pending.append(stimulus)
        # Sort by priority (highest first)
        self._pending.sort(key=lambda s: -s.priority)

    def queue_question(
        self,
        content: str,
        target_agents: list[str] | None = None,
        source: str = "moderator",
    ) -> Stimulus:
        """Queue a question stimulus.

        Args:
            content: Question text
            target_agents: Optional target agents
            source: Question source

        Returns:
            Created and queued Stimulus
        """
        stimulus = create_question(content, target_agents, source)
        self.queue(stimulus)
        return stimulus

    def queue_announcement(
        self,
        content: str,
        source: str = "system",
    ) -> Stimulus:
        """Queue an announcement stimulus.

        Args:
            content: Announcement text
            source: Announcement source

        Returns:
            Created and queued Stimulus
        """
        stimulus = create_announcement(content, source)
        self.queue(stimulus)
        return stimulus

    def pop_next(self) -> Stimulus | None:
        """Get and remove next stimulus to inject.

        Returns:
            Next stimulus or None if queue is empty
        """
        if not self._pending:
            return None
        return self._pending.pop(0)

    def peek_next(self) -> Stimulus | None:
        """Peek at next stimulus without removing.

        Returns:
            Next stimulus or None if queue is empty
        """
        if not self._pending:
            return None
        return self._pending[0]

    async def inject(
        self,
        stimulus: Stimulus,
        step: int,
    ) -> None:
        """Mark stimulus as injected and notify callbacks.

        Args:
            stimulus: Stimulus to inject
            step: Current step number
        """
        stimulus.injected_at = datetime.now(UTC)
        stimulus.injected_at_step = step
        self._history.append(stimulus)

        # Notify callbacks
        for callback in self._on_inject_callbacks:
            import asyncio

            result = callback(stimulus)
            if asyncio.iscoroutine(result):
                await result

    async def inject_next(self, step: int) -> Stimulus | None:
        """Pop and inject the next stimulus.

        Args:
            step: Current step number

        Returns:
            Injected stimulus or None if queue is empty
        """
        stimulus = self.pop_next()
        if stimulus:
            await self.inject(stimulus, step)
        return stimulus

    def clear_pending(self) -> int:
        """Clear all pending stimuli.

        Returns:
            Number of stimuli cleared
        """
        count = len(self._pending)
        self._pending.clear()
        return count

    def get_history_for_step(self, step: int) -> list[Stimulus]:
        """Get stimuli injected at a specific step.

        Args:
            step: Step number

        Returns:
            List of stimuli injected at that step
        """
        return [s for s in self._history if s.injected_at_step == step]

    def get_history_for_agent(self, agent_id: str) -> list[Stimulus]:
        """Get stimuli targeted at a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of stimuli for that agent
        """
        return [
            s
            for s in self._history
            if s.is_broadcast or (s.target_agents and agent_id in s.target_agents)
        ]
