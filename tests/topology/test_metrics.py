"""Tests for TopologyAnalyzer and network metrics."""

import pytest

from agentworld.topology.metrics import TopologyAnalyzer, CentralityMetrics
from agentworld.topology.types import MeshTopology, HubSpokeTopology, create_topology


class TestTopologyAnalyzerCreation:
    """Tests for TopologyAnalyzer creation."""

    def test_creation(self):
        """Test creating analyzer."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])

        analyzer = TopologyAnalyzer(mesh)
        assert analyzer.topology == mesh


class TestGetMetrics:
    """Tests for get_metrics method."""

    def test_basic_metrics(self):
        """Test getting basic topology metrics."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        analyzer = TopologyAnalyzer(mesh)

        metrics = analyzer.get_metrics()

        assert metrics.node_count == 3
        assert metrics.edge_count == 3  # Complete graph K3
        assert 0 <= metrics.density <= 1

    def test_metrics_cached(self):
        """Test that metrics are cached."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        analyzer = TopologyAnalyzer(mesh)

        metrics1 = analyzer.get_metrics()
        metrics2 = analyzer.get_metrics()

        assert metrics1 is metrics2

    def test_metrics_refresh(self):
        """Test that refresh recomputes metrics."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        analyzer = TopologyAnalyzer(mesh)

        metrics1 = analyzer.get_metrics()
        metrics2 = analyzer.get_metrics(refresh=True)

        # Still equal but potentially different objects
        assert metrics1.node_count == metrics2.node_count


class TestGetCentrality:
    """Tests for get_centrality method."""

    def test_centrality_metrics(self):
        """Test getting centrality metrics."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        analyzer = TopologyAnalyzer(mesh)

        centrality = analyzer.get_centrality()

        assert isinstance(centrality, CentralityMetrics)
        assert "a" in centrality.degree
        assert "b" in centrality.betweenness
        assert "c" in centrality.closeness

    def test_centrality_cached(self):
        """Test that centrality is cached."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        analyzer = TopologyAnalyzer(mesh)

        cent1 = analyzer.get_centrality()
        cent2 = analyzer.get_centrality()

        assert cent1 is cent2

    def test_hub_spoke_centrality(self):
        """Test centrality in hub-spoke topology."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        analyzer = TopologyAnalyzer(hub)

        centrality = analyzer.get_centrality()

        # Hub should have highest degree centrality
        assert centrality.degree["center"] > centrality.degree["s1"]

    def test_empty_graph_centrality(self):
        """Test centrality for empty graph."""
        mesh = MeshTopology()
        mesh.build([])
        analyzer = TopologyAnalyzer(mesh)

        centrality = analyzer.get_centrality()

        assert centrality.degree == {}
        assert centrality.betweenness == {}


class TestGetMostCentral:
    """Tests for get_most_central method."""

    def test_most_central_by_degree(self):
        """Test getting most central by degree."""
        hub = HubSpokeTopology()
        hub.build(["center", "s1", "s2", "s3"])
        analyzer = TopologyAnalyzer(hub)

        most_central = analyzer.get_most_central("degree", k=1)
        assert most_central == ["center"]

    def test_most_central_by_betweenness(self):
        """Test getting most central by betweenness."""
        # Create a graph where node in middle has high betweenness
        custom = create_topology("custom", ["a", "b", "c", "d", "e"],
                                  edges=[("a", "c"), ("b", "c"), ("c", "d"), ("c", "e")])
        analyzer = TopologyAnalyzer(custom)

        most_central = analyzer.get_most_central("betweenness", k=1)
        assert "c" in most_central

    def test_most_central_top_k(self):
        """Test getting top k central nodes."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])
        analyzer = TopologyAnalyzer(mesh)

        most_central = analyzer.get_most_central("degree", k=2)
        assert len(most_central) == 2

    def test_invalid_measure_raises(self):
        """Test that invalid measure raises error."""
        mesh = MeshTopology()
        mesh.build(["a", "b"])
        analyzer = TopologyAnalyzer(mesh)

        with pytest.raises(ValueError):
            analyzer.get_most_central("invalid_measure")


class TestStructuralAnalysis:
    """Tests for structural analysis methods."""

    def test_get_structural_holes(self):
        """Test getting structural hole scores."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        analyzer = TopologyAnalyzer(mesh)

        holes = analyzer.get_structural_holes()

        # Should return dict
        assert isinstance(holes, dict)

    def test_get_clustering_by_node(self):
        """Test getting clustering coefficient by node."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])
        analyzer = TopologyAnalyzer(mesh)

        clustering = analyzer.get_clustering_by_node()

        assert isinstance(clustering, dict)
        # In complete graph, clustering is 1.0 for all nodes
        assert all(c == 1.0 for c in clustering.values())

    def test_clustering_empty_graph(self):
        """Test clustering for empty graph."""
        mesh = MeshTopology()
        mesh.build([])
        analyzer = TopologyAnalyzer(mesh)

        clustering = analyzer.get_clustering_by_node()
        assert clustering == {}


class TestCompareToRandom:
    """Tests for compare_to_random method."""

    def test_comparison_returns_dict(self):
        """Test that comparison returns a dictionary."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])
        analyzer = TopologyAnalyzer(mesh)

        result = analyzer.compare_to_random(num_samples=3)

        assert isinstance(result, dict)
        assert "actual_clustering" in result

    def test_small_graph_returns_error(self):
        """Test that small graph returns error."""
        mesh = MeshTopology()
        mesh.build(["a"])
        analyzer = TopologyAnalyzer(mesh)

        result = analyzer.compare_to_random()
        assert "error" in result


class TestToSummary:
    """Tests for to_summary method."""

    def test_summary_returns_string(self):
        """Test that summary returns string."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c"])
        analyzer = TopologyAnalyzer(mesh)

        summary = analyzer.to_summary()

        assert isinstance(summary, str)
        assert "mesh" in summary.lower()
        assert "3" in summary  # Node count

    def test_summary_includes_metrics(self):
        """Test that summary includes key metrics."""
        mesh = MeshTopology()
        mesh.build(["a", "b", "c", "d"])
        analyzer = TopologyAnalyzer(mesh)

        summary = analyzer.to_summary()

        assert "Nodes" in summary
        assert "Edges" in summary
        assert "Density" in summary
