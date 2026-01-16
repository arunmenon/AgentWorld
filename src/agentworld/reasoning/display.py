"""CLI display for reasoning traces per ADR-015."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from agentworld.reasoning.config import VisibilityLevel
from agentworld.reasoning.trace import ReasoningStep, ReasoningTrace

if TYPE_CHECKING:
    from rich.console import Console


class ReasoningEventType(str, Enum):
    """Event types for reasoning WebSocket events."""

    THINKING_START = "reasoning.thinking_start"
    THINKING_STEP = "reasoning.thinking_step"
    THINKING_END = "reasoning.thinking_end"
    TOOL_CALL = "reasoning.tool_call"
    MEMORY_ACCESS = "reasoning.memory_access"


class CLIReasoningDisplay:
    """Display reasoning in CLI based on visibility level."""

    # Step type display configuration
    STEP_ICONS = {
        "chain_of_thought": "\U0001f4ad",  # thought balloon
        "tool_call": "\U0001f527",  # wrench
        "memory_retrieval": "\U0001f4da",  # books
        "prompt": "\U0001f4dd",  # memo
        "completion": "\U0001f4ac",  # speech balloon
    }

    def __init__(
        self,
        console: "Console | None" = None,
        visibility: VisibilityLevel = VisibilityLevel.SUMMARY,
    ) -> None:
        """
        Initialize CLI reasoning display.

        Args:
            console: Rich console for output
            visibility: Visibility level for display
        """
        if console is None:
            from rich.console import Console

            console = Console()
        self.console = console
        self.visibility = visibility

    def display_trace(self, trace: ReasoningTrace) -> None:
        """
        Display reasoning trace in CLI.

        Args:
            trace: Reasoning trace to display
        """
        if self.visibility == VisibilityLevel.NONE:
            return

        # Always show summary
        summary_text = trace.summary or trace.final_action or "No action"
        self.console.print(f"[dim]{trace.agent_id}[/dim] {summary_text}")

        if self.visibility == VisibilityLevel.SUMMARY:
            return

        # Show detailed steps
        if self.visibility in (
            VisibilityLevel.DETAILED,
            VisibilityLevel.FULL,
            VisibilityLevel.DEBUG,
        ):
            for step in trace.steps:
                self._display_step(step)

            # Show metrics in debug mode
            if self.visibility == VisibilityLevel.DEBUG:
                self.console.print(
                    f"  [dim]Tokens: {trace.tokens_used} | "
                    f"Latency: {trace.latency_ms}ms[/dim]"
                )

    def _display_step(self, step: ReasoningStep) -> None:
        """
        Display individual reasoning step.

        Args:
            step: Reasoning step to display
        """
        icon = self.STEP_ICONS.get(step.step_type, "\U00002022")  # bullet

        if step.step_type == "chain_of_thought":
            content = self._truncate(step.content, 100)
            self.console.print(f"  [italic dim]{icon} {content}[/italic dim]")

        elif step.step_type == "tool_call":
            tool = step.metadata.get("tool", "unknown")
            self.console.print(f"  [cyan]{icon} Using tool: {tool}[/cyan]")

        elif step.step_type == "memory_retrieval":
            count = len(step.metadata.get("memory_ids", []))
            self.console.print(f"  [dim]{icon} Retrieved {count} memories[/dim]")

        elif step.step_type == "prompt" and self.visibility == VisibilityLevel.FULL:
            from rich.panel import Panel

            content = self._truncate(step.content, 500)
            prompt_type = step.metadata.get("prompt_type", "user")
            self.console.print(
                Panel(content, title=f"Prompt ({prompt_type})", border_style="dim")
            )

        elif step.step_type == "completion" and self.visibility in (
            VisibilityLevel.FULL,
            VisibilityLevel.DEBUG,
        ):
            content = self._truncate(step.content, 300)
            self.console.print(f"  [green]{icon} {content}[/green]")

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def display_thinking_start(self, agent_id: str, agent_name: str | None = None) -> None:
        """
        Display thinking start indicator.

        Args:
            agent_id: ID of agent starting to think
            agent_name: Optional display name
        """
        if self.visibility == VisibilityLevel.NONE:
            return

        name = agent_name or agent_id
        self.console.print(f"[dim]{name} thinking...[/dim]")

    def display_thinking_end(
        self,
        agent_id: str,
        summary: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
    ) -> None:
        """
        Display thinking end with summary.

        Args:
            agent_id: ID of agent
            summary: Summary of reasoning
            tokens_used: Tokens consumed
            latency_ms: Time taken
        """
        if self.visibility == VisibilityLevel.NONE:
            return

        self.console.print(f"[dim]{agent_id}[/dim] {summary}")

        if self.visibility == VisibilityLevel.DEBUG and (tokens_used or latency_ms):
            self.console.print(
                f"  [dim]Tokens: {tokens_used} | Latency: {latency_ms}ms[/dim]"
            )


def create_reasoning_event(
    event_type: ReasoningEventType,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a reasoning event for WebSocket broadcast.

    Args:
        event_type: Type of reasoning event
        payload: Event payload data

    Returns:
        Event dictionary for WebSocket
    """
    return {
        "type": event_type.value,
        "payload": payload,
    }


def thinking_start_event(
    agent_id: str,
    agent_name: str,
    simulation_step: int,
) -> dict[str, Any]:
    """Create a thinking start event."""
    return create_reasoning_event(
        ReasoningEventType.THINKING_START,
        {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "simulation_step": simulation_step,
        },
    )


def thinking_step_event(
    agent_id: str,
    step_type: str,
    content: str,
    visibility: VisibilityLevel = VisibilityLevel.SUMMARY,
) -> dict[str, Any]:
    """Create a thinking step event."""
    # Redact content based on visibility
    if visibility in (VisibilityLevel.NONE, VisibilityLevel.SUMMARY):
        content = f"[{step_type}]"
    elif visibility == VisibilityLevel.DETAILED:
        content = content[:100] + "..." if len(content) > 100 else content

    return create_reasoning_event(
        ReasoningEventType.THINKING_STEP,
        {
            "agent_id": agent_id,
            "step_type": step_type,
            "content": content,
        },
    )


def thinking_end_event(
    agent_id: str,
    summary: str,
    tokens_used: int,
    latency_ms: int,
) -> dict[str, Any]:
    """Create a thinking end event."""
    return create_reasoning_event(
        ReasoningEventType.THINKING_END,
        {
            "agent_id": agent_id,
            "summary": summary,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
        },
    )
