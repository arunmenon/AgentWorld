"""Tests for agent ordering strategies."""

import pytest

from agentworld.simulation.ordering import (
    OrderingStrategy,
    AgentOrderer,
    RoundRobinOrderer,
    RandomOrderer,
    PriorityOrderer,
    TopologyOrderer,
    SimultaneousOrderer,
    get_orderer,
    batch_agents,
)


class TestOrderingStrategy:
    """Tests for OrderingStrategy enum."""

    def test_strategies_exist(self):
        """Test that all strategies exist."""
        assert OrderingStrategy.ROUND_ROBIN.value == "round_robin"
        assert OrderingStrategy.RANDOM.value == "random"
        assert OrderingStrategy.PRIORITY.value == "priority"
        assert OrderingStrategy.TOPOLOGY.value == "topology"
        assert OrderingStrategy.SIMULTANEOUS.value == "simultaneous"


class TestRoundRobinOrderer:
    """Tests for RoundRobinOrderer."""

    @pytest.fixture
    def orderer(self):
        """Create orderer instance."""
        return RoundRobinOrderer()

    def test_empty_list(self, orderer):
        """Test with empty agent list."""
        result = orderer.get_order([], step=1)
        assert result == []

    def test_single_agent(self, orderer):
        """Test with single agent."""
        result = orderer.get_order(["a1"], step=1)
        assert result == ["a1"]

    def test_rotation_step_0(self, orderer):
        """Test order at step 0."""
        agents = ["c", "a", "b"]  # Will be sorted to ["a", "b", "c"]
        result = orderer.get_order(agents, step=0)
        assert result == ["a", "b", "c"]

    def test_rotation_step_1(self, orderer):
        """Test order rotates at step 1."""
        agents = ["a", "b", "c"]
        result = orderer.get_order(agents, step=1)
        # Rotation by 1
        assert result == ["b", "c", "a"]

    def test_rotation_step_2(self, orderer):
        """Test order rotates at step 2."""
        agents = ["a", "b", "c"]
        result = orderer.get_order(agents, step=2)
        # Rotation by 2
        assert result == ["c", "a", "b"]

    def test_rotation_wraps(self, orderer):
        """Test rotation wraps around."""
        agents = ["a", "b", "c"]
        result_0 = orderer.get_order(agents, step=0)
        result_3 = orderer.get_order(agents, step=3)
        # Step 3 should equal step 0 (3 % 3 = 0)
        assert result_0 == result_3


class TestRandomOrderer:
    """Tests for RandomOrderer."""

    def test_empty_list(self):
        """Test with empty agent list."""
        orderer = RandomOrderer(seed=42)
        result = orderer.get_order([], step=1)
        assert result == []

    def test_single_agent(self):
        """Test with single agent."""
        orderer = RandomOrderer(seed=42)
        result = orderer.get_order(["a1"], step=1)
        assert result == ["a1"]

    def test_deterministic_with_seed(self):
        """Test that same seed produces same order."""
        orderer = RandomOrderer(seed=42)
        agents = ["a", "b", "c", "d", "e"]

        result1 = orderer.get_order(agents, step=5)
        result2 = orderer.get_order(agents, step=5)

        assert result1 == result2

    def test_different_steps_different_order(self):
        """Test that different steps produce different orders."""
        orderer = RandomOrderer(seed=42)
        agents = ["a", "b", "c", "d", "e"]

        result1 = orderer.get_order(agents, step=1)
        result2 = orderer.get_order(agents, step=2)

        # Very unlikely to be the same with 5 agents
        assert result1 != result2

    def test_without_seed(self):
        """Test without seed still returns valid order."""
        orderer = RandomOrderer(seed=None)
        agents = ["a", "b", "c"]

        result = orderer.get_order(agents, step=1)

        assert len(result) == 3
        assert set(result) == set(agents)


class TestPriorityOrderer:
    """Tests for PriorityOrderer."""

    @pytest.fixture
    def orderer(self):
        """Create orderer instance."""
        return PriorityOrderer()

    def test_empty_list(self, orderer):
        """Test with empty agent list."""
        result = orderer.get_order([], step=1)
        assert result == []

    def test_with_priorities(self, orderer):
        """Test ordering by priority."""
        agents = ["a", "b", "c"]
        priorities = {"a": 1.0, "b": 3.0, "c": 2.0}

        result = orderer.get_order(agents, step=1, priorities=priorities)

        # Highest priority first: b(3.0), c(2.0), a(1.0)
        assert result == ["b", "c", "a"]

    def test_without_priorities(self, orderer):
        """Test with no priorities (all default to 0)."""
        agents = ["c", "a", "b"]

        result = orderer.get_order(agents, step=1, priorities=None)

        # Should be sorted by ID for stability
        assert result == ["a", "b", "c"]

    def test_mixed_priorities(self, orderer):
        """Test with some agents having priorities."""
        agents = ["a", "b", "c"]
        priorities = {"b": 5.0}  # Only b has priority

        result = orderer.get_order(agents, step=1, priorities=priorities)

        # b first, then a, c sorted by ID
        assert result[0] == "b"


