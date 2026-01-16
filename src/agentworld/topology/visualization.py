"""ASCII visualization for topologies."""

from typing import Dict, List, Optional, Tuple
import math

from agentworld.topology.base import Topology


class TopologyVisualizer:
    """ASCII visualization of network topologies."""

    def __init__(self, topology: Topology):
        """Initialize visualizer.

        Args:
            topology: Topology to visualize
        """
        self.topology = topology

    def render(
        self,
        width: int = 60,
        height: int = 20,
        show_labels: bool = True
    ) -> str:
        """Render topology as ASCII art.

        Args:
            width: Canvas width in characters
            height: Canvas height in characters
            show_labels: Whether to show node labels

        Returns:
            Multi-line ASCII string
        """
        nodes = self.topology.get_all_nodes()
        edges = self.topology.get_all_edges()

        if not nodes:
            return "(empty topology)"

        if len(nodes) == 1:
            return f"({nodes[0]})"

        # Compute node positions
        positions = self._layout(nodes, width, height)

        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]

        # Draw edges first (so nodes appear on top)
        for source, target in edges:
            self._draw_edge(canvas, positions[source], positions[target])

        # Draw nodes
        for node_id, (x, y) in positions.items():
            self._draw_node(canvas, x, y, node_id if show_labels else "o")

        # Convert canvas to string
        return "\n".join("".join(row) for row in canvas)

    def _layout(
        self,
        nodes: List[str],
        width: int,
        height: int
    ) -> Dict[str, Tuple[int, int]]:
        """Compute node positions using simple circular layout.

        Args:
            nodes: List of node IDs
            width: Canvas width
            height: Canvas height

        Returns:
            Dict of node_id -> (x, y) position
        """
        n = len(nodes)
        positions = {}

        # Use circular layout
        center_x = width // 2
        center_y = height // 2
        radius_x = (width - 10) // 2
        radius_y = (height - 4) // 2

        for i, node_id in enumerate(nodes):
            angle = 2 * math.pi * i / n - math.pi / 2  # Start from top
            x = int(center_x + radius_x * math.cos(angle))
            y = int(center_y + radius_y * math.sin(angle))

            # Clamp to canvas bounds
            x = max(2, min(width - 3, x))
            y = max(1, min(height - 2, y))

            positions[node_id] = (x, y)

        return positions

    def _draw_node(
        self,
        canvas: List[List[str]],
        x: int,
        y: int,
        label: str
    ) -> None:
        """Draw a node on the canvas.

        Args:
            canvas: 2D character canvas
            x: X position
            y: Y position
            label: Node label to display
        """
        height = len(canvas)
        width = len(canvas[0]) if canvas else 0

        if 0 <= y < height and 0 <= x < width:
            # Draw node marker
            canvas[y][x] = "●"

            # Draw label if space permits (truncate if needed)
            if len(label) <= 8:
                label_x = x + 1
                for i, char in enumerate(label[:6]):
                    if label_x + i < width:
                        canvas[y][label_x + i] = char

    def _draw_edge(
        self,
        canvas: List[List[str]],
        pos1: Tuple[int, int],
        pos2: Tuple[int, int]
    ) -> None:
        """Draw an edge between two positions.

        Args:
            canvas: 2D character canvas
            pos1: (x, y) of first node
            pos2: (x, y) of second node
        """
        x1, y1 = pos1
        x2, y2 = pos2

        # Use Bresenham-like line drawing
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        if dx == 0 and dy == 0:
            return

        # Determine line character based on direction
        if dx > dy * 2:
            line_char = "─"
        elif dy > dx * 2:
            line_char = "│"
        elif sx == sy:
            line_char = "\\"
        else:
            line_char = "/"

        # Simple line drawing (skip endpoints which have nodes)
        steps = max(dx, dy)
        if steps == 0:
            return

        for i in range(1, steps):
            t = i / steps
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))

            if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
                # Don't overwrite nodes
                if canvas[y][x] == " ":
                    canvas[y][x] = line_char

    def render_adjacency_matrix(self) -> str:
        """Render topology as adjacency matrix.

        Returns:
            ASCII adjacency matrix representation
        """
        nodes = sorted(self.topology.get_all_nodes())
        if not nodes:
            return "(empty)"

        # Header
        max_len = max(len(n) for n in nodes)
        header = " " * (max_len + 1) + " ".join(n[:3].ljust(3) for n in nodes)

        lines = [header]

        # Rows
        for node in nodes:
            row = [node.ljust(max_len)]
            for other in nodes:
                if node == other:
                    row.append(" - ")
                elif self.topology.can_communicate(node, other):
                    row.append(" 1 ")
                else:
                    row.append(" 0 ")
            lines.append(" ".join(row))

        return "\n".join(lines)

    def render_edge_list(self) -> str:
        """Render topology as edge list.

        Returns:
            Edge list representation
        """
        edges = self.topology.get_all_edges()
        if not edges:
            return "(no edges)"

        lines = ["Edges:"]
        for source, target in sorted(edges):
            lines.append(f"  {source} → {target}")

        return "\n".join(lines)

    def render_summary(self) -> str:
        """Render compact summary of topology.

        Returns:
            Summary string
        """
        metrics = self.topology.get_metrics()
        nodes = self.topology.get_all_nodes()

        lines = [
            f"Type: {self.topology.topology_type}",
            f"Nodes ({metrics.node_count}): {', '.join(sorted(nodes))}",
            f"Edges: {metrics.edge_count}",
            f"Density: {metrics.density:.2f}",
        ]

        if not metrics.is_connected:
            lines.append("WARNING: Graph is disconnected")

        return "\n".join(lines)


def visualize_topology(
    topology: Topology,
    format: str = "ascii",
    width: int = 60,
    height: int = 20
) -> str:
    """Convenience function to visualize a topology.

    Args:
        topology: Topology to visualize
        format: One of "ascii", "matrix", "edges", "summary"
        width: Canvas width for ASCII format
        height: Canvas height for ASCII format

    Returns:
        String visualization
    """
    viz = TopologyVisualizer(topology)

    if format == "ascii":
        return viz.render(width=width, height=height)
    elif format == "matrix":
        return viz.render_adjacency_matrix()
    elif format == "edges":
        return viz.render_edge_list()
    elif format == "summary":
        return viz.render_summary()
    else:
        raise ValueError(f"Unknown format: {format}")
