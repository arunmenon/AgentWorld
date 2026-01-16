"""Tests for topology system."""

import pytest

from agentworld.topology.base import Topology, TopologyMetrics, RoutingMode
from agentworld.topology.types import (
    MeshTopology,
    HubSpokeTopology,
    HierarchicalTopology,
    SmallWorldTopology,
    ScaleFreeTopology,
    CustomTopology,
    create_topology,
)
from agentworld.topology.graph import TopologyGraph
from agentworld.topology.metrics import TopologyAnalyzer


class TestMeshTopology:
    """Tests for MeshTopology class."""

    @pytest.fixture
    def agents(self):
        return ["alice", "bob", "charlie", "diana"]

    def test_mesh_creation(self, agents):
        """Test mesh topology creation."""
        mesh = MeshTopology()
        mesh.build(agents)

        assert mesh.topology_type == "mesh"
        metrics = mesh.get_metrics()
        assert metrics.node_count == len(agents)
        # Complete graph has n*(n-1)/2 edges
        expected_edges = len(agents) * (len(agents) - 1) // 2
        assert metrics.edge_count == expected_edges

    def test_mesh_communication(self, agents):
        """Test all agents can communicate in mesh."""
        mesh = MeshTopology()
        mesh.build(agents)

        for a in agents:
            for b in agents:
                if a != b:
                    assert mesh.can_communicate(a, b)

    def test_mesh_density(self, agents):
        """Test mesh has density 1.0."""
        mesh = MeshTopology()
        mesh.build(agents)
        metrics = mesh.get_metrics()
        assert abs(metrics.density - 1.0) < 0.01


class TestHubSpokeTopology:
    """Tests for HubSpokeTopology class."""

    @pytest.fixture
    def agents(self):
        return ["hub", "spoke1", "spoke2", "spoke3"]

    def test_hub_spoke_creation(self, agents):
        """Test hub-spoke topology creation."""
        topology = HubSpokeTopology()
        topology.build(agents, hub_id="hub")

        assert topology.hub_id == "hub"
        assert topology.topology_type == "hub_spoke"

    def test_hub_connected_to_all(self, agents):
        """Test hub is connected to all spokes."""
        topology = HubSpokeTopology()
        topology.build(agents, hub_id="hub")

        neighbors = topology.get_neighbors("hub")
        assert len(neighbors) == len(agents) - 1

    def test_spokes_only_connected_to_hub(self, agents):
        """Test spokes only connect to hub."""
        topology = HubSpokeTopology()
        topology.build(agents, hub_id="hub")

        for spoke in ["spoke1", "spoke2", "spoke3"]:
            neighbors = topology.get_neighbors(spoke)
            assert len(neighbors) == 1
            assert "hub" in neighbors

    def test_invalid_hub_raises(self, agents):
        """Test invalid hub_id raises ValueError."""
        topology = HubSpokeTopology()
        with pytest.raises(ValueError):
            topology.build(agents, hub_id="nonexistent")


class TestSmallWorldTopology:
    """Tests for SmallWorldTopology class."""

    @pytest.fixture
    def agents(self):
        return [f"agent{i}" for i in range(10)]

    def test_small_world_creation(self, agents):
        """Test small-world topology creation."""
        topology = SmallWorldTopology()
        topology.build(agents, k=4, p=0.3)

        metrics = topology.get_metrics()
        assert metrics.node_count == len(agents)
        assert metrics.is_connected

    def test_small_world_k_validation(self, agents):
        """Test k parameter validation."""
        topology = SmallWorldTopology()
        # Should handle odd k by rounding up
        topology.build(agents, k=3, p=0.3)
        assert topology.graph.number_of_nodes() == len(agents)

    def test_small_world_p_validation(self, agents):
        """Test p must be in [0, 1]."""
        topology = SmallWorldTopology()
        with pytest.raises(ValueError):
            topology.build(agents, k=4, p=1.5)


class TestScaleFreeTopology:
    """Tests for ScaleFreeTopology class."""

    @pytest.fixture
    def agents(self):
        return [f"agent{i}" for i in range(10)]

    def test_scale_free_creation(self, agents):
        """Test scale-free topology creation."""
        topology = ScaleFreeTopology()
        topology.build(agents, m=2)

        metrics = topology.get_metrics()
        assert metrics.node_count == len(agents)
        assert metrics.is_connected


class TestHierarchicalTopology:
    """Tests for HierarchicalTopology class."""

    @pytest.fixture
    def agents(self):
        return [f"agent{i}" for i in range(7)]

    def test_hierarchical_creation(self, agents):
        """Test hierarchical topology creation."""
        topology = HierarchicalTopology()
        topology.build(agents, branching_factor=2)

        metrics = topology.get_metrics()
        assert metrics.node_count >= 1


class TestCustomTopology:
    """Tests for CustomTopology class."""

    def test_custom_with_edges(self):
        """Test custom topology with edge list."""
        agents = ["a", "b", "c"]
        edges = [("a", "b"), ("b", "c")]

        topology = CustomTopology()
        topology.build(agents, edges=edges)

        assert topology.can_communicate("a", "b")
        assert topology.can_communicate("b", "c")
        assert not topology.can_communicate("a", "c")


class TestTopologyFactory:
    """Tests for create_topology factory function."""

    def test_create_mesh(self):
        """Test creating mesh via factory."""
        topology = create_topology("mesh", ["a", "b", "c"])
        assert topology.topology_type == "mesh"

    def test_create_hub_spoke(self):
        """Test creating hub-spoke via factory."""
        topology = create_topology("hub_spoke", ["hub", "s1", "s2"], hub_id="hub")
        assert topology.topology_type == "hub_spoke"

    def test_invalid_type_raises(self):
        """Test invalid type raises ValueError."""
        with pytest.raises(ValueError):
            create_topology("invalid_type", ["a", "b"])


class TestTopologyGraph:
    """Tests for TopologyGraph wrapper."""

    @pytest.fixture
    def mesh_graph(self):
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        return TopologyGraph(mesh, RoutingMode.DIRECT_ONLY)

    def test_can_send_message(self, mesh_graph):
        """Test message sending check."""
        assert mesh_graph.can_send_message("a", "b")
        assert mesh_graph.can_send_message("b", "c")

    def test_get_valid_recipients(self, mesh_graph):
        """Test getting valid recipients."""
        recipients = mesh_graph.get_valid_recipients("a")
        assert "b" in recipients
        assert "c" in recipients
        assert "a" not in recipients

    def test_broadcast_mode(self):
        """Test broadcast routing mode."""
        hub = HubSpokeTopology()
        hub.build(["hub", "s1", "s2"], hub_id="hub")
        graph = TopologyGraph(hub, RoutingMode.BROADCAST)

        # In broadcast mode, everyone can reach everyone
        assert graph.can_send_message("s1", "s2")


class TestTopologyMetrics:
    """Tests for TopologyMetrics and TopologyAnalyzer."""

    def test_metrics_calculation(self):
        """Test metrics are calculated correctly."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])

        analyzer = TopologyAnalyzer(mesh)
        metrics = analyzer.get_metrics()

        assert metrics.node_count == 4
        assert metrics.edge_count == 6
        assert metrics.is_connected

    def test_centrality_calculation(self):
        """Test centrality metrics."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])

        analyzer = TopologyAnalyzer(mesh)
        centrality = analyzer.get_centrality()

        # In mesh, all nodes have same degree centrality
        assert len(centrality.degree) == 3
