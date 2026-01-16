"""Reasoning trace structures per ADR-015."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agentworld.reasoning.config import VisibilityLevel


@dataclass
class ReasoningStep:
    """Single step in agent reasoning."""

    step_type: str  # "prompt", "completion", "tool_call", "memory_retrieval", "chain_of_thought"
    timestamp: datetime
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_type": self.step_type,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasoningStep":
        """Create from dictionary."""
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            step_type=data["step_type"],
            timestamp=timestamp,
            content=data["content"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for an agent action."""

    agent_id: str
    simulation_step: int
    action_id: str
    started_at: datetime
    completed_at: datetime | None = None

    # Reasoning steps
    steps: list[ReasoningStep] = field(default_factory=list)

    # Summary (always available)
    summary: str | None = None

    # Outcome
    final_action: str | None = None
    tokens_used: int = 0
    latency_ms: int = 0

    def add_step(self, step: ReasoningStep) -> None:
        """Add a reasoning step to the trace."""
        self.steps.append(step)

    def complete(self) -> None:
        """Mark the trace as completed."""
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.latency_ms = int(delta.total_seconds() * 1000)

    def to_dict(self, visibility: VisibilityLevel) -> dict[str, Any]:
        """Export trace at specified visibility level."""
        base = {
            "agent_id": self.agent_id,
            "simulation_step": self.simulation_step,
            "action_id": self.action_id,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
        }

        if visibility == VisibilityLevel.NONE:
            return base

        if visibility in (
            VisibilityLevel.SUMMARY,
            VisibilityLevel.DETAILED,
            VisibilityLevel.FULL,
            VisibilityLevel.DEBUG,
        ):
            base["summary"] = self.summary
            base["final_action"] = self.final_action

        if visibility in (
            VisibilityLevel.DETAILED,
            VisibilityLevel.FULL,
            VisibilityLevel.DEBUG,
        ):
            base["steps"] = [self._format_step(s, visibility) for s in self.steps]

        if visibility == VisibilityLevel.DEBUG:
            base["metadata"] = {
                "started_at": (
                    self.started_at.isoformat() if self.started_at else None
                ),
                "completed_at": (
                    self.completed_at.isoformat() if self.completed_at else None
                ),
            }

        return base

    def _format_step(
        self, step: ReasoningStep, visibility: VisibilityLevel
    ) -> dict[str, Any]:
        """Format a step based on visibility level."""
        result: dict[str, Any] = {
            "type": step.step_type,
            "timestamp": step.timestamp.isoformat(),
        }

        if visibility == VisibilityLevel.FULL or visibility == VisibilityLevel.DEBUG:
            result["content"] = step.content
            result["metadata"] = step.metadata
        elif visibility == VisibilityLevel.DETAILED:
            # Redact sensitive content
            result["content"] = self._redact_content(step.content)
            result["metadata"] = {
                k: v
                for k, v in step.metadata.items()
                if k not in ("raw_prompt", "api_key")
            }

        return result

    def _redact_content(self, content: str) -> str:
        """Redact sensitive information from content."""
        # Redact API keys
        content = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]", content)
        content = re.sub(r"Bearer\s+[a-zA-Z0-9\-_.]+", "[REDACTED_BEARER]", content)
        # Redact emails
        content = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[REDACTED_EMAIL]",
            content,
        )
        return content

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasoningTrace":
        """Create from dictionary."""
        started_at = data.get("started_at") or data.get("metadata", {}).get(
            "started_at"
        )
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        elif started_at is None:
            started_at = datetime.now(timezone.utc)

        completed_at = data.get("completed_at") or data.get("metadata", {}).get(
            "completed_at"
        )
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        steps = []
        for step_data in data.get("steps", []):
            steps.append(ReasoningStep.from_dict(step_data))

        return cls(
            agent_id=data["agent_id"],
            simulation_step=data["simulation_step"],
            action_id=data["action_id"],
            started_at=started_at,
            completed_at=completed_at,
            steps=steps,
            summary=data.get("summary"),
            final_action=data.get("final_action"),
            tokens_used=data.get("tokens_used", 0),
            latency_ms=data.get("latency_ms", 0),
        )
