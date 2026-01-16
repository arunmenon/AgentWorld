# ADR-003: Multi-Provider LLM Architecture

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: CAMEL's ModelFactory pattern identified as best-of-breed

## Context

LLM provider flexibility is critical for:

1. **Cost optimization**: Switch between providers based on budget
2. **Capability matching**: Use appropriate models for different agent tasks
3. **Research**: Compare agent behavior across different LLMs (GPT-4 vs Claude vs Llama)
4. **Resilience**: Fallback when primary provider unavailable
5. **Privacy**: Support local models (Ollama) for sensitive data

**Provider Landscape:**

> **Note**: Pricing is approximate and time-sensitive. See provider documentation for current rates.

| Provider | Example Models | Strengths |
|----------|--------|-----------|
| OpenAI | GPT-4o, GPT-4-turbo | Best reasoning, largest ecosystem |
| Anthropic | Claude 3.5 Sonnet/Opus | Safety, long context (200K) |
| Google | Gemini Pro/Ultra | Multimodal, competitive pricing |
| Ollama | Llama 3, Mistral, Qwen | Local, private, free |
| Together AI | Various open models | Cost-effective, fast |

**Existing Abstraction Solutions:**

| Solution | Providers | Complexity | Maintenance |
|----------|-----------|------------|-------------|
| **LiteLLM** | 100+ | Low (drop-in) | Very active |
| LangChain | 50+ | High | Active |
| CAMEL ModelFactory | 100+ | Medium | Active |
| Direct SDKs | 1 each | Low | N/A |

## Decision

Use **LiteLLM** as the LLM abstraction layer with a thin AgentWorld wrapper.

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│              AgentWorld LLMProvider                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │  Response   │ │    Retry     │ │  Token Tracking  │  │
│  │   Cache     │ │    Logic     │ │  & Call Logging  │  │
│  └─────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐│
│  │         Safe Prompt Templates (Jinja2)              ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │       LiteLLM       │
              └──────────┬──────────┘
                         │
    ┌────────┬───────────┼───────────┬────────┐
    ▼        ▼           ▼           ▼        ▼
 OpenAI  Anthropic    Ollama     Google   100+ others
```

### Provider Capability Matrix

| Capability | Required | OpenAI | Anthropic | Ollama | Together |
|------------|----------|--------|-----------|--------|----------|
| Chat completion | Yes | ✅ | ✅ | ✅ | ✅ |
| Streaming | No | ✅ | ✅ | ✅ | ✅ |
| JSON mode | Yes | ✅ | ✅ | ⚠️ | ⚠️ |
| Tool calling | No | ✅ | ✅ | ⚠️ | ⚠️ |
| Temperature control | Yes | ✅ | ✅ | ✅ | ✅ |
| Seed parameter | Preferred | ✅ | ❌ | ⚠️ | ⚠️ |

**Minimum Required Features:**
- Chat completion with message history
- Temperature control (for reproducibility)
- Reasonable context window (8K+ tokens)

### Reproducibility and Auditability

To support research reproducibility (per **[ADR-002](./ADR-002-agent-scale.md)**), every LLM call is logged:

```python
@dataclass
class LLMCallRecord:
    """Audit record for every LLM call."""
    id: str
    timestamp: datetime

    # Request
    provider: str          # "openai", "anthropic", etc.
    model: str             # Exact model including version
    messages: List[dict]   # Full message history
    temperature: float
    seed: Optional[int]
    other_params: dict

    # Response
    response_content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int

    # Context
    agent_id: Optional[str]
    simulation_id: str
    step: int
```

**Strict Mode (for reproducibility):**
- Fallback disabled
- Single provider per run
- All calls logged with full context
- Cache keys include all parameters

### Response Caching

**Cache Key Specification:**
```python
def compute_cache_key(
    model: str,
    messages: List[dict],
    temperature: float,
    seed: Optional[int],
    **kwargs
) -> str:
    """
    Deterministic cache key for response deduplication.

    Key components:
    - model: Exact model string (e.g., "openai/gpt-4o-2024-08-06")
    - messages: SHA256 of JSON-serialized messages
    - temperature: Included in key
    - seed: Included if provided
    - prompt_version: Schema version for cache invalidation
    """
    content = {
        "model": model,
        "messages_hash": hashlib.sha256(
            json.dumps(messages, sort_keys=True).encode()
        ).hexdigest(),
        "temperature": temperature,
        "seed": seed,
        "prompt_version": PROMPT_SCHEMA_VERSION,  # Bump on prompt changes
    }
    return hashlib.sha256(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()
```

**Cache Behavior:**
- TTL: Configurable (default 24 hours, infinite for seed=fixed)
- Storage: SQLite (same DB as persistence, see **[ADR-008](./ADR-008-persistence.md)**)
- Invalidation: Automatic on `PROMPT_SCHEMA_VERSION` bump

### Prompt Safety

Jinja2 templates must prevent injection from untrusted agent content:

```python
from jinja2 import Environment, select_autoescape, sandbox

# Safe template environment
template_env = Environment(
    autoescape=select_autoescape(['html', 'xml']),
    sandbox=sandbox.SandboxedEnvironment(),
)

# Template example with escaped agent content
AGENT_ACTION_TEMPLATE = """
You are {{ agent.name }}, a {{ agent.occupation }}.

Your personality: {{ agent.traits.to_prompt_context() | e }}

Recent observations:
{% for obs in observations %}
- {{ obs.content | e }}
{% endfor %}

Respond in character to: {{ stimulus | e }}
"""

# Usage
prompt = template_env.from_string(AGENT_ACTION_TEMPLATE).render(
    agent=agent,
    observations=observations,
    stimulus=user_input  # Escaped via | e filter
)
```

**Safety Rules:**
1. All user/agent content passed through `| e` (escape) filter
2. No `{% raw %}` blocks with untrusted content
3. Template strings never constructed from user input
4. SandboxedEnvironment prevents dangerous operations

### Wrapper API

```python
class LLMProvider:
    """AgentWorld's LLM abstraction layer."""

    async def complete(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with caching, logging, and retry.

        Args:
            messages: OpenAI-format message list
            model: Override default model
            temperature: Override default temperature
            seed: For reproducibility (provider support varies)
            agent_id: For attribution in logs

        Returns:
            LLMResponse with content, usage, and metadata
        """
        ...

    async def complete_json(
        self,
        messages: List[dict],
        schema: Type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """
        Generate structured JSON output with validation.
        Uses JSON mode where available, falls back to parsing.
        """
        ...
```

## Consequences

**Positive:**
- Single interface for all providers
- Easy provider switching via YAML config
- Active maintenance (daily releases)
- Built-in retry, fallback, load balancing
- Async support out-of-box
- Full auditability for research
- Safe prompt templating prevents injection

**Negative:**
- Additional dependency (~2MB)
- Slight abstraction overhead (<10ms)
- May lag behind provider feature releases by days
- Strict mode limits resilience

**Mitigation:**
- Thin wrapper allows direct provider access if needed
- Pin LiteLLM version for stability
- Cache responses to minimize overhead impact
- Relaxed mode available for non-research use

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): CAMEL's ModelFactory pattern inspiration
- [ADR-002](./ADR-002-agent-scale.md): Reproducibility requirements
- [ADR-006](./ADR-006-dual-memory.md): Uses LLM for importance rating and reflection
- [ADR-008](./ADR-008-persistence.md): Cache storage
- [ADR-010](./ADR-010-evaluation-metrics.md): Uses LLM for validation and extraction
