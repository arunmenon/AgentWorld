# ADR-006: Dual Memory Architecture

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: Generative Agents memory system identified as best-of-breed
- **[ADR-003](./ADR-003-llm-architecture.md)**: Memory system requires LLM for importance rating and reflection

## Context

**Generative Agents Memory System (from ADR-001):**

Stanford's Generative Agents (UIST 2023 Best Paper) established the foundational memory architecture:

1. **Memory Stream**: All experiences stored in natural language with metadata
2. **Retrieval Function**: Combines recency, importance, relevance
3. **Reflection**: Synthesizes observations into higher-level insights
4. **Planning**: Uses memories for goal decomposition

**Key Innovation - Retrieval Function:**
```
score = α × relevance + β × recency + γ × importance

Where:
- relevance: Cosine similarity of embeddings to query
- recency: Exponential decay from timestamp (e^(-Δt/τ))
- importance: LLM-rated 1-10 (mundane to poignant)

Default weights: α=0.5, β=0.3, γ=0.2
```

> **Note**: The original paper uses different variable names. We standardize on α=relevance, β=recency, γ=importance for clarity.

**TinyTroupe Memory (from ADR-001):**
- Episodic memory for sequential experiences
- Semantic memory with vector embeddings
- Mental faculties for extensible retrieval

**Why Dual Memory Matters:**

| Memory Type | Contents | Purpose |
|-------------|----------|---------|
| **Episodic** | Specific events, conversations, observations | "What happened" |
| **Semantic** | Facts, insights, generalizations, reflections | "What I know/believe" |

**Example:**
- Episodic: "At 2pm, talked to Bob about project deadline. He seemed stressed."
- Semantic (Reflection): "Bob tends to get stressed about deadlines" (synthesized insight)

## Decision

Implement **Dual Memory System** with episodic observations and semantic reflections, using the Generative Agents retrieval function.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        Memory System                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │      Episodic        │    │      Semantic        │          │
│  │   (Observations)     │    │   (Reflections)      │          │
│  │                      │    │                      │          │
│  │ • id: UUID           │    │ • id: UUID           │          │
│  │ • content: str       │    │ • content: str       │          │
│  │ • timestamp: datetime│    │ • timestamp: datetime│          │
│  │ • importance: 1-10   │    │ • importance: 8-10   │          │
│  │ • source: str        │    │ • source_memories:[] │          │
│  │ • embedding: vec     │    │ • questions: []      │          │
│  │ • embedding_model:str│    │ • embedding: vec     │          │
│  │ • location: str      │    │ • embedding_model:str│          │
│  └──────────┬───────────┘    └──────────┬───────────┘          │
│             │                           │                       │
│             └─────────────┬─────────────┘                       │
│                           ▼                                     │
│             ┌─────────────────────────────┐                     │
│             │     Retrieval Engine        │                     │
│             │                             │                     │
│             │ score = α×relevance +       │                     │
│             │         β×recency +         │                     │
│             │         γ×importance        │                     │
│             │                             │                     │
│             │ Default: α=0.5, β=0.3, γ=0.2│                     │
│             └─────────────┬───────────────┘                     │
│                           │                                     │
│                           ▼                                     │
│             ┌─────────────────────────────┐                     │
│             │    Reflection Engine        │                     │
│             │                             │                     │
│             │ Triggered when accumulated  │                     │
│             │ importance > threshold      │                     │
│             │ (configurable, default=100) │                     │
│             │                             │                     │
│             │ Uses LLM (ADR-003) to:      │                     │
│             │ 1. Generate questions       │                     │
│             │ 2. Retrieve relevant memories│                    │
│             │ 3. Synthesize insights      │                     │
│             └─────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Embedding Configuration

```python
@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""
    model: str = "text-embedding-3-small"  # Default model
    dimensions: int = 1536  # Output dimensions
    provider: str = "openai"  # Provider for embeddings

    def validate_compatibility(self, other: "EmbeddingConfig") -> bool:
        """Check if embeddings from two configs are comparable."""
        return self.model == other.model and self.dimensions == other.dimensions
```

> **Important**: Embedding similarity is only valid when both vectors use the same model. Store `embedding_model` with each memory to detect incompatibility.

### Data Classes

```python
@dataclass
class Observation:
    """Episodic memory entry."""
    id: str
    content: str
    timestamp: datetime
    importance: float  # 1-10, LLM-rated or heuristic
    embedding: np.ndarray
    embedding_model: str  # e.g., "text-embedding-3-small"
    source: str  # Who/what caused this observation
    location: str = ""  # Optional spatial context

@dataclass
class Reflection:
    """Semantic memory entry."""
    id: str
    content: str
    timestamp: datetime
    importance: float  # 8-10, always high
    embedding: np.ndarray
    embedding_model: str
    source_memories: List[str]  # IDs of observations that led to this
    questions_addressed: List[str]  # Questions this reflection answers
```

### Importance Rating

**LLM-Based (Full Mode):**
```python
async def rate_importance(self, content: str) -> float:
    """Rate observation importance using LLM."""
    prompt = """
    Rate the importance of this observation on a scale of 1-10.
    1 = mundane (routine activity, small talk)
    5 = moderate (notable event, useful information)
    10 = crucial (major event, critical insight)

    Observation: "{content}"

    Return only a number 1-10.
    """
    response = await self.llm.complete([{"role": "user", "content": prompt}])
    return float(response.content.strip())
```

