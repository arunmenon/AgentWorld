"""Agent ordering strategies for step execution.

This module implements different strategies for determining
the order in which agents act during a simulation step.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator
import random


class OrderingStrategy(str, Enum):
    """How agents are ordered within a step."""

    ROUND_ROBIN = "round_robin"  # Fixed order, rotate starting position
    RANDOM = "random"  # Random order each step (with seed)
    PRIORITY = "priority"  # By agent priority attribute
    TOPOLOGY = "topology"  # BFS from hub/central nodes
    SIMULTANEOUS = "simultaneous"  # All at once (parallel only)


class AgentOrderer(ABC):
    """Base class for agent ordering strategies."""

    @abstractmethod
    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        **kwargs: Any,
    ) -> list[str]:
        """Get ordered list of agent IDs for this step.

        Args:
            agent_ids: List of agent IDs
            step: Current step number
            **kwargs: Strategy-specific arguments

        Returns:
            Ordered list of agent IDs
        """
        pass


class RoundRobinOrderer(AgentOrderer):
    """Round-robin ordering: fixed order with rotating start position."""

    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        **kwargs: Any,
    ) -> list[str]:
        """Get agents in round-robin order.

        Args:
            agent_ids: List of agent IDs
            step: Current step number

        Returns:
            Ordered list with rotated start position
        """
        if not agent_ids:
            return []

        # Sort for consistency, then rotate based on step
        sorted_ids = sorted(agent_ids)
        rotation = step % len(sorted_ids)
        return sorted_ids[rotation:] + sorted_ids[:rotation]


class RandomOrderer(AgentOrderer):
    """Random ordering: shuffled order each step."""

    def __init__(self, seed: int | None = None):
        """Initialize random orderer.

        Args:
            seed: Random seed for reproducibility
        """
        self.base_seed = seed

    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        **kwargs: Any,
    ) -> list[str]:
        """Get agents in random order.

        Args:
            agent_ids: List of agent IDs
            step: Current step number

        Returns:
            Shuffled list of agent IDs
        """
        if not agent_ids:
            return []

        # Create deterministic RNG if seed provided
        if self.base_seed is not None:
            step_seed = hash((self.base_seed, step)) & 0xFFFFFFFF
            rng = random.Random(step_seed)
        else:
            rng = random.Random()

        shuffled = agent_ids.copy()
        rng.shuffle(shuffled)
        return shuffled


class PriorityOrderer(AgentOrderer):
    """Priority-based ordering: sorted by agent priority."""

    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        priorities: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Get agents ordered by priority (highest first).

        Args:
            agent_ids: List of agent IDs
            step: Current step number
            priorities: Map of agent_id to priority value

        Returns:
            Priority-sorted list (highest first)
        """
        if not agent_ids:
            return []

        priorities = priorities or {}

        # Sort by priority descending, then by ID for stability
        return sorted(
            agent_ids,
            key=lambda aid: (-priorities.get(aid, 0.0), aid),
        )


class TopologyOrderer(AgentOrderer):
    """Topology-based ordering: BFS from hub/central nodes."""

    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        hub_id: str | None = None,
        adjacency: dict[str, list[str]] | None = None,
        centrality: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Get agents in topology order (BFS from hub).

        Args:
            agent_ids: List of agent IDs
            step: Current step number
            hub_id: ID of hub node (if hub-spoke topology)
            adjacency: Adjacency list for BFS
            centrality: Centrality scores for agents

        Returns:
            BFS-ordered list from hub/most central node
        """
        if not agent_ids:
            return []

        # If no topology info, fall back to centrality or priority
        if adjacency is None or not adjacency:
            if centrality:
                return sorted(
                    agent_ids,
                    key=lambda aid: (-centrality.get(aid, 0.0), aid),
                )
            return sorted(agent_ids)

        # Determine start node
        start_node = hub_id
        if start_node is None or start_node not in agent_ids:
            # Use highest centrality node
            if centrality:
                start_node = max(agent_ids, key=lambda aid: centrality.get(aid, 0.0))
            else:
                start_node = agent_ids[0]

        # BFS traversal
        visited = set()
        queue = [start_node]
        order = []

        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            if node not in agent_ids:
                continue

            visited.add(node)
            order.append(node)

            # Add neighbors
            neighbors = adjacency.get(node, [])
            for neighbor in neighbors:
                if neighbor not in visited and neighbor in agent_ids:
                    queue.append(neighbor)

        # Add any remaining nodes not reached by BFS
        for aid in agent_ids:
            if aid not in visited:
                order.append(aid)

        return order


class SimultaneousOrderer(AgentOrderer):
    """Simultaneous ordering: all agents at once (for parallel execution)."""

    def get_order(
        self,
        agent_ids: list[str],
        step: int,
        **kwargs: Any,
    ) -> list[str]:
        """Get all agents (order doesn't matter for parallel).

        Args:
            agent_ids: List of agent IDs
            step: Current step number

        Returns:
            List of agent IDs (sorted for consistency)
        """
        return sorted(agent_ids)


def get_orderer(strategy: OrderingStrategy, **kwargs: Any) -> AgentOrderer:
    """Factory function to create an orderer for a strategy.

    Args:
        strategy: Ordering strategy
        **kwargs: Strategy-specific configuration

    Returns:
        AgentOrderer instance
    """
    if strategy == OrderingStrategy.ROUND_ROBIN:
        return RoundRobinOrderer()
    elif strategy == OrderingStrategy.RANDOM:
        return RandomOrderer(seed=kwargs.get("seed"))
    elif strategy == OrderingStrategy.PRIORITY:
        return PriorityOrderer()
    elif strategy == OrderingStrategy.TOPOLOGY:
        return TopologyOrderer()
    elif strategy == OrderingStrategy.SIMULTANEOUS:
        return SimultaneousOrderer()
    else:
        raise ValueError(f"Unknown ordering strategy: {strategy}")


def batch_agents(
    agents: list[str],
    batch_size: int,
) -> Iterator[list[str]]:
    """Yield agent batches for controlled parallelism.

    Args:
        agents: List of agent IDs
        batch_size: Maximum agents per batch

    Yields:
        Lists of agent IDs, each up to batch_size
    """
    for i in range(0, len(agents), batch_size):
        yield agents[i : i + batch_size]
