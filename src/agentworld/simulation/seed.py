"""Deterministic execution support via seeding.

This module provides infrastructure for reproducible simulations
as specified in ADR-011.
"""

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeterministicExecution:
    """Manages deterministic execution via seeds.

    Provides consistent random number generation for:
    - Agent ordering
    - Agent internal randomness
    - Step-specific randomness

    Note: Full determinism is impossible with LLM calls.
    We guarantee structural determinism (ordering, routing)
    while acknowledging LLM output variance.
    """

    seed: int
    _step_seeds: dict[int, int] = field(default_factory=dict, repr=False)
    _agent_rngs: dict[tuple[int, str], random.Random] = field(
        default_factory=dict, repr=False
    )

    def get_step_seed(self, step: int) -> int:
        """Get deterministic seed for a specific step.

        Args:
            step: Step number

        Returns:
            Derived step seed
        """
        if step not in self._step_seeds:
            # Derive step seed from master seed
            self._step_seeds[step] = hash((self.seed, step)) & 0xFFFFFFFF
        return self._step_seeds[step]

    def get_agent_seed(self, step: int, agent_id: str) -> int:
        """Get deterministic seed for an agent at a step.

        Args:
            step: Step number
            agent_id: Agent ID

        Returns:
            Agent-specific seed for the step
        """
        step_seed = self.get_step_seed(step)
        return hash((step_seed, agent_id)) & 0xFFFFFFFF

    def create_agent_rng(self, step: int, agent_id: str) -> random.Random:
        """Create deterministic RNG for agent at step.

        The RNG is cached so multiple calls return the same instance.

        Args:
            step: Step number
            agent_id: Agent ID

        Returns:
            Deterministic Random instance
        """
        key = (step, agent_id)
        if key not in self._agent_rngs:
            agent_seed = self.get_agent_seed(step, agent_id)
            self._agent_rngs[key] = random.Random(agent_seed)
        return self._agent_rngs[key]

    def create_step_rng(self, step: int) -> random.Random:
        """Create deterministic RNG for a step.

        Args:
            step: Step number

        Returns:
            Deterministic Random instance
        """
        return random.Random(self.get_step_seed(step))

    def reset(self) -> None:
        """Reset cached seeds and RNGs."""
        self._step_seeds.clear()
        self._agent_rngs.clear()


@dataclass
class SeedConfig:
    """Configuration for deterministic execution."""

    master_seed: int | None = None  # None = non-deterministic
    llm_temperature: float = 0.7  # Lower = more deterministic
    use_llm_seed: bool = False  # Whether to pass seed to LLM provider

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "master_seed": self.master_seed,
            "llm_temperature": self.llm_temperature,
            "use_llm_seed": self.use_llm_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SeedConfig":
        """Create from dictionary."""
        return cls(
            master_seed=data.get("master_seed"),
            llm_temperature=data.get("llm_temperature", 0.7),
            use_llm_seed=data.get("use_llm_seed", False),
        )


def create_deterministic_execution(
    seed: int | None = None,
) -> DeterministicExecution | None:
    """Create deterministic execution context.

    Args:
        seed: Master seed (None for non-deterministic)

    Returns:
        DeterministicExecution or None if no seed
    """
    if seed is None:
        return None
    return DeterministicExecution(seed=seed)


def get_deterministic_llm_params(
    config: SeedConfig,
    step: int,
    agent_id: str,
) -> dict[str, Any]:
    """Get LLM parameters for deterministic execution.

    Args:
        config: Seed configuration
        step: Current step
        agent_id: Agent ID

    Returns:
        Dict of LLM parameters for more deterministic output
    """
    params: dict[str, Any] = {
        "temperature": config.llm_temperature,
    }

    if config.master_seed is not None and config.use_llm_seed:
        # Derive a seed for this specific call
        call_seed = hash((config.master_seed, step, agent_id)) & 0xFFFFFFFF
        params["seed"] = call_seed

    return params


# Utility functions for common randomization patterns


def deterministic_choice(
    items: list[Any],
    rng: random.Random | None = None,
) -> Any:
    """Make a deterministic random choice.

    Args:
        items: List of items to choose from
        rng: Optional deterministic RNG

    Returns:
        Randomly chosen item
    """
    if not items:
        raise ValueError("Cannot choose from empty list")
    if rng is None:
        rng = random.Random()
    return rng.choice(items)


def deterministic_shuffle(
    items: list[Any],
    rng: random.Random | None = None,
) -> list[Any]:
    """Create a deterministically shuffled copy.

    Args:
        items: List to shuffle
        rng: Optional deterministic RNG

    Returns:
        Shuffled copy of the list
    """
    if rng is None:
        rng = random.Random()
    result = items.copy()
    rng.shuffle(result)
    return result


def deterministic_sample(
    items: list[Any],
    k: int,
    rng: random.Random | None = None,
) -> list[Any]:
    """Make a deterministic random sample.

    Args:
        items: List to sample from
        k: Number of items to sample
        rng: Optional deterministic RNG

    Returns:
        List of sampled items
    """
    if rng is None:
        rng = random.Random()
    return rng.sample(items, k)


def deterministic_float(
    low: float = 0.0,
    high: float = 1.0,
    rng: random.Random | None = None,
) -> float:
    """Generate a deterministic random float.

    Args:
        low: Lower bound
        high: Upper bound
        rng: Optional deterministic RNG

    Returns:
        Random float between low and high
    """
    if rng is None:
        rng = random.Random()
    return rng.uniform(low, high)
