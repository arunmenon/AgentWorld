"""Topology system for AgentWorld.

Implements network topology abstractions for agent communication patterns
using NetworkX for graph operations.
"""

from agentworld.topology.base import Topology, TopologyMetrics, RoutingMode
from agentworld.topology.types import (
    MeshTopology,
    HubSpokeTopology,
    HierarchicalTopology,
    SmallWorldTopology,
    ScaleFreeTopology,
    CustomTopology,
)
from agentworld.topology.graph import TopologyGraph

__all__ = [
    "Topology",
    "TopologyMetrics",
    "RoutingMode",
    "TopologyGraph",
    "MeshTopology",
    "HubSpokeTopology",
    "HierarchicalTopology",
    "SmallWorldTopology",
    "ScaleFreeTopology",
    "CustomTopology",
]
