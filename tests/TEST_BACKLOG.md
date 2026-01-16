# Test Backlog

> **Purpose:** Track missing tests for Phase 1 & 2 that must be completed before Phase 3.
> **Last Updated:** 2025-01-15

## Status Summary

| Phase | Tests Written | Tests Needed | Coverage |
|-------|---------------|--------------|----------|
| Phase 1 | 2 | 15 | ~13% |
| Phase 2 | 2 | 9 | ~22% |
| **Total** | **4** | **24** | **~17%** |

---

## Phase 1: Foundation Tests

### LLM Module (`tests/llm/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_provider.py` | 🔴 TODO | HIGH | LLMProvider, complete(), error handling |
| `test_templates.py` | 🔴 TODO | MEDIUM | Jinja2 templates, render() |
| `test_tokens.py` | 🔴 TODO | MEDIUM | Token counting, model-specific counts |
| `test_cost.py` | 🔴 TODO | MEDIUM | Cost calculation, model pricing |
| `test_cache.py` | 🔴 TODO | HIGH | Response caching, cache invalidation |

### Personas Module (`tests/personas/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_traits.py` | 🔴 TODO | HIGH | TraitVector, Big Five, validation |
| `test_prompts.py` | 🔴 TODO | HIGH | System prompt generation |
| `test_serialization.py` | 🔴 TODO | MEDIUM | JSON serialization/deserialization |

### Persistence Module (`tests/persistence/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_database.py` | 🔴 TODO | HIGH | init_db, session management |
| `test_models.py` | 🔴 TODO | HIGH | SimulationModel, AgentModel, MessageModel |
| `test_repository.py` | 🔴 TODO | HIGH | CRUD operations, queries |

### Core Module (`tests/core/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_models.py` | 🔴 TODO | MEDIUM | Message, AgentConfig, SimulationConfig |
| `test_exceptions.py` | 🔴 TODO | LOW | Exception hierarchy |

### Agents Module (`tests/agents/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_agent.py` | 🔴 TODO | HIGH | Agent creation, think(), respond_to() |

### Simulation Module (`tests/simulation/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_runner.py` | 🔴 TODO | HIGH | Simulation, step(), run() |

### CLI Module (`tests/cli/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_config.py` | 🔴 TODO | HIGH | YAML parsing, validation |
| `test_commands.py` | 🔴 TODO | MEDIUM | run, list, inspect commands |

---

## Phase 2: Memory & Topology Tests

### Memory Module (`tests/memory/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_memory.py` | ✅ DONE | - | Basic Memory class tests |
| `test_observation.py` | 🔴 TODO | HIGH | Observation CRUD, serialization |
| `test_reflection.py` | 🔴 TODO | HIGH | Reflection generation, thresholds |
| `test_retrieval.py` | 🔴 TODO | HIGH | Scoring: recency, relevance, importance |
| `test_importance.py` | 🔴 TODO | MEDIUM | Heuristic & LLM rating |
| `test_embeddings.py` | 🔴 TODO | MEDIUM | Embedding generation, similarity |

### Topology Module (`tests/topology/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_topology.py` | ✅ DONE | - | All 5 topology types |
| `test_graph.py` | 🔴 TODO | MEDIUM | TopologyGraph wrapper |
| `test_metrics.py` | 🔴 TODO | MEDIUM | Centrality, clustering |
| `test_visualization.py` | 🔴 TODO | LOW | ASCII rendering |

### Persistence Extensions (`tests/persistence/`)

| Test File | Status | Priority | Components Tested |
|-----------|--------|----------|-------------------|
| `test_memories.py` | 🔴 TODO | HIGH | MemoryModel CRUD |
| `test_topology_persistence.py` | 🔴 TODO | HIGH | TopologyEdgeModel, TopologyConfigModel |

---

## Test Writing Guidelines

### Structure for Each Test File

```python
"""Tests for <module>/<component>."""

import pytest
from agentworld.<module>.<component> import <Class>


class Test<ClassName>:
    """Tests for <ClassName>."""

    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return <Class>(...)

    def test_creation(self, instance):
        """Test basic creation."""
        assert instance is not None

    def test_happy_path(self, instance):
        """Test normal usage."""
        result = instance.method()
        assert result == expected

    def test_edge_case(self, instance):
        """Test edge cases."""
        ...

    def test_error_handling(self, instance):
        """Test error conditions."""
        with pytest.raises(ExpectedError):
            instance.bad_method()
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/llm/ -v
pytest tests/memory/ -v

# Run with coverage
pytest tests/ --cov=src/agentworld --cov-report=html

# Run only Phase 1 tests
pytest tests/llm tests/personas tests/persistence tests/core tests/agents tests/simulation tests/cli -v

# Run only Phase 2 tests
pytest tests/memory tests/topology -v
```

---

## Completion Criteria

Before starting Phase 3:
- [ ] All HIGH priority tests written
- [ ] All MEDIUM priority tests written
- [ ] `pytest tests/ -v` passes with 0 failures
- [ ] Coverage > 70% for Phase 1 & 2 modules
- [ ] Verification scripts pass

---

## Progress Log

| Date | Tests Added | By |
|------|-------------|-----|
| 2025-01-15 | tests/memory/test_memory.py | Claude |
| 2025-01-15 | tests/topology/test_topology.py | Claude |
| | | |
