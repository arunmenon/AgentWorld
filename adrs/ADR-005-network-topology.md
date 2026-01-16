# ADR-005: Network Topology Architecture

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: Identified topology gap across all frameworks

## Context

**Critical Gap (from ADR-001):**
> "No LLM-native framework provides explicit topology configuration (small-world, scale-free, hub-spoke as first-class concepts)."

**Why Topologies Matter for Simulation:**

| Topology | Structure | Real-World Analog | Use Case |
|----------|-----------|-------------------|----------|
| **Full Mesh** | Everyone ↔ Everyone | Open brainstorm | Unconstrained discussion |
| **Hub-Spoke** | Central node ↔ All others | Moderated meeting | Focus groups, interviews |
| **Hierarchical** | Tree structure | Organization chart | Corporate simulation |
| **Small-World** | Clusters + random shortcuts | Social networks | Information spread |
| **Scale-Free** | Power-law degree distribution | Influencer networks | Viral dynamics |

**Research Applications:**
- Information propagation velocity studies
- Opinion dynamics and polarization emergence
- Organizational communication efficiency
- Influence of network structure on consensus

**NetworkX Capabilities:**
```python
import networkx as nx

# Built-in generators for all major topologies
nx.complete_graph(n)              # Full mesh
nx.star_graph(n)                  # Hub-spoke
nx.balanced_tree(r, h)            # Hierarchical (branching r, height h)
nx.watts_strogatz_graph(n, k, p)  # Small-world (k neighbors, p rewire prob)
nx.barabasi_albert_graph(n, m)    # Scale-free (m edges per new node)

# Rich analysis functions
nx.clustering(G)                  # Clustering coefficient
nx.average_shortest_path_length(G)
nx.degree_centrality(G)
```

## Decision

Implement a **Topology abstraction layer** using NetworkX for all graph operations.

**Architecture:**
```
┌───────────────────────────────────────────────────────────┐
│                   Topology (Abstract Base)                 │
│  ─────────────────────────────────────────────────────── │
│  + graph: nx.Graph | nx.DiGraph                           │
│  + build(agent_ids, **kwargs) → None [abstract]          │
│  + add_node(agent_id) → None                             │
│  + add_edge(agent1, agent2, weight) → None               │
│  + get_neighbors(agent_id) → List[str]                   │
│  + can_communicate(sender, receiver) → bool              │
│  + get_shortest_path(from, to) → List[str]               │
│  + get_metrics() → TopologyMetrics                       │
└───────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│MeshTopology │    │HubSpokeTopo  │    │SmallWorldTopo  │
│             │    │              │    │                │
│nx.complete_ │    │nx.star_graph │    │nx.watts_       │
│graph(n)     │    │+ relabeling  │    │strogatz_graph  │
└─────────────┘    └──────────────┘    └────────────────┘
```

### Base Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union
import networkx as nx

@dataclass
class TopologyMetrics:
    """Network analysis metrics."""
    node_count: int
    edge_count: int
    density: float
    is_connected: bool
    clustering_coefficient: Optional[float] = None  # None if not applicable
    avg_path_length: Optional[float] = None  # None if disconnected
    diameter: Optional[int] = None  # None if disconnected
    degree_distribution: dict = None

