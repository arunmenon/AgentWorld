"""Tests for topology type implementations."""

import pytest
import networkx as nx

from agentworld.topology.types import (
    MeshTopology,
    HubSpokeTopology,
    HierarchicalTopology,
    SmallWorldTopology,
    ScaleFreeTopology,
    CustomTopology,
    create_topology,
)


class TestMeshTopology:
    """Tests for MeshTopology (complete graph)."""

    def test_build_basic(self):
        """Test building mesh topology."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])

        assert mesh.graph.number_of_nodes() == 3
        # Complete graph with 3 nodes has 3 edges
        assert mesh.graph.number_of_edges() == 3

    def test_all_connected(self):
        """Test that all nodes are connected in mesh."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])

        assert mesh.can_communicate("a", "b")
        assert mesh.can_communicate("a", "c")
        assert mesh.can_communicate("b", "d")

    def test_empty_build(self):
        """Test building with empty list."""
        mesh = MeshTopology()
        mesh.build([])

        assert mesh.graph.number_of_nodes() == 0

    def test_single_node(self):
        """Test building with single node."""
        mesh = MeshTopology()
        mesh.build(["a"])

        assert mesh.graph.number_of_nodes() == 1
        assert mesh.graph.number_of_edges() == 0

    def test_directed_mesh(self):
        """Test directed mesh topology."""
        mesh = MeshTopology(directed=True)
        mesh.build(["a", "b", "c"])

        assert mesh.graph.is_directed()


class TestHubSpokeTopology:
    """Tests for HubSpokeTopology (star graph)."""

    def test_build_basic(self):
        """Test building hub-spoke topology."""
        hub = HubSpokeTopology()
        hub.build(["hub", "spoke1", "spoke2", "spoke3"])

        assert hub.hub_id == "hub"
        assert hub.graph.number_of_nodes() == 4

    def test_hub_connected_to_all(self):
        """Test that hub is connected to all spokes."""
        hub = HubSpokeTopology()
        hub.build(["center", "a", "b", "c"])

        assert hub.can_communicate("center", "a")
        assert hub.can_communicate("center", "b")
        assert hub.can_communicate("center", "c")

    def test_spokes_not_directly_connected(self):
        """Test that spokes are not directly connected."""
        hub = HubSpokeTopology()
        hub.build(["center", "a", "b"])

        assert not hub.can_communicate("a", "b")

    def test_custom_hub_id(self):
        """Test specifying custom hub ID."""
        hub = HubSpokeTopology()
        hub.build(["a", "b", "c"], hub_id="b")

        assert hub.hub_id == "b"
        assert hub.can_communicate("b", "a")
        assert hub.can_communicate("b", "c")

    def test_invalid_hub_id_raises(self):
        """Test that invalid hub_id raises error."""
        hub = HubSpokeTopology()

        with pytest.raises(ValueError):
            hub.build(["a", "b", "c"], hub_id="nonexistent")


class TestHierarchicalTopology:
    """Tests for HierarchicalTopology (tree graph)."""

    def test_build_basic(self):
        """Test building hierarchical topology."""
        hier = HierarchicalTopology()
        hier.build(["root", "a", "b", "c"])

        assert hier.root_id == "root"
        assert hier.graph.number_of_nodes() <= 4

    def test_custom_root_id(self):
        """Test specifying custom root ID."""
        hier = HierarchicalTopology()
        hier.build(["a", "root", "b"], root_id="root")

        assert hier.root_id == "root"

    def test_branching_factor(self):
        """Test custom branching factor."""
        hier = HierarchicalTopology()
        hier.build(["r", "a", "b", "c", "d", "e"], branching_factor=3)

        assert hier.graph.number_of_nodes() > 0

    def test_invalid_root_raises(self):
        """Test that invalid root_id raises error."""
        hier = HierarchicalTopology()

        with pytest.raises(ValueError):
            hier.build(["a", "b"], root_id="nonexistent")


