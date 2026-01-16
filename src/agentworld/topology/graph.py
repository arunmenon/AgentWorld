"""NetworkX graph utilities and wrapper."""

from typing import List, Optional, Set

import networkx as nx

from agentworld.topology.base import Topology, RoutingMode


class TopologyGraph:
    """Wrapper providing convenient topology operations for simulations.

    Provides message routing, neighborhood queries, and path-finding
    operations on top of a Topology instance.
    """

    def __init__(self, topology: Topology, routing_mode: RoutingMode = RoutingMode.DIRECT_ONLY):
        """Initialize topology graph wrapper.

        Args:
            topology: The underlying topology
            routing_mode: How messages are routed
        """
        self.topology = topology
        self.routing_mode = routing_mode

    def can_send_message(self, sender: str, receiver: str) -> bool:
        """Check if sender can send a message to receiver.

        Respects the current routing mode.

        Args:
            sender: Sending agent ID
            receiver: Receiving agent ID

        Returns:
            True if message can be sent
        """
        if self.routing_mode == RoutingMode.BROADCAST:
            # Broadcast mode ignores topology
            return True
        elif self.routing_mode == RoutingMode.MULTI_HOP:
            # Multi-hop allows any reachable destination
            return self.topology.can_reach(sender, receiver)
        else:
            # Direct only - must have direct edge
            return self.topology.can_communicate(sender, receiver)

    def get_valid_recipients(self, sender: str) -> List[str]:
        """Get all agents that sender can message.

        Respects the current routing mode.

        Args:
            sender: Sending agent ID

        Returns:
            List of valid recipient agent IDs
        """
        all_nodes = set(self.topology.get_all_nodes())
        all_nodes.discard(sender)

        if self.routing_mode == RoutingMode.BROADCAST:
            return list(all_nodes)
        elif self.routing_mode == RoutingMode.MULTI_HOP:
            return [n for n in all_nodes if self.topology.can_reach(sender, n)]
        else:
            return self.topology.get_neighbors(sender)

    def get_message_path(self, sender: str, receiver: str) -> Optional[List[str]]:
        """Get the path a message would take.

        Args:
            sender: Sending agent ID
            receiver: Receiving agent ID

        Returns:
            List of agent IDs in path, or None if not reachable
        """
        if not self.can_send_message(sender, receiver):
            return None

        if self.routing_mode == RoutingMode.BROADCAST:
            return [sender, receiver]
        else:
            return self.topology.get_shortest_path(sender, receiver)

    def get_broadcast_recipients(self, sender: str) -> List[str]:
        """Get all agents that would receive a broadcast from sender.

        Args:
            sender: Broadcasting agent ID

        Returns:
            List of all other agent IDs
        """
        all_nodes = set(self.topology.get_all_nodes())
        all_nodes.discard(sender)
        return list(all_nodes)

    def get_neighborhood(self, agent_id: str, hops: int = 1) -> Set[str]:
        """Get all agents within N hops of an agent.

        Args:
            agent_id: Center agent
            hops: Maximum number of hops

        Returns:
            Set of agent IDs within range (excluding self)
        """
        if agent_id not in self.topology.graph:
            return set()

        neighborhood = set()
        current = {agent_id}

        for _ in range(hops):
            next_level = set()
            for node in current:
                next_level.update(self.topology.get_neighbors(node))
            neighborhood.update(next_level)
            current = next_level

        neighborhood.discard(agent_id)
        return neighborhood

    def get_central_nodes(self, k: int = 1) -> List[str]:
        """Get the k most central nodes by degree centrality.

        Args:
            k: Number of nodes to return

        Returns:
            List of most central agent IDs
        """
        if not self.topology.graph.nodes():
            return []

        centrality = nx.degree_centrality(self.topology.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return [node for node, _ in sorted_nodes[:k]]

    def get_peripheral_nodes(self, k: int = 1) -> List[str]:
        """Get the k least central nodes by degree centrality.

        Args:
            k: Number of nodes to return

        Returns:
            List of least central agent IDs
        """
        if not self.topology.graph.nodes():
            return []

        centrality = nx.degree_centrality(self.topology.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1])
        return [node for node, _ in sorted_nodes[:k]]

    def get_bridges(self) -> List[tuple]:
        """Get edges that, if removed, would disconnect components.

        Returns:
            List of (source, target) tuples representing bridge edges
        """
        if self.topology.graph.is_directed():
            # For directed graphs, return empty (bridges concept applies to undirected)
            return []

        return list(nx.bridges(self.topology.graph))

    def get_articulation_points(self) -> List[str]:
        """Get nodes that, if removed, would disconnect components.

        Returns:
            List of agent IDs that are articulation points
        """
        if self.topology.graph.is_directed():
            return []

        return list(nx.articulation_points(self.topology.graph))

    def is_bipartite(self) -> bool:
        """Check if the network is bipartite (two non-overlapping groups).

        Returns:
            True if topology is bipartite
        """
        if self.topology.graph.is_directed():
            return nx.is_bipartite(self.topology.graph.to_undirected())
        return nx.is_bipartite(self.topology.graph)

    def get_communities(self) -> List[Set[str]]:
        """Detect communities in the network using Louvain method.

        Returns:
            List of sets, each set containing agent IDs in a community
        """
        if not self.topology.graph.nodes():
            return []

        try:
            # Use greedy modularity communities as fallback
            from networkx.algorithms.community import greedy_modularity_communities
            return list(greedy_modularity_communities(self.topology.graph))
        except Exception:
            # Return all nodes as single community
            return [set(self.topology.get_all_nodes())]
