# ADR-016: Agent Injection for External Agent Testing

## Status
Proposed

## Dependencies
- **[ADR-011](./ADR-011-simulation-runtime.md)**: Simulation Runtime & Scheduling (turn semantics, determinism)
- **[ADR-012](./ADR-012-api-event-schema.md)**: API & WS Event Schemas (canonical payloads, versioning)
- **[ADR-013](./ADR-013-security.md)**: Security & Secrets (key storage, allowlists, audit)
- **[ADR-015](./ADR-015-reasoning-visibility.md)**: Prompt/Reasoning Visibility (what is stored/shown)
- **[ADR-014](./ADR-014-plugin-extension.md)**: Plugin Extension (LLMProvider pattern)

## Context

AgentWorld simulations create rich social environments with diverse personas.
Users need to test their own AI agents against these simulated personas to:
- Benchmark agent performance across personality types
- Validate conversation quality before production deployment
- A/B test different agent implementations
- Discover edge cases in agent behavior

**Key Use Cases:**

| Use Case | Description |
|----------|-------------|
| **Benchmarking** | Compare different agent implementations (GPT-4 vs Claude vs custom) |
| **Regression Testing** | Ensure agent updates don't degrade social interaction quality |
| **A/B Testing** | Test prompt variations against consistent persona panel |
| **Edge Case Discovery** | Expose agents to diverse personality types and conversation styles |

**Why This Needs a New ADR:**

Existing ADR-014 (Plugin Extension) provides `LLMProvider` plugins for adding new LLM backends, but does not address:
- Runtime replacement of individual agents with external HTTP endpoints during simulation
- Privacy-tiered context schemas for external systems
- Deterministic failure handling for reproducible benchmarks
- Record/replay patterns for benchmark fixtures

## Decision

Implement HTTP endpoint injection with privacy-tiered schemas, explicit versioning for reproducibility, and record/replay benchmark mode.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Injection Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  Simulation  │     │   External   │     │   Simulated  │    │
│  │   Runner     │     │   Agent      │     │   Agents     │    │
│  └──────┬───────┘     │   Provider   │     └──────────────┘    │
│         │             └──────┬───────┘                          │
│         │                    │                                   │
│         ▼                    │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Agent Router                           │   │
│  │                                                           │   │
│  │   if agent_id in injected_agents:                        │   │
│  │       return ExternalAgentProvider.generate(context)      │   │
│  │   else:                                                   │   │
│  │       return SimulatedAgent.think(context)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Circuit Breaker                            │   │
│  │                                                           │   │
│  │   failure_threshold: 5 → OPEN                            │   │
│  │   half_open_probe: 30s                                   │   │
│  │   success_threshold: 2 → CLOSED                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Request Schema (POST to External Endpoint)

```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "run_id": "uuid",
  "turn_id": "uuid",
  "message_id": "uuid",

  "simulation_config_hash": "sha256:...",
  "persona_hash": "sha256:...",

  "agent_id": "string",
  "persona_ref": {
    "persona_id": "string",
    "persona_version": "string",
    "persona_hash": "sha256:..."
  },
  "persona_snapshot": {
    "name": "string",
    "background": "string",
    "traits": { "openness": 0.8, "conscientiousness": 0.7 }
  },

  "conversation_context": {
    "last_k_turns": [
      { "sender": "string", "content": "string", "timestamp": "ISO8601" }
    ],
    "conversation_summary": "string",
    "token_budget": 4000,
    "max_context_chars": 16000
  },
  "current_stimulus": "string",

  "topology_edge_context": {
    "can_message": ["agent_id_1", "agent_id_2"]
  },

  "timeout_ms": 30000,
  "response_format": {
    "type": "text"
  }
}
```

### Privacy Tiers

Context sent to external endpoints is controlled by privacy tier configuration:

| Tier | What's Sent | Use Case |
|------|-------------|----------|
| `minimal` | persona_ref only (ID + hash) | External systems with own persona storage |
| `basic` | + name, traits (no background) | Testing trait-based responses |
| `full` | + background, system prompt | Full context for accurate testing |

Configuration in injection setup:
```yaml
injection:
  privacy_tier: "basic"
  send_persona_details_externally: true
  redact_pii_patterns: true
```

### Response Schema

```json
{
  "response_text": "string",

  "explanation": "string",
  "debug": {
    "model": "gpt-4",
    "temperature": 0.7,
    "tool_calls_count": 0
  },
  "confidence": 0.85,
  "latency_ms": 1234,

  "error": {
    "code": "TIMEOUT | RATE_LIMITED | INTERNAL | INVALID_REQUEST",
    "message": "string"
  }
}
```

**Security Note:** Response schema intentionally excludes chain-of-thought/reasoning fields. Internal reasoning is a security liability if stored or transmitted. Use `explanation` for short, user-facing rationale and `debug` for structured metadata.

### Failure Semantics

| Failure Type | Default Behavior | Alternative |
|--------------|------------------|-------------|
| Timeout | `fallback_to_simulated_agent=true` | `emit_error_message` into transcript |
| 429 Rate Limited | Exponential backoff (1s, 2s, 4s) + max 3 retries | Fail closed after retries |
| Connection Error | Circuit breaker evaluation | Emit error message |
| Invalid Response | Log + fallback to simulated | Emit parse error message |

