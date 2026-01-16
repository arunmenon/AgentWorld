"""Tests for deterministic execution support."""

import pytest
import random

from agentworld.simulation.seed import (
    DeterministicExecution,
    SeedConfig,
    create_deterministic_execution,
    get_deterministic_llm_params,
    deterministic_choice,
    deterministic_shuffle,
    deterministic_sample,
    deterministic_float,
)


class TestDeterministicExecution:
    """Tests for DeterministicExecution class."""

    @pytest.fixture
    def execution(self):
        """Create execution instance."""
        return DeterministicExecution(seed=42)

    def test_creation(self, execution):
        """Test creating execution context."""
        assert execution.seed == 42

    def test_get_step_seed(self, execution):
        """Test getting step seed."""
        seed1 = execution.get_step_seed(1)
        seed2 = execution.get_step_seed(2)

        assert isinstance(seed1, int)
        assert isinstance(seed2, int)
        assert seed1 != seed2

    def test_step_seed_deterministic(self, execution):
        """Test that step seeds are deterministic."""
        seed1a = execution.get_step_seed(1)
        seed1b = execution.get_step_seed(1)

        assert seed1a == seed1b

    def test_get_agent_seed(self, execution):
        """Test getting agent seed."""
        seed_a1 = execution.get_agent_seed(step=1, agent_id="agent1")
        seed_a2 = execution.get_agent_seed(step=1, agent_id="agent2")

        assert isinstance(seed_a1, int)
        assert seed_a1 != seed_a2  # Different agents get different seeds

    def test_agent_seed_deterministic(self, execution):
        """Test that agent seeds are deterministic."""
        seed1 = execution.get_agent_seed(step=5, agent_id="agent1")

        # Create new execution with same master seed
        execution2 = DeterministicExecution(seed=42)
        seed2 = execution2.get_agent_seed(step=5, agent_id="agent1")

        assert seed1 == seed2

    def test_create_agent_rng(self, execution):
        """Test creating agent RNG."""
        rng = execution.create_agent_rng(step=1, agent_id="agent1")

        assert isinstance(rng, random.Random)

    def test_agent_rng_cached(self, execution):
        """Test that agent RNG is cached."""
        rng1 = execution.create_agent_rng(step=1, agent_id="agent1")
        rng2 = execution.create_agent_rng(step=1, agent_id="agent1")

        assert rng1 is rng2

    def test_agent_rng_deterministic(self, execution):
        """Test that agent RNG produces deterministic results."""
        rng = execution.create_agent_rng(step=1, agent_id="agent1")
        result1 = [rng.random() for _ in range(5)]

        # Create new execution and new RNG
        execution2 = DeterministicExecution(seed=42)
        rng2 = execution2.create_agent_rng(step=1, agent_id="agent1")
        result2 = [rng2.random() for _ in range(5)]

        assert result1 == result2

    def test_create_step_rng(self, execution):
        """Test creating step RNG."""
        rng = execution.create_step_rng(step=1)

        assert isinstance(rng, random.Random)

    def test_reset(self, execution):
        """Test resetting cached values."""
        execution.get_step_seed(1)
        execution.create_agent_rng(step=1, agent_id="agent1")

        execution.reset()

        assert len(execution._step_seeds) == 0
        assert len(execution._agent_rngs) == 0