class TestTopologyOrderer:
    """Tests for TopologyOrderer."""

    @pytest.fixture
    def orderer(self):
        """Create orderer instance."""
        return TopologyOrderer()

    def test_empty_list(self, orderer):
        """Test with empty agent list."""
        result = orderer.get_order([], step=1)
        assert result == []

    def test_with_hub(self, orderer):
        """Test BFS from hub."""
        agents = ["a", "b", "c", "hub"]
        adjacency = {
            "hub": ["a", "b", "c"],
            "a": ["hub"],
            "b": ["hub"],
            "c": ["hub"],
        }

        result = orderer.get_order(agents, step=1, hub_id="hub", adjacency=adjacency)

        # Hub should be first
        assert result[0] == "hub"
        # All agents should be included
        assert set(result) == set(agents)

    def test_with_centrality(self, orderer):
        """Test ordering by centrality when no adjacency."""
        agents = ["a", "b", "c"]
        centrality = {"a": 0.5, "b": 0.9, "c": 0.3}

        result = orderer.get_order(agents, step=1, centrality=centrality)

        # Highest centrality first
        assert result[0] == "b"

    def test_fallback_to_sorted(self, orderer):
        """Test fallback to sorted when no topology info."""
        agents = ["c", "a", "b"]

        result = orderer.get_order(agents, step=1)

        assert result == ["a", "b", "c"]


class TestSimultaneousOrderer:
    """Tests for SimultaneousOrderer."""

    @pytest.fixture
    def orderer(self):
        """Create orderer instance."""
        return SimultaneousOrderer()

    def test_empty_list(self, orderer):
        """Test with empty agent list."""
        result = orderer.get_order([], step=1)
        assert result == []

    def test_returns_sorted_list(self, orderer):
        """Test that list is returned sorted."""
        agents = ["c", "a", "b"]

        result = orderer.get_order(agents, step=1)

        assert result == ["a", "b", "c"]

    def test_all_agents_included(self, orderer):
        """Test all agents are included."""
        agents = ["a", "b", "c", "d"]

        result = orderer.get_order(agents, step=1)

        assert set(result) == set(agents)


class TestGetOrderer:
    """Tests for get_orderer factory function."""

    def test_round_robin(self):
        """Test creating round-robin orderer."""
        orderer = get_orderer(OrderingStrategy.ROUND_ROBIN)
        assert isinstance(orderer, RoundRobinOrderer)

    def test_random_with_seed(self):
        """Test creating random orderer with seed."""
        orderer = get_orderer(OrderingStrategy.RANDOM, seed=42)
        assert isinstance(orderer, RandomOrderer)

    def test_priority(self):
        """Test creating priority orderer."""
        orderer = get_orderer(OrderingStrategy.PRIORITY)
        assert isinstance(orderer, PriorityOrderer)

    def test_topology(self):
        """Test creating topology orderer."""
        orderer = get_orderer(OrderingStrategy.TOPOLOGY)
        assert isinstance(orderer, TopologyOrderer)

    def test_simultaneous(self):
        """Test creating simultaneous orderer."""
        orderer = get_orderer(OrderingStrategy.SIMULTANEOUS)
        assert isinstance(orderer, SimultaneousOrderer)

    def test_invalid_strategy(self):
        """Test that invalid strategy raises error."""
        with pytest.raises(ValueError):
            get_orderer("invalid_strategy")


class TestBatchAgents:
    """Tests for batch_agents function."""

    def test_empty_list(self):
        """Test batching empty list."""
        batches = list(batch_agents([], batch_size=3))
        assert batches == []

    def test_exact_batch_size(self):
        """Test when agents divide evenly into batches."""
        agents = ["a", "b", "c", "d", "e", "f"]
        batches = list(batch_agents(agents, batch_size=3))

        assert len(batches) == 2
        assert batches[0] == ["a", "b", "c"]
        assert batches[1] == ["d", "e", "f"]

    def test_partial_batch(self):
        """Test when last batch is partial."""
        agents = ["a", "b", "c", "d", "e"]
        batches = list(batch_agents(agents, batch_size=3))

        assert len(batches) == 2
        assert batches[0] == ["a", "b", "c"]
        assert batches[1] == ["d", "e"]

    def test_batch_size_larger_than_list(self):
        """Test when batch size is larger than list."""
        agents = ["a", "b"]
        batches = list(batch_agents(agents, batch_size=5))

        assert len(batches) == 1
        assert batches[0] == ["a", "b"]

    def test_batch_size_one(self):
        """Test with batch size of 1."""
        agents = ["a", "b", "c"]
        batches = list(batch_agents(agents, batch_size=1))

        assert len(batches) == 3
        assert batches == [["a"], ["b"], ["c"]]
