"""Trait vector system based on Big Five personality model."""

import random
from dataclasses import dataclass, field
from typing import Any

from agentworld.core.exceptions import ValidationError


# Big Five trait descriptors (low to high)
TRAIT_DESCRIPTORS = {
    "openness": {
        "name": "Openness to Experience",
        "low": "practical, conventional, prefers routine",
        "high": "creative, curious, open to new ideas",
    },
    "conscientiousness": {
        "name": "Conscientiousness",
        "low": "flexible, spontaneous, may overlook details",
        "high": "organized, disciplined, detail-oriented",
    },
    "extraversion": {
        "name": "Extraversion",
        "low": "reserved, thoughtful, prefers solitude",
        "high": "outgoing, energetic, seeks social interaction",
    },
    "agreeableness": {
        "name": "Agreeableness",
        "low": "competitive, skeptical, challenging",
        "high": "cooperative, trusting, helpful",
    },
    "neuroticism": {
        "name": "Neuroticism",
        "low": "calm, emotionally stable, resilient",
        "high": "sensitive, prone to stress, emotionally reactive",
    },
}


def validate_trait_value(value: float, trait_name: str = "trait") -> float:
    """Validate that a trait value is in the 0-1 range.

    Args:
        value: Trait value to validate
        trait_name: Name of trait (for error messages)

    Returns:
        Validated value

    Raises:
        ValidationError: If value is out of range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{trait_name} must be a number, got {type(value).__name__}")
    if value < 0 or value > 1:
        raise ValidationError(f"{trait_name} must be between 0 and 1, got {value}")
    return float(value)


@dataclass
class CustomTrait:
    """Typed custom trait with metadata.

    Custom traits extend the Big Five with domain-specific dimensions.
    They include descriptive metadata for prompt generation and
    weighted similarity calculations.
    """

    value: float  # 0.0 to 1.0
    description: str  # What this trait measures
    high_label: str  # Label for high values (e.g., "tech-savvy")
    low_label: str  # Label for low values (e.g., "tech-averse")
    weight: float = 1.0  # Weight in similarity calculations

    def __post_init__(self) -> None:
        """Validate trait value after initialization."""
        self.value = validate_trait_value(self.value, "custom trait value")
        if self.weight < 0:
            raise ValidationError(f"Weight must be non-negative, got {self.weight}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "description": self.description,
            "high_label": self.high_label,
            "low_label": self.low_label,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomTrait":
        """Create from dictionary."""
        return cls(
            value=data["value"],
            description=data.get("description", ""),
            high_label=data.get("high_label", "high"),
            low_label=data.get("low_label", "low"),
            weight=data.get("weight", 1.0),
        )


@dataclass
class TraitVector:
    """Big Five personality trait vector with optional custom traits.

    The Big Five (OCEAN) model:
    - Openness: creativity, curiosity vs. consistency, caution
    - Conscientiousness: organization, dependability vs. flexibility, spontaneity
    - Extraversion: outgoing, energetic vs. solitary, reserved
    - Agreeableness: friendly, compassionate vs. challenging, detached
    - Neuroticism: sensitive, nervous vs. resilient, confident

    All trait values are continuous in the range [0, 1].
    """

    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    custom_traits: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate trait values after initialization."""
        self.openness = validate_trait_value(self.openness, "openness")
        self.conscientiousness = validate_trait_value(self.conscientiousness, "conscientiousness")
        self.extraversion = validate_trait_value(self.extraversion, "extraversion")
        self.agreeableness = validate_trait_value(self.agreeableness, "agreeableness")
        self.neuroticism = validate_trait_value(self.neuroticism, "neuroticism")

        # Validate custom traits
        for name, value in self.custom_traits.items():
            self.custom_traits[name] = validate_trait_value(value, name)

    @property
    def big_five(self) -> dict[str, float]:
        """Get the Big Five traits as a dictionary."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

    def to_dict(self) -> dict[str, float]:
        """Convert all traits to a flat dictionary."""
        result = self.big_five.copy()
        result.update(self.custom_traits)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraitVector":
        """Create a TraitVector from a dictionary.

        Big Five traits are extracted, all others become custom traits.

        Args:
            data: Dictionary of trait names to values

        Returns:
            TraitVector instance
        """
        big_five_keys = {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}

        big_five = {k: v for k, v in data.items() if k in big_five_keys}
        custom = {k: v for k, v in data.items() if k not in big_five_keys}

        return cls(**big_five, custom_traits=custom)

    def get_trait_level(self, trait: str) -> str:
        """Get a descriptive level for a trait value.

        Args:
            trait: Trait name

        Returns:
            "low", "moderate", or "high"
        """
        value = self.to_dict().get(trait, 0.5)
        if value < 0.35:
            return "low"
        elif value > 0.65:
            return "high"
        return "moderate"

    def to_prompt_description(self) -> str:
        """Generate a natural language description of the personality.

        Uses 5-level interpolation per ADR-004 for richer mapping.

        Returns:
            Human-readable personality description
        """
        descriptions = []

        # Openness - 5 levels
        if self.openness >= 0.8:
            descriptions.append("highly creative, curious, and open to unconventional ideas")
        elif self.openness >= 0.6:
            descriptions.append("creative and intellectually curious")
        elif self.openness >= 0.4:
            pass  # Moderate - skip
        elif self.openness >= 0.2:
            descriptions.append("practical and grounded, preferring proven approaches")
        else:
            descriptions.append("highly conventional and focused on concrete matters")

        # Conscientiousness - 5 levels
        if self.conscientiousness >= 0.8:
            descriptions.append("highly organized, disciplined, and detail-oriented")
        elif self.conscientiousness >= 0.6:
            descriptions.append("organized and dependable")
        elif self.conscientiousness >= 0.4:
            pass  # Moderate - skip
        elif self.conscientiousness >= 0.2:
            descriptions.append("flexible and spontaneous")
        else:
            descriptions.append("highly spontaneous, may overlook details")

        # Extraversion - 5 levels
        if self.extraversion >= 0.8:
            descriptions.append("highly outgoing, energetic, and talkative")
        elif self.extraversion >= 0.6:
            descriptions.append("outgoing and sociable")
        elif self.extraversion >= 0.4:
            pass  # Moderate - skip
        elif self.extraversion >= 0.2:
            descriptions.append("reserved and thoughtful")
        else:
            descriptions.append("highly reserved, prefers solitude")

        # Agreeableness - 5 levels
        if self.agreeableness >= 0.8:
            descriptions.append("highly cooperative, trusting, and helpful")
        elif self.agreeableness >= 0.6:
            descriptions.append("cooperative and friendly")
        elif self.agreeableness >= 0.4:
            pass  # Moderate - skip
        elif self.agreeableness >= 0.2:
            descriptions.append("skeptical and questioning")
        else:
            descriptions.append("highly competitive and challenging")

        # Neuroticism - 5 levels
        if self.neuroticism >= 0.8:
            descriptions.append("emotionally sensitive, prone to stress")
        elif self.neuroticism >= 0.6:
            descriptions.append("somewhat anxious and emotionally reactive")
        elif self.neuroticism >= 0.4:
            pass  # Moderate - skip
        elif self.neuroticism >= 0.2:
            descriptions.append("emotionally stable and resilient")
        else:
            descriptions.append("highly calm, stable, and unflappable")

        # Add custom trait descriptions (typed CustomTrait or float)
        for trait_name, trait_data in self.custom_traits.items():
            if isinstance(trait_data, CustomTrait):
                if trait_data.value >= 0.7:
                    descriptions.append(trait_data.high_label)
                elif trait_data.value <= 0.3:
                    descriptions.append(trait_data.low_label)
            else:
                # Legacy float support
                value = trait_data
                if value >= 0.7:
                    descriptions.append(f"high {trait_name.replace('_', ' ')}")
                elif value <= 0.3:
                    descriptions.append(f"low {trait_name.replace('_', ' ')}")

        if not descriptions:
            return "balanced personality with moderate traits"

        return ", ".join(descriptions)

    def to_prompt_context(self) -> str:
        """Generate full prompt context for LLM.

        Alias for to_prompt_description() with 'You are' prefix.

        Returns:
            Prompt-ready personality context string
        """
        desc = self.to_prompt_description()
        return f"You are {desc}."

    def similarity(self, other: "TraitVector", include_custom: bool = True) -> float:
        """Calculate weighted similarity to another trait vector.

        Uses weighted cosine similarity per ADR-004.
        Big Five traits have equal weight (1.0 each).
        Custom traits use their defined weights.

        Args:
            other: Another TraitVector
            include_custom: Whether to include custom traits in calculation

        Returns:
            Similarity score between 0 and 1
        """
        import math

        big_five_weight = 1.0
        self_vec = [
            self.openness * big_five_weight,
            self.conscientiousness * big_five_weight,
            self.extraversion * big_five_weight,
            self.agreeableness * big_five_weight,
            self.neuroticism * big_five_weight,
        ]
        other_vec = [
            other.openness * big_five_weight,
            other.conscientiousness * big_five_weight,
            other.extraversion * big_five_weight,
            other.agreeableness * big_five_weight,
            other.neuroticism * big_five_weight,
        ]

        if include_custom:
            # Find shared custom traits
            self_keys = set(self.custom_traits.keys())
            other_keys = set(other.custom_traits.keys())
            shared_traits = self_keys & other_keys

            for trait_name in sorted(shared_traits):
                self_trait = self.custom_traits[trait_name]
                other_trait = other.custom_traits[trait_name]

                # Handle both CustomTrait objects and raw floats
                if isinstance(self_trait, CustomTrait):
                    self_val = self_trait.value
                    self_weight = self_trait.weight
                else:
                    self_val = self_trait
                    self_weight = 1.0

                if isinstance(other_trait, CustomTrait):
                    other_val = other_trait.value
                    other_weight = other_trait.weight
                else:
                    other_val = other_trait
                    other_weight = 1.0

                # Average the weights
                weight = (self_weight + other_weight) / 2
                self_vec.append(self_val * weight)
                other_vec.append(other_val * weight)

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(self_vec, other_vec))
        norm_self = math.sqrt(sum(a * a for a in self_vec))
        norm_other = math.sqrt(sum(b * b for b in other_vec))

        if norm_self == 0 or norm_other == 0:
            return 0.0

        return dot_product / (norm_self * norm_other)

    def __repr__(self) -> str:
        """String representation."""
        traits = ", ".join(f"{k}={v:.2f}" for k, v in self.big_five.items())
        if self.custom_traits:
            custom = ", ".join(f"{k}={v:.2f}" for k, v in self.custom_traits.items())
            return f"TraitVector({traits}, custom={{{custom}}})"
        return f"TraitVector({traits})"


def create_trait_vector(
    openness: float = 0.5,
    conscientiousness: float = 0.5,
    extraversion: float = 0.5,
    agreeableness: float = 0.5,
    neuroticism: float = 0.5,
    **custom_traits: float,
) -> TraitVector:
    """Factory function to create a TraitVector.

    Args:
        openness: Openness to experience (0-1)
        conscientiousness: Conscientiousness (0-1)
        extraversion: Extraversion (0-1)
        agreeableness: Agreeableness (0-1)
        neuroticism: Neuroticism (0-1)
        **custom_traits: Additional custom traits

    Returns:
        TraitVector instance
    """
    return TraitVector(
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
        custom_traits=custom_traits,
    )


# Preset personality archetypes
ARCHETYPES = {
    "creative_innovator": TraitVector(
        openness=0.9,
        conscientiousness=0.4,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
    ),
    "analytical_thinker": TraitVector(
        openness=0.7,
        conscientiousness=0.9,
        extraversion=0.3,
        agreeableness=0.5,
        neuroticism=0.3,
    ),
    "social_enthusiast": TraitVector(
        openness=0.6,
        conscientiousness=0.5,
        extraversion=0.9,
        agreeableness=0.8,
        neuroticism=0.4,
    ),
    "skeptical_critic": TraitVector(
        openness=0.5,
        conscientiousness=0.7,
        extraversion=0.4,
        agreeableness=0.2,
        neuroticism=0.5,
    ),
    "calm_mediator": TraitVector(
        openness=0.6,
        conscientiousness=0.6,
        extraversion=0.5,
        agreeableness=0.9,
        neuroticism=0.1,
    ),
}


@dataclass
class PersonaProfile:
    """Complete agent identity combining traits with demographics.

    Per ADR-004, this provides a full agent identity that includes
    both quantifiable traits and descriptive demographics.
    """

    name: str
    traits: TraitVector

    # Structured demographics (optional)
    occupation: str | None = None
    age: int | None = None
    background: str | None = None
    goals: list[str] = field(default_factory=list)

    # Free-form description (supplements traits)
    description: str | None = None

    def to_system_prompt(self) -> str:
        """Generate full system prompt for LLM.

        Returns:
            Complete system prompt incorporating identity and traits
        """
        parts = [f"You are {self.name}."]

        if self.occupation:
            parts.append(f"You work as a {self.occupation}.")
        if self.age:
            parts.append(f"You are {self.age} years old.")
        if self.background:
            parts.append(self.background)

        # Trait-based personality
        parts.append(self.traits.to_prompt_context())

        if self.goals:
            parts.append("Your goals: " + ", ".join(self.goals))

        if self.description:
            parts.append(self.description)

        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "traits": self.traits.to_dict(),
            "occupation": self.occupation,
            "age": self.age,
            "background": self.background,
            "goals": self.goals,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaProfile":
        """Create from dictionary."""
        traits_data = data.get("traits", {})
        traits = TraitVector.from_dict(traits_data) if traits_data else TraitVector()

        return cls(
            name=data["name"],
            traits=traits,
            occupation=data.get("occupation"),
            age=data.get("age"),
            background=data.get("background"),
            goals=data.get("goals", []),
            description=data.get("description"),
        )


def generate_diverse_population(
    n: int,
    trait_distributions: dict[str, tuple[float, float]] | None = None,
    seed: int | None = None,
) -> list[TraitVector]:
    """Generate a population with controlled trait distributions.

    Per ADR-004, this enables systematic generation of diverse
    agent populations for research and simulation.

    Args:
        n: Number of agents to generate
        trait_distributions: Dict of trait_name -> (mean, std)
            Defaults to neutral distribution (0.5, 0.2) for all traits
        seed: Random seed for reproducibility

    Returns:
        List of TraitVectors sampled from distributions
    """
    rng = random.Random(seed)

    defaults = {
        "openness": (0.5, 0.2),
        "conscientiousness": (0.5, 0.2),
        "extraversion": (0.5, 0.2),
        "agreeableness": (0.5, 0.2),
        "neuroticism": (0.5, 0.2),
    }
    distributions = {**defaults, **(trait_distributions or {})}

    population = []
    for _ in range(n):
        traits = {}
        for trait, (mean, std) in distributions.items():
            # Sample and clamp to [0, 1]
            value = rng.gauss(mean, std)
            value = max(0.0, min(1.0, value))
            traits[trait] = value
        population.append(TraitVector(**traits))

    return population


def generate_population_with_profiles(
    n: int,
    name_prefix: str = "Agent",
    trait_distributions: dict[str, tuple[float, float]] | None = None,
    seed: int | None = None,
) -> list[PersonaProfile]:
    """Generate a population of PersonaProfiles.

    Convenience function that wraps generate_diverse_population
    and creates full PersonaProfile objects.

    Args:
        n: Number of profiles to generate
        name_prefix: Prefix for agent names (e.g., "Agent" -> "Agent_1")
        trait_distributions: Dict of trait_name -> (mean, std)
        seed: Random seed for reproducibility

    Returns:
        List of PersonaProfile instances
    """
    trait_vectors = generate_diverse_population(n, trait_distributions, seed)

    return [
        PersonaProfile(name=f"{name_prefix}_{i + 1}", traits=tv)
        for i, tv in enumerate(trait_vectors)
    ]