class TestSeedConfig:
    """Tests for SeedConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = SeedConfig()

        assert config.master_seed is None
        assert config.llm_temperature == 0.7
        assert config.use_llm_seed is False

    def test_custom_values(self):
        """Test custom values."""
        config = SeedConfig(
            master_seed=42,
            llm_temperature=0.0,
            use_llm_seed=True,
        )

        assert config.master_seed == 42
        assert config.llm_temperature == 0.0
        assert config.use_llm_seed is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SeedConfig(master_seed=42)
        data = config.to_dict()

        assert data["master_seed"] == 42
        assert data["llm_temperature"] == 0.7

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "master_seed": 123,
            "llm_temperature": 0.5,
            "use_llm_seed": True,
        }
        config = SeedConfig.from_dict(data)

        assert config.master_seed == 123
        assert config.llm_temperature == 0.5
        assert config.use_llm_seed is True


class TestCreateDeterministicExecution:
    """Tests for create_deterministic_execution function."""

    def test_with_seed(self):
        """Test creating with seed."""
        execution = create_deterministic_execution(seed=42)

        assert execution is not None
        assert execution.seed == 42

    def test_without_seed(self):
        """Test creating without seed."""
        execution = create_deterministic_execution(seed=None)

        assert execution is None


class TestGetDeterministicLLMParams:
    """Tests for get_deterministic_llm_params function."""

    def test_basic_params(self):
        """Test basic parameters."""
        config = SeedConfig(llm_temperature=0.5)
        params = get_deterministic_llm_params(config, step=1, agent_id="agent1")

        assert params["temperature"] == 0.5
        assert "seed" not in params

    def test_with_llm_seed(self):
        """Test with LLM seed enabled."""
        config = SeedConfig(
            master_seed=42,
            llm_temperature=0.3,
            use_llm_seed=True,
        )
        params = get_deterministic_llm_params(config, step=1, agent_id="agent1")

        assert params["temperature"] == 0.3
        assert "seed" in params
        assert isinstance(params["seed"], int)

    def test_llm_seed_deterministic(self):
        """Test that LLM seed is deterministic."""
        config = SeedConfig(master_seed=42, use_llm_seed=True)

        params1 = get_deterministic_llm_params(config, step=1, agent_id="agent1")
        params2 = get_deterministic_llm_params(config, step=1, agent_id="agent1")

        assert params1["seed"] == params2["seed"]

    def test_llm_seed_varies_by_agent(self):
        """Test that different agents get different seeds."""
        config = SeedConfig(master_seed=42, use_llm_seed=True)

        params1 = get_deterministic_llm_params(config, step=1, agent_id="agent1")
        params2 = get_deterministic_llm_params(config, step=1, agent_id="agent2")

        assert params1["seed"] != params2["seed"]


class TestDeterministicChoice:
    """Tests for deterministic_choice function."""

    def test_with_rng(self):
        """Test choice with deterministic RNG."""
        rng = random.Random(42)
        items = ["a", "b", "c", "d", "e"]

        choice1 = deterministic_choice(items, rng=random.Random(42))
        choice2 = deterministic_choice(items, rng=random.Random(42))

        assert choice1 == choice2

    def test_without_rng(self):
        """Test choice without RNG."""
        items = ["a", "b", "c"]
        choice = deterministic_choice(items)

        assert choice in items

    def test_empty_list(self):
        """Test choice with empty list."""
        with pytest.raises(ValueError):
            deterministic_choice([])


class TestDeterministicShuffle:
    """Tests for deterministic_shuffle function."""

    def test_with_rng(self):
        """Test shuffle with deterministic RNG."""
        items = ["a", "b", "c", "d", "e"]

        shuffled1 = deterministic_shuffle(items, rng=random.Random(42))
        shuffled2 = deterministic_shuffle(items, rng=random.Random(42))

        assert shuffled1 == shuffled2
        assert set(shuffled1) == set(items)

    def test_original_unchanged(self):
        """Test that original list is unchanged."""
        items = ["a", "b", "c"]
        shuffled = deterministic_shuffle(items, rng=random.Random(42))

        # Original should be unchanged
        assert items == ["a", "b", "c"]
        # Shuffled might be different
        assert set(shuffled) == set(items)

    def test_without_rng(self):
        """Test shuffle without RNG."""
        items = ["a", "b", "c", "d"]
        shuffled = deterministic_shuffle(items)

        assert set(shuffled) == set(items)


class TestDeterministicSample:
    """Tests for deterministic_sample function."""

    def test_with_rng(self):
        """Test sample with deterministic RNG."""
        items = ["a", "b", "c", "d", "e"]

        sample1 = deterministic_sample(items, k=3, rng=random.Random(42))
        sample2 = deterministic_sample(items, k=3, rng=random.Random(42))

        assert sample1 == sample2
        assert len(sample1) == 3

    def test_without_rng(self):
        """Test sample without RNG."""
        items = ["a", "b", "c", "d", "e"]
        sample = deterministic_sample(items, k=2)

        assert len(sample) == 2
        assert all(item in items for item in sample)


class TestDeterministicFloat:
    """Tests for deterministic_float function."""

    def test_with_rng(self):
        """Test float generation with deterministic RNG."""
        float1 = deterministic_float(0.0, 1.0, rng=random.Random(42))
        float2 = deterministic_float(0.0, 1.0, rng=random.Random(42))

        assert float1 == float2
        assert 0.0 <= float1 <= 1.0

    def test_custom_range(self):
        """Test float generation with custom range."""
        value = deterministic_float(10.0, 20.0, rng=random.Random(42))

        assert 10.0 <= value <= 20.0

    def test_without_rng(self):
        """Test float generation without RNG."""
        value = deterministic_float(0.0, 100.0)

        assert 0.0 <= value <= 100.0
