# Agent Benchmark Deep Dive: AgentWorld vs τ-bench vs Industry Benchmarks

> **Document Version:** 1.2
> **Last Updated:** 2026-01-27
> **Author:** Research Analysis
> **Changelog:**
> - v1.2 - Added comprehensive τ²-bench analysis and AgentWorld comparison
> - v1.1 - Fixed pass^k/pass@k definitions and examples; added citations

---

## Executive Summary

This document provides a comprehensive comparison of AgentWorld's evaluation framework against τ-bench (Sierra Research) and other major agent benchmarks in the industry. We analyze architectural differences, metric approaches, and use cases to understand where AgentWorld fits in the agent evaluation landscape.

| Benchmark | Focus | Primary Metric | Multi-Agent | Dual-Control | RL Support | Leaderboard |
|-----------|-------|----------------|-------------|--------------|------------|-------------|
| **AgentWorld** | Multi-agent simulation | pass^k + Quality | ✅ N agents | ❌ No | ❌ No | ❌ No |
| **τ-bench** | Tool-Agent-User | pass^k | ❌ 2 parties | ❌ No | ❌ No | ❌ No |
| **τ²-bench** | Dual-control coordination | pass^k | ❌ 2 parties | ✅ Dec-POMDP | ✅ Gymnasium | ✅ taubench.com |
| **AgentBench** | LLM-as-Agent | Success Rate | ❌ Single | ❌ No | ❌ No | ✅ Yes |
| **WebArena** | Web navigation | Task Success | ❌ Single | ❌ No | ❌ No | ✅ Yes |
| **SWE-bench** | Code generation | pass@k | ❌ Single | ❌ No | ❌ No | ✅ Yes |
| **GAIA** | General assistant | Accuracy | ❌ Single | ❌ No | ❌ No | ✅ HuggingFace |

---

## 1. τ-bench (Sierra Research)

### Overview

