"""Tests for TopologyGraph wrapper."""

import pytest

from agentworld.topology.graph import TopologyGraph
from agentworld.topology.base import RoutingMode
from agentworld.topology.types import MeshTopology, HubSpokeTopology, create_topology


class TestTopologyGraphCreation:
    """Tests for TopologyGraph creation."""

    def test_creation_default_routing(self):
        """Test creating TopologyGraph with default routing."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])

        graph = TopologyGraph(mesh)
        assert graph.routing_mode == RoutingMode.DIRECT_ONLY

    def test_creation_custom_routing(self):
        """Test creating TopologyGraph with custom routing mode."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])

        graph = TopologyGraph(mesh, routing_mode=RoutingMode.BROADCAST)
        assert graph.routing_mode == RoutingMode.BROADCAST


class TestCanSendMessage:
    """Tests for can_send_message method."""

    def test_direct_only_with_edge(self):
        """Test direct-only mode with existing edge."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        graph = TopologyGraph(mesh, RoutingMode.DIRECT_ONLY)

        assert graph.can_send_message("a", "b")
        assert graph.can_send_message("b", "c")

    def test_direct_only_without_edge(self):
        """Test direct-only mode without edge."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2"])
        graph = TopologyGraph(hub, RoutingMode.DIRECT_ONLY)

        # Spokes can't directly message each other
        assert not graph.can_send_message("s1", "s2")

    def test_broadcast_ignores_topology(self):
        """Test broadcast mode ignores topology."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2"])
        graph = TopologyGraph(hub, RoutingMode.BROADCAST)

        # In broadcast mode, anyone can send to anyone
        assert graph.can_send_message("s1", "s2")
        assert graph.can_send_message("s2", "s1")

    def test_multi_hop_allows_reachable(self):
        """Test multi-hop mode allows reachable destinations."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2"])
        graph = TopologyGraph(hub, RoutingMode.MULTI_HOP)

        # Spokes can reach each other through hub
        assert graph.can_send_message("s1", "s2")


class TestGetValidRecipients:
    """Tests for get_valid_recipients method."""

    def test_mesh_all_recipients(self):
        """Test mesh returns all other nodes."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        graph = TopologyGraph(mesh, RoutingMode.DIRECT_ONLY)

        recipients = graph.get_valid_recipients("a")
        assert len(recipients) == 2
        assert "b" in recipients
        assert "c" in recipients
        assert "a" not in recipients

    def test_hub_spoke_direct_only(self):
        """Test hub-spoke in direct-only mode."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        graph = TopologyGraph(hub, RoutingMode.DIRECT_ONLY)

        # Hub can reach all spokes
        hub_recipients = graph.get_valid_recipients("center")
        assert len(hub_recipients) == 3

        # Spoke can only reach hub
        spoke_recipients = graph.get_valid_recipients("s1")
        assert len(spoke_recipients) == 1
        assert "center" in spoke_recipients

    def test_broadcast_all_recipients(self):
        """Test broadcast mode returns all nodes."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2"])
        graph = TopologyGraph(hub, RoutingMode.BROADCAST)

        recipients = graph.get_valid_recipients("s1")
        assert "center" in recipients
        assert "s2" in recipients


class TestGetMessagePath:
    """Tests for get_message_path method."""

    def test_direct_path(self):
        """Test direct path in mesh."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        graph = TopologyGraph(mesh, RoutingMode.DIRECT_ONLY)

        path = graph.get_message_path("a", "b")
        assert path is not None
        assert "a" in path
        assert "b" in path

    def test_no_path_returns_none(self):
        """Test no path returns None."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2"])
        graph = TopologyGraph(hub, RoutingMode.DIRECT_ONLY)

        # Spokes can't directly reach each other
        path = graph.get_message_path("s1", "s2")
        assert path is None

    def test_broadcast_path(self):
        """Test broadcast returns simple path."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        graph = TopologyGraph(mesh, RoutingMode.BROADCAST)

        path = graph.get_message_path("a", "b")
        assert path == ["a", "b"]


class TestGetNeighborhood:
    """Tests for get_neighborhood method."""

    def test_one_hop_neighbors(self):
        """Test getting 1-hop neighbors."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])
        graph = TopologyGraph(mesh)

        neighborhood = graph.get_neighborhood("a", hops=1)
        assert len(neighborhood) == 3
        assert "a" not in neighborhood

    def test_multi_hop_neighborhood(self):
        """Test getting multi-hop neighborhood."""
        # Create a line graph: a - b - c - d
        custom = create_topology("custom", ["a", "b", "c", "d"],
                                  edges=[("a", "b"), ("b", "c"), ("c", "d")])
        graph = TopologyGraph(custom)

        # 1-hop from a should just be b
        one_hop = graph.get_neighborhood("a", hops=1)
        assert "b" in one_hop
        assert "c" not in one_hop

        # 2-hop from a should include c
        two_hop = graph.get_neighborhood("a", hops=2)
        assert "b" in two_hop
        assert "c" in two_hop

    def test_invalid_node_returns_empty(self):
        """Test invalid node returns empty set."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        graph = TopologyGraph(mesh)

        neighborhood = graph.get_neighborhood("nonexistent", hops=1)
        assert neighborhood == set()


class TestCentralityMethods:
    """Tests for centrality-related methods."""

    def test_get_central_nodes(self):
        """Test getting most central nodes."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        graph = TopologyGraph(hub)

        central = graph.get_central_nodes(k=1)
        assert central == ["center"]

    def test_get_peripheral_nodes(self):
        """Test getting least central nodes."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        graph = TopologyGraph(hub)

        peripheral = graph.get_peripheral_nodes(k=2)
        assert "center" not in peripheral
        assert len(peripheral) == 2

    def test_empty_graph_returns_empty(self):
        """Test empty graph returns empty list."""
        mesh = MeshTopology()
        mesh.build([])
        graph = TopologyGraph(mesh)

        assert graph.get_central_nodes(k=1) == []
        assert graph.get_peripheral_nodes(k=1) == []


class TestGraphAnalysis:
    """Tests for graph analysis methods."""

    def test_get_bridges(self):
        """Test getting bridge edges."""
        # Create a graph with a bridge
        custom = create_topology("custom", ["a", "b", "c", "d"],
                                  edges=[("a", "b"), ("b", "c"), ("c", "d")])
        graph = TopologyGraph(custom)

        bridges = graph.get_bridges()
        # All edges in a line are bridges
        assert len(bridges) > 0

    def test_get_articulation_points(self):
        """Test getting articulation points."""
        # Create a graph with articulation point
        custom = create_topology("custom", ["a", "b", "c", "d", "e"],
                                  edges=[("a", "b"), ("b", "c"), ("b", "d"), ("d", "e")])
        graph = TopologyGraph(custom)

        points = graph.get_articulation_points()
        assert "b" in points  # b is an articulation point

    def test_is_bipartite_true(self):
        """Test bipartite check returns True for star graph."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        graph = TopologyGraph(hub)

        assert graph.is_bipartite()

    def test_get_communities(self):
        """Test community detection."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        graph = TopologyGraph(mesh)

        communities = graph.get_communities()
        assert len(communities) >= 1
        # All nodes should be in some community
        all_nodes = set()
        for community in communities:
            all_nodes.update(community)
        assert "a" in all_nodes
        assert "b" in all_nodes
        assert "c" in all_nodes
