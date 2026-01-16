# ADR-010: Evaluation and Metrics System

## Status
Accepted

## Dependencies
- **[ADR-003](./ADR-003-llm-architecture.md)**: Validators use LLM for quality assessment
- **[ADR-006](./ADR-006-dual-memory.md)**: Metrics track memory system performance
- **[ADR-009](./ADR-009-use-case-scenarios.md)**: Evaluates scenario outputs

## Context

**TinyTroupe Evaluation Capabilities (from ADR-001):**
- **Propositions**: Monitor persona adherence, self-consistency
- **ResultsExtractor**: Structured data extraction from outputs
- **ResultsReducer**: Aggregate results across agents
- **InPlaceExperimentRunner**: A/B testing support
- **Action quality checks**: LLM-based validation

**Key Metrics Categories:**

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Behavioral** | Message count, response length, interaction frequency | Activity levels |
| **Memory (ADR-006)** | Observations/agent, reflections generated, retrieval hits | Memory health |
| **Network (ADR-005)** | Clustering coefficient, path length, centrality | Topology effects |
| **Quality** | Persona consistency, coherence, relevance | Output quality |
| **Cost** | Tokens used, API calls, estimated spend | Budget tracking |

## Decision

Implement **comprehensive evaluation system** with metrics collection, validators, and extractors.

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Evaluation System                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ MetricsCollector│  │   Validators    │  │ResultsExtractor│ │
│  │                 │  │                 │  │                │ │
│  │ • Behavioral    │  │ • Persona       │  │ • Opinions     │ │
│  │ • Memory        │  │   Adherence     │  │ • Sentiment    │ │
│  │ • Network       │  │ • Consistency   │  │ • Themes       │ │
│  │ • Cost          │  │ • Coherence     │  │ • Quotes       │ │
│  │                 │  │                 │  │                │ │
│  │ Uses: ADR-005,  │  │ Uses: ADR-003   │  │ Uses: ADR-003  │ │
│  │       ADR-006   │  │ (LLM scoring)   │  │ (LLM extraction│ │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘ │
│           │                    │                   │           │
│           └────────────────────┼───────────────────┘           │
│                                │                               │
│                                ▼                               │
│                    ┌─────────────────────┐                     │
│                    │   EvaluationReport  │                     │
│                    │                     │                     │
│                    │ • metrics: Dict     │                     │
│                    │ • validations: []   │                     │
│                    │ • extractions: {}   │                     │
│                    │ • recommendations   │                     │
│                    └─────────────────────┘                     │
└────────────────────────────────────────────────────────────────┘
```

### LLM Interface Wrapper

> **Consistency Note**: All evaluation components use a unified `LLMClient` wrapper that abstracts the underlying provider (ADR-003). This ensures consistent interface across validation, extraction, and other LLM operations.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json

@dataclass
class LLMResponse:
    """Standardized response from LLM calls."""
    content: str
    tokens_used: int
    model: str
    latency_ms: float

class LLMClient:
    """
    Unified LLM interface for evaluation components.

    Wraps LiteLLM (ADR-003) with:
    - Consistent async interface
    - Structured output parsing
    - Error handling with retries
    - Cost tracking
    """

    def __init__(self, provider: "LLMProvider"):  # From ADR-003
        self._provider = provider

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Send completion request with standardized response.

        Uses temperature=0 for deterministic evaluation by default.
        """
        response = await self._provider.acompletion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            model=response.model,
            latency_ms=response.response_ms
        )

    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any] = None,
        retries: int = 2
    ) -> Dict[str, Any]:
        """
        Request JSON-formatted response with validation.

        Args:
            messages: Conversation messages
            schema: Optional JSON schema for validation
            retries: Number of retries on parse failure

        Returns:
            Parsed JSON dict

        Raises:
            JSONParseError: After all retries exhausted
        """
        for attempt in range(retries + 1):
            try:
                response = await self.complete(messages)
                # Extract JSON from response (may be wrapped in markdown)
                json_str = self._extract_json(response.content)
                parsed = json.loads(json_str)

                if schema:
                    self._validate_schema(parsed, schema)

                return parsed
            except (json.JSONDecodeError, SchemaValidationError) as e:
                if attempt == retries:
                    raise JSONParseError(
                        f"Failed to parse JSON after {retries + 1} attempts: {e}"
                    )
                # Retry with clarified prompt
                messages = messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": "Please respond with valid JSON only."}
                ]

    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, handling markdown code blocks."""
        # Try to find JSON in code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            return content[start:end].strip()
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        # Assume entire content is JSON
        return content.strip()

    def _validate_schema(self, data: dict, schema: dict) -> None:
        """Basic schema validation (required fields, types)."""
        for field, field_type in schema.get("required", {}).items():
            if field not in data:
                raise SchemaValidationError(f"Missing required field: {field}")
            if not isinstance(data[field], field_type):
                raise SchemaValidationError(
                    f"Field {field} should be {field_type}, got {type(data[field])}"
                )

class JSONParseError(Exception):
    """Raised when JSON parsing fails after retries."""
    pass

class SchemaValidationError(Exception):
    """Raised when JSON doesn't match expected schema."""
    pass
```

### Metrics Collector

```python
@dataclass
class SimulationMetrics:
    """Collected metrics during simulation run."""

    # Behavioral metrics
    total_messages: int = 0
    messages_per_agent: Dict[str, int] = field(default_factory=dict)
    avg_response_length: float = 0.0
    interaction_matrix: Dict[Tuple[str, str], int] = field(default_factory=dict)

    # Memory metrics (ADR-006) - SEPARATE counters for observations and reflections
    observations_per_agent: Dict[str, int] = field(default_factory=dict)
    reflections_per_agent: Dict[str, int] = field(default_factory=dict)
    total_reflections: int = 0
    avg_memory_importance: float = 0.0
    retrieval_calls: int = 0
    retrieval_hit_rate: float = 0.0  # Fraction of retrievals returning results

    # Network metrics (ADR-005) - with safe handling for disconnected graphs
    clustering_coefficient: Optional[float] = None  # None if not computable
    avg_path_length: Optional[float] = None  # None if disconnected
    diameter: Optional[int] = None  # None if disconnected
    degree_distribution: Dict[str, int] = field(default_factory=dict)
    is_connected: bool = True

    # Cost metrics
    total_tokens: int = 0
    tokens_per_agent: Dict[str, int] = field(default_factory=dict)
    api_calls: int = 0
    estimated_cost_usd: float = 0.0

class MetricsCollector:
    """
    Collect metrics during simulation via event subscription.

    Subscribes to SimulationEventBus (ADR-007) and accumulates metrics.
    """

    def __init__(self):
        self.metrics = SimulationMetrics()
        self._importance_sum = 0.0
        self._importance_count = 0
        self._retrieval_attempts = 0
        self._retrieval_successes = 0

    def reset(self) -> None:
        """Reset all metrics for a new run."""
        self.metrics = SimulationMetrics()
        self._importance_sum = 0.0
        self._importance_count = 0
        self._retrieval_attempts = 0
        self._retrieval_successes = 0

    async def on_message(self, event: MessageEvent) -> None:
        """Track message metrics."""
        self.metrics.total_messages += 1
        self.metrics.messages_per_agent[event.sender] = \
            self.metrics.messages_per_agent.get(event.sender, 0) + 1

        # Track interaction pairs
        if event.receiver:
            pair = (event.sender, event.receiver)
            self.metrics.interaction_matrix[pair] = \
                self.metrics.interaction_matrix.get(pair, 0) + 1

        # Update average response length
        total_length = sum(
            len(m.content) for m in self._all_messages
        ) if hasattr(self, '_all_messages') else len(event.content)
        self.metrics.avg_response_length = total_length / self.metrics.total_messages

    async def on_memory_added(self, event: MemoryEvent) -> None:
        """
        Track memory system metrics (ADR-006).

        IMPORTANT: Observations and reflections are tracked SEPARATELY
        to provide accurate memory health metrics.
        """
        # Track importance for averaging
        self._importance_sum += event.importance
        self._importance_count += 1
        self.metrics.avg_memory_importance = (
            self._importance_sum / self._importance_count
        )

        # FIXED: Increment correct counter based on memory type
        if event.memory_type == "observation":
            self.metrics.observations_per_agent[event.agent_id] = \
                self.metrics.observations_per_agent.get(event.agent_id, 0) + 1
        elif event.memory_type == "reflection":
            self.metrics.reflections_per_agent[event.agent_id] = \
                self.metrics.reflections_per_agent.get(event.agent_id, 0) + 1
            self.metrics.total_reflections += 1

    async def on_memory_retrieval(self, event: RetrievalEvent) -> None:
        """Track memory retrieval metrics."""
        self.metrics.retrieval_calls += 1
        self._retrieval_attempts += 1
        if event.results_count > 0:
            self._retrieval_successes += 1
        self.metrics.retrieval_hit_rate = (
            self._retrieval_successes / self._retrieval_attempts
            if self._retrieval_attempts > 0 else 0.0
        )

    async def on_llm_call(self, event: LLMCallEvent) -> None:
        """Track cost metrics (ADR-003)."""
        self.metrics.total_tokens += event.tokens
        self.metrics.api_calls += 1
        self.metrics.estimated_cost_usd += event.estimated_cost

        # Track per-agent if available
        if event.agent_id:
            self.metrics.tokens_per_agent[event.agent_id] = \
                self.metrics.tokens_per_agent.get(event.agent_id, 0) + event.tokens

    def compute_network_metrics(self, topology: "Topology") -> None:
        """
        Compute network metrics (ADR-005).

        Safely handles disconnected graphs by:
        1. Always computing degree distribution
        2. Computing path metrics only for connected graphs
        3. For disconnected: computing metrics on largest connected component
        """
        import networkx as nx

        graph = topology.graph
        n = graph.number_of_nodes()

        if n == 0:
            return

        # Always compute degree distribution
        self.metrics.degree_distribution = dict(graph.degree())

        # Check connectivity (handle directed vs undirected)
        if topology._directed:
            self.metrics.is_connected = nx.is_weakly_connected(graph)
            # Use underlying undirected for clustering
            undirected = graph.to_undirected()
        else:
            self.metrics.is_connected = nx.is_connected(graph)
            undirected = graph

        # Clustering coefficient (always computable)
        try:
            self.metrics.clustering_coefficient = nx.average_clustering(undirected)
        except nx.NetworkXError:
            self.metrics.clustering_coefficient = None

        # Path metrics require connectivity
        if self.metrics.is_connected and n > 1:
            try:
                self.metrics.avg_path_length = nx.average_shortest_path_length(graph)
                self.metrics.diameter = nx.diameter(graph)
            except nx.NetworkXError:
                pass  # Leave as None
        else:
            # For disconnected graphs: compute on largest component
            if not self.metrics.is_connected:
                if topology._directed:
                    components = list(nx.weakly_connected_components(graph))
                else:
                    components = list(nx.connected_components(graph))

                if components:
                    largest = max(components, key=len)
                    subgraph = graph.subgraph(largest)
                    if len(largest) > 1:
                        try:
                            self.metrics.avg_path_length = \
                                nx.average_shortest_path_length(subgraph)
                            self.metrics.diameter = nx.diameter(subgraph)
                        except nx.NetworkXError:
                            pass

    def get_metrics(self) -> SimulationMetrics:
        """Return current metrics snapshot."""
        return self.metrics

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary for serialization."""
        return {
            "behavioral": {
                "total_messages": self.metrics.total_messages,
                "messages_per_agent": self.metrics.messages_per_agent,
                "avg_response_length": self.metrics.avg_response_length,
            },
            "memory": {
                "observations_per_agent": self.metrics.observations_per_agent,
                "reflections_per_agent": self.metrics.reflections_per_agent,
                "total_reflections": self.metrics.total_reflections,
                "avg_importance": self.metrics.avg_memory_importance,
                "retrieval_calls": self.metrics.retrieval_calls,
                "retrieval_hit_rate": self.metrics.retrieval_hit_rate,
            },
            "network": {
                "is_connected": self.metrics.is_connected,
                "clustering_coefficient": self.metrics.clustering_coefficient,
                "avg_path_length": self.metrics.avg_path_length,
                "diameter": self.metrics.diameter,
            },
            "cost": {
                "total_tokens": self.metrics.total_tokens,
                "api_calls": self.metrics.api_calls,
                "estimated_cost_usd": self.metrics.estimated_cost_usd,
            }
        }
```

### Validators

```python
@dataclass
class ValidationConfig:
    """Configuration for validation thresholds."""
    persona_adherence_threshold: float = 0.7
    consistency_threshold: float = 0.6
    coherence_threshold: float = 0.5
    use_separate_model: bool = False  # Use different model to reduce bias
    evaluation_model: str = "gpt-4o-mini"  # Cheaper model for evaluation
    max_validations_per_run: int = 100  # Budget control
    sampling_rate: float = 1.0  # Sample rate for validation (1.0 = all)

@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_type: str
    score: float  # 0-1
    passed: bool  # score >= threshold
    explanation: str
    agent_id: Optional[str] = None
    response_excerpt: str = ""  # First 100 chars of validated response

class Validator:
    """
    Validate agent behavior quality using LLM scoring.

    Uses configurable thresholds and optional separate evaluation model
    to reduce scoring bias.
    """

    def __init__(self, llm_client: LLMClient, config: ValidationConfig = None):
        self.llm = llm_client
        self.config = config or ValidationConfig()
        self._validation_count = 0

    def _should_validate(self) -> bool:
        """Check if we should run validation (budget/sampling)."""
        if self._validation_count >= self.config.max_validations_per_run:
            return False
        if self.config.sampling_rate < 1.0:
            import random
            return random.random() < self.config.sampling_rate
        return True

    async def check_persona_adherence(
        self,
        agent: "Agent",
        response: str
    ) -> ValidationResult:
        """
        Score how well response matches agent's persona (ADR-004).
        Returns score 0-1 with explanation.
        """
        if not self._should_validate():
            return ValidationResult(
                check_type="persona_adherence",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling",
                agent_id=agent.id
            )

        self._validation_count += 1

        prompt = f"""
Evaluate if this response matches the agent's personality profile.

Agent Persona:
{agent.persona.to_prompt_context()}

Agent's Response:
"{response[:1000]}"

Rate adherence from 0.0 (completely out of character) to 1.0 (perfectly in character).
Consider: tone, vocabulary, expressed opinions, and behavioral patterns.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}}
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="persona_adherence",
                score=score,
                passed=score >= self.config.persona_adherence_threshold,
                explanation=result["explanation"],
                agent_id=agent.id,
                response_excerpt=response[:100]
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="persona_adherence",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}",
                agent_id=agent.id
            )

    async def check_consistency(
        self,
        agent: "Agent",
        response: str,
        previous_responses: List[str]
    ) -> ValidationResult:
        """Check if response is consistent with agent's previous statements."""
        if not self._should_validate():
            return ValidationResult(
                check_type="consistency",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling",
                agent_id=agent.id
            )

        if not previous_responses:
            return ValidationResult(
                check_type="consistency",
                score=1.0,
                passed=True,
                explanation="No previous responses to compare",
                agent_id=agent.id
            )

        self._validation_count += 1

        # Use last 5 responses for context
        context_responses = previous_responses[-5:]
        prompt = f"""
Check if this new response is consistent with the agent's previous statements.

Previous statements:
{chr(10).join(f'- "{r[:200]}"' for r in context_responses)}

New response:
"{response[:500]}"

Rate consistency from 0.0 (contradicts previous statements) to 1.0 (fully consistent).
Consider: factual claims, opinions, personality, and knowledge.

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}}
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="consistency",
                score=score,
                passed=score >= self.config.consistency_threshold,
                explanation=result["explanation"],
                agent_id=agent.id,
                response_excerpt=response[:100]
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="consistency",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}",
                agent_id=agent.id
            )

    async def check_coherence(self, response: str) -> ValidationResult:
        """
        Check if response is coherent and well-formed.

        Evaluates:
        - Grammatical correctness
        - Logical flow
        - Completeness (not cut off)
        - Relevance to context
        """
        if not self._should_validate():
            return ValidationResult(
                check_type="coherence",
                score=0.0,
                passed=False,
                explanation="Skipped due to budget/sampling"
            )

        self._validation_count += 1

        prompt = f"""
Evaluate the coherence and quality of this response.

Response:
"{response[:1000]}"

Consider:
1. Grammatical correctness
2. Logical flow and structure
3. Completeness (not abruptly cut off)
4. Internal consistency

Rate coherence from 0.0 (incoherent/broken) to 1.0 (clear and well-formed).

Respond with JSON:
{{"score": <0.0-1.0>, "explanation": "<reasoning>"}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}],
                schema={"required": {"score": float, "explanation": str}}
            )
            score = float(result["score"])
            return ValidationResult(
                check_type="coherence",
                score=score,
                passed=score >= self.config.coherence_threshold,
                explanation=result["explanation"],
                response_excerpt=response[:100]
            )
        except (JSONParseError, KeyError) as e:
            return ValidationResult(
                check_type="coherence",
                score=0.0,
                passed=False,
                explanation=f"Validation failed: {e}"
            )

    async def validate_all(
        self,
        agent: "Agent",
        response: str,
        previous_responses: List[str] = None
    ) -> List[ValidationResult]:
        """Run all validation checks on a response."""
        results = []
        results.append(await self.check_persona_adherence(agent, response))
        results.append(await self.check_consistency(
            agent, response, previous_responses or []
        ))
        results.append(await self.check_coherence(response))
        return results

    def reset_budget(self) -> None:
        """Reset validation count for new run."""
        self._validation_count = 0
```

### Results Extractor

```python
@dataclass
class Opinion:
    """Extracted opinion about a topic."""
    agent_id: str
    stance: str  # positive, negative, neutral, mixed
    summary: str
    key_points: List[str]
    confidence: float

@dataclass
class Theme:
    """Recurring theme across messages."""
    name: str
    frequency: int
    representative_quotes: List[str]
    sentiment: str

@dataclass
class Quote:
    """Notable quote from simulation."""
    agent_id: str
    content: str
    relevance_score: float
    context: str

class ResultsExtractor:
    """
    Extract structured data from simulation outputs.

    Uses LLM for semantic extraction with error handling
    and schema validation.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _format_messages(self, messages: List["Message"]) -> str:
        """Format messages for LLM prompt."""
        return "\n".join(
            f"[{msg.sender}]: {msg.content[:200]}"
            for msg in messages[:50]  # Limit to prevent context overflow
        )

    async def extract_opinions(
        self,
        messages: List["Message"],
        topic: str
    ) -> Dict[str, Opinion]:
        """Extract each agent's opinion on a topic."""
        prompt = f"""
Analyze these messages and extract each speaker's opinion on "{topic}".

Messages:
{self._format_messages(messages)}

For each speaker who expressed a view, provide their opinion.

Respond with JSON:
{{
  "opinions": [
    {{
      "agent_id": "<speaker id>",
      "stance": "<positive|negative|neutral|mixed>",
      "summary": "<one sentence summary>",
      "key_points": ["<point 1>", "<point 2>"],
      "confidence": <0.0-1.0>
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            opinions = {}
            for op in result.get("opinions", []):
                opinions[op["agent_id"]] = Opinion(
                    agent_id=op["agent_id"],
                    stance=op.get("stance", "neutral"),
                    summary=op.get("summary", ""),
                    key_points=op.get("key_points", []),
                    confidence=float(op.get("confidence", 0.5))
                )
            return opinions
        except (JSONParseError, KeyError, TypeError) as e:
            # Return empty dict on extraction failure
            return {}

    async def extract_themes(
        self,
        messages: List["Message"]
    ) -> List[Theme]:
        """Identify recurring themes across all messages."""
        prompt = f"""
Identify the main recurring themes in this conversation.

Messages:
{self._format_messages(messages)}

Find themes that appear multiple times across different speakers.

Respond with JSON:
{{
  "themes": [
    {{
      "name": "<theme name>",
      "frequency": <number of mentions>,
      "representative_quotes": ["<quote 1>", "<quote 2>"],
      "sentiment": "<positive|negative|neutral|mixed>"
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            return [
                Theme(
                    name=t["name"],
                    frequency=t.get("frequency", 1),
                    representative_quotes=t.get("representative_quotes", []),
                    sentiment=t.get("sentiment", "neutral")
                )
                for t in result.get("themes", [])
            ]
        except (JSONParseError, KeyError, TypeError):
            return []

    async def extract_quotes(
        self,
        messages: List["Message"],
        criteria: str
    ) -> List[Quote]:
        """Extract notable quotes matching criteria."""
        prompt = f"""
Extract notable quotes from this conversation that match: "{criteria}"

Messages:
{self._format_messages(messages)}

Find the most relevant and impactful quotes.

Respond with JSON:
{{
  "quotes": [
    {{
      "agent_id": "<speaker>",
      "content": "<exact quote>",
      "relevance_score": <0.0-1.0>,
      "context": "<brief context>"
    }}
  ]
}}
"""
        try:
            result = await self.llm.complete_json(
                [{"role": "user", "content": prompt}]
            )
            return [
                Quote(
                    agent_id=q["agent_id"],
                    content=q["content"],
                    relevance_score=float(q.get("relevance_score", 0.5)),
                    context=q.get("context", "")
                )
                for q in result.get("quotes", [])
            ]
        except (JSONParseError, KeyError, TypeError):
            return []

    def extract_sentiment_scores(
        self,
        messages: List["Message"]
    ) -> Dict[str, float]:
        """
        Compute sentiment per agent using local heuristics.

        Uses simple keyword-based sentiment (no LLM call).
        For more accurate sentiment, use extract_opinions().
        """
        positive_words = {"good", "great", "love", "excellent", "amazing",
                         "helpful", "useful", "agree", "yes", "definitely"}
        negative_words = {"bad", "terrible", "hate", "awful", "useless",
                         "disagree", "no", "never", "problem", "issue"}

        agent_scores: Dict[str, List[float]] = {}

        for msg in messages:
            words = set(msg.content.lower().split())
            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)
            total = pos_count + neg_count

            if total > 0:
                score = (pos_count - neg_count) / total  # -1 to 1
                normalized = (score + 1) / 2  # 0 to 1
            else:
                normalized = 0.5  # Neutral

            if msg.sender not in agent_scores:
                agent_scores[msg.sender] = []
            agent_scores[msg.sender].append(normalized)

        # Average scores per agent
        return {
            agent: sum(scores) / len(scores)
            for agent, scores in agent_scores.items()
            if scores
        }
```

### A/B Testing Support

```python
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import statistics

@dataclass
class RunResult:
    """Result of a single scenario run."""
    scenario_result: "ScenarioResult"
    metrics: SimulationMetrics
    validations: List[ValidationResult]
    run_index: int

@dataclass
class VariantResults:
    """Aggregated results for a single variant."""
    variant_name: str
    runs: List[RunResult]
    avg_metrics: Dict[str, float]
    validation_pass_rate: float

@dataclass
class StatisticalComparison:
    """Statistical comparison between variants."""
    metric_name: str
    variant_a: str
    variant_b: str
    mean_a: float
    mean_b: float
    difference: float
    significant: bool  # True if difference is statistically significant
    p_value: Optional[float] = None

@dataclass
class ABTestResult:
    """Complete A/B test results."""
    variants: Dict[str, VariantResults]
    comparisons: List[StatisticalComparison]
    winner: Optional[str] = None  # Variant with best results
    recommendation: str = ""

class ExperimentRunner:
    """
    Run comparative experiments (inspired by TinyTroupe).

    IMPORTANT: Uses deep copies of config to prevent cross-variant
    contamination. Each run is fully isolated.
    """

    def __init__(
        self,
        scenario_factory: "ScenarioFactory",
        metrics_collector: MetricsCollector,
        validator: Validator
    ):
        self.scenario_factory = scenario_factory
        self.metrics_collector = metrics_collector
        self.validator = validator

    async def run_ab_test(
        self,
        base_config: "ScenarioConfig",
        variants: Dict[str, Dict[str, Any]],  # variant_name -> config changes
        runs_per_variant: int = 3
    ) -> ABTestResult:
        """
        Run scenario with different configurations.

        FIXED: Uses deep copies to prevent config mutation between variants.
        Each variant starts from a fresh copy of base_config.
        """
        variant_results: Dict[str, VariantResults] = {}

        for variant_name, config_overrides in variants.items():
            runs = []

            for run_idx in range(runs_per_variant):
                # CRITICAL: Deep copy base config for each run
                run_config = deepcopy(base_config)

                # Apply variant overrides to the copy
                self._apply_overrides(run_config, config_overrides)

                # Reset metrics and validation budget
                self.metrics_collector.reset()
                self.validator.reset_budget()

                # Create fresh scenario instance
                scenario = self.scenario_factory.create(run_config)

                # Run scenario
                scenario_result = await scenario.run()
                metrics = self.metrics_collector.get_metrics()

                # Validate sample of responses
                validations = await self._validate_responses(scenario_result)

                runs.append(RunResult(
                    scenario_result=scenario_result,
                    metrics=metrics,
                    validations=validations,
                    run_index=run_idx
                ))

            # Aggregate variant results
            variant_results[variant_name] = self._aggregate_variant(
                variant_name, runs
            )

        # Compute statistical comparisons
        comparisons = self._compute_comparisons(variant_results)

        # Determine winner
        winner, recommendation = self._determine_winner(
            variant_results, comparisons
        )

        return ABTestResult(
            variants=variant_results,
            comparisons=comparisons,
            winner=winner,
            recommendation=recommendation
        )

    def _apply_overrides(self, config: "ScenarioConfig",
                         overrides: Dict[str, Any]) -> None:
        """Apply config overrides using dot notation."""
        for key, value in overrides.items():
            parts = key.split(".")
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)

    async def _validate_responses(
        self,
        result: "ScenarioResult"
    ) -> List[ValidationResult]:
        """Validate sample of responses from scenario."""
        validations = []
        # Sample messages for validation (avoid validating everything)
        sample_size = min(10, len(result.messages))
        sampled = result.messages[:sample_size]

        for msg in sampled:
            if hasattr(msg, 'agent') and msg.agent:
                v = await self.validator.check_coherence(msg.content)
                validations.append(v)

        return validations

    def _aggregate_variant(
        self,
        variant_name: str,
        runs: List[RunResult]
    ) -> VariantResults:
        """Aggregate metrics across runs."""
        # Average key metrics
        avg_metrics = {
            "total_messages": statistics.mean(
                r.metrics.total_messages for r in runs
            ),
            "avg_response_length": statistics.mean(
                r.metrics.avg_response_length for r in runs
            ),
            "total_reflections": statistics.mean(
                r.metrics.total_reflections for r in runs
            ),
            "estimated_cost_usd": statistics.mean(
                r.metrics.estimated_cost_usd for r in runs
            ),
        }

        # Validation pass rate
        all_validations = [v for r in runs for v in r.validations]
        pass_rate = (
            sum(1 for v in all_validations if v.passed) / len(all_validations)
            if all_validations else 0.0
        )

        return VariantResults(
            variant_name=variant_name,
            runs=runs,
            avg_metrics=avg_metrics,
            validation_pass_rate=pass_rate
        )

    def _compute_comparisons(
        self,
        variants: Dict[str, VariantResults]
    ) -> List[StatisticalComparison]:
        """Compute statistical comparisons between variant pairs."""
        comparisons = []
        variant_names = list(variants.keys())

        for i, name_a in enumerate(variant_names):
            for name_b in variant_names[i + 1:]:
                var_a = variants[name_a]
                var_b = variants[name_b]

                for metric in ["total_messages", "avg_response_length",
                              "estimated_cost_usd"]:
                    mean_a = var_a.avg_metrics.get(metric, 0)
                    mean_b = var_b.avg_metrics.get(metric, 0)
                    diff = mean_b - mean_a

                    # Simple significance check (>10% difference)
                    threshold = max(abs(mean_a), abs(mean_b)) * 0.1
                    significant = abs(diff) > threshold

                    comparisons.append(StatisticalComparison(
                        metric_name=metric,
                        variant_a=name_a,
                        variant_b=name_b,
                        mean_a=mean_a,
                        mean_b=mean_b,
                        difference=diff,
                        significant=significant
                    ))

        return comparisons

    def _determine_winner(
        self,
        variants: Dict[str, VariantResults],
        comparisons: List[StatisticalComparison]
    ) -> Tuple[Optional[str], str]:
        """Determine winning variant based on results."""
        if len(variants) < 2:
            return None, "Need at least 2 variants for comparison"

        # Score variants by validation pass rate (primary metric)
        scores = {
            name: var.validation_pass_rate
            for name, var in variants.items()
        }

        winner = max(scores, key=scores.get)
        runner_up = sorted(scores, key=scores.get, reverse=True)[1]

        diff = scores[winner] - scores[runner_up]

        if diff < 0.05:
            return None, f"No clear winner. {winner} and {runner_up} are similar."

        return winner, (
            f"{winner} outperforms {runner_up} with "
            f"{scores[winner]:.1%} vs {scores[runner_up]:.1%} validation pass rate."
        )
```

### Evaluation Model Configuration

```python
@dataclass
class EvaluationConfig:
    """Configuration for the evaluation system."""

    # Model selection
    use_separate_evaluation_model: bool = True
    evaluation_model: str = "gpt-4o-mini"  # Cheaper, reduces bias

    # Budget controls
    max_validation_calls: int = 100
    max_extraction_calls: int = 50
    validation_sampling_rate: float = 0.3  # Sample 30% of responses

    # Thresholds
    persona_adherence_threshold: float = 0.7
    consistency_threshold: float = 0.6
    coherence_threshold: float = 0.5

    # A/B testing
    default_runs_per_variant: int = 3
    significance_threshold: float = 0.1  # 10% difference for significance
```

## Consequences

**Positive:**
- Quantitative evaluation of simulation quality
- A/B testing capability for systematic experiments
- Research-grade metrics collection
- Structured extraction for downstream analysis
- Cost tracking prevents budget overruns
- Separate observation/reflection counters for accurate memory metrics
- Isolated A/B test runs prevent contamination
- Safe handling of disconnected network topologies

**Negative:**
- LLM-based validation adds cost (~3 calls per validation)
- Metric interpretation requires domain knowledge
- Statistical significance needs multiple runs

**Questions Addressed:**
- **Separate evaluation model**: Yes, configurable via `use_separate_evaluation_model`
- **Budget control**: Sampling rate and max calls limit validation cost

**Integration Points:**
- Uses **[ADR-003](./ADR-003-llm-architecture.md)** LLM provider for validation and extraction
- Tracks **[ADR-006](./ADR-006-dual-memory.md)** memory system health (observations AND reflections)
- Computes **[ADR-005](./ADR-005-network-topology.md)** network metrics (safe for disconnected)
- Evaluates **[ADR-009](./ADR-009-use-case-scenarios.md)** scenario outputs

## Related ADRs
- [ADR-003](./ADR-003-llm-architecture.md): LLM for validation and extraction
- [ADR-005](./ADR-005-network-topology.md): Network metrics computation
- [ADR-006](./ADR-006-dual-memory.md): Memory system metrics
- [ADR-009](./ADR-009-use-case-scenarios.md): Scenario output evaluation
