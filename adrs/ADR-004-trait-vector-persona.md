# ADR-004: Trait Vector Persona System

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: TinyTroupe's Big Five approach identified as best-of-breed

## Context

Agent personas can be specified in multiple approaches:

| Approach | Example | Pros | Cons |
|----------|---------|------|------|
| **Natural Language** | "Lisa is curious and organized..." | Flexible, human-readable | Inconsistent, hard to compare |
| **Structured Fields** | `{occupation: "engineer", age: 30}` | Reproducible, queryable | Limited expressiveness |
| **Trait Vectors** | `{openness: 0.8, conscientiousness: 0.9}` | Quantifiable, comparable, tunable | Requires mapping to behavior |
| **Hybrid** | Traits + descriptions | Best of both | More complex |

**Big Five (OCEAN) Model:**

The Five-Factor Model is psychology's dominant personality framework with decades of validation:

| Trait | High Score (→1.0) | Low Score (→0.0) |
|-------|-------------------|------------------|
| **Openness** | Creative, curious, open to new ideas | Practical, conventional, focused |
| **Conscientiousness** | Organized, dependable, disciplined | Flexible, spontaneous, careless |
| **Extraversion** | Outgoing, energetic, talkative | Reserved, solitary, quiet |
| **Agreeableness** | Cooperative, trusting, helpful | Competitive, skeptical, challenging |
| **Neuroticism** | Anxious, moody, easily stressed | Calm, stable, resilient |

**TinyTroupe Approach (from ADR-001):**
```python
lisa.define("personality", {
    "traits": ["curious", "analytical"],
    "big_five": {
        "openness": "High. Very imaginative.",
        "conscientiousness": "High. Meticulously organized."
    }
})
```
Uses text descriptions ("High", "Low") - not directly quantifiable.

**User Requirement:**
> "I want to model agent personas as a trait vector - collection of traits with a knob which is more like a continuum"

## Decision

Implement **Trait Vectors with continuous 0-1 values** for Big Five traits plus extensible custom traits.

### Data Structure

```python
@dataclass
class TraitVector:
    # Big Five (0.0 to 1.0 continuous)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Custom traits (domain-specific, extensible)
    custom_traits: Dict[str, CustomTrait] = field(default_factory=dict)

    def __post_init__(self):
        # Validate Big Five in [0, 1]
        for trait in ['openness', 'conscientiousness', 'extraversion',
                      'agreeableness', 'neuroticism']:
            value = getattr(self, trait)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{trait} must be in [0, 1], got {value}")

@dataclass
class CustomTrait:
    """Typed custom trait with metadata."""
    value: float  # 0.0 to 1.0
    description: str  # What this trait measures
    high_label: str  # Label for high values (e.g., "tech-savvy")
    low_label: str   # Label for low values (e.g., "tech-averse")
    weight: float = 1.0  # Weight in similarity calculations

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Custom trait value must be in [0, 1]")
```

### Prompt Text Generation (Interpolated)

Instead of coarse thresholds, use interpolated descriptions for richer mapping:

```python
def to_prompt_context(self) -> str:
    """Generate natural language description with interpolation."""
    descriptions = []

    # Openness: interpolate between anchors
    if self.openness >= 0.8:
        descriptions.append("highly creative, curious, and open to unconventional ideas")
    elif self.openness >= 0.6:
        descriptions.append("creative and intellectually curious")
    elif self.openness >= 0.4:
        descriptions.append("balanced between creativity and practicality")
    elif self.openness >= 0.2:
        descriptions.append("practical and grounded, preferring proven approaches")
    else:
        descriptions.append("highly conventional and focused on concrete matters")

    # Similar interpolation for other traits...

    # Include significant custom traits
    for name, trait in self.custom_traits.items():
        if trait.value >= 0.7:
            descriptions.append(f"{trait.high_label}")
        elif trait.value <= 0.3:
            descriptions.append(f"{trait.low_label}")

    return "You are " + ", ".join(descriptions) + "."
```

### Similarity Computation (Weighted)

