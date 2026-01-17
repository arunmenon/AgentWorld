# AgentWorld Implementation Tracker

> **Last Updated:** 2026-01-16
> **Current Phase:** Phase 7+ - Agent Infrastructure Features (COMPLETE)
> **Overall Progress:** 16/24 ADRs implemented (Phase 1: ADR-003, ADR-004, ADR-008, UI-ADR-005; Phase 2: ADR-005, ADR-006; Phase 3: ADR-009, ADR-011; Phase 4+: ADR-010, ADR-014, ADR-015; Phase 5: ADR-012, ADR-013; Phase 6: UI-ADR-001, UI-ADR-002; Phase 7: UI-ADR-003, UI-ADR-004; Phase 7+: ADR-016)

---

## Status Legend

| Icon | Meaning |
|------|---------|
| 🔴 | Not Started |
| 🟡 | In Progress |
| 🟢 | Complete |
| ⏸️ | Blocked |
| 🔵 | Deferred |

---

## Phase Overview

| Phase | Name | Status | Tests | ADRs | Key Deliverable | Verification |
|-------|------|--------|-------|------|-----------------|--------------|
| 1 | Foundation | 🟢 | 🟢 | 003, 004, 008, UI-005 | Two agents converse via CLI | `scripts/verify_phase1.py` |
| 2 | Memory & Topology | 🟢 | 🟢 | 005, 006 | Context-aware agents, network constraints | `scripts/verify_phase2.py` |
| 3 | Scenarios & Runtime | 🟢 | 🟢 | 009, 011 | Focus groups, pause/resume | `scripts/verify_phase3.py` |
| 4 | Evaluation & Personas | 🟢 | 🟢 | 010, 008+ | Metrics, persona library | `scripts/verify_phase4.py` |
| 5 | API Layer | 🟢 | 🟢 | 012, 013 | REST + WebSocket backend | `scripts/verify_phase5.py` |
| 6 | Web Foundation | 🟢 | 🟢 | UI-001, UI-002 | Basic web dashboard | `scripts/verify_phase6.py` |
| 7 | Real-time Web | 🟡 | 🔴 | UI-003, UI-004 | Live visualization | `scripts/verify_phase7.py` |
| 8 | Advanced Web | 🔴 | 🔴 | UI-006, UI-007, UI-008 | Full web workflows | `scripts/verify_phase8.py` |
| 9 | Production | 🟡 | 🟢 | 013+, 014, 015 | Security, plugins, traces | `scripts/verify_phase9.py` |

> **Test Status Legend:** 🟢 All tests pass | ⚠️ Tests incomplete | 🔴 No tests
>
> **Note:** Phase 1, 2, and 3 are complete with all 600 tests passing.

---

## How to Use This Tracker

### Document Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION_TRACKER.md                                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Header & Status Legend .......... Status icons & metadata   │
│  2. Phase Overview Table ............ 9 phases at a glance      │
│  3. How to Use This Tracker ......... This section              │
│  4. Phase 1-9 Detailed Sections ..... Per-ADR component tables  │
│  5. Appendix A: Project Structure ... Full directory tree       │
│  6. Appendix B: Verification Script . Python validation template│
│  7. Appendix C: Status Update Log ... Change history            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Elements Per Phase

Each phase section contains:

| Element | Purpose | Example |
|---------|---------|---------|
| **Goal** | One-sentence objective | "Run a basic conversation between agents via CLI" |
| **Exit Criteria** | Definition of done | "Two agents can have a multi-turn conversation, persisted to DB" |
| **Depends On** | Phase dependencies | "Phase 1 ✅" |
| **Component Tables** | Granular tracking | File paths, test commands, status |
| **Schema** | Database changes | SQL for new tables |
| **Acceptance Tests** | What must pass | Code snippets showing test intent |
| **Verification Checklist** | Checkbox list | Manual and automated checks |

### Component Table Format

```markdown
| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| LiteLLM wrapper | 🟢 | `src/agentworld/llm/provider.py` | `pytest tests/llm/test_provider.py` | |
```

- **Component**: What to build
- **Status**: 🔴→🟡→🟢 as you progress
- **File(s)**: Exact path where code goes
- **Verification**: How to prove it works
- **Notes**: Blockers, decisions, links

### Workflow: When Starting Work

1. Find current phase section
2. Pick a 🔴 component
3. Change status to 🟡 (In Progress)
4. Implement at the specified file path
5. **Write tests for the component** (MANDATORY)
6. Run the verification command (`pytest tests/<module>/`)
7. If passing, change status to 🟢 (Complete)
8. Update Appendix C status log

### Testing Policy (MANDATORY)

**No component is complete without tests.** This is non-negotiable.

```
┌─────────────────────────────────────────────────────────────────┐
│  DEFINITION OF DONE                                             │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Code implemented at specified file path                      │
│  ✓ Unit tests written in tests/<module>/test_<component>.py     │
│  ✓ Tests pass: pytest tests/<module>/ -v                        │
│  ✓ Verification script passes (if phase complete)               │
│  ✓ Status updated in tracker                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Test File Naming Convention:**
```
src/agentworld/<module>/<file>.py  →  tests/<module>/test_<file>.py

Examples:
  src/agentworld/llm/provider.py      →  tests/llm/test_provider.py
  src/agentworld/memory/retrieval.py  →  tests/memory/test_retrieval.py
  src/agentworld/topology/types.py    →  tests/topology/test_types.py
```

**Minimum Test Requirements Per Component:**
| Component Type | Minimum Tests |
|----------------|---------------|
| Data class     | Creation, serialization, validation |
| Service class  | Happy path, edge cases, error handling |
| CLI command    | Invocation, output format, error messages |
| API endpoint   | Request/response, auth, validation |

**Phase Completion Checklist:**
- [ ] All component tests written
- [ ] `pytest tests/<phase_modules>/ -v` passes
- [ ] `scripts/verify_phase<N>.py` passes
- [ ] Test coverage reported

### Workflow: Checking Progress

```bash
# Count components by status
grep -c "🔴" adrs/IMPLEMENTATION_TRACKER.md  # Not started
grep -c "🟡" adrs/IMPLEMENTATION_TRACKER.md  # In progress
grep -c "🟢" adrs/IMPLEMENTATION_TRACKER.md  # Complete
```

### Workflow: Verifying a Phase

```bash
# Run the phase verification script
python scripts/verify_phase1.py

