"""Reasoning capture during agent execution per ADR-015."""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Generator

from agentworld.reasoning.config import VisibilityConfig
from agentworld.reasoning.trace import ReasoningStep, ReasoningTrace

if TYPE_CHECKING:
    from agentworld.memory.base import Memory


class ReasoningCapture:
    """Captures reasoning traces during agent execution."""

    def __init__(
        self,
        config: VisibilityConfig | None = None,
        on_trace_complete: Callable[[ReasoningTrace], None] | None = None,
    ) -> None:
        """
        Initialize reasoning capture.

        Args:
            config: Visibility configuration
            on_trace_complete: Callback when a trace is completed
        """
        self.config = config or VisibilityConfig()
        self._current_trace: ReasoningTrace | None = None
        self._on_trace_complete = on_trace_complete
        self._traces: list[ReasoningTrace] = []

    @contextmanager
    def trace(
        self, agent_id: str, simulation_step: int
    ) -> Generator[ReasoningTrace, None, None]:
        """
        Context manager for capturing a reasoning trace.

        Args:
            agent_id: ID of the agent being traced
            simulation_step: Current simulation step

        Yields:
            ReasoningTrace for the current action
        """
        self._current_trace = ReasoningTrace(
            agent_id=agent_id,
            simulation_step=simulation_step,
            action_id=str(uuid.uuid4()),
            started_at=datetime.now(timezone.utc),
        )

        try:
            yield self._current_trace
        finally:
            self._current_trace.complete()
            self._emit_trace(self._current_trace)
            self._current_trace = None

    def _emit_trace(self, trace: ReasoningTrace) -> None:
        """Emit completed trace."""
        self._traces.append(trace)
        if self._on_trace_complete:
            self._on_trace_complete(trace)

    def log_prompt(self, prompt: str, prompt_type: str = "user") -> None:
        """
        Log a prompt being sent to LLM.

        Args:
            prompt: The prompt content
            prompt_type: Type of prompt ("system", "user", "assistant")
        """
        if not self._current_trace:
            return

        if not self.config.capture_system_prompts and prompt_type == "system":
            return

        self._current_trace.add_step(
            ReasoningStep(
                step_type="prompt",
                timestamp=datetime.now(timezone.utc),
                content=prompt,
                metadata={"prompt_type": prompt_type},
            )
        )

    def log_completion(self, completion: str, tokens: int = 0) -> None:
        """
        Log LLM completion.

        Args:
            completion: The completion content
            tokens: Number of tokens used
        """
        if not self._current_trace:
            return

        self._current_trace.tokens_used += tokens
        self._current_trace.add_step(
            ReasoningStep(
                step_type="completion",
                timestamp=datetime.now(timezone.utc),
                content=completion,
                metadata={"tokens": tokens},
            )
        )

    def log_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], output: str
    ) -> None:
        """
        Log agent tool usage.

        Args:
            tool_name: Name of the tool called
            tool_input: Input arguments to the tool
            output: Output from the tool
        """
        if not self._current_trace or not self.config.capture_tool_calls:
            return

        self._current_trace.add_step(
            ReasoningStep(
                step_type="tool_call",
                timestamp=datetime.now(timezone.utc),
                content=f"Tool: {tool_name}\nInput: {json.dumps(tool_input)}\nOutput: {output}",
                metadata={"tool": tool_name, "input": tool_input},
            )
        )

    def log_memory_retrieval(
        self,
        query: str,
        retrieved: list["Memory"] | list[Any],
        scores: list[float] | None = None,
    ) -> None:
        """
        Log memory retrieval for context.

        Args:
            query: The retrieval query
            retrieved: List of retrieved memories
            scores: Relevance scores for each memory
        """
        if not self._current_trace or not self.config.capture_memory_retrieval:
            return

        # Extract memory IDs safely
        memory_ids = []
        for m in retrieved:
            if hasattr(m, "id"):
                memory_ids.append(m.id)
            elif isinstance(m, dict) and "id" in m:
                memory_ids.append(m["id"])
            else:
                memory_ids.append(str(m)[:50])

        self._current_trace.add_step(
            ReasoningStep(
                step_type="memory_retrieval",
                timestamp=datetime.now(timezone.utc),
                content=f"Query: {query}\nRetrieved {len(retrieved)} memories",
                metadata={
                    "query": query,
                    "memory_ids": memory_ids,
                    "scores": scores or [],
                },
            )
        )

    def log_chain_of_thought(self, thought: str) -> None:
        """
        Log intermediate reasoning.

        Args:
            thought: The reasoning thought
        """
        if not self._current_trace or not self.config.capture_chain_of_thought:
            return

        self._current_trace.add_step(
            ReasoningStep(
                step_type="chain_of_thought",
                timestamp=datetime.now(timezone.utc),
                content=thought,
                metadata={},
            )
        )

    def set_summary(self, summary: str) -> None:
        """
        Set human-readable summary of reasoning.

        Args:
            summary: Summary text
        """
        if self._current_trace:
            self._current_trace.summary = summary

    def set_final_action(self, action: str) -> None:
        """
        Set the final action taken.

        Args:
            action: The action content
        """
        if self._current_trace:
            self._current_trace.final_action = action

    @property
    def current_trace(self) -> ReasoningTrace | None:
        """Get the current active trace."""
        return self._current_trace

    @property
    def traces(self) -> list[ReasoningTrace]:
        """Get all completed traces."""
        return self._traces.copy()

    def clear_traces(self) -> None:
        """Clear all stored traces."""
        self._traces.clear()

    def get_traces_for_agent(self, agent_id: str) -> list[ReasoningTrace]:
        """Get all traces for a specific agent."""
        return [t for t in self._traces if t.agent_id == agent_id]

    def get_traces_for_step(self, step: int) -> list[ReasoningTrace]:
        """Get all traces for a specific simulation step."""
        return [t for t in self._traces if t.simulation_step == step]
