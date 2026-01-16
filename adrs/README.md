# AgentWorld - Architecture Decision Records

## ADR Index

| ADR | Title | Status | Dependencies |
|-----|-------|--------|--------------|
| [ADR-001](./ADR-001-framework-inspiration.md) | Framework Inspiration & Feature Selection | Accepted | None (Foundation) |
| [ADR-002](./ADR-002-agent-scale.md) | Agent Scale & Quality Tradeoff | Accepted | ADR-001 |
| [ADR-003](./ADR-003-llm-architecture.md) | Multi-Provider LLM Architecture | Accepted | ADR-001 |
| [ADR-004](./ADR-004-trait-vector-persona.md) | Trait Vector Persona System | Accepted | ADR-001 |
| [ADR-005](./ADR-005-network-topology.md) | Network Topology Architecture | Accepted | ADR-001 |
| [ADR-006](./ADR-006-dual-memory.md) | Dual Memory Architecture | Accepted | ADR-001, ADR-003 |
| [ADR-007](./ADR-007-visualization.md) | Visualization Strategy | Accepted | ADR-001 |
| [ADR-008](./ADR-008-persistence.md) | Persistence & State Management | Accepted | ADR-006 |
| [ADR-009](./ADR-009-use-case-scenarios.md) | Use Case Scenarios | Accepted | ADR-004, ADR-005, ADR-006 |
| [ADR-010](./ADR-010-evaluation-metrics.md) | Evaluation & Metrics System | Accepted | ADR-003, ADR-006, ADR-009 |

## Dependency Graph

```
ADR-001 (Foundation)
    │
    ├──► ADR-002 (Scale)
    │
    ├──► ADR-003 (LLM) ──────────────────┐
    │         │                          │
    │         ▼                          ▼
    ├──► ADR-006 (Memory) ◄───────  ADR-010 (Evaluation)
    │         │                          ▲
    │         ▼                          │
    │    ADR-008 (Persistence)           │
    │                                    │
    ├──► ADR-004 (Personas) ──┐          │
    │                         ▼          │
    ├──► ADR-005 (Topology) ──► ADR-009 (Scenarios)
    │
    └──► ADR-007 (Visualization)
```

## Requirements Traceability

### Functional Requirements

| ID | Requirement | Priority | ADR Source |
|----|-------------|----------|------------|
| FR-01 | Support 10-50 agents with deep personas | High | ADR-002 |
| FR-02 | Trait vectors with 0-1 continuous values | High | ADR-004 |
| FR-03 | Big Five personality model + custom traits | High | ADR-004 |
| FR-04 | Multi-provider LLM support (OpenAI, Anthropic, Ollama) | High | ADR-003 |
| FR-05 | All network topologies (mesh, hub-spoke, hierarchical, small-world, scale-free) | High | ADR-005 |
| FR-06 | Dual memory system (episodic + semantic) | High | ADR-006 |
| FR-07 | Memory retrieval (recency, importance, relevance) | High | ADR-006 |
| FR-08 | Reflection generation mechanism | Medium | ADR-006 |
| FR-09 | Product testing scenario (focus groups, interviews) | High | ADR-009 |
| FR-10 | Data generation scenario (conversations, Q&A) | High | ADR-009 |
| FR-11 | SQLite persistence with pause/resume | High | ADR-008 |
| FR-12 | Rich CLI visualization | High | ADR-007 |
| FR-13 | Web dashboard with real-time updates | Medium | ADR-007 |
| FR-14 | YAML-based configuration | Medium | ADR-001 |
| FR-15 | Evaluation metrics and validators | Medium | ADR-010 |
| FR-16 | Export to JSON/CSV/HuggingFace format | Medium | ADR-009 |

### Non-Functional Requirements

| ID | Requirement | Target | ADR Source |
|----|-------------|--------|------------|
| NFR-01 | Simulation startup time | < 5 seconds for 10 agents | ADR-002 |
| NFR-02 | Step execution time | < 30 seconds per step (parallel) | ADR-002 |
| NFR-03 | Memory usage | < 1GB for 50 agents | ADR-002, ADR-006 |
| NFR-04 | LLM response caching | Reduce duplicate calls by 50%+ | ADR-003 |
| NFR-05 | Test coverage | > 80% for core modules | - |
