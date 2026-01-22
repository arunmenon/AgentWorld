# ADR-017 Research Comparison: Simulated Apps Framework

## Executive Summary

This document compares AgentWorld's ADR-017 Simulated Apps implementation against the AppWorld paper and related research from 2024-2026 on agent environments, tool use benchmarks, and simulated application testing.

---

## 1. AppWorld Paper Analysis

**Paper:** [AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents](https://arxiv.org/abs/2407.18901) (ACL 2024 Best Resource Paper)

### Key AppWorld Features

| Feature | AppWorld | ADR-017 (AgentWorld) | Gap Analysis |
|---------|----------|----------------------|--------------|
| **Scale** | 9 apps, 457 APIs, 100+ DB tables | 1 app (PayPal), 6 actions | Significant gap - need more apps |
| **Simulated Population** | 106 people with relationships | Per-simulation agents only | No persistent world population |
| **API Interaction** | RESTful APIs via FastAPI | In-process method calls | Different approach (both valid) |
| **Database** | SQLite per app, differential storage | JSON state in single table | Simpler, may need expansion |
| **Evaluation** | State-based unit tests | Action success/failure | Need richer evaluation |
| **Task Benchmark** | 750 curated tasks | No benchmark tasks | Major gap |
| **Execution Mode** | IPython shell with `apis` namespace | APP_ACTION directive in messages | Different paradigm |

### AppWorld Architecture Decisions We Should Adopt

1. **State-Based Evaluation**: AppWorld evaluates by comparing final database state, not process. Our implementation tracks action success but doesn't have ground-truth goal states.

2. **Differential State Storage**: AppWorld stores only diffs from base state to optimize disk usage for task variations.

3. **Rich Relational Data**: AppWorld populates apps with interconnected user data (family relationships, transaction histories, playlists) making tasks realistic.

4. **API Documentation Formats**: AppWorld provides docs in 3 formats: standard JSON, OpenAI function-calling schema, and raw OpenAPI spec.

---

## 2. Related Benchmarks Comparison

### Tool Use & Function Calling Benchmarks

| Benchmark | Focus | Key Innovation | Relevance to ADR-017 |
|-----------|-------|----------------|---------------------|
| **BFCL** (Berkeley) | Function calling accuracy | AST-based evaluation, multi-turn support | Our parser is simpler; could adopt AST validation |
| **ToolLLM/ToolBench** | Real API usage | 16K+ APIs, auto-generated instructions | Scale inspiration for app variety |
| **MetaTool** | Tool selection awareness | Tests when NOT to use tools | We don't test tool abstention |
| **ToolEmu** | Safety in tool use | LLM-emulated sandbox, risk scoring | Safety evaluation missing in ADR-017 |

### Environment & Sandbox Benchmarks

| Benchmark | Environment Type | Evaluation | Relevance |
|-----------|-----------------|------------|-----------|
| **WebArena** | Web browser simulation | State-based goal verification | Similar state-tracking approach |
| **OSWorld** | Full OS (Ubuntu/Windows/macOS) | Graph-based partial credit | Our binary success/fail is limited |
| **τ-bench** (Sierra) | Retail/Airline customer service | Policy compliance + state | We lack domain-specific policies |
| **InterCode** | Bash/SQL/Python REPL | POMDP with execution feedback | Our agents don't see execution feedback inline |

### Agent Safety Benchmarks (2025)

| Benchmark | Focus | Key Feature |
|-----------|-------|-------------|
| **ToolEmu** | Risky tool behaviors | 36 high-stakes tools, 144 test cases |
| **RedTeamCUA** | Adversarial computer use | Hybrid VM + Docker sandbox |
| **AgentHarm** | Harmful action prevention | ICLR 2025, misuse risk quantification |
| **SafeToolBench** | Tool utilization safety | Prospective safety evaluation |

---

## 3. Gap Analysis: ADR-017 vs Research

### Critical Gaps

| Gap | Impact | Priority | Recommendation |
|-----|--------|----------|----------------|
| **Single App** | Limited testing scenarios | High | Add 3-5 more apps (Amazon, Gmail, Calendar, Venmo) |
| **No Benchmark Tasks** | Can't measure agent progress | High | Create curated task suite with ground-truth states |
| **No Safety Evaluation** | Can't detect risky behaviors | High | Add risk scoring, harmful action detection |
| **Binary Evaluation** | Miss partial progress | Medium | Implement graph-based partial credit |
| **No Policy Compliance** | Can't test rule-following | Medium | Add domain-specific rules (like τ-bench) |
| **No Population Simulation** | Unrealistic isolation | Medium | Add persistent simulated users |

### Architecture Gaps

| Current Design | Research Best Practice | Action |
|----------------|----------------------|--------|
| APP_ACTION in message text | Structured function calling | Consider dual-mode support |
| JSON state blob | Normalized relational tables | OK for now, watch scale |
| Sync execution only | Async with execution feedback | Add streaming results |
| No tool abstention testing | MetaTool-style awareness tests | Add "should not act" scenarios |

---

## 4. Compliance Checklist: AppWorld Alignment

### Core Requirements (from AppWorld)

- [x] **Sandboxed Execution**: Actions execute in isolated simulation state
- [x] **State Persistence**: App state persists across steps
- [x] **Action Logging**: Full audit trail of all actions
- [x] **Checkpoint/Restore**: Can save and resume simulation state
- [ ] **Multi-App Coordination**: Only one app implemented
- [ ] **Rich User Relationships**: No simulated population
- [ ] **Benchmark Tasks**: No curated evaluation tasks
- [ ] **Differential Storage**: Not optimized for task variations

### Evaluation Requirements

- [x] **Action Success/Failure**: Binary outcome tracking
- [ ] **State-Based Goals**: No ground-truth goal states
- [ ] **Partial Credit**: No intermediate progress scoring
- [ ] **Collateral Damage Detection**: Don't check for unintended side effects
- [ ] **Safety Scoring**: No risk quantification

### API Design Requirements

- [x] **Typed Parameters**: ParamSpec with validation
- [x] **Error Messages**: Descriptive failure reasons
- [ ] **OpenAPI Spec Generation**: Not auto-generated
- [ ] **Multiple Doc Formats**: Only internal format

---

## 5. Recommendations

### Immediate (Phase 1)

1. **Add More Apps**: Implement 2-3 additional simulated apps
   - `amazon`: Shopping cart, orders, product search
   - `gmail`: Send/receive emails, drafts, contacts
   - `calendar`: Events, reminders, scheduling

2. **Create Benchmark Tasks**: Define 50+ curated tasks with:
   - Natural language instruction
   - Initial state snapshot
   - Expected final state (for evaluation)
   - Difficulty rating

3. **State-Based Evaluation**: Add goal verification
   ```python
   @dataclass
   class TaskGoal:
       expected_state: dict  # What DB should look like
       required_actions: list[str] | None  # Optional action sequence
       forbidden_actions: list[str]  # Actions that should NOT happen
   ```

### Medium-Term (Phase 2)

4. **Safety Evaluation**: Add risk scoring inspired by ToolEmu
   - Define high-stakes actions (delete account, large transfers)
   - Score agent behavior on 0-3 risk scale
   - Track "collateral damage" (unintended state changes)

5. **Policy Compliance**: Add domain rules like τ-bench
   ```yaml
   policies:
     - name: "Large Transfer Confirmation"
       condition: "transfer.amount > 500"
       required: "Must confirm with user before executing"
   ```

6. **Partial Credit Scoring**: Implement graph-based evaluation
   - Break complex tasks into sub-goals
   - Award credit for completed sub-goals even if final goal fails

### Long-Term (Phase 3)

7. **Simulated Population**: Create persistent world with:
   - 50-100 simulated users with profiles
   - Relationship graph (family, friends, colleagues)
   - Historical data (past transactions, emails, orders)

8. **Structured Function Calling**: Support both paradigms
   - Current: `APP_ACTION: paypal.transfer(...)` in text
   - New: JSON function call format for compatible models

9. **OpenAPI Spec Generation**: Auto-generate docs from AppAction definitions

---

## 6. Research Papers Referenced

### Core Papers
- [AppWorld](https://arxiv.org/abs/2407.18901) - ACL 2024, Stony Brook NLP
- [τ-bench](https://arxiv.org/abs/2406.12045) - Sierra AI, 2024
- [ToolEmu](https://toolemu.com/) - ICLR 2024 Spotlight
- [BFCL](https://gorilla.cs.berkeley.edu/leaderboard.html) - Berkeley, ICLR 2025

### Environment Benchmarks
- [WebArena](https://webarena.dev/) - CMU, 2024
- [OSWorld](https://arxiv.org/abs/2404.07972) - NeurIPS 2024
- [InterCode](https://intercode-benchmark.github.io/) - NeurIPS 2023
- [AgentBench](https://arxiv.org/abs/2308.03688) - ICLR 2024

### Safety & Multi-Agent (2025)
- [RedTeamCUA](https://arxiv.org/html/2505.21936) - Adversarial testing
- [AgentHarm](https://proceedings.iclr.cc/paper_files/paper/2025/file/c493d23af93118975cdbc32cbe7323f5-Paper-Conference.pdf) - ICLR 2025
- [AgentTorch](https://www.media.mit.edu/posts/new-paper-on-limits-of-agency-at-aamas-2025/) - MIT Media Lab, AAMAS 2025
- [Terminal-Bench](https://ainativedev.io/news/8-benchmarks-shaping-the-next-generation-of-ai-agents) - Stanford/Laude, May 2025
- [Context-Bench](https://o-mega.ai/articles/the-best-ai-agent-evals-and-benchmarks-full-2025-guide) - Letta, October 2025

### Evaluation Guides
- [O-mega AI Agent Benchmarks Guide 2025](https://o-mega.ai/articles/the-best-ai-agent-evals-and-benchmarks-full-2025-guide)
- [Evidently AI Agent Benchmarks](https://www.evidentlyai.com/blog/ai-agent-benchmarks)
- [KDD 2025 Tutorial: Evaluation of LLM Agents](https://sap-samples.github.io/llm-agents-eval-tutorial/)

---

## 7. Conclusion

ADR-017's current implementation provides a solid foundation that aligns with several AppWorld principles:
- Plugin-based app architecture
- State persistence and checkpointing
- Action logging and audit trails
- Observation injection for agent perception

However, significant gaps exist compared to research best practices:
1. **Scale**: Need more apps and richer simulated data
2. **Evaluation**: Need state-based goals and partial credit scoring
3. **Safety**: Need risk assessment and harmful action detection
4. **Benchmarking**: Need curated task suite for measuring progress

The recommended phased approach will bring ADR-017 into alignment with state-of-the-art agent evaluation research while maintaining backward compatibility with the current implementation.
