"""Topology type implementations.

Provides 5 main topology types plus custom topology support:
- MeshTopology: Full mesh (everyone connected to everyone)
- HubSpokeTopology: Star with central hub
- HierarchicalTopology: Tree structure
- SmallWorldTopology: Watts-Strogatz small-world network
- ScaleFreeTopology: Barabasi-Albert scale-free network
- CustomTopology: User-defined topology
"""

from typing import List, Optional

import networkx as nx

from agentworld.topology.base import Topology


class MeshTopology(Topology):
    """Full mesh topology where every agent can communicate with every other.

    Also known as complete graph. Useful for unconstrained discussions
    and brainstorming scenarios.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "mesh"

    def build(self, agent_ids: List[str], **kwargs) -> None:
        """Build full mesh topology.

        Args:
            agent_ids: List of agent IDs to include
        """
        if not agent_ids:
            return

        # Create complete graph
        complete = nx.complete_graph(len(agent_ids))

        # Map numeric nodes to agent IDs
        mapping = {i: aid for i, aid in enumerate(agent_ids)}

        # Apply mapping
        self.graph = nx.relabel_nodes(complete, mapping)

        # Convert to DiGraph if needed
        if self._directed:
            self.graph = self.graph.to_directed()


class HubSpokeTopology(Topology):
    """Hub-spoke (star) topology with designated central hub.

    The hub can communicate with all other agents, but spoke agents
    can only communicate with the hub. Useful for moderated meetings,
    focus groups, and interview scenarios.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "hub_spoke"
        self.hub_id: Optional[str] = None

    def build(
        self,
        agent_ids: List[str],
        hub_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Build hub-spoke topology.

        Args:
            agent_ids: All agent IDs (must include hub_id if specified)
            hub_id: ID of the hub agent. If None, first agent is hub.

        Raises:
            ValueError: If hub_id not in agent_ids
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

        if self._directed:
            self.graph = self.graph.to_directed()


class HierarchicalTopology(Topology):
    """Hierarchical tree topology representing organizational structure.

    Creates a balanced tree with configurable branching factor.
    Useful for corporate simulations and hierarchical decision-making.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "hierarchical"
        self.root_id: Optional[str] = None

    def build(
        self,
        agent_ids: List[str],
        branching_factor: int = 2,
        root_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Build hierarchical tree topology.

        Args:
            agent_ids: All agent IDs
            branching_factor: Children per parent node (default 2)
            root_id: ID of root agent. If None, first agent is root.

        Note:
            The tree may not use all agents if the tree structure
            doesn't accommodate them all.
        """
        if not agent_ids:
            return

        if root_id is None:
            root_id = agent_ids[0]
        elif root_id not in agent_ids:
            raise ValueError(f"root_id '{root_id}' not in agent_ids")

        self.root_id = root_id
        n = len(agent_ids)

        # Calculate tree height needed to fit all agents
        # For branching factor r, a tree of height h has (r^(h+1) - 1)/(r-1) nodes
        import math
        if branching_factor > 1:
            height = max(1, int(math.ceil(math.log(n * (branching_factor - 1) + 1, branching_factor))) - 1)
        else:
            height = n - 1  # Linear tree for branching factor 1

        # Create balanced tree
        tree = nx.balanced_tree(branching_factor, height)

        # Relabel nodes
        other_agents = [a for a in agent_ids if a != root_id]
        mapping = {0: root_id}

        # Use BFS order for assignment
        node_idx = 1
        for i, node in enumerate(list(tree.nodes())[1:]):
            if i < len(other_agents):
                mapping[node] = other_agents[i]
            node_idx += 1

        # Remove nodes that don't have agent mappings
        nodes_to_remove = [n for n in tree.nodes() if n not in mapping]
        tree.remove_nodes_from(nodes_to_remove)

        self.graph = nx.relabel_nodes(tree, mapping)

        if self._directed:
            self.graph = self.graph.to_directed()


class SmallWorldTopology(Topology):
    """Watts-Strogatz small-world network.

    Combines high clustering (like regular lattice) with short path lengths
    (like random graphs). Models social networks where people have local
    clusters but also some random long-range connections.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "small_world"

    def build(
        self,
        agent_ids: List[str],
        k: int = 4,
        p: float = 0.3,
        **kwargs
    ) -> None:
        """Build small-world topology.

        Args:
            agent_ids: List of agent IDs
            k: Each node connected to k nearest neighbors (must be even, < n)
            p: Probability of rewiring each edge (0 = ring, 1 = random)

        Raises:
            ValueError: If p is not in [0, 1]
        """
        n = len(agent_ids)

        if n < 3:
            # Fall back to complete graph for tiny networks
            self.graph = nx.complete_graph(agent_ids)
            if self._directed:
                self.graph = self.graph.to_directed()
            return

        # Validate and adjust k
        if k % 2 != 0:
            k = k + 1  # Round up to even
        if k >= n:
            k = n - 1 if (n - 1) % 2 == 0 else n - 2
        if k < 2:
            k = 2

        if not 0.0 <= p <= 1.0:
            raise ValueError(f"p must be in [0, 1], got {p}")

        # Build Watts-Strogatz graph
        self.graph = nx.watts_strogatz_graph(n, k, p)

        # Relabel nodes
        mapping = {i: aid for i, aid in enumerate(agent_ids)}
        self.graph = nx.relabel_nodes(self.graph, mapping)

        if self._directed:
            self.graph = self.graph.to_directed()


class ScaleFreeTopology(Topology):
    """Barabasi-Albert scale-free network.

    Creates a network with power-law degree distribution where some nodes
    (hubs) have many more connections than others. Models networks with
    influencers or viral dynamics.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "scale_free"

    def build(
        self,
        agent_ids: List[str],
        m: int = 2,
        **kwargs
    ) -> None:
        """Build scale-free topology.

        Args:
            agent_ids: List of agent IDs
            m: Number of edges to attach from new node to existing nodes
               (higher m = more connected network)
        """
        n = len(agent_ids)

        if n < 2:
            # Can't create BA graph with < 2 nodes
            if agent_ids:
                self.graph.add_node(agent_ids[0])
            return

        # Adjust m if necessary
        if m >= n:
            m = n - 1
        if m < 1:
            m = 1

        # Build Barabasi-Albert graph
        self.graph = nx.barabasi_albert_graph(n, m)

        # Relabel nodes
        mapping = {i: aid for i, aid in enumerate(agent_ids)}
        self.graph = nx.relabel_nodes(self.graph, mapping)

        if self._directed:
            self.graph = self.graph.to_directed()


class CustomTopology(Topology):
    """Custom topology for user-defined network structures.

    Allows building arbitrary topologies by adding nodes and edges
    manually, or by providing a NetworkX graph directly.
    """

    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self._topology_type = "custom"

    def build(
        self,
        agent_ids: List[str],
        edges: Optional[List[tuple]] = None,
        graph: Optional[nx.Graph] = None,
        **kwargs
    ) -> None:
        """Build custom topology.

        Args:
            agent_ids: List of agent IDs (all will be added as nodes)
            edges: Optional list of (source, target) or (source, target, weight) tuples
            graph: Optional NetworkX graph to use directly (takes precedence over edges)
        """
        if graph is not None:
            # Use provided graph
            if self._directed and not graph.is_directed():
                self.graph = graph.to_directed()
            elif not self._directed and graph.is_directed():
                self.graph = graph.to_undirected()
            else:
                self.graph = graph.copy()
            return

        # Add all nodes
        for agent_id in agent_ids:
            self.add_node(agent_id)

        # Add edges if provided
        if edges:
            for edge in edges:
                if len(edge) == 2:
                    self.add_edge(edge[0], edge[1])
                elif len(edge) >= 3:
                    self.add_edge(edge[0], edge[1], weight=edge[2])


def create_topology(
    topology_type: str,
    agent_ids: List[str],
    directed: bool = False,
    **kwargs
) -> Topology:
    """Factory function to create topologies by type name.

    Args:
        topology_type: One of "mesh", "hub_spoke", "hierarchical", "small_world", "scale_free", "custom"
        agent_ids: List of agent IDs
        directed: Whether to use directed graph
        **kwargs: Topology-specific parameters

    Returns:
        Configured Topology instance

    Raises:
        ValueError: If topology_type is unknown
    """
    topology_classes = {
        "mesh": MeshTopology,
        "hub_spoke": HubSpokeTopology,
        "hierarchical": HierarchicalTopology,
        "small_world": SmallWorldTopology,
        "scale_free": ScaleFreeTopology,
        "custom": CustomTopology,
    }

    if topology_type not in topology_classes:
        raise ValueError(
            f"Unknown topology type: {topology_type}. "
            f"Valid types: {list(topology_classes.keys())}"
        )

    topology = topology_classes[topology_type](directed=directed)
    topology.build(agent_ids, **kwargs)
    return topology