[τ-bench](https://github.com/sierra-research/tau-bench) (Tool-Agent-User benchmark) was introduced by Sierra Research in June 2024 to address a critical gap in agent evaluation: **testing agents on human interaction and domain-specific rule compliance**.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      τ-bench Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐        ┌─────────────┐                    │
│   │    User     │◄──────►│    Agent    │                    │
│   │  Simulator  │        │   (LLM +    │                    │
│   │   (LLM)     │        │   Tools)    │                    │
│   └─────────────┘        └──────┬──────┘                    │
│                                 │                            │
│                                 ▼                            │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Domain Environment                      │   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│   │  │ Database│  │  APIs   │  │ Policy  │             │   │
│   │  │ (JSON)  │  │ (Tools) │  │  Doc    │             │   │
│   │  └─────────┘  └─────────┘  └─────────┘             │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Domains

| Domain | Description | Complexity | GPT-4o pass^1 | Source |
|--------|-------------|------------|---------------|--------|
| **Retail** | Order management, returns, cancellations | Medium | 50.0% | [arXiv:2406.12045](https://arxiv.org/abs/2406.12045) |
| **Airline** | Flight booking, changes, customer service | High | 35.2% | [arXiv:2406.12045](https://arxiv.org/abs/2406.12045) |
| **Telecom** (τ²) | Troubleshooting, plan changes | Very High | ~34% | [τ²-bench repo](https://github.com/sierra-research/tau2-bench) |

### Key Innovation: pass^k Metric

Unlike traditional pass@k ("at least one of k sampled attempts succeeds"), τ-bench introduces **pass^k** ("all k sampled attempts must succeed"):

```
pass^k = C(c, k) / C(n, k)

Where:
  n = total number of trials run
  c = number of successful trials
  k = number of trials sampled for evaluation
  C(a,b) = binomial coefficient "a choose b"
```

**Note:** This is NOT about temporal "consecutive" successes. It asks: "If we randomly sample k trials from our n total trials, what is the probability that all k are successes?" This measures reliability more strictly than pass@k.

**Interpretation Example (n=10, c=8):**
- **pass^1 = 80%**: Standard success rate
- **pass^4 = 33.3%**: Only 33% chance all 4 sampled trials succeed
- **pass^8 = 2.2%**: Only 2.2% chance all 8 sampled trials succeed
- **The steep drop from pass^1 to pass^k exposes reliability issues**

### State Verification

τ-bench validates task completion by comparing the **final database state** against an **annotated goal state** using exact equality:

```python
# τ-bench verification (conceptual)
def verify_task(final_state, expected_state):
    # Deep equality comparison of state dictionaries
    return final_state == expected_state

# Example: Order cancellation
expected_state = {"order_123": {"status": "cancelled"}}
final_state = database.get_state()
success = verify_task(final_state, expected_state)
```

**Note:** Some implementations use hash comparison for efficiency (`hash(json.dumps(state, sort_keys=True))`), but the semantic meaning is exact state equality.

### Key Results

Results from the τ-bench paper ([Yao et al., 2024, arXiv:2406.12045](https://arxiv.org/abs/2406.12045), Table 2):

| Model | Retail pass^1 | Airline pass^1 | Notes |
|-------|--------------|----------------|-------|
| GPT-4o (2024-05-13) | 50.0% | 35.2% | Best overall at publication |
| Claude 3.5 Sonnet | 69.2% | 46.0% | Highest retail performance |
| Gemini 1.5 Pro | 45.0% | 30.0% | Comparable to GPT-4o |

**Note:** pass^8 values were not directly reported in the paper. The paper emphasizes that pass^k for k>1 drops significantly, demonstrating reliability gaps even for high pass^1 models.

**Key Finding:** Even state-of-the-art models show significant reliability gaps as k increases.

### References
- [τ-bench GitHub](https://github.com/sierra-research/tau-bench)
- [Sierra τ-bench Blog](https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents)
- [arXiv Paper](https://arxiv.org/abs/2406.12045)

---

## 1.5. τ²-bench: Dual-Control Evolution (June 2025)

### Overview

[τ²-bench](https://github.com/sierra-research/tau2-bench) ([arXiv:2506.07982](https://arxiv.org/abs/2506.07982)) represents a significant evolution from τ-bench, introducing **dual-control environments** where both AI agent AND user have tools to modify shared state. This models real-world scenarios like technical support where users must actively participate.

### Key Innovation: Dual-Control Environment

```
┌─────────────────────────────────────────────────────────────────────┐
│                    τ²-bench Dual-Control Architecture                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────┐              ┌─────────────────┐              │
│   │      USER       │◄────────────►│      AGENT      │              │
│   │   (LLM + Tools) │   dialogue   │   (LLM + Tools) │              │
│   └────────┬────────┘              └────────┬────────┘              │
│            │                                │                        │
│            │ user actions                   │ agent actions          │
│            ▼                                ▼                        │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                  SHARED ENVIRONMENT (Dec-POMDP)              │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│   │   │   Device    │  │   Network   │  │   Account   │         │   │
│   │   │   Settings  │  │   Status    │  │   State     │         │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘         │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   Key Difference: User can toggle settings, agent can modify        │
│   account - both affect shared state that other must observe        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Dec-POMDP Formulation:** The environment is modeled as a Decentralized Partially Observable Markov Decision Process where:
- Both agent and user have **partial observability** of shared state
- Actions from either party affect the environment
- Success requires **coordination and communication**

### Domains

| Domain | Description | Control Type | Complexity |
|--------|-------------|--------------|------------|
| **Mock** | Testing/validation | Single | Low |
| **Retail** | Order management, returns | Single (agent only) | Medium |
| **Airline** | Flight booking, changes | Single (agent only) | High |
| **Telecom** ⭐NEW | Network troubleshooting, device settings | **Dual** (agent + user) | Very High |

### Telecom Domain Deep Dive

The Telecom domain is the flagship dual-control domain with tasks like:
- Fixing broken data connections (user toggles settings, agent diagnoses)
- Resolving MMS issues (user checks phone, agent modifies account)
- Switching network modes (coordinated actions required)

```python
# Example Telecom Task Flow
# 1. User reports: "My mobile data isn't working"
# 2. Agent uses tool: check_account_data_status(user_id) → "enabled"
# 3. Agent instructs user: "Please toggle mobile data off and on"
# 4. User uses tool: toggle_mobile_data() → "mobile_data: off"
# 5. User uses tool: toggle_mobile_data() → "mobile_data: on"
# 6. Agent verifies: check_device_status(user_id) → "data: connected"
# 7. Task complete when shared state matches goal
```

### Key Features (New in τ²-bench)

| Feature | Description | Source |
|---------|-------------|--------|
| **Gymnasium Interface** | RL-compatible `AgentGymEnv` and `UserGymEnv` | [v0.2.1](https://github.com/sierra-research/tau2-bench/blob/main/RELEASE_NOTES.md) |
| **Interactive Play Mode** | `tau2 play` for manual control as agent or user | CLI |
| **Compositional Task Generator** | Programmatic task creation from atomic actions | [Paper](https://arxiv.org/abs/2506.07982) |
| **Constrained User Simulator** | Tool-bound behavior, can't invent states | Architecture |
| **Train/Test Splits** | Standardized splits for RL research | v0.2.1 |
| **Leaderboard** | [taubench.com](https://taubench.com) with pass^k metrics | v0.2.0 |

### Performance Impact: Solo vs Dual-Control

From [Sierra blog](https://sierra.ai/uk/blog/benchmarking-agents-in-collaborative-real-world-scenarios):

| Mode | Description | GPT-4.1 Performance Drop |
|------|-------------|--------------------------|
| **Solo** | Agent has full information upfront | Baseline |
| **Dual-Control** | Agent must guide user actions | **-25 points** |

**Key Finding:** Even top-tier models (GPT-4.1, o4-mini) show ~25 percentage point drops when shifting from autonomous to collaborative mode, exposing coordination challenges.

### Ablation Modes

τ²-bench provides ablation modes for fine-grained analysis:

```bash
# Standard dual-control
tau2 run --domain telecom --agent-llm gpt-4.1 --user-llm gpt-4.1

# No-user mode (agent gets all info upfront)
tau2 run --domain telecom --agent llm_agent_solo --user dummy_user

# Oracle-plan mode (agent given predetermined action plan)
tau2 run --domain telecom --agent llm_agent_gt --user-llm gpt-4.1
```

### Evaluation Commands

```bash
# Install
pip install -e .

# Run evaluation (4 trials across all tasks)
tau2 run --domain telecom --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 4

# Interactive debugging
tau2 play

# View results
tau2 view
```

### References
- [τ²-bench GitHub](https://github.com/sierra-research/tau2-bench)
- [arXiv:2506.07982](https://arxiv.org/abs/2506.07982) - Dong et al., June 2025
- [Sierra Blog](https://sierra.ai/uk/blog/benchmarking-agents-in-collaborative-real-world-scenarios)
- [Leaderboard](https://taubench.com)

---

## 2. AgentWorld Evaluation Framework

### Overview

AgentWorld provides a **multi-agent simulation platform** with integrated evaluation capabilities spanning two ADRs:
- **ADR-020**: τ-bench inspired task evaluation (pass^k, state verification, fault classification)
- **ADR-021**: App-specific quality metrics and benchmark apps

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AgentWorld Evaluation Architecture                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                   MULTI-AGENT SIMULATION                     │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │   │
│   │   │ Agent A │◄►│ Agent B │◄►│ Agent C │◄►│   ...   │       │   │
│   │   │(Persona)│  │(Persona)│  │(Persona)│  │         │       │   │
│   │   └────┬────┘  └────┬────┘  └────┬────┘  └─────────┘       │   │
│   │        │            │            │                          │   │
│   │        └────────────┼────────────┘                          │   │
│   │                     ▼                                        │   │
│   │   ┌─────────────────────────────────────────────────────┐   │   │
│   │   │               SIMULATED APPS                         │   │   │
│   │   │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │   │
│   │   │  │ PayPal  │  │ Shopping│  │  Email  │  ...        │   │   │
│   │   │  │   App   │  │   App   │  │   App   │             │   │   │
│   │   │  └─────────┘  └─────────┘  └─────────┘             │   │   │
│   │   └─────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                 │                                    │
│                                 ▼                                    │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    EVALUATION LAYER                          │   │
│   │                                                              │   │
│   │   ADR-020 (τ-bench)          ADR-021 (App Quality)          │   │
│   │   ┌─────────────────┐        ┌─────────────────┐            │   │
│   │   │ • Pass^k Metrics│        │ • Quality Score │            │   │
│   │   │ • State Verify  │        │ • Scenario Tests│            │   │
│   │   │ • Fault Classify│        │ • Benchmark Apps│            │   │
│   │   │ • Policy Engine │        │ • YAML Runner   │            │   │
│   │   └─────────────────┘        └─────────────────┘            │   │
│   │                                                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### ADR-020: τ-bench Inspired Evaluation

AgentWorld implements the core τ-bench concepts with extensions for multi-agent scenarios:

| Component | τ-bench | AgentWorld | Notes |
|-----------|---------|------------|-------|
| pass^k Metric | ✅ | ✅ | Same formula: `C(c,k)/C(n,k)` |
| State Verification | ✅ | ✅ | Exact state equality comparison |
| Fault Classification | Basic | Extended | 3 assignments × 10 fault types |
| Policy Engine | ✅ | ✅ | Rule-based compliance checking |
| Multi-Agent | ❌ | ✅ | Native multi-agent support |
| Predefined Scenarios | 2-3 domains | 17 scenarios | Payment + Shopping domains |

#### Fault Classification (AgentWorld Extension)

```python
class FaultAssignment(Enum):
    AGENT = "agent"           # Agent made an error
    ENVIRONMENT = "environment"  # System/API error
    TASK = "task"             # Task definition issue

class FaultType(Enum):
    GOAL_NOT_ACHIEVED = "goal_not_achieved"
    GOAL_PARTIAL = "goal_partial"
    WRONG_ACTION = "wrong_action"
    WRONG_PARAMS = "wrong_params"
    MISSING_ACTION = "missing_action"
    EXTRA_ACTION = "extra_action"
    POLICY_VIOLATION = "policy_violation"
    MISSING_CONFIRMATION = "missing_confirmation"
    MISUNDERSTOOD_TASK = "misunderstood_task"
    REASONING_ERROR = "reasoning_error"
```

### ADR-021: App Quality Metrics

AgentWorld adds **app-specific evaluation** not present in τ-bench:

#### Quality Scoring (6 Dimensions)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Completeness | 25% | Required fields, actions, state schema |
| Documentation | 20% | Action/parameter descriptions |
| Validation | 20% | Parameter constraints (min, max, pattern) |
| Error Handling | 15% | ERROR blocks in logic |
| State Safety | 10% | Validation before state updates |
| Consistency | 10% | Naming conventions |

#### Quality Levels

| Level | Score Range | Interpretation |
|-------|-------------|----------------|
| Excellent | ≥ 85% | Production-ready |
| Good | 70-84% | Minor improvements needed |
| Fair | 50-69% | Significant gaps |
| Poor | < 50% | Not recommended for use |

#### Benchmark Apps

AgentWorld provides 5 reference implementations for comparison:

| App | Category | Actions | Purpose |
|-----|----------|---------|---------|
| `bench_counter` | Custom | 2 | Minimal state mutation |
| `bench_wallet` | Payment | 4 | Transfer testing |
| `bench_inventory` | Shopping | 6 | CRUD with constraints |
| `bench_messaging` | Communication | 5 | Multi-party messaging |
| `bench_workflow` | Custom | 8 | Complex branching logic |

---

## 3. Other Major Benchmarks

### AgentBench

[AgentBench](https://openreview.net/forum?id=zAdUB0aCTQ) evaluates LLM-as-Agent across 8 diverse environments:

| Environment | Type | Key Challenge |
|-------------|------|---------------|
| Operating System | CLI | Multi-step commands |
| Database | SQL | Query generation |
| Knowledge Graph | QA | Reasoning over graphs |
| Digital Card Game | Game | Strategic planning |
| Lateral Thinking | Puzzle | Creative reasoning |
| House-Holding | Embodied | Object manipulation |
| Web Shopping | Web | Multi-step navigation |
| Web Browsing | Web | Information retrieval |

**Limitation:** Single-run success rates, no reliability measurement.

### WebArena

[WebArena](https://webarena.dev/) ([Zhou et al., 2024, arXiv:2307.13854](https://arxiv.org/abs/2307.13854)) provides high-fidelity web simulations:

- **4 Domains:** E-commerce, forums, coding, CMS
- **812 Tasks:** Diverse web navigation and interaction tasks
- **Initial GPT-4 Performance:** 14.41% (from paper, Table 3)
- **Architecture Insight:** Modular "standard model" (Planner → Executor → Memory)

**Limitation:** No state verification beyond task completion; single-attempt success rate.

### SWE-bench

[SWE-bench](https://www.swebench.com/) ([Jimenez et al., 2024, arXiv:2310.06770](https://arxiv.org/abs/2310.06770)) evaluates code generation on real GitHub issues:

| Variant | # Tasks | Description | Source |
|---------|---------|-------------|--------|
| SWE-bench Full | 2,294 | Complete dataset | [arXiv:2310.06770](https://arxiv.org/abs/2310.06770) |
| SWE-bench Lite | 300 | Curated subset | [swebench.com](https://www.swebench.com/) |
| SWE-bench Verified | 500 | Human-verified | [OpenAI blog](https://openai.com/index/introducing-swe-bench-verified/) |

**Key Finding:** "Agentless" approaches (3-step: localize → edit → validate) can outperform complex agent systems ([Xia et al., 2024](https://arxiv.org/abs/2407.01489)).

### GAIA

[GAIA](https://huggingface.co/spaces/gaia-benchmark/leaderboard) ([Mialon et al., 2024, arXiv:2311.12983](https://arxiv.org/abs/2311.12983)) tests general assistant capabilities:

- **466 questions** requiring reasoning, tool use, web search
- **3 difficulty levels** with clear factual answers
- **Human baseline:** 92% (from paper, Table 2)
- **GPT-4 with plugins:** 15% on Level 1, 5% on Level 2, 0% on Level 3 (paper Table 2)

### MultiAgentBench (2025)

[MultiAgentBench](https://arxiv.org/abs/2503.01935) specifically addresses multi-agent evaluation:

- **Collaboration & Competition** scenarios
- **Coordination Protocols:** Star, chain, tree, graph topologies
- **Novel KPIs:** Milestone-based performance indicators

---

## 4. Key Differentiators

### AgentWorld vs τ²-bench: Deep Comparison

| Aspect | τ²-bench | AgentWorld | Winner |
|--------|----------|------------|--------|
| **Multi-Agent** | ❌ Agent + User (2 parties) | ✅ N agents (any topology) | AgentWorld |
| **Control Model** | Dual-control (Dec-POMDP) | Shared app state | Different focus |
| **Domains** | 4 fixed (retail, airline, telecom, mock) | ∞ dynamic (JSON-defined) | AgentWorld |
| **Task Generation** | Compositional (atomic → task) | Manual + scenarios | τ²-bench |
| **RL Support** | ✅ Gymnasium interface | ❌ Not yet | τ²-bench |
| **User Simulation** | Tool-constrained LLM | Agent-to-agent | Different |
| **Leaderboard** | ✅ taubench.com | ❌ Internal | τ²-bench |
| **Customization** | Code changes required | No-code UI | AgentWorld |
| **Quality Metrics** | ❌ Only pass^k | ✅ 6-dimension scoring | AgentWorld |
| **Fault Classification** | Basic | ✅ 3×10 taxonomy | AgentWorld |

### Architecture Comparison

```
τ²-bench (Dual-Control)                    AgentWorld (Multi-Agent)
═════════════════════════                  ═════════════════════════

     ┌─────────┐                              ┌─────────┐
     │  Agent  │◄──────────┐                  │ Agent A │◄──┐
     │  (LLM)  │           │                  │(Persona)│   │
     └────┬────┘           │                  └────┬────┘   │
          │                │                       │        │
          ▼                ▼                       ▼        ▼
    ┌──────────────────────────┐            ┌──────────────────────────┐
    │   SHARED ENVIRONMENT     │            │       SIMULATED APP      │
    │  (Dec-POMDP: partial     │            │   (Full state visible    │
    │   observability)         │            │    to all agents)        │
    └──────────────────────────┘            └──────────────────────────┘
          ▲                ▲                       ▲        ▲
          │                │                       │        │
     ┌────┴────┐           │                  ┌────┴────┐   │
     │  User   │───────────┘                  │ Agent B │───┘
     │  (LLM)  │                              │(Persona)│
     └─────────┘                              └─────────┘

Key Difference:                            Key Difference:
- 2 parties with tools                     - N agents with personas
- Partial observability                    - Full state transparency
- Coordination challenge                   - Collaboration/competition
```

### Feature Gap Analysis

#### What AgentWorld Can Learn from τ²-bench

| τ²-bench Feature | Status in AgentWorld | Recommendation |
|------------------|---------------------|----------------|
| Gymnasium RL interface | ❌ Missing | Add `AgentGymEnv` wrapper |
| Compositional task generator | ❌ Manual only | Build atomic→task composer |
| Public leaderboard | ❌ Internal | Consider taubench.com integration |
| Interactive play mode | ❌ Missing | Add `agentworld play` CLI |
| Train/test splits | ⚠️ Partial | Formalize standard splits |

#### What τ²-bench Lacks (AgentWorld Advantages)

| AgentWorld Feature | τ²-bench Status | Impact |
|--------------------|-----------------|--------|
| True multi-agent (N>2) | ❌ Only 2 parties | Can't model complex social dynamics |
| Dynamic app definitions | ❌ Fixed domains | Requires code to add domains |
| No-code app creation | ❌ None | Higher barrier to entry |
| 6-dimension quality scoring | ❌ None | No app quality feedback |
| Extended fault taxonomy | ⚠️ Basic | Less diagnostic insight |
| YAML scenario runner | ❌ None | Harder to create test suites |

### When to Use Each

| Use Case | Best Choice | Reason |
|----------|-------------|--------|
| **LLM customer service benchmark** | τ²-bench | Industry-standard, leaderboard |
| **Agent-user coordination research** | τ²-bench | Dec-POMDP, dual-control |
| **Multi-agent collaboration** | AgentWorld | N-agent support, topologies |
| **Custom domain simulation** | AgentWorld | JSON app definitions |
| **App quality assurance** | AgentWorld | 6-dimension scoring |
| **RL agent training** | τ²-bench | Gymnasium interface |
| **Reliability measurement** | Either | Both use pass^k |
| **Quick prototyping** | AgentWorld | No-code UI, YAML scenarios |

### Integration Opportunity

The frameworks are **complementary**, not competing:

```
┌─────────────────────────────────────────────────────────────────┐
│                  POTENTIAL INTEGRATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  τ²-bench Domains ──────┐                                        │
│  (retail, airline,      │                                        │
│   telecom)              │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │     AgentWorld       │                           │
│              │   Multi-Agent Core   │                           │
│              │                      │                           │
│              │  - N agent support   │                           │
│              │  - Quality scoring   │◄──── τ²-bench Gymnasium   │
│              │  - Fault taxonomy    │       interface            │
│              │  - YAML scenarios    │                           │
│              └──────────────────────┘                           │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │    taubench.com      │                           │
│              │     Leaderboard      │                           │
│              └──────────────────────┘                           │
│                                                                  │
│  Possible: Import τ²-bench domains as AgentWorld apps,          │
│  export AgentWorld results to taubench.com leaderboard          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Metric Comparison: pass@k vs pass^k

### pass@k (Traditional - HumanEval, SWE-bench)

**Definition:** Probability of **at least one** correct answer when sampling k attempts.

```
pass@k = 1 - C(n-c, k) / C(n, k)

Where:
  n = total trials, c = successes, k = samples drawn
  This is: 1 - (ways to pick k failures) / (ways to pick k from n)
```

**Interpretation:** "Did it work at least once out of k samples?" (optimistic)

### pass^k (τ-bench, AgentWorld)

**Definition:** Probability that **all k** sampled attempts are successes.

```
pass^k = C(c, k) / C(n, k)

Where:
  This is: (ways to pick k successes) / (ways to pick k from n)
```

**Note:** This is NOT "k consecutive" in a temporal sense. It measures: "If we sample k trials, what's the probability all are successes?"

**Interpretation:** "Can it work reliably every time?" (stringent)

### Comparison Example (Mathematically Verified)

Given n=10 trials with c successes:

| Metric | n=10, c=8 (80%) | n=10, c=6 (60%) | Formula |
|--------|-----------------|-----------------|---------|
| pass@1 | 80.0% | 60.0% | 1 - C(n-c,1)/C(n,1) |
| pass^1 | 80.0% | 60.0% | C(c,1)/C(n,1) |
| pass@4 | **100%** | **99.5%** | 1 - C(n-c,4)/C(n,4) |
| pass^4 | **33.3%** | **7.1%** | C(c,4)/C(n,4) |
| pass@8 | **100%** | **100%** | 1 - C(n-c,8)/C(n,8) |
| pass^8 | **2.2%** | **0%** | C(c,8)/C(n,8) |

**Calculation Details (c=8, n=10):**
- pass^4 = C(8,4)/C(10,4) = 70/210 = 33.3%
- pass^8 = C(8,8)/C(10,8) = 1/45 = 2.2%
- pass@4 = 1 - C(2,4)/C(10,4) = 1 - 0/210 = 100% (can't choose 4 from 2 failures)

**Key Insight:** pass@k approaches 100% quickly (hiding reliability issues), while pass^k drops steeply (exposing fragility).

---

## 6. Implementation Recommendations

### For Researchers

1. **Use τ-bench** for single-agent customer service benchmarking
2. **Use AgentWorld** for multi-agent interaction research
3. **Report both pass@k and pass^k** to show reliability
4. **Include state verification** for meaningful completion metrics

### For Practitioners

1. **Start with pass^4 or pass^8** as reliability threshold
2. **Use fault classification** to diagnose failures systematically
3. **Implement policy engines** for compliance-critical applications
4. **Test with diverse topologies** (hub-spoke, mesh) for multi-agent systems

### For AgentWorld Users

1. **ADR-020 (τ-bench):** Use for task-based evaluation with reliability metrics
2. **ADR-021 (App Quality):** Use for app definition validation before deployment
3. **Combine both:** Run quality checks, then reliability tests, then fault analysis

---

## 7. Future Directions

### Industry Trends

1. **Reliability-First Metrics:** Shift from pass@k to pass^k adoption
2. **Multi-Agent Evaluation:** Growing focus on collaboration/competition
3. **Real-World Grounding:** Moving beyond synthetic to production-like environments
4. **Context & Memory:** New benchmarks for long-context agent behavior

### AgentWorld Roadmap

1. **Phase 10f-E:** UI dashboard for τ-bench evaluation
2. **Phase 10g+:** Extended scenario library (communication, calendar)
3. **Future:** Integration with external benchmark leaderboards

---

## 8. References

### Primary Papers (Peer-Reviewed / arXiv)

| Benchmark | Paper | Citation |
|-----------|-------|----------|
| τ-bench | [arXiv:2406.12045](https://arxiv.org/abs/2406.12045) | Yao et al., "τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains", 2024 |
| **τ²-bench** | [arXiv:2506.07982](https://arxiv.org/abs/2506.07982) | Dong et al., "τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment", June 2025 |
| WebArena | [arXiv:2307.13854](https://arxiv.org/abs/2307.13854) | Zhou et al., "WebArena: A Realistic Web Environment for Building Autonomous Agents", 2024 |
| SWE-bench | [arXiv:2310.06770](https://arxiv.org/abs/2310.06770) | Jimenez et al., "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", 2024 |
| GAIA | [arXiv:2311.12983](https://arxiv.org/abs/2311.12983) | Mialon et al., "GAIA: A Benchmark for General AI Assistants", 2024 |
| AgentBench | [OpenReview](https://openreview.net/forum?id=zAdUB0aCTQ) | Liu et al., "AgentBench: Evaluating LLMs as Agents", ICLR 2024 |
| MultiAgentBench | [arXiv:2503.01935](https://arxiv.org/abs/2503.01935) | Multi-agent evaluation framework, 2025 |

### Official Repositories & Sites

- [τ-bench GitHub](https://github.com/sierra-research/tau-bench) - Original Sierra Research benchmark (2024)
- [τ²-bench GitHub](https://github.com/sierra-research/tau2-bench) - Dual-control evolution with telecom domain (2025)
- [τ²-bench Leaderboard](https://taubench.com) - Official pass^k leaderboard
- [WebArena](https://webarena.dev/) - Official benchmark site
- [SWE-bench](https://www.swebench.com/) - Official leaderboard
- [GAIA Leaderboard](https://huggingface.co/spaces/gaia-benchmark/leaderboard) - HuggingFace

### Secondary Sources (Guides & Summaries)

*Note: These are useful overviews but should be cross-referenced with primary papers.*

- [Sierra τ-bench Blog](https://sierra.ai/blog/tau-bench-shaping-development-evaluation-agents) - Original τ-bench announcement
- [Sierra τ²-bench Blog](https://sierra.ai/uk/blog/benchmarking-agents-in-collaborative-real-world-scenarios) - τ²-bench deep dive
- [Evidently AI: Agent Benchmarks](https://www.evidentlyai.com/blog/ai-agent-benchmarks) - Overview article
- [Confident AI: Evaluation Metrics](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation) - Metrics guide
- [Galileo: Multi-Agent Benchmarks](https://galileo.ai/blog/benchmarks-multi-agent-ai) - Industry overview

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **pass@k** | Probability of **at least one** success when sampling k trials; formula: `1 - C(n-c,k)/C(n,k)` |
| **pass^k** | Probability that **all k** sampled trials are successes; formula: `C(c,k)/C(n,k)` |
| **C(n,k)** | Binomial coefficient "n choose k" = n!/(k!(n-k)!) |
| **Dec-POMDP** | Decentralized Partially Observable Markov Decision Process; multi-agent model where agents have partial observability and must coordinate |
| **Dual-Control** | Environment where both AI agent AND user have tools to modify shared state (τ²-bench innovation) |
| **Single-Control** | Traditional setup where only the AI agent can act on the environment |
| **Fault Classification** | Categorizing failures by assignment (who) and type (what) |
| **State Verification** | Comparing final state to expected state using exact equality |
| **Policy Compliance** | Adherence to domain-specific rules |
| **Goal State** | Expected database/app state after task completion |
| **Reliability Gap** | Difference between pass^1 and pass^k; larger gap = more fragile agent |
| **Compositional Task Generator** | Programmatic creation of tasks from atomic components (τ²-bench feature) |

---

## Appendix B: Quick Comparison Matrix

```
                    Multi-   Dual-    State    Policy   pass^k   RL       Leader-
                    Agent    Control  Verify   Engine   Metric   Support  board
τ-bench              ❌        ❌        ✅        ✅       ✅       ❌       ❌
τ²-bench             ❌        ✅        ✅        ✅       ✅       ✅       ✅
AgentWorld           ✅        ❌        ✅        ✅       ✅       ❌       ❌
AgentBench           ❌        ❌        ⚠️        ❌       ❌       ❌       ✅
WebArena             ❌        ❌        ❌        ❌       ❌       ❌       ✅
SWE-bench            ❌        ❌        ✅        ❌       ❌       ❌       ✅
GAIA                 ❌        ❌        ❌        ❌       ❌       ❌       ✅
MultiAgentBench      ✅        ❌        ⚠️        ❌       ❌       ❌       ❌

Legend: ✅ = Yes  ⚠️ = Partial  ❌ = No

Key τ²-bench advantages: Dual-Control (Dec-POMDP), RL Support (Gymnasium), Leaderboard (taubench.com)
Key AgentWorld advantages: True Multi-Agent (N>2), Custom Apps (JSON), Quality Scoring
```
