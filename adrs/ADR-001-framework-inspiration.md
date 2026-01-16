# ADR-001: Framework Inspiration and Feature Selection

## Status
Accepted

## Dependencies
None (Foundation ADR)

## Context

The multi-agent LLM simulation landscape has matured significantly since Stanford's Generative Agents paper (2023). We surveyed the leading frameworks to identify best-of-breed features for AgentWorld.

> **Survey Date**: January 2025. Framework capabilities and versions are time-sensitive; this analysis should be re-validated before major architectural changes.

### Frameworks Analyzed

| Framework | Organization | Primary Strength | Scale | License |
|-----------|--------------|------------------|-------|---------|
| **TinyTroupe** | Microsoft Research | Persona depth, business insights | ~100 agents | MIT |
| **Generative Agents** | Stanford | Emergent behavior, memory architecture | ~25 agents | Apache 2.0 |
| **AgentSociety** | Tsinghua FIB-Lab | Large-scale social simulation | 10K+ agents | - |
| **AgentVerse** | OpenBMB | Versatile environments, ICLR 2024 | Variable | Apache 2.0 |
| **CAMEL** | CAMEL-AI | LLM flexibility, data generation, NeurIPS 2023 | 1M+ (OASIS) | Apache 2.0 |
| **CrewAI** | CrewAI Inc | Production-ready, workflow automation | Variable | MIT |
| **AutoGen** | Microsoft | Multi-agent conversations, tool use | Variable | MIT |
| **AI Town** | a16z | Visual sandbox, JS/TS stack | ~25 agents | MIT |
| **Mesa** | Mesa Project | Traditional ABM, NetworkX native | 10K+ | Apache 2.0 |

### Framework Deep Dive

**TinyTroupe (Microsoft Research)**
- Implements most sophisticated persona specification with Big Five personality traits
- JSON-based agent configurations with structured fields
- `TinyPersonFactory` for LLM-powered agent generation
- Dual memory: episodic + semantic with vector embeddings
- Mental faculties for extensible agent capabilities
- Evaluation via Propositions (persona adherence, self-consistency)
- `ResultsExtractor` and `ResultsReducer` for analysis
- `InPlaceExperimentRunner` for A/B testing
- **Limitation**: OpenAI/Azure only, no native topology support

