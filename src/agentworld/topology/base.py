"""Base topology class and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

import networkx as nx


class RoutingMode(Enum):
    """Message routing modes for topologies.

    DIRECT_ONLY: Agents can only message direct neighbors
    MULTI_HOP: Agents can message anyone reachable via path
    BROADCAST: Topology ignored for broadcast messages
    """
    DIRECT_ONLY = "direct"
    MULTI_HOP = "multi_hop"
    BROADCAST = "broadcast"


@dataclass
class TopologyMetrics:
    """Network analysis metrics.

    Attributes:
        node_count: Number of agents in the network
        edge_count: Number of connections
        density: Graph density (0-1)
        is_connected: Whether all agents can reach each other
        clustering_coefficient: Average clustering coefficient
        avg_path_length: Average shortest path length
        diameter: Maximum shortest path length
        degree_distribution: Dict of node -> degree
    """
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    is_connected: bool = True
    clustering_coefficient: Optional[float] = None
    avg_path_length: Optional[float] = None
    diameter: Optional[int] = None
    degree_distribution: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "density": self.density,
            "is_connected": self.is_connected,
            "clustering_coefficient": self.clustering_coefficient,
            "avg_path_length": self.avg_path_length,
            "diameter": self.diameter,
            "degree_distribution": self.degree_distribution,
        }


class Topology(ABC):
    """Abstract base for all topology types.

    Provides a uniform interface for different network structures
    using NetworkX for graph operations.
    """

    def __init__(self, directed: bool = False):
        """Initialize topology.

        Args:
            directed: If True, use DiGraph for asymmetric communication
        """
        self.graph: Union[nx.Graph, nx.DiGraph] = (
            nx.DiGraph() if directed else nx.Graph()
        )
        self._directed = directed
        self._topology_type: str = "base"

    @property
    def topology_type(self) -> str:
        """Get the topology type name."""
        return self._topology_type

    @abstractmethod
    def build(self, agent_ids: List[str], **kwargs) -> None:
        """Build topology with given agents.

        Must be implemented by subclasses.

        Args:
            agent_ids: List of agent identifiers
            **kwargs: Topology-specific parameters
        """
        pass

    def add_node(self, agent_id: str, **attrs) -> None:
        """Add a node to the topology.

        Args:
            agent_id: Agent identifier
            **attrs: Optional node attributes
        """
        self.graph.add_node(agent_id, **attrs)

    def remove_node(self, agent_id: str) -> None:
        """Remove a node and all its edges.

        Args:
            agent_id: Agent to remove
        """
        if agent_id in self.graph:
            self.graph.remove_node(agent_id)

    def add_edge(
        self,
        agent1: str,
        agent2: str,
        weight: float = 1.0,
        **attrs
    ) -> None:
        """Add an edge between agents.

        Args:
            agent1: First agent
            agent2: Second agent
            weight: Edge weight (default 1.0)
            **attrs: Optional edge attributes
        """
        self.graph.add_edge(agent1, agent2, weight=weight, **attrs)

    def remove_edge(self, agent1: str, agent2: str) -> None:
        """Remove edge between agents.

        Args:
            agent1: First agent
            agent2: Second agent
        """
        if self.graph.has_edge(agent1, agent2):
            self.graph.remove_edge(agent1, agent2)

    def get_neighbors(self, agent_id: str) -> List[str]:
        """Get agents this agent can directly communicate with.

        Args:
            agent_id: Agent to get neighbors for

        Returns:
            List of neighbor agent IDs
        """
        if agent_id not in self.graph:
            return []
        return list(self.graph.neighbors(agent_id))

    def can_communicate(self, sender: str, receiver: str) -> bool:
        """Check if direct communication is allowed.

        Args:
            sender: Sending agent
            receiver: Receiving agent

        Returns:
            True if direct edge exists
        """
        return self.graph.has_edge(sender, receiver)

    def can_reach(self, sender: str, receiver: str) -> bool:
        """Check if multi-hop communication is possible.

        Args:
            sender: Sending agent
            receiver: Receiving agent

        Returns:
            True if any path exists
        """
        if sender not in self.graph or receiver not in self.graph:
            return False
        return nx.has_path(self.graph, sender, receiver)

    def get_shortest_path(
        self,
        source: str,
        target: str
    ) -> Optional[List[str]]:
        """Get shortest path between agents.

        Args:
            source: Starting agent
            target: Destination agent

        Returns:
            List of agent IDs in path, or None if unreachable
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_all_nodes(self) -> List[str]:
        """Get all node IDs in the topology.

        Returns:
            List of all agent IDs
        """
        return list(self.graph.nodes())

    def get_all_edges(self) -> List[tuple]:
        """Get all edges in the topology.

        Returns:
            List of (source, target) tuples
        """
        return list(self.graph.edges())

    def get_metrics(self) -> TopologyMetrics:
        """Compute network analysis metrics.

        Returns:
            TopologyMetrics with computed values
        """
        n = self.graph.number_of_nodes()
        m = self.graph.number_of_edges()

        # Check connectivity
        if n > 0:
            if self._directed:
                is_connected = nx.is_weakly_connected(self.graph)
            else:
                is_connected = nx.is_connected(self.graph)
        else:
            is_connected = True

        metrics = TopologyMetrics(
            node_count=n,
            edge_count=m,
            density=nx.density(self.graph) if n > 0 else 0.0,
            is_connected=is_connected,
            degree_distribution=dict(self.graph.degree()) if n > 0 else {}
        )

        # Only compute these for connected graphs with multiple nodes
        if is_connected and n > 1:
            try:
                if self._directed:
                    # Use underlying undirected graph for clustering
                    undirected = self.graph.to_undirected()
                    metrics.clustering_coefficient = nx.average_clustering(undirected)
                else:
                    metrics.clustering_coefficient = nx.average_clustering(self.graph)

                metrics.avg_path_length = nx.average_shortest_path_length(self.graph)
                metrics.diameter = nx.diameter(self.graph)
            except nx.NetworkXError:
                pass  # Leave as None for disconnected components

        return metrics

    def to_dict(self) -> dict:
        """Serialize topology to dictionary.

        Returns:
            Dictionary representation for persistence
        """
        return {
            "type": self._topology_type,
            "directed": self._directed,
            "nodes": list(self.graph.nodes()),
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "weight": d.get("weight", 1.0)
                }
                for u, v, d in self.graph.edges(data=True)
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Topology":
        """Create topology from dictionary.

        Args:
            data: Dictionary with topology data

        Returns:
            Reconstructed topology
        """
        # Import here to avoid circular imports
        from agentworld.topology.types import CustomTopology

        topology = CustomTopology(directed=data.get("directed", False))
        topology._topology_type = data.get("type", "custom")

        for node in data.get("nodes", []):
            topology.add_node(node)

        for edge in data.get("edges", []):
            topology.add_edge(
                edge["source"],
                edge["target"],
                weight=edge.get("weight", 1.0)
            )

        return topology
