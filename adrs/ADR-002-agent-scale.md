# ADR-002: Agent Scale and Quality Tradeoff

## Status
Accepted

## Dependencies
- **[ADR-001](./ADR-001-framework-inspiration.md)**: Framework analysis informs scale decision

## Context

Agent simulation frameworks face a fundamental tradeoff between agent count and cognitive depth. Analysis from **ADR-001** shows frameworks cluster into scale tiers:

| Scale Tier | Agent Count | Characteristics | Example Frameworks |
|------------|-------------|-----------------|-------------------|
| Small | 10-50 | Deep personas, rich memory, detailed interactions | TinyTroupe, Generative Agents |
| Medium | 50-500 | Balanced depth/scale, role-based personas | AgentVerse, CrewAI |
| Large | 500-10K+ | Simple behaviors, statistical emergence | AgentSociety, Mesa |
| Massive | 10K-1M+ | Minimal per-agent cognition, macro patterns | CAMEL OASIS |

**User Requirements:**
- Primary use cases: Product testing, Data generation
- Need detailed persona interactions for feedback quality
- Research applications require reproducible agent behavior

### Cost Model

**Base Cost Assumptions (GPT-4o, January 2025):**
- Input: ~$0.0025 per 1K tokens
- Output: ~$0.01 per 1K tokens
- Blended: ~$0.005 per 1K tokens

**Comprehensive Cost per Simulation (10 agents, 20 steps):**

| Component | Tokens | Calls | Cost |
|-----------|--------|-------|------|
| Agent actions | 400K | 200 | $2.00 |
| Importance rating (ADR-006) | 40K | 200 | $0.20 |
| Reflection generation | 30K | ~6 | $0.15 |
| Evaluation/validation (ADR-010) | 20K | ~10 | $0.10 |
| **Total** | **490K** | **~416** | **~$2.50** |

**Scale Impact:**
- 10 agents: ~$2.50/simulation
- 50 agents: ~$12.50/simulation (linear with optimizations)
- 1000 agents: ~$250/simulation (prohibitive without lite mode)

### Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Simulation startup | < 5 seconds (10 agents) | Interactive iteration |
| Step execution | < 30 seconds (parallel) | Reasonable wait time |
| Tokens per agent per step | < 2K average | Cost control |
| Memory per agent | < 20MB | 50 agents in < 1GB |
| Wall-clock per run | < 15 minutes (20 steps) | Research iteration cycle |

## Decision

Target **Small scale (10-50 agents)** with focus on persona depth and interaction quality.

**Rationale:**
1. Product testing requires realistic, nuanced feedback - shallow agents produce generic responses
2. Data generation quality correlates with agent cognitive depth
3. 10-50 agents sufficient for focus groups, user studies, conversation datasets
4. Cost-effective iteration cycle (~$2.50-12.50 per simulation)
5. Can always reduce persona complexity to scale up, harder to add depth later

### Reproducibility Strategy

To meet the reproducibility requirement, all simulations must support deterministic replay:

| Control | Implementation | Default |
|---------|----------------|---------|
| **LLM Temperature** | Configurable per simulation | 0.0 (deterministic) |
| **Random Seed** | Global seed for all random operations | Required in config |
| **Model Pinning** | Exact model version in config | e.g., `gpt-4o-2024-08-06` |
| **Response Caching** | Cache key includes full prompt + params | Enabled |
| **Provider Locking** | Single provider per simulation run | No fallback in strict mode |

```yaml
# Example reproducibility config
simulation:
  seed: 42
  reproducibility: strict  # strict | relaxed

llm:
  model: "openai/gpt-4o-2024-08-06"  # Pinned version
  temperature: 0.0
  fallback_enabled: false  # Disable in strict mode
```

### Lite Agent Mode

For scenarios requiring more agents or lower cost, we define a "lite" mode:

| Feature | Full Mode | Lite Mode |
|---------|-----------|-----------|
| Memory system | Dual (episodic + semantic) | Simple list (last N) |
| Reflection | Enabled | Disabled |
| Importance rating | LLM-based | Heuristic (length + keywords) |
| Trait complexity | Full Big Five + custom | Simplified 3-trait |
| Embedding storage | Per observation | None |
| Target scale | 10-50 agents | 50-200 agents |
| Cost multiplier | 1.0x | ~0.3x |

```python
# Lite mode configuration
agent_config:
  mode: lite  # full | lite
  memory_window: 20  # Last N observations only
  reflection_enabled: false
  importance_heuristic: true
```

### Data Generation Throughput

For data generation use cases requiring large sample sizes:

1. **Parallel Runs**: Multiple simulation instances with different seeds
2. **Batch Processing**: Run N simulations overnight with varied parameters
3. **Model Tiering**: Use cheaper models (GPT-4o-mini, Claude Haiku) for bulk generation
4. **Result Aggregation**: Combine outputs across runs for statistical validity

```python
# High-throughput data generation
data_generation:
  target_samples: 10000
  strategy: parallel_runs
  runs_per_batch: 100
  model_tier: budget  # premium | standard | budget
  agents_per_run: 10
```

## Consequences

**Positive:**
- Rich memory systems enable context-aware responses
- Trait vectors allow precise behavioral control
- Suitable for rigorous A/B testing and evaluation
- Affordable development iteration
- Reproducibility enables scientific validity
- Lite mode provides scaling escape hatch

**Negative:**
- Won't support massive social simulations out-of-box
- Higher per-agent compute cost (more LLM calls)
- Limited to scenarios where individual behavior matters
- Strict reproducibility requires temperature=0, limiting creativity

**Mitigation:**
- Lite agent mode for cost-sensitive scenarios
- Parallel runs for data generation volume
- Model tiering for budget flexibility
- Document scale limitations clearly

## Related ADRs
- [ADR-001](./ADR-001-framework-inspiration.md): Framework analysis source
- [ADR-003](./ADR-003-llm-architecture.md): LLM caching and model pinning
- [ADR-006](./ADR-006-dual-memory.md): Memory system sized for this scale