**Heuristic-Based (Lite Mode, per [ADR-002](./ADR-002-agent-scale.md)):**
```python
def rate_importance_heuristic(self, content: str) -> float:
    """Fast heuristic importance rating."""
    score = 3.0  # Baseline

    # Length bonus (longer = more detail = more important)
    if len(content) > 200:
        score += 1.0
    if len(content) > 500:
        score += 1.0

    # Keyword signals
    important_keywords = ["important", "critical", "urgent", "decision",
                          "agree", "disagree", "believe", "feel"]
    for keyword in important_keywords:
        if keyword in content.lower():
            score += 0.5

    return min(10.0, max(1.0, score))
```

**Batched Rating (Cost Optimization):**
```python
async def rate_importance_batch(self, observations: List[str]) -> List[float]:
    """Rate multiple observations in single LLM call."""
    prompt = f"""
    Rate the importance of each observation (1-10 scale).
    Return one number per line.

    Observations:
    {chr(10).join(f'{i+1}. {obs}' for i, obs in enumerate(observations))}
    """
    response = await self.llm.complete([{"role": "user", "content": prompt}])
    scores = [float(line.strip()) for line in response.content.strip().split('\n')]
    return scores
```

### Reflection Configuration

```python
@dataclass
class ReflectionConfig:
    """Configurable reflection parameters."""
    threshold: float = 100.0  # Accumulated importance to trigger
    questions_per_reflection: int = 3
    memories_per_question: int = 10
    min_reflection_importance: float = 8.0
    enabled: bool = True  # Can disable for lite mode
```

### Reflection Algorithm

```python
async def generate_reflections(self) -> List[Reflection]:
    """Generate reflections when accumulated importance exceeds threshold."""
    if not self.config.enabled:
        return []

    if self._importance_accumulator < self.config.threshold:
        return []

    # Get recent observations
    recent = self.observations[-100:]

    # Generate questions (uses LLM from ADR-003)
    questions = await self._generate_questions(recent)

    # For each question, retrieve and synthesize
    reflections = []
    for question in questions[:self.config.questions_per_reflection]:
        relevant = await self.retrieve(question, k=self.config.memories_per_question)
        insight = await self._synthesize(question, relevant)

        reflection = Reflection(
            id=str(uuid.uuid4()),
            content=insight,
            timestamp=datetime.now(),
            importance=self.config.min_reflection_importance,
            embedding=await self._embed(insight),
            embedding_model=self.embedding_config.model,
            source_memories=[m.id for m in relevant],
            questions_addressed=[question]
        )
        reflections.append(reflection)

    self._importance_accumulator = 0
    return reflections
```

### Memory Retention Policy

```python
@dataclass
class RetentionPolicy:
    """Policy for managing memory growth in long-running simulations."""
    max_observations: int = 1000  # Per agent
    max_reflections: int = 100    # Per agent
    prune_strategy: str = "importance_weighted"  # or "fifo", "recency"

    def should_prune(self, observation_count: int) -> bool:
        return observation_count > self.max_observations

def prune_memories(self, policy: RetentionPolicy) -> List[str]:
    """Remove low-value memories, return pruned IDs."""
    if not policy.should_prune(len(self.observations)):
        return []

    if policy.prune_strategy == "importance_weighted":
        # Keep high-importance and recent memories
        scored = [
            (obs, obs.importance * 0.7 + self._recency_score(obs) * 0.3)
            for obs in self.observations
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        keep = scored[:policy.max_observations]
        pruned = scored[policy.max_observations:]
        self.observations = [obs for obs, _ in keep]
        return [obs.id for obs, _ in pruned]

    # ... other strategies
```

## Consequences

**Positive:**
- Agents maintain coherent long-term understanding
- Reflections compress many observations into insights (context efficiency)
- Retrieval balances recent vs important vs relevant memories
- Enables emergent agent insights and learning
- Well-validated approach (Generative Agents paper)
- Configurable thresholds for tuning
- Retention policy prevents unbounded growth

**Negative:**
- Additional LLM calls for importance rating (~1 call per observation, or batched)
- Reflection generation adds latency (~3 LLM calls when triggered)
- Embedding storage requirements (varies by model)
- Complexity in managing two memory types
- Embedding model changes invalidate old memories

**MVP Simplification:**
- Phase 1: List-based memory with simple recency retrieval
- Phase 2: Full dual memory with embeddings and reflection

**Interactions:**
- Uses LLM provider from **[ADR-003](./ADR-003-llm-architecture.md)** for importance rating and reflection
- Persisted via **[ADR-008](./ADR-008-persistence.md)** (schema must include all fields)
- Used by scenarios in **[ADR-009](./ADR-009-use-case-scenarios.md)**
- Evaluated by metrics in **[ADR-010](./ADR-010-evaluation-metrics.md)**

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): Generative Agents memory architecture
- [ADR-002](./ADR-002-agent-scale.md): Lite mode disables reflection
- [ADR-003](./ADR-003-llm-architecture.md): LLM for importance and reflection
- [ADR-008](./ADR-008-persistence.md): Memory persistence in SQLite (must match schema)
- [ADR-009](./ADR-009-use-case-scenarios.md): Memory enables context-aware scenarios
- [ADR-010](./ADR-010-evaluation-metrics.md): Memory system metrics