class TestSmallWorldTopology:
    """Tests for SmallWorldTopology (Watts-Strogatz)."""

    def test_build_basic(self):
        """Test building small-world topology."""
        sw = SmallWorldTopology()
        sw.build(["a", "b", "c", "d", "e", "f"])

        assert sw.graph.number_of_nodes() == 6
        assert sw.graph.number_of_edges() > 0

    def test_small_network_fallback(self):
        """Test that small networks fall back to complete graph."""
        sw = SmallWorldTopology()
        sw.build(["a", "b"])

        # Should still work for 2 nodes
        assert sw.graph.number_of_nodes() == 2

    def test_custom_k_and_p(self):
        """Test custom k (neighbors) and p (rewire probability)."""
        sw = SmallWorldTopology()
        sw.build(["a", "b", "c", "d", "e", "f"], k=4, p=0.5)

        assert sw.graph.number_of_nodes() == 6

    def test_invalid_p_raises(self):
        """Test that invalid p raises error."""
        sw = SmallWorldTopology()

        with pytest.raises(ValueError):
            sw.build(["a", "b", "c", "d"], p=1.5)


class TestScaleFreeTopology:
    """Tests for ScaleFreeTopology (Barabasi-Albert)."""

    def test_build_basic(self):
        """Test building scale-free topology."""
        sf = ScaleFreeTopology()
        sf.build(["a", "b", "c", "d", "e"])

        assert sf.graph.number_of_nodes() == 5
        assert sf.graph.number_of_edges() > 0

    def test_custom_m(self):
        """Test custom m (edges per new node)."""
        sf = ScaleFreeTopology()
        sf.build(["a", "b", "c", "d", "e"], m=3)

        assert sf.graph.number_of_nodes() == 5

    def test_single_node(self):
        """Test with single node."""
        sf = ScaleFreeTopology()
        sf.build(["a"])

        assert sf.graph.number_of_nodes() == 1


class TestCustomTopology:
    """Tests for CustomTopology."""

    def test_build_with_edges(self):
        """Test building custom topology with edges."""
        custom = CustomTopology()
        custom.build(
            agent_ids=["a", "b", "c"],
            edges=[("a", "b"), ("b", "c")]
        )

        assert custom.can_communicate("a", "b")
        assert custom.can_communicate("b", "c")
        assert not custom.can_communicate("a", "c")

    def test_build_with_weighted_edges(self):
        """Test building with weighted edges."""
        custom = CustomTopology()
        custom.build(
            agent_ids=["a", "b"],
            edges=[("a", "b", 2.5)]
        )

        assert custom.can_communicate("a", "b")

    def test_build_with_graph(self):
        """Test building with existing NetworkX graph."""
        g = nx.Graph()
        g.add_edges_from([("x", "y"), ("y", "z")])

        custom = CustomTopology()
        custom.build([], graph=g)

        assert custom.can_communicate("x", "y")
        assert custom.can_communicate("y", "z")


class TestCreateTopology:
    """Tests for create_topology factory function."""

    def test_create_mesh(self):
        """Test creating mesh topology."""
        topology = create_topology("mesh", ["a", "b", "c"])
        assert topology.topology_type == "mesh"
        assert topology.graph.number_of_nodes() == 3

    def test_create_hub_spoke(self):
        """Test creating hub-spoke topology."""
        topology = create_topology("hub_spoke", ["h", "s1", "s2"])
        assert topology.topology_type == "hub_spoke"

    def test_create_hierarchical(self):
        """Test creating hierarchical topology."""
        topology = create_topology("hierarchical", ["r", "a", "b"])
        assert topology.topology_type == "hierarchical"

    def test_create_small_world(self):
        """Test creating small-world topology."""
        topology = create_topology("small_world", ["a", "b", "c", "d"])
        assert topology.topology_type == "small_world"

    def test_create_scale_free(self):
        """Test creating scale-free topology."""
        topology = create_topology("scale_free", ["a", "b", "c", "d"])
        assert topology.topology_type == "scale_free"

    def test_create_custom(self):
        """Test creating custom topology."""
        topology = create_topology("custom", ["a", "b"], edges=[("a", "b")])
        assert topology.topology_type == "custom"

    def test_create_with_directed(self):
        """Test creating directed topology."""
        topology = create_topology("mesh", ["a", "b"], directed=True)
        assert topology.graph.is_directed()

    def test_unknown_type_raises(self):
        """Test that unknown type raises error."""
        with pytest.raises(ValueError) as exc:
            create_topology("unknown", ["a", "b"])
        assert "unknown" in str(exc.value).lower()