# Expected output on success:
# ============================================================
# PHASE 1 VERIFICATION RESULTS
# ============================================================
#   ✓ CLI --help works
#   ✓ Run simulation
#   ✓ Simulation persisted
#   ...
# ============================================================
# ✓ PHASE 1 COMPLETE
```

### Tracker Metrics

| Metric | Count |
|--------|-------|
| Total Phases | 9 |
| Total ADRs Covered | 23 |
| Phase 1 Components | ~35 |
| Total Components (all phases) | ~180 |
| CLI Commands Defined | ~25 |
| API Endpoints Defined | ~17 |
| Database Tables (cumulative) | ~12 |

### Why This Tracker Works

| Feature | Benefit |
|---------|---------|
| **Traceability** | Every component links back to an ADR |
| **Verifiability** | Every component has a test command |
| **Predictability** | File paths are pre-defined (no guessing) |
| **Progress visibility** | Status icons show at-a-glance progress |
| **Incremental delivery** | Each phase has clear exit criteria |
| **Automation-ready** | Verification scripts can run in CI |

---

## Phase 1: Foundation

**Goal:** Run a basic conversation between agents via CLI
**Exit Criteria:** Two agents can have a multi-turn conversation, persisted to DB
**Status:** 🟢 Complete

### ADR-003: Multi-Provider LLM Architecture

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| LiteLLM wrapper | 🟢 | `src/agentworld/llm/provider.py` | `pytest tests/llm/test_provider.py` | |
| Unified completion interface | 🟢 | `src/agentworld/llm/provider.py` | `pytest tests/llm/test_completion.py` | |
| Prompt templates (Jinja2) | 🟢 | `src/agentworld/llm/templates.py` | `pytest tests/llm/test_templates.py` | |
| Token counting | 🟢 | `src/agentworld/llm/tokens.py` | `pytest tests/llm/test_tokens.py` | |
| Cost tracking | 🟢 | `src/agentworld/llm/cost.py` | `pytest tests/llm/test_cost.py` | |
| Response caching | 🟢 | `src/agentworld/llm/cache.py` | `pytest tests/llm/test_cache.py` | |
| Provider config (env vars) | 🟢 | `src/agentworld/llm/config.py` | Manual: `agentworld config check` | |

**Acceptance Test:** `tests/acceptance/test_llm_layer.py`
```python
# Must pass:
# - Can call OpenAI/Anthropic/Ollama via unified interface
# - Token counts are accurate
# - Caching reduces duplicate calls
```

---

### ADR-004: Trait Vector Persona System

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| TraitVector dataclass | 🟢 | `src/agentworld/personas/traits.py` | `pytest tests/personas/test_traits.py` | |
| Big Five implementation | 🟢 | `src/agentworld/personas/traits.py` | `pytest tests/personas/test_big_five.py` | |
| Custom traits support | 🟢 | `src/agentworld/personas/traits.py` | `pytest tests/personas/test_custom_traits.py` | |
| 0-1 range validation | 🟢 | `src/agentworld/personas/traits.py` | `pytest tests/personas/test_validation.py` | |
| Trait serialization (JSON) | 🟢 | `src/agentworld/personas/serialization.py` | `pytest tests/personas/test_serialization.py` | |
| Trait-aware prompt generation | 🟢 | `src/agentworld/personas/prompts.py` | `pytest tests/personas/test_prompts.py` | |

**Acceptance Test:** `tests/acceptance/test_trait_system.py`
```python
# Must pass:
# - TraitVector can be created with Big Five values
# - Traits influence generated prompts
# - High openness agent responds differently than low openness
```

---

### ADR-008: Persistence & State Management (Phase 1 Subset)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| SQLite database setup | 🟢 | `src/agentworld/persistence/database.py` | `pytest tests/persistence/test_db_init.py` | |
| SQLAlchemy models | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_models.py` | |
| Simulations table | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_simulations.py` | |
| Agents table | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_agents.py` | |
| Messages table | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_messages.py` | |
| Repository pattern | 🟢 | `src/agentworld/persistence/repository.py` | `pytest tests/persistence/test_repository.py` | |

**Schema (Phase 1):**
```sql
simulations (id, name, status, config_json, created_at, updated_at)
agents (id, simulation_id, name, traits_json, created_at)
messages (id, simulation_id, sender_id, receiver_id, content, step, timestamp)
```

**Acceptance Test:** `tests/acceptance/test_persistence.py`
```python
# Must pass:
# - Database initializes without error
# - Simulations persist and can be retrieved
# - Messages persist with correct relationships
```

---

### UI-ADR-005: CLI Design (Phase 1 Subset)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Typer app setup | 🟢 | `src/agentworld/cli/app.py` | `agentworld --help` | |
| `run` command | 🟢 | `src/agentworld/cli/commands/run.py` | `agentworld run --help` | |
| `list` command | 🟢 | `src/agentworld/cli/commands/list.py` | `agentworld list` | |
| `inspect` command | 🟢 | `src/agentworld/cli/commands/inspect.py` | `agentworld inspect <id>` | |
| YAML config parsing | 🟢 | `src/agentworld/cli/config.py` | `pytest tests/cli/test_config.py` | |
| Rich output formatting | 🟢 | `src/agentworld/cli/output.py` | Visual inspection | |
| JSON output mode | 🟢 | `src/agentworld/cli/output.py` | `agentworld list --json` | |

**CLI Commands (Phase 1):**
```bash
agentworld run <config.yaml>      # Run simulation
agentworld list                   # List simulations
agentworld inspect <sim_id>       # Show simulation details
agentworld --help                 # Help
agentworld --version              # Version
```

**Acceptance Test:** `tests/acceptance/test_cli.py`
```python
# Must pass:
# - All commands execute without error
# - Output is properly formatted
# - JSON mode produces valid JSON
```

---

### Core Components (Cross-cutting)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Project structure | 🟢 | `pyproject.toml`, dirs | `pip install -e .` | |
| Protocol definitions | 🟢 | `src/agentworld/core/protocols.py` | Import check | |
| Core dataclasses | 🟢 | `src/agentworld/core/models.py` | `pytest tests/core/test_models.py` | |
| Exception hierarchy | 🟢 | `src/agentworld/core/exceptions.py` | Import check | |
| Agent class | 🟢 | `src/agentworld/agents/agent.py` | `pytest tests/agents/test_agent.py` | |
| Simulation runner | 🟢 | `src/agentworld/simulation/runner.py` | `pytest tests/simulation/test_runner.py` | |
| Example config | 🟢 | `examples/two_agents.yaml` | `agentworld run examples/two_agents.yaml` | |

---

### Phase 1 Verification Checklist

```markdown
## Pre-Implementation
- [ ] Project scaffold created (`pyproject.toml`, directory structure)
- [ ] All protocols defined in `core/protocols.py`
- [ ] Acceptance tests written (will fail initially)

## LLM Layer
- [ ] `python -c "from agentworld.llm import complete"` works
- [ ] `pytest tests/llm/` all pass
- [ ] Can call at least one provider (OpenAI or Ollama)

## Trait System
- [ ] `python -c "from agentworld.personas import TraitVector"` works
- [ ] `pytest tests/personas/` all pass
- [ ] Traits serialize/deserialize correctly

## Persistence
- [ ] `agentworld db init` creates database
- [ ] `pytest tests/persistence/` all pass
- [ ] Can query simulations after restart

## CLI
- [ ] `agentworld --help` shows all commands
- [ ] `agentworld run examples/two_agents.yaml` completes
- [ ] `agentworld list` shows the simulation
- [ ] `agentworld inspect <id>` shows details

## Integration
- [ ] `pytest tests/acceptance/test_phase1.py` all pass
- [ ] `scripts/verify_phase1.py` exits with code 0
- [ ] Two agents have 3+ turn conversation
- [ ] Conversation persists to database
- [ ] Traits visibly influence responses
```

---

## Phase 2: Memory & Topology

**Goal:** Agents remember context; network structure constrains communication
**Exit Criteria:** Memories influence responses; messages flow along topology edges
**Status:** 🟢 Complete
**Depends On:** Phase 1 ✅

### ADR-006: Dual Memory Architecture

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Memory base class | 🟢 | `src/agentworld/memory/memory.py` | `pytest tests/memory/test_memory.py` | |
| Observation storage | 🟢 | `src/agentworld/memory/observation.py` | `pytest tests/memory/test_observation.py` | |
| Reflection generation | 🟢 | `src/agentworld/memory/reflection.py` | `pytest tests/memory/test_reflection.py` | |
| Importance scoring (LLM) | 🟢 | `src/agentworld/memory/importance.py` | `pytest tests/memory/test_importance.py` | |
| Embedding generation | 🟢 | `src/agentworld/memory/embeddings.py` | `pytest tests/memory/test_embeddings.py` | |
| Retrieval function | 🟢 | `src/agentworld/memory/retrieval.py` | `pytest tests/memory/test_retrieval.py` | |
| Recency scoring | 🟢 | `src/agentworld/memory/retrieval.py` | `pytest tests/memory/test_retrieval.py` | |
| Relevance scoring | 🟢 | `src/agentworld/memory/retrieval.py` | `pytest tests/memory/test_retrieval.py` | |
| Reflection threshold trigger | 🟢 | `src/agentworld/memory/reflection.py` | `pytest tests/memory/test_reflection.py` | |
| Memory persistence | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_repository.py` | |

**Schema Additions:**
```sql
memories (id, agent_id, type, content, importance, embedding, created_at)
-- type: 'observation' | 'reflection'
-- embedding: BLOB (numpy serialized)
```

**Acceptance Test:** `tests/acceptance/test_memory.py`
```python
# Must pass:
# - Agent stores observations from conversations
# - Retrieval returns relevant memories
# - Reflections generated when threshold exceeded
# - Memories persist across sessions
```

---

### ADR-005: Network Topology Architecture

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| NetworkX integration | 🟢 | `src/agentworld/topology/graph.py` | `pytest tests/topology/test_graph.py` | |
| Topology base class | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| Mesh topology | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| Hub-spoke topology | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| Hierarchical topology | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| Small-world topology | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| Scale-free topology | 🟢 | `src/agentworld/topology/types.py` | `pytest tests/topology/test_types.py` | |
| `get_neighbors()` | 🟢 | `src/agentworld/topology/graph.py` | `pytest tests/topology/test_graph.py` | |
| `can_communicate()` | 🟢 | `src/agentworld/topology/graph.py` | `pytest tests/topology/test_graph.py` | |
| Network metrics | 🟢 | `src/agentworld/topology/metrics.py` | `pytest tests/topology/test_metrics.py` | |
| Topology persistence | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_repository.py` | |
| ASCII visualization | 🔵 | `src/agentworld/topology/visualization.py` | `agentworld topology show <id>` | Deferred |

**Schema Additions:**
```sql
topology_edges (simulation_id, source_id, target_id, weight, created_at)
```

**Acceptance Test:** `tests/acceptance/test_topology.py`
```python
# Must pass:
# - All 5 topology types can be created
# - Messages only flow along edges
# - Metrics (clustering, centrality) computed correctly
```

---

### Phase 2 Verification Checklist

```markdown
## Memory System
- [ ] Agent creates observation after receiving message
- [ ] `agent.memories` returns stored memories
- [ ] Retrieval ranks by recency + importance + relevance
- [ ] Reflection auto-generates at threshold (150 importance)
- [ ] `pytest tests/memory/` all pass

