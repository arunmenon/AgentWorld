"""Network metrics and analysis for topologies."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import networkx as nx

from agentworld.topology.base import Topology, TopologyMetrics


@dataclass
class CentralityMetrics:
    """Centrality measures for network nodes.

    Attributes:
        degree: Number of connections per node (normalized)
        betweenness: How often node lies on shortest paths between others
        closeness: Average distance to all other nodes (inverse)
        eigenvector: Importance based on connections to important nodes
    """
    degree: Dict[str, float]
    betweenness: Dict[str, float]
    closeness: Dict[str, float]
    eigenvector: Optional[Dict[str, float]] = None


class TopologyAnalyzer:
    """Analyzes topology structure and computes network metrics."""

    def __init__(self, topology: Topology):
        """Initialize analyzer.

        Args:
            topology: Topology to analyze
        """
        self.topology = topology
        self._metrics_cache: Optional[TopologyMetrics] = None
        self._centrality_cache: Optional[CentralityMetrics] = None

    def get_metrics(self, refresh: bool = False) -> TopologyMetrics:
        """Get basic topology metrics.

        Args:
            refresh: If True, recompute even if cached

        Returns:
            TopologyMetrics instance
        """
        if self._metrics_cache is None or refresh:
            self._metrics_cache = self.topology.get_metrics()
        return self._metrics_cache

    def get_centrality(self, refresh: bool = False) -> CentralityMetrics:
        """Compute centrality measures for all nodes.

        Args:
            refresh: If True, recompute even if cached

        Returns:
            CentralityMetrics instance
        """
        if self._centrality_cache is not None and not refresh:
            return self._centrality_cache

        graph = self.topology.graph
        n = graph.number_of_nodes()

        if n == 0:
            self._centrality_cache = CentralityMetrics(
                degree={}, betweenness={}, closeness={}, eigenvector={}
            )
            return self._centrality_cache

        # Compute various centrality measures
        degree = nx.degree_centrality(graph)
        betweenness = nx.betweenness_centrality(graph)
        closeness = nx.closeness_centrality(graph)

        # Eigenvector centrality can fail for some graphs
        eigenvector = None
        try:
            eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)
        except (nx.NetworkXError, nx.PowerIterationFailedConvergence):
            pass

        self._centrality_cache = CentralityMetrics(
            degree=degree,
            betweenness=betweenness,
            closeness=closeness,
            eigenvector=eigenvector,
        )
        return self._centrality_cache

    def get_most_central(self, measure: str = "degree", k: int = 1) -> List[str]:
        """Get the k most central nodes by specified measure.

        Args:
            measure: One of "degree", "betweenness", "closeness", "eigenvector"
            k: Number of nodes to return

        Returns:
            List of agent IDs sorted by centrality (descending)
        """
        centrality = self.get_centrality()

        if measure == "degree":
            scores = centrality.degree
        elif measure == "betweenness":
            scores = centrality.betweenness
        elif measure == "closeness":
            scores = centrality.closeness
        elif measure == "eigenvector":
            scores = centrality.eigenvector or {}
        else:
            raise ValueError(f"Unknown measure: {measure}")

        if not scores:
            return []

        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [node for node, _ in sorted_nodes[:k]]

    def get_structural_holes(self) -> Dict[str, float]:
        """Compute structural hole scores (constraint measure).

        Nodes with low constraint values bridge otherwise disconnected groups.

        Returns:
            Dict of node -> constraint score (lower = more bridging)
        """
        if self.topology.graph.number_of_nodes() == 0:
            return {}

        try:
            return nx.constraint(self.topology.graph)
        except Exception:
            return {}

    def get_clustering_by_node(self) -> Dict[str, float]:
        """Get clustering coefficient for each node.

        Returns:
            Dict of node -> clustering coefficient
        """
        if self.topology.graph.number_of_nodes() == 0:
            return {}

        if self.topology.graph.is_directed():
            return nx.clustering(self.topology.graph.to_undirected())
        return dict(nx.clustering(self.topology.graph))

    def compare_to_random(self, num_samples: int = 10) -> dict:
        """Compare topology metrics to random graphs with same n, m.

        Args:
            num_samples: Number of random graphs to generate

        Returns:
            Dict with comparison statistics
        """
        metrics = self.get_metrics()
        n = metrics.node_count
        m = metrics.edge_count

        if n < 2 or m < 1:
            return {"error": "Graph too small for comparison"}

        # Calculate probability for Erdos-Renyi model
        max_edges = n * (n - 1) // 2
        if max_edges == 0:
            return {"error": "Cannot create random graph"}
        p = m / max_edges

        random_clusterings = []
        random_path_lengths = []

        for _ in range(num_samples):
            try:
                random_graph = nx.erdos_renyi_graph(n, p)
                if nx.is_connected(random_graph):
                    random_clusterings.append(nx.average_clustering(random_graph))
                    random_path_lengths.append(
                        nx.average_shortest_path_length(random_graph)
                    )
            except Exception:
                continue

        result = {
            "actual_clustering": metrics.clustering_coefficient,
            "actual_path_length": metrics.avg_path_length,
        }

        if random_clusterings:
            result["random_clustering_mean"] = sum(random_clusterings) / len(random_clusterings)
            result["clustering_ratio"] = (
                metrics.clustering_coefficient / result["random_clustering_mean"]
                if result["random_clustering_mean"] > 0
                else None
            )

        if random_path_lengths:
            result["random_path_length_mean"] = sum(random_path_lengths) / len(random_path_lengths)
            result["path_length_ratio"] = (
                metrics.avg_path_length / result["random_path_length_mean"]
                if result["random_path_length_mean"] > 0
                else None
            )

        # Small-world indicator: high clustering ratio, low path length ratio
        if "clustering_ratio" in result and "path_length_ratio" in result:
            if result["clustering_ratio"] and result["path_length_ratio"]:
                result["small_world_index"] = (
                    result["clustering_ratio"] / result["path_length_ratio"]
                )

        return result

    def to_summary(self) -> str:
        """Generate human-readable summary of topology.

        Returns:
            Multi-line summary string
        """
        metrics = self.get_metrics()
        centrality = self.get_centrality()

        lines = [
            f"Topology: {self.topology.topology_type}",
            f"Nodes: {metrics.node_count}",
            f"Edges: {metrics.edge_count}",
            f"Density: {metrics.density:.3f}",
            f"Connected: {metrics.is_connected}",
        ]

        if metrics.clustering_coefficient is not None:
            lines.append(f"Clustering: {metrics.clustering_coefficient:.3f}")

        if metrics.avg_path_length is not None:
            lines.append(f"Avg Path Length: {metrics.avg_path_length:.2f}")

        if metrics.diameter is not None:
            lines.append(f"Diameter: {metrics.diameter}")

        if centrality.degree:
            most_central = self.get_most_central("degree", k=3)
            lines.append(f"Most Central (degree): {', '.join(most_central)}")

        return "\n".join(lines)
