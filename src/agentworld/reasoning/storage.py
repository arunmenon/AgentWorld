"""Storage and export for reasoning traces per ADR-015."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from agentworld.reasoning.config import VisibilityConfig, VisibilityLevel
from agentworld.reasoning.trace import ReasoningTrace

if TYPE_CHECKING:
    from agentworld.persistence.repository import Repository


class ReasoningStorage:
    """Store and export reasoning traces."""

    def __init__(
        self,
        repository: "Repository | None" = None,
        config: VisibilityConfig | None = None,
    ) -> None:
        """
        Initialize reasoning storage.

        Args:
            repository: Database repository for persistence
            config: Visibility configuration
        """
        self._repository = repository
        self.config = config or VisibilityConfig()
        self._memory_traces: dict[str, list[ReasoningTrace]] = {}  # simulation_id -> traces

    @property
    def repository(self) -> "Repository":
        """Get repository, creating if needed."""
        if self._repository is None:
            from agentworld.persistence.database import init_db
            from agentworld.persistence.repository import Repository

            init_db()
            self._repository = Repository()
        return self._repository

    def store(
        self,
        trace: ReasoningTrace,
        simulation_id: str | None = None,
    ) -> None:
        """
        Store reasoning trace.

        Args:
            trace: Reasoning trace to store
            simulation_id: Optional simulation ID for grouping
        """
        # Store at configured export visibility level
        trace_dict = trace.to_dict(self.config.export_visibility)

        # Store in memory for quick access
        sim_id = simulation_id or "default"
        if sim_id not in self._memory_traces:
            self._memory_traces[sim_id] = []
        self._memory_traces[sim_id].append(trace)

        # Store to database if available
        try:
            self._store_to_db(trace, trace_dict, simulation_id)
        except Exception:
            # Silently fail if DB not available
            pass

    def _store_to_db(
        self,
        trace: ReasoningTrace,
        trace_dict: dict[str, Any],
        simulation_id: str | None,
    ) -> None:
        """Store trace to database."""
        # This would use a ReasoningTraceModel if defined
        # For now, store as JSON in metrics or a generic table
        pass

    def get_traces(
        self,
        simulation_id: str | None = None,
        agent_id: str | None = None,
        step: int | None = None,
    ) -> list[ReasoningTrace]:
        """
        Get stored traces with optional filters.

        Args:
            simulation_id: Filter by simulation
            agent_id: Filter by agent
            step: Filter by simulation step

        Returns:
            List of matching traces
        """
        sim_id = simulation_id or "default"
        traces = self._memory_traces.get(sim_id, [])

        if agent_id:
            traces = [t for t in traces if t.agent_id == agent_id]

        if step is not None:
            traces = [t for t in traces if t.simulation_step == step]

        return traces

    def export(
        self,
        simulation_id: str | None = None,
        visibility: VisibilityLevel | None = None,
        format: str = "jsonl",
    ) -> str:
        """
        Export reasoning traces.

        Args:
            simulation_id: Simulation to export (or all if None)
            visibility: Visibility level for export (defaults to config)
            format: Output format ("jsonl" or "json")

        Returns:
            Exported traces as string
        """
        effective_visibility = visibility or self.config.export_visibility
        traces = self.get_traces(simulation_id)

        output = []
        for trace in traces:
            # Apply visibility filter
            trace_dict = trace.to_dict(effective_visibility)

            # Can only reduce visibility from stored level
            if effective_visibility != VisibilityLevel.NONE:
                filtered = self._filter_to_visibility(trace_dict, effective_visibility)
                output.append(filtered)

        if format == "jsonl":
            return "\n".join(json.dumps(t) for t in output)
        elif format == "json":
            return json.dumps(output, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _filter_to_visibility(
        self,
        trace: dict[str, Any],
        visibility: VisibilityLevel,
    ) -> dict[str, Any]:
        """
        Filter trace data to visibility level.

        Args:
            trace: Trace dictionary to filter
            visibility: Target visibility level

        Returns:
            Filtered trace dictionary
        """
        if visibility == VisibilityLevel.NONE:
            return {}

        if visibility == VisibilityLevel.SUMMARY:
            return {
                "agent_id": trace.get("agent_id"),
                "simulation_step": trace.get("simulation_step"),
                "summary": trace.get("summary"),
                "final_action": trace.get("final_action"),
                "tokens_used": trace.get("tokens_used"),
                "latency_ms": trace.get("latency_ms"),
            }

        if visibility == VisibilityLevel.DETAILED:
            # Include steps but filter content
            result = trace.copy()
            if "steps" in result:
                result["steps"] = [
                    {
                        "type": s.get("type"),
                        "timestamp": s.get("timestamp"),
                        "content": s.get("content", "")[:100] + "..."
                        if len(s.get("content", "")) > 100
                        else s.get("content", ""),
                    }
                    for s in result["steps"]
                ]
            # Remove debug metadata
            result.pop("metadata", None)
            return result

        # FULL and DEBUG return everything
        return trace

    def clear(self, simulation_id: str | None = None) -> None:
        """
        Clear stored traces.

        Args:
            simulation_id: Clear only this simulation, or all if None
        """
        if simulation_id:
            self._memory_traces.pop(simulation_id, None)
        else:
            self._memory_traces.clear()

    def get_statistics(
        self,
        simulation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get statistics about stored traces.

        Args:
            simulation_id: Simulation to get stats for

        Returns:
            Statistics dictionary
        """
        traces = self.get_traces(simulation_id)

        if not traces:
            return {
                "total_traces": 0,
                "total_tokens": 0,
                "total_latency_ms": 0,
                "agents": [],
            }

        agents = set(t.agent_id for t in traces)
        total_tokens = sum(t.tokens_used for t in traces)
        total_latency = sum(t.latency_ms for t in traces)

        return {
            "total_traces": len(traces),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / len(traces) if traces else 0,
            "avg_tokens": total_tokens / len(traces) if traces else 0,
            "agents": list(agents),
            "steps_by_type": self._count_steps_by_type(traces),
        }

    def _count_steps_by_type(
        self,
        traces: list[ReasoningTrace],
    ) -> dict[str, int]:
        """Count reasoning steps by type."""
        counts: dict[str, int] = {}
        for trace in traces:
            for step in trace.steps:
                step_type = step.step_type
                counts[step_type] = counts.get(step_type, 0) + 1
        return counts