class Topology(ABC):
    """Abstract base for all topology types."""

    def __init__(self, directed: bool = False):
        """
        Args:
            directed: If True, use DiGraph for asymmetric communication
        """
        self.graph: Union[nx.Graph, nx.DiGraph] = (
            nx.DiGraph() if directed else nx.Graph()
        )
        self._directed = directed

    @abstractmethod
    def build(self, agent_ids: List[str], **kwargs) -> None:
        """Build topology with given agents. Must be implemented by subclasses."""
        pass

    def add_node(self, agent_id: str) -> None:
        """Add a node to the topology."""
        self.graph.add_node(agent_id)

    def remove_node(self, agent_id: str) -> None:
        """Remove a node and all its edges."""
        if agent_id in self.graph:
            self.graph.remove_node(agent_id)

    def add_edge(self, agent1: str, agent2: str, weight: float = 1.0) -> None:
        """Add an edge between agents with optional weight."""
        self.graph.add_edge(agent1, agent2, weight=weight)

    def get_neighbors(self, agent_id: str) -> List[str]:
        """Who can this agent directly communicate with?"""
        if agent_id not in self.graph:
            return []
        return list(self.graph.neighbors(agent_id))

    def can_communicate(self, sender: str, receiver: str) -> bool:
        """Check if direct communication is allowed."""
        return self.graph.has_edge(sender, receiver)

    def can_reach(self, sender: str, receiver: str) -> bool:
        """Check if multi-hop communication is possible."""
        if sender not in self.graph or receiver not in self.graph:
            return False
        return nx.has_path(self.graph, sender, receiver)

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Get shortest path between agents, or None if unreachable."""
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_metrics(self) -> TopologyMetrics:
        """Compute network analysis metrics with safe handling."""
        n = self.graph.number_of_nodes()
        m = self.graph.number_of_edges()

        # Check connectivity
        if self._directed:
            is_connected = nx.is_weakly_connected(self.graph) if n > 0 else True
        else:
            is_connected = nx.is_connected(self.graph) if n > 0 else True

        metrics = TopologyMetrics(
            node_count=n,
            edge_count=m,
            density=nx.density(self.graph) if n > 0 else 0.0,
            is_connected=is_connected,
            degree_distribution=dict(self.graph.degree()) if n > 0 else {}
        )

        # Only compute these for connected graphs
        if is_connected and n > 1:
            try:
                if self._directed:
                    # Use underlying undirected graph for clustering
                    metrics.clustering_coefficient = nx.average_clustering(
                        self.graph.to_undirected()
                    )
                else:
                    metrics.clustering_coefficient = nx.average_clustering(self.graph)
                metrics.avg_path_length = nx.average_shortest_path_length(self.graph)
                metrics.diameter = nx.diameter(self.graph)
            except nx.NetworkXError:
                pass  # Leave as None for disconnected components

        return metrics
```

### Hub-Spoke Topology (with proper hub mapping)

```python
class HubSpokeTopology(Topology):
    """Star topology with designated hub agent."""

    def build(self, agent_ids: List[str], hub_id: str = None, **kwargs) -> None:
        """
        Build hub-spoke topology.

        Args:
            agent_ids: All agent IDs (must include hub_id if specified)
            hub_id: ID of the hub agent. If None, first agent is hub.
        """
        if not agent_ids:
            return

        # Determine hub
        if hub_id is None:
            hub_id = agent_ids[0]
        elif hub_id not in agent_ids:
            raise ValueError(f"hub_id '{hub_id}' not in agent_ids")

        self.hub_id = hub_id

        # Build star graph with proper labeling
        # nx.star_graph creates nodes 0, 1, 2, ... with 0 as center
        n = len(agent_ids)
        star = nx.star_graph(n - 1)

        # Map numeric nodes to agent IDs
        # Node 0 (center) -> hub_id
        # Nodes 1, 2, ... -> other agents
        other_agents = [a for a in agent_ids if a != hub_id]
        mapping = {0: hub_id}
        mapping.update({i + 1: agent for i, agent in enumerate(other_agents)})

        self.graph = nx.relabel_nodes(star, mapping)
```

### Small-World Topology (with validation)

```python
class SmallWorldTopology(Topology):
    """Watts-Strogatz small-world network."""

    def build(self, agent_ids: List[str], k: int = 4, p: float = 0.3, **kwargs) -> None:
        """
        Build small-world topology.

        Args:
            agent_ids: List of agent IDs
            k: Each node connected to k nearest neighbors (must be even, < n)
            p: Probability of rewiring each edge (0 = ring, 1 = random)

        Raises:
            ValueError: If k is invalid for the given number of agents
        """
        n = len(agent_ids)

        # Validate parameters
        if n < 3:
            # Fall back to complete graph for tiny networks
            self.graph = nx.complete_graph(agent_ids)
            return

        if k % 2 != 0:
            k = k + 1  # Round up to even
        if k >= n:
            k = n - 1 if (n - 1) % 2 == 0 else n - 2
        if k < 2:
            k = 2

        if not 0.0 <= p <= 1.0:
            raise ValueError(f"p must be in [0, 1], got {p}")

        # Build and relabel
        self.graph = nx.watts_strogatz_graph(n, k, p)
        mapping = {i: aid for i, aid in enumerate(agent_ids)}
        self.graph = nx.relabel_nodes(self.graph, mapping)
```

### Topology Types Summary

| Class | NetworkX Generator | Parameters | Notes |
|-------|-------------------|------------|-------|
| `MeshTopology` | `complete_graph(n)` | None | All-to-all |
| `HubSpokeTopology` | `star_graph(n)` + relabel | `hub_id` | Hub must be valid agent |
| `HierarchicalTopology` | `balanced_tree(r, h)` | `branching_factor` | Tree structure |
| `SmallWorldTopology` | `watts_strogatz_graph` | `k`, `p` | Validates k is even, < n |
| `ScaleFreeTopology` | `barabasi_albert_graph` | `m` | Power-law degree |
| `CustomTopology` | User-provided | `nx.Graph` | Full control |

### Message Routing Modes

```python
class RoutingMode(Enum):
    DIRECT_ONLY = "direct"      # Can only message neighbors
    MULTI_HOP = "multi_hop"     # Can message anyone reachable
    BROADCAST = "broadcast"     # Topology ignored for broadcasts
```

## Consequences

**Positive:**
- Full topology flexibility not available in any existing LLM framework
- NetworkX is mature (15+ years), well-documented, performant
- Rich network metrics available (with safe disconnected handling)
- Easy to add new topology types
- Enables rigorous network structure experiments
- Supports both directed and undirected graphs

**Negative:**
- Must manage message routing based on topology in World
- Dynamic topology changes need careful handling
- Additional complexity vs simple broadcast model

**Features Enabled:**
- Information propagation studies
- Controlled experiments varying network structure
- Realistic social network simulation
- Organizational hierarchy modeling
- Asymmetric influence flows (via directed graphs)

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): Topology gap identified
- [ADR-009](./ADR-009-use-case-scenarios.md): Scenarios use topology for communication patterns
- [ADR-010](./ADR-010-evaluation-metrics.md): Computes network metrics
