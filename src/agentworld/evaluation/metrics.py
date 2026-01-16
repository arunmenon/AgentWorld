"""Metrics collection for simulation evaluation per ADR-010."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentworld.topology.base import Topology


@dataclass
class SimulationMetrics:
    """Collected metrics during simulation run."""

    # Behavioral metrics
    total_messages: int = 0
    messages_per_agent: dict[str, int] = field(default_factory=dict)
    avg_response_length: float = 0.0
    interaction_matrix: dict[tuple[str, str], int] = field(default_factory=dict)

    # Memory metrics (ADR-006) - SEPARATE counters for observations and reflections
    observations_per_agent: dict[str, int] = field(default_factory=dict)
    reflections_per_agent: dict[str, int] = field(default_factory=dict)
    total_reflections: int = 0
    avg_memory_importance: float = 0.0
    retrieval_calls: int = 0
    retrieval_hit_rate: float = 0.0  # Fraction of retrievals returning results

    # Network metrics (ADR-005) - with safe handling for disconnected graphs
    clustering_coefficient: float | None = None  # None if not computable
    avg_path_length: float | None = None  # None if disconnected
    diameter: int | None = None  # None if disconnected
    degree_distribution: dict[str, int] = field(default_factory=dict)
    is_connected: bool = True

    # Cost metrics
    total_tokens: int = 0
    tokens_per_agent: dict[str, int] = field(default_factory=dict)
    api_calls: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class MessageEvent:
    """Event for message tracking."""

    sender: str
    receiver: str | None
    content: str


@dataclass
class MemoryEvent:
    """Event for memory tracking."""

    agent_id: str
    memory_type: str  # "observation" or "reflection"
    importance: float


@dataclass
class RetrievalEvent:
    """Event for memory retrieval tracking."""

    agent_id: str
    results_count: int


@dataclass
class LLMCallEvent:
    """Event for LLM call tracking."""

    tokens: int
    estimated_cost: float
    agent_id: str | None = None


class MetricsCollector:
    """
    Collect metrics during simulation via event subscription.

    Subscribes to simulation events and accumulates metrics.
    """

    def __init__(self) -> None:
        self.metrics = SimulationMetrics()
        self._importance_sum = 0.0
        self._importance_count = 0
        self._retrieval_attempts = 0
        self._retrieval_successes = 0
        self._total_response_length = 0

    def reset(self) -> None:
        """Reset all metrics for a new run."""
        self.metrics = SimulationMetrics()
        self._importance_sum = 0.0
        self._importance_count = 0
        self._retrieval_attempts = 0
        self._retrieval_successes = 0
        self._total_response_length = 0

    def on_message(self, event: MessageEvent) -> None:
        """Track message metrics."""
        self.metrics.total_messages += 1
        self.metrics.messages_per_agent[event.sender] = (
            self.metrics.messages_per_agent.get(event.sender, 0) + 1
        )

        # Track interaction pairs
        if event.receiver:
            pair = (event.sender, event.receiver)
            self.metrics.interaction_matrix[pair] = (
                self.metrics.interaction_matrix.get(pair, 0) + 1
            )

        # Update average response length
        self._total_response_length += len(event.content)
        self.metrics.avg_response_length = (
            self._total_response_length / self.metrics.total_messages
        )

    async def on_message_async(self, event: MessageEvent) -> None:
        """Async version of on_message for event bus compatibility."""
        self.on_message(event)

    def on_memory_added(self, event: MemoryEvent) -> None:
        """
        Track memory system metrics (ADR-006).

        Observations and reflections are tracked SEPARATELY
        to provide accurate memory health metrics.
        """
        # Track importance for averaging
        self._importance_sum += event.importance
        self._importance_count += 1
        self.metrics.avg_memory_importance = (
            self._importance_sum / self._importance_count
        )

        # Increment correct counter based on memory type
        if event.memory_type == "observation":
            self.metrics.observations_per_agent[event.agent_id] = (
                self.metrics.observations_per_agent.get(event.agent_id, 0) + 1
            )
        elif event.memory_type == "reflection":
            self.metrics.reflections_per_agent[event.agent_id] = (
                self.metrics.reflections_per_agent.get(event.agent_id, 0) + 1
            )
            self.metrics.total_reflections += 1

    async def on_memory_added_async(self, event: MemoryEvent) -> None:
        """Async version of on_memory_added for event bus compatibility."""
        self.on_memory_added(event)

    def on_memory_retrieval(self, event: RetrievalEvent) -> None:
        """Track memory retrieval metrics."""
        self.metrics.retrieval_calls += 1
        self._retrieval_attempts += 1
        if event.results_count > 0:
            self._retrieval_successes += 1
        self.metrics.retrieval_hit_rate = (
            self._retrieval_successes / self._retrieval_attempts
            if self._retrieval_attempts > 0
            else 0.0
        )

    async def on_memory_retrieval_async(self, event: RetrievalEvent) -> None:
        """Async version of on_memory_retrieval for event bus compatibility."""
        self.on_memory_retrieval(event)

    def on_llm_call(self, event: LLMCallEvent) -> None:
        """Track cost metrics (ADR-003)."""
        self.metrics.total_tokens += event.tokens
        self.metrics.api_calls += 1
        self.metrics.estimated_cost_usd += event.estimated_cost

        # Track per-agent if available
        if event.agent_id:
            self.metrics.tokens_per_agent[event.agent_id] = (
                self.metrics.tokens_per_agent.get(event.agent_id, 0) + event.tokens
            )

    async def on_llm_call_async(self, event: LLMCallEvent) -> None:
        """Async version of on_llm_call for event bus compatibility."""
        self.on_llm_call(event)

    def compute_network_metrics(self, topology: "Topology") -> None:
        """
        Compute network metrics (ADR-005).

        Safely handles disconnected graphs by:
        1. Always computing degree distribution
        2. Computing path metrics only for connected graphs
        3. For disconnected: computing metrics on largest connected component
        """
        import networkx as nx

        graph = topology.graph
        n = graph.number_of_nodes()

        if n == 0:
            return

        # Always compute degree distribution
        self.metrics.degree_distribution = dict(graph.degree())

        # Check connectivity (handle directed vs undirected)
        is_directed = graph.is_directed()
        if is_directed:
            self.metrics.is_connected = nx.is_weakly_connected(graph)
            # Use underlying undirected for clustering
            undirected = graph.to_undirected()
        else:
            self.metrics.is_connected = nx.is_connected(graph)
            undirected = graph

        # Clustering coefficient (always computable)
        try:
            self.metrics.clustering_coefficient = nx.average_clustering(undirected)
        except nx.NetworkXError:
            self.metrics.clustering_coefficient = None

        # Path metrics require connectivity
        if self.metrics.is_connected and n > 1:
            try:
                self.metrics.avg_path_length = nx.average_shortest_path_length(graph)
                self.metrics.diameter = nx.diameter(graph)
            except nx.NetworkXError:
                pass  # Leave as None
        elif not self.metrics.is_connected:
            # For disconnected graphs: compute on largest component
            if is_directed:
                components = list(nx.weakly_connected_components(graph))
            else:
                components = list(nx.connected_components(graph))

            if components:
                largest = max(components, key=len)
                subgraph = graph.subgraph(largest)
                if len(largest) > 1:
                    try:
                        self.metrics.avg_path_length = nx.average_shortest_path_length(
                            subgraph
                        )
                        self.metrics.diameter = nx.diameter(subgraph)
                    except nx.NetworkXError:
                        pass

    def get_metrics(self) -> SimulationMetrics:
        """Return current metrics snapshot."""
        return self.metrics

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary for serialization."""
        return {
            "behavioral": {
                "total_messages": self.metrics.total_messages,
                "messages_per_agent": self.metrics.messages_per_agent,
                "avg_response_length": self.metrics.avg_response_length,
                "interaction_matrix": {
                    f"{k[0]}->{k[1]}": v
                    for k, v in self.metrics.interaction_matrix.items()
                },
            },
            "memory": {
                "observations_per_agent": self.metrics.observations_per_agent,
                "reflections_per_agent": self.metrics.reflections_per_agent,
                "total_reflections": self.metrics.total_reflections,
                "avg_importance": self.metrics.avg_memory_importance,
                "retrieval_calls": self.metrics.retrieval_calls,
                "retrieval_hit_rate": self.metrics.retrieval_hit_rate,
            },
            "network": {
                "is_connected": self.metrics.is_connected,
                "clustering_coefficient": self.metrics.clustering_coefficient,
                "avg_path_length": self.metrics.avg_path_length,
                "diameter": self.metrics.diameter,
            },
            "cost": {
                "total_tokens": self.metrics.total_tokens,
                "api_calls": self.metrics.api_calls,
                "estimated_cost_usd": self.metrics.estimated_cost_usd,
            },
        }