```python
def similarity(self, other: "TraitVector",
               include_custom: bool = True) -> float:
    """
    Weighted cosine similarity between personalities.

    Big Five traits have equal weight (1.0 each).
    Custom traits use their defined weights.
    """
    # Big Five vector (equal weights)
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
        # Align custom traits (only shared traits)
        shared_traits = set(self.custom_traits.keys()) & set(other.custom_traits.keys())
        for trait_name in sorted(shared_traits):
            self_trait = self.custom_traits[trait_name]
            other_trait = other.custom_traits[trait_name]
            weight = (self_trait.weight + other_trait.weight) / 2
            self_vec.append(self_trait.value * weight)
            other_vec.append(other_trait.value * weight)

    # Cosine similarity
    dot = sum(a * b for a, b in zip(self_vec, other_vec))
    norm_self = sum(a * a for a in self_vec) ** 0.5
    norm_other = sum(b * b for b in other_vec) ** 0.5

    if norm_self == 0 or norm_other == 0:
        return 0.0
    return dot / (norm_self * norm_other)
```

### Persona Profile (Full Agent Identity)

```python
@dataclass
class PersonaProfile:
    """Complete agent identity combining traits with demographics."""
    name: str
    traits: TraitVector

    # Structured demographics (optional)
    occupation: Optional[str] = None
    age: Optional[int] = None
    background: Optional[str] = None
    goals: List[str] = field(default_factory=list)

    # Free-form description (supplements traits)
    description: Optional[str] = None

    def to_system_prompt(self) -> str:
        """Generate full system prompt for LLM."""
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
```

### Population Generation

```python
def generate_diverse_population(
    n: int,
    trait_distributions: Optional[Dict[str, Tuple[float, float]]] = None,
    seed: int = None
) -> List[TraitVector]:
    """
    Generate a population with controlled trait distributions.

    Args:
        n: Number of agents
        trait_distributions: Dict of trait_name -> (mean, std)
        seed: For reproducibility

    Returns:
        List of TraitVectors sampled from distributions
    """
    rng = random.Random(seed)

    defaults = {
        'openness': (0.5, 0.2),
        'conscientiousness': (0.5, 0.2),
        'extraversion': (0.5, 0.2),
        'agreeableness': (0.5, 0.2),
        'neuroticism': (0.5, 0.2),
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
```

### Determinism Clarification

> **Important**: Trait vectors provide *reproducible personality specification*, not deterministic LLM output. The same TraitVector will generate the same system prompt, but LLM responses depend on temperature and sampling settings (see **[ADR-002](./ADR-002-agent-scale.md)** Reproducibility Strategy).

## Consequences

**Positive:**
- **Quantifiable**: Run experiments varying specific traits systematically
- **Comparable**: Compute weighted similarity between agents
- **Reproducible**: Same vector = same prompt (LLM settings control output)
- **Extensible**: Add typed domain-specific traits with metadata
- **Research-friendly**: Statistical analysis of trait effects on behavior
- **Population sampling**: Generate diverse agent groups from distributions

**Negative:**
- Requires mapping traits to natural language for prompts
- May feel less "human" than prose descriptions
- Big Five doesn't capture all personality dimensions (values, goals separate)
- Interpolated mapping requires careful prompt engineering

**Implementation Notes:**
- `to_prompt_context()` uses 5-level interpolation for smoother mapping
- Custom traits must include metadata for meaningful similarity
- `PersonaProfile` links demographics to traits for full identity
- Provider-specific prompt testing recommended (see **[ADR-003](./ADR-003-llm-architecture.md)**)

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): TinyTroupe's Big Five approach
- [ADR-002](./ADR-002-agent-scale.md): Reproducibility requires LLM settings control
- [ADR-003](./ADR-003-llm-architecture.md): Prompt templates use trait context
- [ADR-008](./ADR-008-persistence.md): Stores trait vectors in SQLite
- [ADR-009](./ADR-009-use-case-scenarios.md): Scenarios use personas for agent behavior
- [ADR-010](./ADR-010-evaluation-metrics.md): Validates persona adherence