## Topology System
- [ ] All 5 topology types instantiate correctly
- [ ] `topology.can_communicate(a, b)` enforced in simulation
- [ ] `agentworld topology show <id>` renders ASCII graph
- [ ] `pytest tests/topology/` all pass

## Integration
- [ ] Memory influences agent responses (context retrieval visible)
- [ ] Hub-spoke simulation: only hub sees all messages
- [ ] `pytest tests/acceptance/test_phase2.py` all pass
- [ ] `scripts/verify_phase2.py` exits with code 0
```

---

## Phase 3: Scenarios & Runtime

**Goal:** Run structured scenarios with proper execution control
**Exit Criteria:** Can run focus groups, pause/resume, deterministic replay
**Status:** 🟢 Complete
**Depends On:** Phase 2 ✅

### ADR-011: Simulation Runtime & Scheduling

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Step semantics | 🟢 | `src/agentworld/simulation/step.py` | `pytest tests/simulation/test_step.py` | |
| Round-robin ordering | 🟢 | `src/agentworld/simulation/ordering.py` | `pytest tests/simulation/test_ordering.py` | |
| Random ordering | 🟢 | `src/agentworld/simulation/ordering.py` | `pytest tests/simulation/test_ordering.py` | |
| Priority-based ordering | 🟢 | `src/agentworld/simulation/ordering.py` | `pytest tests/simulation/test_ordering.py` | |
| Topology-based ordering | 🟢 | `src/agentworld/simulation/ordering.py` | `pytest tests/simulation/test_ordering.py` | |
| Simultaneous ordering | 🟢 | `src/agentworld/simulation/ordering.py` | `pytest tests/simulation/test_ordering.py` | |
| Deterministic replay (seed) | 🟢 | `src/agentworld/simulation/seed.py` | `pytest tests/simulation/test_seed.py` | |
| Pause/resume | 🟢 | `src/agentworld/simulation/control.py` | `pytest tests/simulation/test_control.py` | |
| Cancellation | 🟢 | `src/agentworld/simulation/control.py` | `pytest tests/simulation/test_control.py` | |
| Timeout handling | 🟢 | `src/agentworld/simulation/control.py` | `pytest tests/simulation/test_control.py` | |
| Rate limiting | 🟢 | `src/agentworld/simulation/control.py` | `pytest tests/simulation/test_control.py` | Semaphore-based |
| Checkpoint save | 🟢 | `src/agentworld/simulation/checkpoint.py` | `pytest tests/simulation/test_checkpoint.py` | |
| Checkpoint restore | 🟢 | `src/agentworld/simulation/checkpoint.py` | `pytest tests/simulation/test_checkpoint.py` | |

**Schema Additions:**
```sql
checkpoints (id, simulation_id, step, state_blob, created_at)
-- state_blob: msgpack serialized world state
```

---

### ADR-009: Use Case Scenarios

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Scenario base class | 🟢 | `src/agentworld/scenarios/base.py` | `pytest tests/scenarios/test_base.py` | |
| Focus group scenario | 🟢 | `src/agentworld/scenarios/focus_group.py` | `pytest tests/scenarios/test_focus_group.py` | |
| Interview scenario | 🔵 | `src/agentworld/scenarios/interview.py` | `pytest tests/scenarios/test_interview.py` | Deferred |
| Survey scenario | 🔵 | `src/agentworld/scenarios/survey.py` | `pytest tests/scenarios/test_survey.py` | Deferred |
| Data generation scenario | 🔵 | `src/agentworld/scenarios/data_gen.py` | `pytest tests/scenarios/test_data_gen.py` | Deferred |
| Debate scenario | 🔵 | `src/agentworld/scenarios/debate.py` | `pytest tests/scenarios/test_debate.py` | Deferred |
| Stimulus injection | 🟢 | `src/agentworld/scenarios/stimulus.py` | `pytest tests/scenarios/test_stimulus.py` | |
| Moderator role | 🟢 | `src/agentworld/scenarios/moderator.py` | `pytest tests/scenarios/test_moderator.py` | |
| Scenario templates (YAML) | 🔵 | `templates/scenarios/*.yaml` | `agentworld run --scenario=focus_group` | Deferred |

---

### CLI Additions (Phase 3)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| `step` command | 🟢 | `src/agentworld/cli/commands/step.py` | `agentworld step <id>` | |
| `inject` command | 🟢 | `src/agentworld/cli/commands/inject.py` | `agentworld inject <id> "msg"` | |
| `checkpoint save` | 🟢 | `src/agentworld/cli/commands/checkpoint.py` | `agentworld checkpoint save <id>` | |
| `checkpoint restore` | 🟢 | `src/agentworld/cli/commands/checkpoint.py` | `agentworld checkpoint restore <chk>` | |
| `checkpoint list` | 🟢 | `src/agentworld/cli/commands/checkpoint.py` | `agentworld checkpoint list <id>` | |
| `checkpoint delete` | 🟢 | `src/agentworld/cli/commands/checkpoint.py` | `agentworld checkpoint delete <chk>` | |
| Interactive mode | 🔵 | `src/agentworld/cli/interactive.py` | `agentworld interactive <id>` | Deferred |

---

### Phase 3 Verification Checklist

```markdown
## Runtime
- [ ] `agentworld step <id>` advances one step
- [ ] `agentworld step <id> --count=5` advances five steps
- [ ] Same seed produces identical conversation
- [ ] Pause → restart → resume works
- [ ] Timeout cancels stuck simulation

## Scenarios
- [ ] `agentworld run --scenario=focus_group` works
- [ ] Hub-spoke topology auto-configured for focus group
- [ ] Moderator can inject questions mid-simulation
- [ ] Data generation produces structured output

## Checkpoints
- [ ] `agentworld checkpoint save <id>` creates checkpoint
- [ ] `agentworld checkpoint restore <chk>` restores state
- [ ] Restored simulation continues correctly

## Integration
- [ ] `pytest tests/acceptance/test_phase3.py` all pass
- [ ] `scripts/verify_phase3.py` exits with code 0
```

---

## Phase 4: Evaluation & Persona Library

**Goal:** Measure simulation quality; reuse personas across simulations
**Exit Criteria:** Metrics computed, personas persist in library
**Status:** 🟢 Complete
**Depends On:** Phase 3 ✅

### ADR-010: Evaluation & Metrics System

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Evaluation config | 🟢 | `src/agentworld/evaluation/config.py` | `pytest tests/evaluation/` | ValidationConfig, EvaluationConfig |
| LLM client wrapper | 🟢 | `src/agentworld/evaluation/client.py` | `pytest tests/evaluation/` | complete_json method |
| Metrics collector | 🟢 | `src/agentworld/evaluation/metrics.py` | `pytest tests/evaluation/` | SimulationMetrics, MetricsCollector |
| Behavioral metrics | 🟢 | `src/agentworld/evaluation/metrics.py` | `pytest tests/evaluation/` | In MetricsCollector |
| Memory metrics | 🟢 | `src/agentworld/evaluation/metrics.py` | `pytest tests/evaluation/` | In SimulationMetrics |
| Network metrics | 🟢 | `src/agentworld/evaluation/metrics.py` | `pytest tests/evaluation/` | In SimulationMetrics |
| Cost metrics | 🟢 | `src/agentworld/evaluation/metrics.py` | `pytest tests/evaluation/` | In SimulationMetrics |
| Persona adherence validator | 🟢 | `src/agentworld/evaluation/validators.py` | `pytest tests/evaluation/` | Validator.check_persona_adherence |
| Consistency validator | 🟢 | `src/agentworld/evaluation/validators.py` | `pytest tests/evaluation/` | Validator.check_consistency |
| Coherence validator | 🟢 | `src/agentworld/evaluation/validators.py` | `pytest tests/evaluation/` | Validator.check_coherence |
| Results extractor | 🟢 | `src/agentworld/evaluation/extractors.py` | `pytest tests/evaluation/` | ResultsExtractor class |
| Opinion extraction | 🟢 | `src/agentworld/evaluation/extractors.py` | `pytest tests/evaluation/` | extract_opinions method |
| Theme extraction | 🟢 | `src/agentworld/evaluation/extractors.py` | `pytest tests/evaluation/` | extract_themes method |
| Quote extraction | 🟢 | `src/agentworld/evaluation/extractors.py` | `pytest tests/evaluation/` | extract_quotes method |
| Experiment runner | 🟢 | `src/agentworld/evaluation/experiment.py` | `pytest tests/evaluation/` | A/B testing support |

**Schema Additions:**
```sql
metrics (id, simulation_id, step, metric_type, value_json, created_at)
```

---

### ADR-008: Persistence (Persona Library Extension)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Personas table | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_persona_library.py` | PersonaLibraryModel |
| Persona collections | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_persona_library.py` | PersonaCollectionModel |
| Collection members | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_persona_library.py` | PersonaCollectionMemberModel |
| Population templates | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_persona_library.py` | PopulationTemplateModel |
| Persona repository | 🟢 | `src/agentworld/persistence/repository.py` | `pytest tests/persistence/test_persona_library.py` | Methods in Repository class |

**Schema Additions:**
```sql
personas (id, name, traits_json, background, tags, created_at, updated_at)
persona_collections (id, name, description, created_at)
persona_collection_members (collection_id, persona_id)
population_templates (id, name, demographic_config, trait_distributions, created_at)
```

---

### CLI Additions (Phase 4)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| `persona create` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona create` | Supports --interactive |
| `persona list` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona list` | |
| `persona show` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona show <id>` | |
| `persona import` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona import <file>` | |
| `persona export` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona export` | |
| `persona search` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona search <query>` | |
| `persona collection` | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona collection` | Subcommands: create, list, add, remove, show |
| `metrics` command | 🔴 | `src/agentworld/cli/commands/metrics.py` | `agentworld metrics <id>` | |
| `results` command | 🔴 | `src/agentworld/cli/commands/results.py` | `agentworld results <id>` | |
| `validate` command | 🔴 | `src/agentworld/cli/commands/validate.py` | `agentworld validate <id>` | |
| Interactive persona wizard | 🟢 | `src/agentworld/cli/commands/persona.py` | `agentworld persona create --interactive` | Big Five traits wizard |

---

### Phase 4 Verification Checklist

```markdown
## Metrics
- [ ] `agentworld metrics <id>` shows behavioral metrics
- [ ] Cost tracking shows tokens + estimated spend
- [ ] Memory metrics show observations/reflections per agent
- [ ] `agentworld metrics <id> --export=csv` produces CSV

## Validation
- [ ] `agentworld validate <id>` runs persona adherence check

## Persona Library (Completed 2026-01-16)
- [x] `agentworld persona create --interactive` wizard works
- [x] Personas persist across sessions
- [x] `agentworld persona list` shows saved personas
- [x] `agentworld persona show <id>` displays traits
- [x] `agentworld persona collection` manages collections
- [x] Import/export JSON works
- [x] 25 tests pass in test_persona_library.py
- [ ] Validation produces 0-1 score with explanation
- [ ] Low scores identify specific inconsistencies

## Results Extraction
- [ ] `agentworld results <id>` shows AI-extracted insights
- [ ] Themes, opinions, quotes extracted correctly
- [ ] Sentiment analysis produces per-agent scores

## Persona Library
- [ ] `agentworld persona create --interactive` wizard works
- [ ] Personas persist across sessions
- [ ] Can create simulation from saved personas
- [ ] Import/export JSON works

## Integration
- [ ] `pytest tests/acceptance/test_phase4.py` all pass
- [ ] `scripts/verify_phase4.py` exits with code 0
```

---

## Phase 5: API Layer

**Goal:** Backend ready for web frontend and external integrations
**Exit Criteria:** All CLI functionality accessible via REST API; real-time events via WebSocket
**Status:** 🟢 Complete
**Depends On:** Phase 4 ✅

### ADR-012: API & WebSocket Event Schema

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| FastAPI app setup | 🟢 | `src/agentworld/api/app.py` | `pytest tests/api/test_api_endpoints.py` | CORS, lifespan, route registration |
| Simulations endpoints | 🟢 | `src/agentworld/api/routes/simulations.py` | `pytest tests/api/test_api_endpoints.py` | CRUD, start/pause/resume, step, inject |
| Agents endpoints | 🟢 | `src/agentworld/api/routes/agents.py` | `pytest tests/api/test_api_endpoints.py` | List, get, memories |
| Messages endpoints | 🟢 | `src/agentworld/api/routes/messages.py` | `pytest tests/api/test_api_endpoints.py` | List, get |
| Personas endpoints | 🟢 | `src/agentworld/api/routes/personas.py` | `pytest tests/api/test_api_endpoints.py` | CRUD, search, collections |
| Health endpoints | 🟢 | `src/agentworld/api/routes/health.py` | `pytest tests/api/test_api_endpoints.py` | /health, /api/v1/health |
| WebSocket handler | 🟢 | `src/agentworld/api/websocket.py` | `pytest tests/api/test_websocket.py` | Global and per-simulation |
| Event emitter | 🟢 | `src/agentworld/api/events.py` | `pytest tests/api/test_websocket.py` | SimulationEventEmitter |
| Pydantic schemas | 🟢 | `src/agentworld/api/schemas/` | `pytest tests/api/` | common, simulations, agents, messages, personas |
| Pagination | 🟢 | `src/agentworld/api/schemas/common.py` | `pytest tests/api/` | Built into list endpoints |
| OpenAPI spec | 🟢 | Auto-generated | `/docs` endpoint | |
| Checkpoints endpoints | 🔵 | `src/agentworld/api/routes/checkpoints.py` | - | Deferred |
| Metrics endpoints | 🔵 | `src/agentworld/api/routes/metrics.py` | - | Deferred |

**REST Endpoints:**
```
POST   /api/simulations
GET    /api/simulations
GET    /api/simulations/:id
DELETE /api/simulations/:id
POST   /api/simulations/:id/step
POST   /api/simulations/:id/inject
GET    /api/simulations/:id/messages
GET    /api/simulations/:id/metrics
GET    /api/agents/:id
GET    /api/agents/:id/memories
POST   /api/checkpoints
GET    /api/checkpoints/:id
POST   /api/checkpoints/:id/restore
GET    /api/personas
POST   /api/personas
GET    /api/personas/:id
```

**WebSocket Events:**
```
agent_thinking, agent_spoke, message_sent, memory_added,
reflection_generated, step_completed, cost_updated,
simulation_paused, simulation_done, error_occurred
```

---

### ADR-013: Security (Phase 5 Subset)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| CORS configuration | 🟢 | `src/agentworld/api/app.py` | Manual test | All origins allowed for dev |
| API key authentication | 🔵 | `src/agentworld/api/auth.py` | - | Deferred to Phase 9 |
| Rate limiting middleware | 🔵 | `src/agentworld/api/middleware.py` | - | Deferred to Phase 9 |

---

### Phase 5 Verification Checklist

```markdown
## REST API (Completed 2026-01-16)
- [x] `POST /api/v1/simulations` creates simulation
- [x] `GET /api/v1/simulations` returns list with pagination
- [x] `POST /api/v1/simulations/:id/step` advances simulation
- [x] All CRUD operations work for simulations, personas, collections
- [x] OpenAPI docs at `/docs` are complete
- [x] 38 tests pass in tests/api/

## WebSocket (Completed 2026-01-16)
- [x] Connect to `/ws` for global events
- [x] Connect to `/ws/simulations/:id` for simulation events
- [x] Ping/pong mechanism works
- [x] Subscription from global to simulation works
- [x] Event types defined (connected, step.completed, message.created, etc.)

## Security
- [x] CORS allows configured origins
- [ ] Requests without API key rejected (401) - Deferred to Phase 9
- [ ] Rate limiting triggers after threshold - Deferred to Phase 9

## Integration
- [x] Can create/start/step simulations via API
- [x] `pytest tests/api/` all pass (38 tests)
```

---

## Phase 6: Web Foundation

**Goal:** Basic web UI to manage simulations
**Exit Criteria:** Can create and list simulations via web dashboard
**Status:** 🟢 Complete
**Depends On:** Phase 5 ✅

### UI-ADR-001: Design System

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Tailwind configuration | 🟢 | `web/tailwind.config.js` | Build succeeds | Dark theme, custom colors |
| Color palette (dark theme) | 🟢 | `web/src/index.css` | Visual inspection | background, foreground, primary, etc. |
| Typography scale | 🟢 | `web/tailwind.config.js` | Visual inspection | Inter font |
| Spacing system | 🟢 | `web/tailwind.config.js` | Visual inspection | Custom spacing |
| Button components | 🟢 | `web/src/components/ui/Button.tsx` | `npm run test` | 5 variants, loading state |
| Input components | 🟢 | `web/src/components/ui/Input.tsx` | `npm run test` | Input, Textarea, Label |
| Card components | 🟢 | `web/src/components/ui/Card.tsx` | `npm run test` | Card, Header, Content, Footer |
| Badge components | 🟢 | `web/src/components/ui/Badge.tsx` | `npm run test` | 6 variants |
| Tooltip components | 🟢 | `web/src/components/ui/Tooltip.tsx` | `npm run test` | 4 positions |
| Modal components | 🟢 | `web/src/components/ui/Modal.tsx` | `npm run test` | Modal, Header, Content, Footer |

---

### UI-ADR-002: Information Architecture

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| React Router setup | 🟢 | `web/src/App.tsx` | Navigation works | 6 routes |
| Shell layout | 🟢 | `web/src/layouts/Shell.tsx` | Visual inspection | Collapsible sidebar |
| Navigation sidebar | 🟢 | `web/src/layouts/Shell.tsx` | Visual inspection | Mobile responsive |
| Dashboard page | 🟢 | `web/src/pages/Dashboard.tsx` | `/` route works | Stats, recent sims |
| Simulations list page | 🟢 | `web/src/pages/Simulations.tsx` | `/simulations` works | Filter, search |
| Simulation create page | 🟢 | `web/src/pages/SimulationCreate.tsx` | `/simulations/new` works | Agent config, trait sliders |
| Simulation detail page | 🟢 | `web/src/pages/SimulationDetail.tsx` | `/simulations/:id` works | Controls, agents, messages |
| Personas list page | 🟢 | `web/src/pages/Personas.tsx` | `/personas` works | Grid/list view, create modal |
| Settings page | 🟢 | `web/src/pages/Settings.tsx` | `/settings` works | API, LLM, appearance |
| Empty states | 🟢 | `web/src/components/EmptyState.tsx` | Shows when no data | |

---

### State Management (UI-ADR-004 Foundation)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Zustand store setup | 🟢 | `web/src/stores/index.ts` | Import works | |
| UI state store | 🟢 | `web/src/stores/uiStore.ts` | `npm run test` | Sidebar, theme, notifications |
| Simulation store | 🟢 | `web/src/stores/simulationStore.ts` | `npm run test` | WebSocket, events |
| React Query setup | 🟢 | `web/src/main.tsx` | Queries work | QueryClientProvider |
| API client | 🟢 | `web/src/lib/api.ts` | API calls work | All endpoints |

---

### Phase 6 Verification Checklist

```markdown
## Design System (Completed 2026-01-16)
- [x] `npm run build` succeeds
- [x] Dark theme applied correctly
- [x] All UI components have tests (30 tests passing)
- [x] Responsive sidebar (collapsible, mobile menu)

## Pages (Completed 2026-01-16)
- [x] Dashboard shows recent simulations with stats
- [x] Simulation list with search and filter
- [x] Create wizard with trait sliders
- [x] Simulation detail with controls
- [x] Personas page with grid/list views
- [x] Settings page for configuration

## State Management (Completed 2026-01-16)
- [x] React Query configured
- [x] Zustand stores for UI state
- [x] Simulation store for WebSocket

## Integration
- [x] API client with all endpoints
- [x] `npm run build` produces dist/
- [x] `npm run test` passes (30 tests)
```

---

## Phase 7: Real-time Web Visualization

**Goal:** Watch simulations live in browser
**Exit Criteria:** Topology updates in real-time; messages stream; agent inspection works
**Status:** 🟡 In Progress
**Depends On:** Phase 6 ✅

### UI-ADR-004: Real-time Visualization

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| react-force-graph setup | 🟢 | `web/src/components/simulation/TopologyGraph.tsx` | Renders | |
| Node rendering | 🟢 | `web/src/components/simulation/TopologyGraph.tsx` | Nodes visible | |
| Edge rendering | 🟢 | `web/src/components/simulation/TopologyGraph.tsx` | Edges visible | |
| Node state (selected) | 🟢 | `web/src/components/simulation/TopologyGraph.tsx` | States highlight | |
| Edge animation (message pulse) | 🟢 | `web/src/components/simulation/TopologyGraph.tsx` | Pulses on message | Built-in particles |
| WebSocket connection | 🟢 | `web/src/stores/realtimeStore.ts` | Events received | Auto-reconnect, batching |
| Conversation stream | 🟢 | `web/src/components/simulation/ConversationStream.tsx` | Messages render | |
| Virtualized list | 🟢 | `web/src/components/simulation/ConversationStream.tsx` | Handles 1000+ msgs | react-window |
| Message filtering | 🟢 | `web/src/components/simulation/ConversationStream.tsx` | Filters work | |
| Message search | 🟢 | `web/src/components/simulation/ConversationStream.tsx` | Search works | |
| Agent inspector panel | 🟢 | `web/src/components/simulation/AgentInspector.tsx` | Panel opens | Slide-out |
| Traits tab (Overview) | 🟢 | `web/src/components/simulation/AgentInspector.tsx` | Traits display | Radar chart |
| Memories tab | 🟢 | `web/src/components/simulation/AgentMemoryList.tsx` | Memories display | |
| Stats tab | 🟢 | `web/src/components/simulation/AgentStats.tsx` | Stats display | Sparkline |
| Message bubble component | 🟢 | `web/src/components/simulation/MessageBubble.tsx` | Renders | Expandable |

---

### UI-ADR-003: Simulation Control Interface

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| SimulationControls component | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Renders | Progress bar included |
| Start/Resume button | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Starts simulation | |
| Pause button | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Pauses simulation | |
| Step button | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Steps once | |
| Quick step buttons | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | +5/+10/+25 steps | |
| Connection status | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Live/Offline indicator | |
| Progress bar | 🟢 | `web/src/components/simulation/SimulationControls.tsx` | Shows step/total | Animated when running |
| Stimulus injector | 🟢 | `web/src/components/simulation/StimulusInjector.tsx` | Injects message | Target agent selection |
| Timeline component | 🔵 | `web/src/components/Timeline.tsx` | Renders | Deferred |
| Checkpoint controls | 🔵 | `web/src/components/CheckpointControls.tsx` | Creates checkpoint | Deferred |
| Speed control | 🔵 | `web/src/components/PlaybackControls.tsx` | 0.5x-4x works | Deferred |
| Cost monitor | 🔵 | `web/src/components/CostMonitor.tsx` | Shows spend | Deferred |

---

### Phase 7 Verification Checklist

```markdown
## Topology Visualization (Completed 2026-01-16)
- [x] Graph renders all agents as nodes
- [x] Edges show communication paths
- [x] Selected agent highlights
- [x] Message animates along edge (particles)
- [x] Click node to select agent

## Conversation Stream (Completed 2026-01-16)
- [x] Messages appear in real-time (via WebSocket)
- [x] Scroll handles 1000+ messages (virtualized)
- [x] Filter by agent works
- [x] Search finds messages
- [x] Step dividers between steps

## Agent Inspector (Completed 2026-01-16)
- [x] Click agent opens inspector
- [x] Overview tab shows traits (radar chart)
- [x] Messages tab shows filtered messages
- [x] Memories tab shows observations/reflections
- [x] Stats tab shows activity timeline

## Playback Controls (Completed 2026-01-16)
- [x] Start/Resume button works
- [x] Pause stops execution
- [x] Step advances once
- [x] Quick step buttons (+5/+10/+25)
- [x] Stimulus injection with target selection
- [x] Connection status indicator
- [ ] Speed control slider - Deferred
- [ ] Timeline scrubbing - Deferred

## Backend Integration (Completed 2026-01-16)
- [x] EventEmitter wired into simulation runner
- [x] step_started/step_completed events emitted
- [x] agent_thinking/agent_responded events emitted
- [x] message_created events emitted
- [x] API step endpoint executes actual steps

## Integration
- [x] SimulationDetail page refactored with new components
- [x] React Query + WebSocket integration
- [ ] Full test coverage - Pending
- [ ] `scripts/verify_phase7.py` exits with code 0 - Pending
```

---

## Phase 8: Advanced Web Features

**Goal:** Full web workflow for personas, results, experiments
**Exit Criteria:** Can build personas, analyze results, run experiments via web
**Status:** 🔴 Not Started
**Depends On:** Phase 7 ✅

### UI-ADR-006: Persona Builder & Library

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Persona wizard (3-step) | 🔴 | `web/src/components/PersonaWizard.tsx` | Flow completes | |
| Step 1: Basic info | 🔴 | `web/src/components/PersonaWizard.tsx` | Name/background | |
| Step 2: Trait sliders | 🔴 | `web/src/components/PersonaWizard.tsx` | Big Five sliders | |
| Step 3: Preview/save | 🔴 | `web/src/components/PersonaWizard.tsx` | Preview accurate | |
| Trait slider component | 🔴 | `web/src/components/TraitSlider.tsx` | Smooth dragging | |
| Low/high trait labels | 🔴 | `web/src/components/TraitSlider.tsx` | Labels visible | |
| Persona library grid | 🔴 | `web/src/pages/Personas.tsx` | Grid view works | |
| Persona library list | 🔴 | `web/src/pages/Personas.tsx` | List view works | |
| Persona search | 🔴 | `web/src/pages/Personas.tsx` | Search works | |
| Persona tags | 🔴 | `web/src/pages/Personas.tsx` | Tag filtering | |
| Collection management | 🔴 | `web/src/components/CollectionManager.tsx` | CRUD works | |
| Population generator | 🔴 | `web/src/components/PopulationGenerator.tsx` | Generates batch | |
| Import/export buttons | 🔴 | `web/src/pages/Personas.tsx` | JSON import/export | |

---

### UI-ADR-007: Results Analysis & Export

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Results dashboard | 🔴 | `web/src/pages/Results.tsx` | 5 tabs render | |
| Overview tab | 🔴 | `web/src/components/results/Overview.tsx` | Summary stats | |
| Conversation tab | 🔴 | `web/src/components/results/Conversation.tsx` | Full transcript | |
| Agents tab | 🔴 | `web/src/components/results/Agents.tsx` | Per-agent analysis | |
| Network tab | 🔴 | `web/src/components/results/Network.tsx` | Network metrics | |
| Insights tab | 🔴 | `web/src/components/results/Insights.tsx` | AI-extracted | |
| Theme visualization | 🔴 | `web/src/components/results/Themes.tsx` | Theme clusters | |
| Opinion cards | 🔴 | `web/src/components/results/Opinions.tsx` | Opinion display | |
| Notable quotes | 🔴 | `web/src/components/results/Quotes.tsx` | Quote highlight | |
| Message timeline | 🔴 | `web/src/components/results/Timeline.tsx` | Timeline chart | |
| Export JSON button | 🔴 | `web/src/pages/Results.tsx` | Downloads JSON | |
| Export CSV button | 🔴 | `web/src/pages/Results.tsx` | Downloads CSV | |
| Export HuggingFace | 🔴 | `web/src/pages/Results.tsx` | HF format | |
| Export PDF report | 🔴 | `web/src/pages/Results.tsx` | PDF generation | |

---

### UI-ADR-008: Experiments & A/B Testing

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Experiment list page | 🔴 | `web/src/pages/Experiments.tsx` | Lists experiments | |
| Experiment builder | 🔴 | `web/src/components/ExperimentBuilder.tsx` | Creates experiment | |
| Hypothesis input | 🔴 | `web/src/components/ExperimentBuilder.tsx` | Text input | |
| Base config selector | 🔴 | `web/src/components/ExperimentBuilder.tsx` | Config selection | |
| Variant editor | 🔴 | `web/src/components/VariantEditor.tsx` | Config overrides | |
| Variant color coding | 🔴 | `web/src/components/VariantEditor.tsx` | Visual distinction | |
| Dependent variable selector | 🔴 | `web/src/components/ExperimentBuilder.tsx` | Metric selection | |
| Batch execution UI | 🔴 | `web/src/components/BatchRunner.tsx` | Progress display | |
| Run queue | 🔴 | `web/src/components/BatchRunner.tsx` | Queue management | |
| Parallel execution toggle | 🔴 | `web/src/components/BatchRunner.tsx` | Parallel option | |
| Results comparison | 🔴 | `web/src/pages/ExperimentResults.tsx` | Side-by-side | |
| Box plot visualization | 🔴 | `web/src/components/charts/BoxPlot.tsx` | Renders | |
| Bar chart comparison | 🔴 | `web/src/components/charts/BarChart.tsx` | Renders | |
| Statistical significance | 🔴 | `web/src/components/StatisticalAnalysis.tsx` | p-values shown | |
| Effect size display | 🔴 | `web/src/components/StatisticalAnalysis.tsx` | Cohen's d | |

---

### Phase 8 Verification Checklist

```markdown
## Persona Builder
- [ ] 3-step wizard completes
- [ ] Trait sliders smooth and accurate
- [ ] Preview matches final persona
- [ ] Persona saves to library

## Persona Library
- [ ] Grid/list toggle works
- [ ] Search finds personas
- [ ] Tags filter correctly
- [ ] Collections organize personas
- [ ] Import/export JSON works

## Results Analysis
- [ ] All 5 tabs render with data
- [ ] AI insights extracted correctly
- [ ] Charts render properly
- [ ] All export formats work

## Experiments
- [ ] Can create experiment with variants
- [ ] Batch runs execute
- [ ] Results comparison renders
- [ ] Statistical analysis correct

## Integration
- [ ] Full workflow: create personas → run experiment → analyze results
- [ ] `scripts/verify_phase8.py` exits with code 0
```

---

## Phase 9: Production Hardening

**Goal:** Production-ready with security, plugins, and full observability
**Exit Criteria:** Multi-user RBAC, plugin system, full reasoning traces
**Status:** 🔴 Not Started
**Depends On:** Phase 8 ✅

### ADR-013: Security & Secrets Management (Full)

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Secret vault integration | 🔴 | `src/agentworld/security/vault.py` | `pytest tests/security/test_vault.py` | |
| Encrypted config storage | 🔴 | `src/agentworld/security/encryption.py` | `pytest tests/security/test_encryption.py` | |
| User authentication | 🔴 | `src/agentworld/security/auth.py` | `pytest tests/security/test_auth.py` | |
| RBAC implementation | 🔴 | `src/agentworld/security/rbac.py` | `pytest tests/security/test_rbac.py` | |
| Role definitions | 🔴 | `src/agentworld/security/roles.py` | `pytest tests/security/test_roles.py` | |
| Permission checks | 🔴 | `src/agentworld/security/permissions.py` | `pytest tests/security/test_permissions.py` | |
| Prompt redaction | 🔴 | `src/agentworld/security/redaction.py` | `pytest tests/security/test_redaction.py` | |
| Response redaction | 🔴 | `src/agentworld/security/redaction.py` | `pytest tests/security/test_response_redact.py` | |
| Audit logging | 🔴 | `src/agentworld/security/audit.py` | `pytest tests/security/test_audit.py` | |
| Audit log persistence | 🔴 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/test_audit.py` | |

**Schema Additions:**
```sql
users (id, email, password_hash, role, created_at)
audit_logs (id, user_id, action, resource_type, resource_id, details_json, timestamp)
```

---

### ADR-014: Plugin & Extension Model

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Plugin protocols | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | All 7 plugin types |
| Plugin registry | 🟢 | `src/agentworld/plugins/registry.py` | `pytest tests/plugins/` | Entry-point discovery |
| Plugin sandbox | 🟢 | `src/agentworld/plugins/sandbox.py` | `pytest tests/plugins/` | Timeout/error handling |
| Plugin hooks | 🟢 | `src/agentworld/plugins/hooks.py` | `pytest tests/plugins/` | Lifecycle events |
| Built-in plugins | 🟢 | `src/agentworld/plugins/builtin.py` | `pytest tests/plugins/` | Calculator, time, random, formats |
| TopologyPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| ScenarioPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| ValidatorPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| ExtractorPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| AgentToolPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| LLMProviderPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| OutputFormatPlugin protocol | 🟢 | `src/agentworld/plugins/protocols.py` | `pytest tests/plugins/` | |
| Plugin CLI commands | 🟢 | `src/agentworld/plugins/cli.py` | `agentworld plugins list` | list, info, groups, reload, validate |
| Entry points config | 🟢 | `pyproject.toml` | Entry points configured | All 7 groups |
| Simulation hooks integration | 🟢 | `src/agentworld/simulation/runner.py` | `pytest tests/simulation/` | PluginHooks called |

---

### ADR-015: Reasoning & Prompt Visibility

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Visibility config | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel enum, VisibilityConfig |
| Reasoning trace | 🟢 | `src/agentworld/reasoning/trace.py` | `pytest tests/reasoning/` | ReasoningStep, ReasoningTrace |
| Reasoning capture | 🟢 | `src/agentworld/reasoning/capture.py` | `pytest tests/reasoning/` | Context manager with logging |
| Privacy manager | 🟢 | `src/agentworld/reasoning/privacy.py` | `pytest tests/reasoning/` | Redaction of API keys, emails |
| CLI display | 🟢 | `src/agentworld/reasoning/display.py` | `pytest tests/reasoning/` | CLIReasoningDisplay |
| Reasoning storage | 🟢 | `src/agentworld/reasoning/storage.py` | `pytest tests/reasoning/` | Persistence and export |
| None level | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel.NONE |
| Summary level | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel.SUMMARY |
| Detailed level | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel.DETAILED |
| Full level | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel.FULL |
| Debug level | 🟢 | `src/agentworld/reasoning/config.py` | `pytest tests/reasoning/` | VisibilityLevel.DEBUG |
| Trace redaction | 🟢 | `src/agentworld/reasoning/privacy.py` | `pytest tests/reasoning/` | PrivacyManager |
| JSON export | 🟢 | `src/agentworld/reasoning/storage.py` | `pytest tests/reasoning/` | export_json method |
| JSONL export | 🟢 | `src/agentworld/reasoning/storage.py` | `pytest tests/reasoning/` | export_jsonl method |
| UI inspector integration | 🔴 | `web/src/components/ReasoningInspector.tsx` | Panel works | Deferred to web phase |

---

### Phase 9 Verification Checklist

```markdown
## Security
- [ ] Users can register and login
- [ ] Roles (admin, user, viewer) enforced
- [ ] Sensitive data redacted in logs
- [ ] Audit log captures all actions
- [ ] Secrets loaded from vault

## Plugins
- [ ] `agentworld plugin list` shows installed
- [ ] `agentworld plugin install <pkg>` works
- [ ] Custom persona generator plugin works
- [ ] Custom topology plugin works
- [ ] Sandboxing prevents malicious code

## Reasoning Visibility
- [ ] `agentworld inspect <id> --reasoning` shows traces
- [ ] Visibility levels filter appropriately
- [ ] Export produces valid research format
- [ ] UI inspector shows full traces

## Integration
- [ ] Multi-user scenario works
- [ ] Plugin extends functionality
- [ ] `pytest tests/acceptance/test_phase9.py` all pass
- [ ] `scripts/verify_phase9.py` exits with code 0
```

---

## Appendix A: Project Structure

```
agentworld/
├── pyproject.toml
├── README.md
├── adrs/
│   ├── README.md
│   ├── IMPLEMENTATION_TRACKER.md      # This file
│   ├── ADR-*.md
│   └── UI-ADR-*.md
├── examples/
│   ├── two_agents.yaml
│   ├── focus_group.yaml
│   └── data_generation.yaml
├── scripts/
│   ├── verify_phase1.py
│   ├── verify_phase2.py
│   └── ...
├── templates/
│   ├── prompts/
│   │   ├── agent_think.jinja2
│   │   └── reflection.jinja2
│   └── scenarios/
│       ├── focus_group.yaml
│       └── interview.yaml
├── src/
│   └── agentworld/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── protocols.py
│       │   ├── models.py
│       │   └── exceptions.py
│       ├── llm/
│       │   ├── provider.py
│       │   ├── templates.py
│       │   ├── tokens.py
│       │   ├── cost.py
│       │   └── cache.py
│       ├── personas/
│       │   ├── traits.py
│       │   ├── prompts.py
│       │   └── serialization.py
│       ├── agents/
│       │   └── agent.py
│       ├── memory/
│       │   ├── base.py
│       │   ├── observation.py
│       │   ├── reflection.py
│       │   ├── embeddings.py
│       │   └── retrieval.py
│       ├── topology/
│       │   ├── base.py
│       │   ├── graph.py
│       │   ├── types.py
│       │   ├── metrics.py
│       │   └── visualization.py
│       ├── simulation/
│       │   ├── runner.py
│       │   ├── step.py
│       │   ├── ordering.py
│       │   ├── control.py
│       │   ├── checkpoint.py
│       │   └── seed.py
│       ├── scenarios/
│       │   ├── base.py
│       │   ├── focus_group.py
│       │   ├── interview.py
│       │   ├── data_gen.py
│       │   └── stimulus.py
│       ├── evaluation/
│       │   ├── collector.py
│       │   ├── behavioral.py
│       │   ├── validators.py
│       │   └── extractor.py
│       ├── persistence/
│       │   ├── database.py
│       │   ├── models.py
│       │   ├── repository.py
│       │   └── persona_repo.py
│       ├── api/
│       │   ├── app.py
│       │   ├── routes/
│       │   ├── websocket.py
│       │   ├── events.py
│       │   └── auth.py
│       ├── security/
│       │   ├── auth.py
│       │   ├── rbac.py
│       │   ├── redaction.py
│       │   └── audit.py
│       ├── plugins/
│       │   ├── discovery.py
│       │   ├── registry.py
│       │   └── points/
│       ├── reasoning/
│       │   ├── trace.py
│       │   ├── visibility.py
│       │   └── export.py
│       └── cli/
│           ├── app.py
│           ├── output.py
│           ├── config.py
│           ├── interactive.py
│           ├── wizards/
│           └── commands/
│               ├── run.py
│               ├── list.py
│               ├── inspect.py
│               ├── step.py
│               ├── inject.py
│               ├── checkpoint.py
│               ├── persona.py
│               ├── metrics.py
│               ├── results.py
│               ├── validate.py
│               └── plugin.py
├── web/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.tsx
│   │   ├── lib/
│   │   ├── stores/
│   │   ├── queries/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── components/
│   │       ├── ui/
│   │       ├── TopologyGraph.tsx
│   │       ├── ConversationStream.tsx
│   │       ├── AgentInspector.tsx
│   │       ├── PlaybackControls.tsx
│   │       └── ...
│   └── public/
└── tests/
    ├── conftest.py
    ├── acceptance/
    │   ├── test_phase1.py
    │   ├── test_phase2.py
    │   └── ...
    ├── core/
    ├── llm/
    ├── personas/
    ├── memory/
    ├── topology/
    ├── simulation/
    ├── scenarios/
    ├── evaluation/
    ├── persistence/
    ├── api/
    ├── security/
    ├── plugins/
    └── reasoning/
```

---

## Appendix B: Verification Scripts Template

```python
#!/usr/bin/env python
"""
scripts/verify_phase1.py

Run this script to verify Phase 1 is complete.
Exit code 0 = all checks pass
Exit code 1 = one or more checks failed
"""

import subprocess
import sys
import json

class PhaseVerifier:
    def __init__(self):
        self.checks = []
        self.failed = False

    def run(self, cmd: str) -> tuple[bool, str, str]:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr

    def check(self, name: str, condition: bool, error_msg: str = ""):
        self.checks.append((name, condition, error_msg))
        if not condition:
            self.failed = True

    def report(self):
        print("\n" + "=" * 60)
        print("PHASE 1 VERIFICATION RESULTS")
        print("=" * 60)

        for name, passed, error in self.checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            if not passed and error:
                print(f"      Error: {error}")

        print("=" * 60)
        if self.failed:
            print("✗ PHASE 1 INCOMPLETE")
            return 1
        else:
            print("✓ PHASE 1 COMPLETE")
            return 0

def main():
    v = PhaseVerifier()

    # CLI exists
    ok, out, err = v.run("agentworld --help")
    v.check("CLI --help works", ok, err)

    # Can run simulation
    ok, out, err = v.run("agentworld run examples/two_agents.yaml --json")
    v.check("Run simulation", ok, err)

    sim_id = None
    if ok:
        try:
            data = json.loads(out)
            sim_id = data.get("id")
        except:
            pass

    # Simulation persisted
    ok, out, _ = v.run("agentworld list --json")
    has_sim = sim_id and sim_id in out if ok else False
    v.check("Simulation persisted", has_sim)

    # Can inspect
    if sim_id:
        ok, out, _ = v.run(f"agentworld inspect {sim_id}")
        v.check("Inspect shows agents", ok and "alice" in out.lower())

    # Messages exist
    if sim_id:
        ok, out, _ = v.run(f"agentworld inspect {sim_id} --messages --json")
        if ok:
            try:
                msgs = json.loads(out)
                v.check("Messages persisted", len(msgs) >= 2)
            except:
                v.check("Messages persisted", False, "Invalid JSON")

    # Traits stored
    if sim_id:
        ok, out, _ = v.run(f"agentworld inspect {sim_id} --agents --json")
        if ok:
            try:
                agents = json.loads(out)
                has_traits = all("traits" in a for a in agents)
                v.check("Traits stored", has_traits)
            except:
                v.check("Traits stored", False, "Invalid JSON")

    # Unit tests pass
    ok, _, err = v.run("pytest tests/llm tests/personas tests/persistence tests/cli -q")
    v.check("Unit tests pass", ok, err[:200] if err else "")

    # Acceptance tests pass
    ok, _, err = v.run("pytest tests/acceptance/test_phase1.py -q")
    v.check("Acceptance tests pass", ok, err[:200] if err else "")

    return v.report()

if __name__ == "__main__":
    sys.exit(main())
```

---

## Appendix C: Status Update Log

| Date | Phase | Update | By |
|------|-------|--------|-----|
| 2025-01-15 | - | Initial tracker created | - |
| 2025-01-15 | 1 | Phase 1 Foundation complete - all components implemented and verified | Claude |
| 2025-01-15 | 2 | Phase 2 Memory & Topology complete - all components implemented with 370 tests | Claude |
| 2025-01-15 | 3 | Phase 3 Scenarios & Runtime complete - step models, ordering, control, checkpoints, seeds, scenarios, stimulus, moderator. 600 tests passing | Claude |
| 2025-01-16 | 4 | ADR-010 Evaluation & Metrics System complete - config, client, metrics, validators, extractors, experiment runner. 100% compliance | Claude |
| 2025-01-16 | 9 | ADR-015 Reasoning Visibility complete - config, trace, capture, privacy, display, storage. 99% compliance | Claude |
| 2025-01-16 | 9 | ADR-014 Plugin Extension Model complete - protocols, registry, sandbox, hooks, cli, builtin, entry points, simulation integration. 98% compliance | Claude |
| 2026-01-16 | - | Auto-tracked: ADR-010 (1 files modified) | Hook |
| 2026-01-16 | 4 | ADR-008 Persona Library Extension complete - models (PersonaCollectionModel, PersonaCollectionMemberModel, PopulationTemplateModel), repository methods, CLI (persona create/list/show/search/import/export/collection), 25 tests passing | Claude |
| 2026-01-16 | 5 | Phase 5 API Layer complete - FastAPI app, REST endpoints (simulations, agents, messages, personas, collections, health), WebSocket (global & per-simulation events), Pydantic schemas, 38 tests passing | Claude |
| 2026-01-16 | 6 | Phase 6 Web Foundation complete - React/Vite/TypeScript, Tailwind dark theme, UI components (Button, Card, Badge, Modal, etc.), React Router with Shell layout, 6 pages (Dashboard, Simulations, Personas, Settings), Zustand + React Query, API client, 30 tests passing | Claude |
| 2026-01-16 | 7 | Phase 7 Real-time Web Visualization implementation - EventEmitter wired into simulation runner, realtimeStore with WebSocket/auto-reconnect/event batching, TopologyGraph (react-force-graph-2d), ConversationStream (virtualized react-window), AgentInspector (4-tab panel with radar chart), SimulationControls (progress bar, quick steps), StimulusInjector, SimulationDetail refactored | Claude |
| 2026-01-16 | 7+ | Agent Infrastructure Features - ADR-016 (Agent Injection), ExportService (6 formats: JSONL/OpenAI/Anthropic/ShareGPT/Alpaca/DPO), Evaluation Framework (evaluator protocol, built-in evaluators, message_evaluations DB table), Export/Evaluation/Injection API endpoints, UI panels (ExportPanel, EvaluationPanel, AgentInjector), Circuit breaker + concurrency limits for external agents | Claude |
| 2026-01-17 | - | Auto-tracked: ADR-009, ADR-011, ADR-012 (3 files modified) | Hook |
| 2026-01-17 | 7+ | ADR-016 status updated to Accepted - agent injection fully implemented | Claude |

---

## Agent Infrastructure Features (ADR-016+)

**Goal:** Support agent testing and training data generation workflows
**Exit Criteria:** Can inject external agents, export fine-tuning data, evaluate message quality
**Status:** 🟢 Complete
**Depends On:** Phase 7 ✅

### ADR-016: Agent Injection

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| ADR-016 Documentation | 🟢 | `adrs/ADR-016-agent-injection.md` | File exists | HTTP protocol, privacy tiers, circuit breaker |
| External Agent Provider | 🟢 | `src/agentworld/agents/external.py` | `pytest tests/agents/` | Privacy tiers, request/response schema |
| Circuit Breaker | 🟢 | `src/agentworld/agents/external.py` | `pytest tests/agents/` | CLOSED/OPEN/HALF_OPEN states |
| Concurrency Limits | 🟢 | `src/agentworld/agents/external.py` | `pytest tests/agents/` | Semaphore-based rate limiting |
| Injected Agent Manager | 🟢 | `src/agentworld/agents/external.py` | `pytest tests/agents/` | Per-simulation management |
| Injection API Endpoints | 🟢 | `src/agentworld/api/routes/simulations.py` | `pytest tests/api/` | inject-agent, metrics, health-check |
| Injection Schemas | 🟢 | `src/agentworld/api/schemas/injection.py` | Import check | Request/Response Pydantic models |
| AgentInjector UI | 🟢 | `web/src/components/simulation/AgentInjector.tsx` | TypeScript check | Privacy tier selection, metrics modal |

### Export Pipeline

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Export Service | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | 6 formats, redaction, manifest |
| JSONL Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Raw messages |
| OpenAI Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Fine-tuning format |
| Anthropic Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Fine-tuning format |
| ShareGPT Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Open-source models |
| Alpaca Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Instruction tuning |
| DPO Pairs Format | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | Preference pairs from scores |
| Redaction Profiles | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | none, basic, strict |
| Export Manifest | 🟢 | `src/agentworld/services/export.py` | `pytest tests/services/` | SHA256 hashes, provenance |
| Export API Endpoints | 🟢 | `src/agentworld/api/routes/export.py` | `pytest tests/api/` | formats, download, manifest |
| Export Schemas | 🟢 | `src/agentworld/api/schemas/export.py` | Import check | Request/Response Pydantic models |
| ExportPanel UI | 🟢 | `web/src/components/simulation/ExportPanel.tsx` | TypeScript check | Format/redaction selection, download |

### Evaluation Framework

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| message_evaluations Table | 🟢 | `src/agentworld/persistence/models.py` | `pytest tests/persistence/` | Provenance fields |
| Evaluator Protocol | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | Protocol-based extensibility |
| PersonaAdherenceEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | LLM-based |
| CoherenceEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | LLM-based |
| RelevanceEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | LLM-based |
| ConsistencyEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | LLM-based |
| LengthCheckEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | Heuristic |
| KeywordFilterEvaluator | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | Heuristic |
| Evaluator Registry | 🟢 | `src/agentworld/evaluation/evaluators.py` | `pytest tests/evaluation/` | discover_evaluators() |
| Evaluation API Endpoints | 🟢 | `src/agentworld/api/routes/evaluation.py` | `pytest tests/api/` | evaluate, evaluations, summary |
| Evaluation Schemas | 🟢 | `src/agentworld/api/schemas/evaluation.py` | Import check | Request/Response Pydantic models |
| EvaluationPanel UI | 🟢 | `web/src/components/simulation/EvaluationPanel.tsx` | TypeScript check | Run evaluators, view scores |

### API Integration

| Component | Status | File(s) | Verification | Notes |
|-----------|--------|---------|--------------|-------|
| Export API Methods | 🟢 | `web/src/lib/api.ts` | TypeScript check | getExportFormats, downloadExport |
| Evaluation API Methods | 🟢 | `web/src/lib/api.ts` | TypeScript check | runEvaluation, getEvaluations |
| Injection API Methods | 🟢 | `web/src/lib/api.ts` | TypeScript check | injectAgent, getInjectionMetrics |
| SimulationDetail Integration | 🟢 | `web/src/pages/SimulationDetail.tsx` | TypeScript check | Advanced tools section |

---

*This document is the source of truth for AgentWorld implementation progress. Update component statuses as work progresses.*