**Generative Agents (Stanford)**
- Pioneered memory-reflection-planning architecture
- Memory stream stores all experiences in natural language
- Retrieval combines recency decay, importance weighting, semantic relevance
- Reflection synthesizes observations into higher-level abstractions
- Planning uses top-down decomposition from daily schedules to actions
- 25-agent Smallville produced emergent behaviors (Valentine's Day party)
- **Limitation**: OpenAI-locked, high cost, complex setup

**CAMEL (CAMEL-AI)**
- First multi-agent framework (NeurIPS 2023)
- ModelFactory supports 100+ models across providers
- Role-playing framework with "inception prompting"
- Workforce module for hierarchical multi-agent architectures
- OASIS platform: up to 1 million simultaneous agents
- AgentOps integration for observability
- **Limitation**: Role-playing optimized for dyadic interaction

**AgentSociety (Tsinghua)**
- Large-scale social simulation (10K+ agents, 5M+ interactions)
- Cognitive realism with Maslow's hierarchy integration
- Message layer supports P2P, broadcast, group topologies
- Observation and intervention tools (surveys, interviews)
- Validated replication of real-world social phenomena
- **Limitation**: Complex setup, research-focused

**CrewAI**
- Production-ready with clean API
- YAML configuration for agents and tasks
- Persistent memory across runs
- Tool registry with clear interfaces
- Sequential vs hierarchical execution modes
- **Limitation**: Task-focused, not simulation-focused

**AI Town (a16z)**
- JavaScript/TypeScript stack
- Visual 2D sandbox with game-like interface
- Shared global state with transactional updates
- Time-step based simulation
- Multi-player connections (humans can join)
- **Limitation**: JS ecosystem, demo-focused

**Mesa (Traditional ABM)**
- Mature Python framework for agent-based modeling (10+ years)
- Native NetworkX integration via `NetworkGrid` class
- Supports grid-based and network-based agent placement
- **Limitation**: Not LLM-native; requires custom integration for LLM agents

### Key Findings

1. **No LLM-native framework provides explicit topology configuration** (small-world, scale-free, hub-spoke as first-class concepts). Mesa provides NetworkX integration for traditional ABM, but lacks LLM agent abstractions. This gap drives our custom topology layer.

2. **TinyTroupe leads in persona depth** with Big Five traits, structured JSON configs, and cognitive architecture

3. **CAMEL offers superior LLM flexibility** with 100+ model support via ModelFactory pattern

4. **Generative Agents pioneered** the memory-reflection-planning architecture now adopted by most frameworks

5. **AgentSociety demonstrates scale** with 10K+ agents and validated social phenomena replication

### Feature Evaluation Matrix

| Feature | Weight | TinyTroupe | Gen. Agents | CAMEL | Mesa | CrewAI |
|---------|--------|------------|-------------|-------|------|--------|
| Persona depth | 25% | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | ★☆☆☆☆ | ★★★☆☆ |
| Memory system | 20% | ★★★★☆ | ★★★★★ | ★★☆☆☆ | ★☆☆☆☆ | ★★★☆☆ |
| LLM flexibility | 20% | ★★☆☆☆ | ★☆☆☆☆ | ★★★★★ | N/A | ★★★☆☆ |
| Topology support | 15% | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★★★☆ | ★☆☆☆☆ |
| Evaluation tools | 10% | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ | ★★☆☆☆ |
| Config system | 10% | ★★★☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ |

## Decision

Create AgentWorld by synthesizing the best features from each framework:

| Feature | Source Framework | What We Adopt | Rationale |
|---------|-----------------|---------------|-----------|
| Persona specification | TinyTroupe | Big Five model, structured JSON schema | Most sophisticated personality framework |
| Memory architecture | Generative Agents | Dual memory + retrieval function design | Proven emergent behavior |
| LLM abstraction | CAMEL | Multi-provider pattern (via LiteLLM) | 100+ model support critical |
| Topology system | Mesa + Custom | NetworkX integration pattern | Mesa shows how; we add LLM-native API |
| Configuration system | CrewAI | YAML-based declarative approach | Clean separation of config from code |
| CLI interface | AgentVerse | CLI-first workflow, progress display | Research iteration patterns |
| Evaluation tools | TinyTroupe | Propositions, extractors, A/B testing | Rigorous validation approach |
| Scenario patterns | TinyTroupe + CAMEL | Focus groups, data generation | Covers both primary use cases |

### Adoption Policy

**We adopt design ideas and patterns only, not source code.** All implementation is original to AgentWorld. This avoids license complexity while benefiting from proven designs. If code is ever directly incorporated, it must:
1. Be compatible with our Apache 2.0 license
2. Include proper attribution
3. Be documented in this ADR

### Minimal Core Interface

To manage integration complexity across borrowed patterns, we define a minimal interface contract:

```python
# All components must implement these boundaries
class Agent(Protocol):
    id: str
    traits: TraitVector
    memory: MemorySystem
    async def act(self, context: Context) -> Action

class MemorySystem(Protocol):
    async def add(self, observation: Observation) -> None
    async def retrieve(self, query: str, k: int) -> List[Memory]

class Topology(Protocol):
    def get_neighbors(self, agent_id: str) -> List[str]
    def can_communicate(self, sender: str, receiver: str) -> bool
```

## Consequences

**Positive:**
- Combines proven patterns from production frameworks
- Addresses topology gap that all LLM frameworks share
- Multi-provider LLM support enables comparative research
- Best-of-breed features reduce design risk
- Clear adoption policy avoids license issues

**Negative:**
- Higher initial complexity vs single-framework approach
- Must maintain compatibility with evolving upstream patterns
- No single community to draw from

**Risks:**
- Framework APIs may change (TinyTroupe still "experimental")
- Integration complexity between patterns from different sources
- Survey data may become stale; recommend annual re-evaluation

## References

- Park et al. "Generative Agents: Interactive Simulacra of Human Behavior" (UIST 2023)
- Li et al. "CAMEL: Communicative Agents for Mind Exploration" (NeurIPS 2023)
- TinyTroupe GitHub: https://github.com/microsoft/TinyTroupe
- Mesa Documentation: https://mesa.readthedocs.io/

## Related ADRs
- [ADR-002](./ADR-002-agent-scale.md): Scale decision informed by framework analysis
- [ADR-003](./ADR-003-llm-architecture.md): LLM abstraction from CAMEL's ModelFactory
- [ADR-004](./ADR-004-trait-vector-persona.md): Persona system from TinyTroupe
- [ADR-005](./ADR-005-network-topology.md): Topology gap identified here
- [ADR-006](./ADR-006-dual-memory.md): Memory architecture from Generative Agents
- [ADR-007](./ADR-007-visualization.md): Visualization approaches surveyed