### Circuit Breaker Configuration

```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5  # Consecutive failures to open
    half_open_probe_interval_seconds: int = 30
    success_threshold: int = 2  # Successes to close from half-open

    max_inflight_requests_per_endpoint: int = 10
    per_endpoint_qps_cap: int = 100
```

State transitions:
```
CLOSED --[5 failures]--> OPEN --[30s]--> HALF_OPEN --[2 successes]--> CLOSED
                                              |
                                         [1 failure]
                                              |
                                              v
                                            OPEN
```

### Benchmark Mode (Record/Replay)

Instead of requiring perfect simulation determinism, record exact inputs at the injection boundary:

**Recording Phase:**
1. Run baseline simulation with Agent A
2. Serialize request payloads: `(run_id, turn_id, agent_id) → serialized_request`
3. Store as "benchmark fixture"

**Replay Phase:**
1. Load benchmark fixtures
2. Send identical requests to Agent B endpoint
3. Compare outputs at identical decision points

**Storage:**
```json
{
  "fixture_version": "1.0",
  "created_at": "ISO8601",
  "baseline_agent": { "endpoint": "...", "model": "gpt-4" },
  "payloads": [
    {
      "turn_id": "uuid",
      "agent_id": "lisa",
      "request": { /* full request object */ },
      "baseline_response": { /* optional: store baseline for comparison */ }
    }
  ]
}
```

### External Agent Metrics

```python
@dataclass
class ExternalAgentMetrics:
    # Response Quality (evaluated via ADR-010)
    persona_consistency: float
    conversation_coherence: float
    instruction_following: float

    # Operational
    latency_p50_ms: int
    latency_p99_ms: int
    error_rate: float
    timeout_rate: float
    circuit_state: str  # "CLOSED" | "OPEN" | "HALF_OPEN"

    # Comparative (A/B)
    preference_score: float
    elo_rating: float
```

### API Endpoints

```python
# Register external agent
POST /simulations/{id}/inject-agent
{
    "agent_id": "lisa",
    "endpoint_url": "https://my-agent.example.com/respond",
    "api_key": "...",
    "timeout_seconds": 30,
    "privacy_tier": "basic",
    "fallback_to_simulated": true
}

# Remove injection
DELETE /simulations/{id}/inject-agent/{agent_id}

# List injected agents
GET /simulations/{id}/injected-agents

# Get injection metrics
GET /simulations/{id}/inject-agent/{agent_id}/metrics

# Health check for endpoint
POST /simulations/{id}/inject-agent/{agent_id}/health-check
```

### Runner Integration

```python
class SimulationRunner:
    def __init__(self):
        self.injected_agents: Dict[str, ExternalAgentProvider] = {}

    async def get_agent_response(
        self,
        agent: Agent,
        stimulus: str,
        context: ConversationContext
    ) -> str:
        if agent.id in self.injected_agents:
            provider = self.injected_agents[agent.id]
            return await provider.generate_response(
                agent_id=agent.id,
                persona=agent.persona,
                context=context,
                stimulus=stimulus
            )
        else:
            return await agent.think(stimulus, context)
```

### Configuration Schema

```yaml
simulation:
  name: "Agent Benchmark"

  agent_injection:
    endpoints:
      - agent_id: "lisa"
        url: "https://my-agent.example.com/respond"
        api_key_env: "MY_AGENT_API_KEY"
        timeout_seconds: 30
        privacy_tier: "basic"

    circuit_breaker:
      failure_threshold: 5
      half_open_probe_interval_seconds: 30
      success_threshold: 2

    concurrency:
      max_inflight_per_endpoint: 10
      qps_cap: 100

    fallback:
      strategy: "simulated_agent"  # or "error_message" or "skip"

    benchmark:
      record: true
      fixture_path: "./benchmarks/run-{timestamp}.json"
```

## Consequences

**Positive:**
- Privacy-tiered schemas minimize data exposure to external systems
- Record/replay enables robust A/B testing without requiring full determinism
- Circuit breaker + concurrency limits improve reliability and prevent cascade failures
- Versioned schemas (schema_version, config_hash, persona_hash) enable reproducible benchmarks
- Clear failure semantics ensure deterministic behavior for regression testing

**Negative:**
- Benchmark fixtures require storage management
- Tiered persona access adds configuration complexity
- Circuit breaker state adds runtime complexity
- External endpoint latency may slow simulation

**Tradeoffs:**
- Privacy vs testing fidelity (tiered approach)
- Reliability vs simplicity (circuit breaker)
- Flexibility vs determinism (record/replay pattern)

## Related ADRs
- [ADR-011](./ADR-011-simulation-runtime.md): Turn semantics used in request schema
- [ADR-012](./ADR-012-api-event-schema.md): Event patterns for injection status
- [ADR-013](./ADR-013-security.md): API key management for external endpoints
- [ADR-014](./ADR-014-plugin-extension.md): LLMProvider as related pattern
- [ADR-015](./ADR-015-reasoning-visibility.md): Why reasoning is excluded from response schema
