# ADR-021: App Benchmark & Evaluation Framework

## Status
Proposed

## Date
2026-01-27

## Dependencies
- **ADR-017**: Simulated Apps Framework (app execution)
- **ADR-018**: App Studio Backend (dynamic apps)
- **ADR-019**: App Definition Schema (logic language)
- **ADR-020**: τ-bench Evaluation Framework (task-based evaluation)

## Context

### Problem Statement
As users create custom apps in the App Studio, there's no systematic way to evaluate app quality, measure agent performance with apps, or benchmark app behavior. We need a framework for:

1. **App Quality Assessment**: Is the app well-defined? Are actions consistent?
2. **Agent Performance Evaluation**: How well do agents use the app?
3. **Regression Testing**: Do app changes break expected behavior?

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-21-01 | App Quality Metrics | Must | Measurable quality criteria for app definitions |
| REQ-21-02 | Test Scenario Runner | Must | Execute predefined test scenarios against apps |
| REQ-21-03 | Agent Evaluation | Should | Measure agent competency with apps |
| REQ-21-04 | Benchmark Suite | Should | Standard benchmark apps for comparison |
| REQ-21-05 | Regression Detection | Should | Detect behavior changes between versions |
| REQ-21-06 | Coverage Analysis | Should | Measure action/logic coverage with path enumeration |
| REQ-21-07 | Export Results | Should | Export evaluation results for analysis |

## Decision

### App Quality Metrics

Every app definition can be scored on the following dimensions:

| Metric | Weight | Description | Scoring |
|--------|--------|-------------|---------|
| **Completeness** | 25% | All required fields populated | 0-100 based on field coverage |
| **Documentation** | 20% | Actions have descriptions | % of actions with descriptions |
| **Validation** | 20% | Actions validate inputs | % of actions with VALIDATE blocks |
| **Error Handling** | 15% | Logic handles error cases | % of paths with ERROR blocks |
| **State Safety** | 10% | No unbounded state growth | Specific rules (see below) |
| **Consistency** | 10% | Naming conventions followed | snake_case compliance, etc. |

**Quality Score Calculation:**

```python
def calculate_quality_score(app: AppDefinition) -> QualityReport:
    scores = {
        "completeness": score_completeness(app),
        "documentation": score_documentation(app),
        "validation": score_validation(app),
        "error_handling": score_error_handling(app),
        "state_safety": score_state_safety(app),
        "consistency": score_consistency(app),
    }

    weights = {
        "completeness": 0.25,
        "documentation": 0.20,
        "validation": 0.20,
        "error_handling": 0.15,
        "state_safety": 0.10,
        "consistency": 0.10,
    }

    overall = sum(scores[k] * weights[k] for k in scores)

    return QualityReport(
        overall_score=overall,
        dimension_scores=scores,
        suggestions=generate_suggestions(scores)
    )
```

#### State Safety Rules (Detailed)

The "State Safety" dimension uses specific heuristic rules rather than vague analysis:

```python
@dataclass
class StateSafetyRule:
    rule_id: str
    name: str
    check: Callable[[AppDefinition], tuple[bool, str]]
    weight: float  # Contribution to state safety score

STATE_SAFETY_RULES = [
    StateSafetyRule(
        rule_id="no_unbounded_arrays",
        name="No Unbounded Array Growth",
        check=check_bounded_arrays,
        weight=0.30
    ),
    StateSafetyRule(
        rule_id="no_recursive_state",
        name="No Self-Referential State",
        check=check_no_recursive_state,
        weight=0.20
    ),
    StateSafetyRule(
        rule_id="max_state_depth",
        name="Maximum Nesting Depth ≤ 5",
        check=lambda app: check_max_depth(app, max_depth=5),
        weight=0.15
    ),
    StateSafetyRule(
        rule_id="array_size_limits",
        name="Arrays Have Size Limits",
        check=check_array_limits,
        weight=0.20
    ),
    StateSafetyRule(
        rule_id="no_dynamic_keys",
        name="No Dynamic Object Keys from User Input",
        check=check_no_dynamic_keys,
        weight=0.15
    ),
]

def check_bounded_arrays(app: AppDefinition) -> tuple[bool, str]:
    """Check that arrays in state schema have bounds or cleanup logic."""
    for field in app.state_schema:
        if field.type == "array":
            # Check for max_items in schema
            if not field.max_items:
                # Check for cleanup logic in actions
                has_cleanup = any(
                    action_has_array_cleanup(action, field.name)
                    for action in app.actions
                )
                if not has_cleanup:
                    return False, f"Array '{field.name}' has no size limit or cleanup"
    return True, "All arrays are bounded"

def check_no_recursive_state(app: AppDefinition) -> tuple[bool, str]:
    """Check for self-referential state structures."""
    for field in app.state_schema:
        if field.type == "object" and field.properties:
            if has_self_reference(field, app.state_schema):
                return False, f"Field '{field.name}' has self-reference"
    return True, "No recursive state structures"

def check_max_depth(app: AppDefinition, max_depth: int) -> tuple[bool, str]:
    """Check maximum nesting depth of state schema."""
    for field in app.state_schema:
        depth = calculate_depth(field)
        if depth > max_depth:
            return False, f"Field '{field.name}' has depth {depth} > {max_depth}"
    return True, f"All fields within depth limit of {max_depth}"

def check_array_limits(app: AppDefinition) -> tuple[bool, str]:
    """Check that arrays have explicit size limits."""
    unlimited_arrays = []
    for field in app.state_schema:
        if field.type == "array" and not field.max_items:
            unlimited_arrays.append(field.name)
    if unlimited_arrays:
        return False, f"Arrays without limits: {unlimited_arrays}"
    return True, "All arrays have size limits"

def check_no_dynamic_keys(app: AppDefinition) -> tuple[bool, str]:
    """Check that object keys aren't derived from user input."""
    for action in app.actions:
        for block in action.logic:
            if block.type == "update":
                if uses_param_as_key(block.target):
                    return False, f"Action '{action.name}' uses param as object key"
    return True, "No dynamic object keys from user input"
```

**Quality Thresholds:**

| Level | Score Range | Meaning |
|-------|-------------|---------|
| Excellent | 90-100 | Production-ready, well-documented |
| Good | 70-89 | Functional, minor improvements possible |
| Acceptable | 50-69 | Works but has gaps |
| Needs Work | 0-49 | Missing critical elements |

### Test Scenario Format

Test scenarios define expected behavior sequences:

```yaml
# scenarios/payment_transfer.yaml
name: "Basic Transfer Test"
description: "Test that transfers work correctly between agents"
app_id: "paypal"

setup:
  agents: ["alice", "bob"]
  initial_state:
    per_agent:
      alice:
        balance: 1000
        transactions: []
      bob:
        balance: 500
        transactions: []
    shared: {}

steps:
  - name: "Alice transfers to Bob"
    agent: "alice"
    action: "transfer"
    params:
      to: "bob"
      amount: 100
      note: "Test transfer"
    expect:
      success: true
      data:
        new_balance: 900
      state:
        alice.balance: 900
        bob.balance: 600

  - name: "Insufficient funds fails"
    agent: "alice"
    action: "transfer"
    params:
      to: "bob"
      amount: 10000
    expect:
      success: false
      error_contains: "Insufficient funds"
      state:
        alice.balance: 900  # unchanged
        bob.balance: 600    # unchanged

  - name: "Self-transfer fails"
    agent: "alice"
    action: "transfer"
    params:
      to: "alice"
      amount: 50
    expect:
      success: false
      error_contains: "yourself"

assertions:
  - "Final alice.balance == 900"
  - "Final bob.balance == 600"
  - "len(alice.transactions) == 1"
  - "len(bob.transactions) == 0"  # Bob didn't initiate
```

### Test Runner Implementation

> **Architecture Note:** To avoid fragmented execution engines, `ScenarioRunner`
> is implemented as a thin wrapper around the shared `ExecutionEngine` from ADR-017.
> ADR-020's `TaskRunner` uses the same engine. See [Execution Engine Unification](#execution-engine-unification).

```python
@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    steps_passed: int
    steps_total: int
    failures: list[StepFailure]
    duration_ms: float
    partial_credit: float  # Shared with ADR-020 TrialResult

@dataclass
class StepFailure:
    step_name: str
    expected: dict
    actual: dict
    error: str

class ScenarioRunner:
    """Executes test scenarios against apps.

    Uses shared ExecutionEngine (ADR-017) to avoid duplication with TaskRunner.
    """

    def __init__(self, app: DynamicApp, engine: ExecutionEngine = None):
        self.app = app
        self.engine = engine or get_default_execution_engine()

    async def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        # Delegate to shared execution engine
        execution_result = await self.engine.execute_sequence(
            app=self.app,
            steps=[
                ExecutionStep(
                    agent_id=step.agent,
                    action=step.action,
                    params=step.params,
                    expectations=step.expect
                )
                for step in scenario.steps
            ],
            initial_state=scenario.setup.initial_state,
            stop_on_failure=scenario.stop_on_failure
        )

        # Convert to ScenarioResult format
        return ScenarioResult(
            scenario_name=scenario.name,
            passed=execution_result.all_passed,
            steps_passed=execution_result.steps_completed,
            steps_total=len(scenario.steps),
            failures=execution_result.failures,
            duration_ms=execution_result.duration_ms,
            partial_credit=execution_result.partial_credit
        )
```

#### Execution Engine Unification

Both ADR-020 (TaskRunner) and ADR-021 (ScenarioRunner) execute actions and verify state. To avoid duplication:

```python
# src/agentworld/apps/execution.py (shared engine from ADR-017)

class ExecutionEngine:
    """Shared execution engine for all evaluation frameworks.

    Used by:
    - TaskRunner (ADR-020): Task-based evaluation with pass^k
    - ScenarioRunner (ADR-021): App testing scenarios
    - DualControlRunner (ADR-020.1): Dual-control evaluation
    """

    async def execute_sequence(
        self,
        app: BaseSimulatedApp,
        steps: list[ExecutionStep],
        initial_state: dict,
        stop_on_failure: bool = True,
        checkpoints: list[Checkpoint] = None  # From ADR-020
    ) -> ExecutionResult:
        """Execute a sequence of actions with state verification."""
        state = initial_state
        completed = 0
        failures = []

        for i, step in enumerate(steps):
            # Check any checkpoints at this position
            if checkpoints:
                await self._verify_checkpoints(checkpoints, i, state)

            result = await app.execute(
                agent_id=step.agent_id,
                action=step.action,
                params=step.params,
                state=state
            )

            if step.expectations:
                passed, failure = self._verify(result, step.expectations, state)
                if not passed:
                    failures.append(failure)
                    if stop_on_failure:
                        break

            if result.success:
                completed += 1
                state = result.state_after

        return ExecutionResult(
            all_passed=len(failures) == 0,
            steps_completed=completed,
            steps_total=len(steps),
            failures=failures,
            final_state=state,
            partial_credit=completed / len(steps) if steps else 1.0
        )
```

### Semantic Coherence Checking

Beyond syntactic validation (action→expected), we check if the app "makes sense":

```python
@dataclass
class SemanticCoherenceResult:
    """LLM-based semantic analysis of app definition."""
    coherent: bool
    score: float  # 0.0-1.0
    issues: list[SemanticIssue]
    suggestions: list[str]

@dataclass
class SemanticIssue:
    severity: str  # "error", "warning", "info"
    location: str  # e.g., "action:transfer.description"
    issue: str     # What's wrong
    suggestion: str  # How to fix

async def check_semantic_coherence(app: AppDefinition) -> SemanticCoherenceResult:
    """Use LLM to check if app definition is semantically coherent.

    Checks:
    1. Action names match descriptions
    2. Parameter names are meaningful
    3. Error messages are helpful
    4. State field names match their purpose
    5. Overall app cohesion
    """
    prompt = f"""Analyze this app definition for semantic coherence.

App: {app.name}
Description: {app.description}
Category: {app.category}

Actions:
{format_actions_for_prompt(app.actions)}

State Schema:
{format_state_for_prompt(app.state_schema)}

Check for:
1. Do action names clearly describe what they do?
2. Are parameter names meaningful and consistent?
3. Do error messages help users understand what went wrong?
4. Does the app description match its actual capabilities?
5. Are there any confusing or contradictory elements?

Return JSON with:
- coherent: boolean
- score: 0.0-1.0
- issues: [{severity, location, issue, suggestion}]
- suggestions: [improvement suggestions]
"""

    response = await llm.generate(prompt, response_format="json")
    return SemanticCoherenceResult(**response)

# Example issues detected:
# - "Action 'getData' description says 'Delete user data'" (name/desc mismatch)
# - "Parameter 'x' in action 'transfer' - unclear purpose" (vague naming)
# - "Error message 'Error occurred' provides no actionable info" (unhelpful error)
```

### Agent Evaluation Framework

Evaluate how well agents interact with apps:

```python
@dataclass
class AgentEvaluation:
    """Results of agent evaluation with an app."""
    agent_id: str
    app_id: str

    # Success metrics
    actions_attempted: int
    actions_succeeded: int
    success_rate: float

    # Efficiency metrics
    actions_to_goal: int         # Actions taken to reach goal
    optimal_actions: int          # Minimum possible actions
    efficiency_ratio: float       # optimal / actual

    # Error patterns
    validation_errors: int        # Input validation failures
    logic_errors: int             # Business logic errors
    repeated_errors: int          # Same error multiple times

    # Comprehension
    used_all_actions: bool        # Agent tried all available actions
    appropriate_action_choice: float  # % of times chose correct action

@dataclass
class EvaluationTask:
    """A goal-oriented task for agent evaluation."""
    name: str
    description: str
    app_id: str
    initial_state: AppState
    goal_condition: str  # Expression that must become true
    max_steps: int
    optimal_steps: int  # Known optimal solution length
```

### Benchmark Suite

Standard benchmark apps for comparing implementations:

| Benchmark App | Category | Actions | Complexity | Purpose |
|---------------|----------|---------|------------|---------|
| `bench_counter` | Minimal | 2 | Low | Baseline state mutation |
| `bench_wallet` | Payment | 4 | Medium | Standard payment flow |
| `bench_inventory` | Shopping | 6 | Medium | CRUD with constraints |
| `bench_messaging` | Communication | 5 | Medium | Multi-party interaction |
| `bench_workflow` | Custom | 8 | High | Complex branching logic |

**Benchmark Metrics:**

```python
@dataclass
class BenchmarkResult:
    app_id: str
    timestamp: str

    # Performance
    avg_action_latency_ms: float
    p99_action_latency_ms: float
    actions_per_second: float

    # Correctness
    scenario_pass_rate: float
    edge_case_coverage: float

    # Quality
    quality_score: float
    dimension_scores: dict[str, float]
```

### Regression Detection

Compare behavior between app versions:

```python
@dataclass
class RegressionReport:
    old_version: int
    new_version: int

    # Behavioral changes
    new_failures: list[str]       # Tests that newly fail
    fixed_tests: list[str]        # Tests that now pass
    output_changes: list[OutputDiff]  # Different but valid outputs

    # Performance changes
    latency_change_pct: float     # Positive = slower
    throughput_change_pct: float  # Positive = faster

    # Quality changes
    quality_score_delta: float
    dimension_changes: dict[str, float]

    is_breaking: bool  # True if new_failures > 0

def detect_regressions(
    app_old: AppDefinition,
    app_new: AppDefinition,
    scenarios: list[TestScenario]
) -> RegressionReport:
    """Compare behavior between two app versions."""
    ...
```

### Coverage Analysis

Coverage analysis measures how thoroughly test scenarios exercise the app's logic:

```python
@dataclass
class CoverageReport:
    """Coverage analysis results."""
    action_coverage: float      # % of actions called
    branch_coverage: float      # % of BRANCH paths taken
    logic_block_coverage: float # % of logic blocks executed
    uncovered_actions: list[str]
    uncovered_branches: list[BranchInfo]
    recommendations: list[str]

@dataclass
class BranchInfo:
    action_name: str
    block_index: int
    branch_type: str  # "then" | "else"
    condition: str

def analyze_coverage(
    app: AppDefinition,
    execution_traces: list[ExecutionTrace]
) -> CoverageReport:
    """Analyze test coverage using execution traces.

    Path enumeration algorithm:
    1. Build control flow graph for each action
    2. Track which paths were executed in traces
    3. Calculate coverage percentages
    """
    # Step 1: Enumerate all possible paths
    all_paths = {}
    for action in app.actions:
        cfg = build_control_flow_graph(action.logic)
        all_paths[action.name] = enumerate_paths(cfg)

    # Step 2: Track executed paths from traces
    executed = {action.name: set() for action in app.actions}
    for trace in execution_traces:
        for step in trace.steps:
            if step.action in executed:
                executed[step.action].add(step.path_id)

    # Step 3: Calculate coverage
    action_coverage = len([
        a for a in app.actions
        if a.name in executed and len(executed[a.name]) > 0
    ]) / len(app.actions)

    total_branches = sum(
        count_branches(a.logic) for a in app.actions
    )
    executed_branches = sum(
        len(executed[a.name]) for a in app.actions
    )
    branch_coverage = executed_branches / total_branches if total_branches > 0 else 1.0

    # Step 4: Find uncovered items
    uncovered_actions = [
        a.name for a in app.actions
        if a.name not in executed or len(executed[a.name]) == 0
    ]

    uncovered_branches = []
    for action in app.actions:
        for i, block in enumerate(action.logic):
            if block.type == "branch":
                if f"{action.name}:{i}:then" not in executed[action.name]:
                    uncovered_branches.append(BranchInfo(
                        action_name=action.name,
                        block_index=i,
                        branch_type="then",
                        condition=block.condition
                    ))
                if f"{action.name}:{i}:else" not in executed[action.name]:
                    uncovered_branches.append(BranchInfo(
                        action_name=action.name,
                        block_index=i,
                        branch_type="else",
                        condition=block.condition
                    ))

    return CoverageReport(
        action_coverage=action_coverage,
        branch_coverage=branch_coverage,
        logic_block_coverage=calculate_block_coverage(app, execution_traces),
        uncovered_actions=uncovered_actions,
        uncovered_branches=uncovered_branches,
        recommendations=generate_coverage_recommendations(uncovered_actions, uncovered_branches)
    )

def build_control_flow_graph(logic: list[LogicBlock]) -> ControlFlowGraph:
    """Build CFG from logic blocks for path enumeration."""
    cfg = ControlFlowGraph()
    current_node = cfg.entry

    for i, block in enumerate(logic):
        node = cfg.add_node(block, index=i)
        current_node.add_edge(node)

        if block.type == "branch":
            # Create two paths: then and else
            then_node = cfg.add_node(f"then_{i}")
            else_node = cfg.add_node(f"else_{i}")
            node.add_edge(then_node, label="then")
            node.add_edge(else_node, label="else")
            # Both paths converge after branch
            merge_node = cfg.add_node(f"merge_{i}")
            then_node.add_edge(merge_node)
            else_node.add_edge(merge_node)
            current_node = merge_node
        elif block.type in ("return", "error"):
            # Terminal nodes
            cfg.exit_nodes.append(node)
            current_node = None
        else:
            current_node = node

    return cfg

def enumerate_paths(cfg: ControlFlowGraph) -> list[str]:
    """Enumerate all paths through CFG (DFS)."""
    paths = []

    def dfs(node, path):
        path.append(node.id)
        if node in cfg.exit_nodes or not node.edges:
            paths.append(":".join(path))
            return
        for edge in node.edges:
            dfs(edge.target, path.copy())

    dfs(cfg.entry, [])
    return paths
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/app-definitions/:id/quality` | Get quality score |
| GET | `/api/v1/app-definitions/:id/coverage` | Get coverage report |
| POST | `/api/v1/app-definitions/:id/evaluate` | Run test scenarios |
| POST | `/api/v1/app-definitions/:id/benchmark` | Run benchmark suite |
| GET | `/api/v1/app-definitions/:id/compare/:version` | Compare versions |
| GET | `/api/v1/benchmarks` | List available benchmarks |
| POST | `/api/v1/benchmarks/:id/run` | Run specific benchmark |

### File Structure

```
src/agentworld/
├── apps/
│   └── evaluation/
│       ├── __init__.py
│       ├── quality.py          # Quality scoring
│       ├── scenarios.py        # Scenario parser and runner
│       ├── agent_eval.py       # Agent evaluation
│       ├── benchmarks.py       # Benchmark suite
│       └── regression.py       # Regression detection
├── api/
│   └── routes/
│       └── evaluation.py       # API endpoints
└── data/
    └── benchmarks/
        ├── bench_counter.yaml  # Benchmark app definitions
        ├── bench_wallet.yaml
        └── scenarios/          # Test scenarios
            └── *.yaml
```

## Consequences

### Positive
- Objective quality measurement for apps
- Automated regression testing
- Agent performance insights
- Standard benchmarks for comparison
- Continuous improvement feedback

### Negative
- Additional complexity in app development workflow
- Benchmark maintenance overhead
- Quality metrics may not capture all aspects of "good" apps

### Neutral
- Evaluation is optional (not blocking)
- Benchmarks need periodic updates

---

## Validation Checklist

### REQ-21-01: App Quality Metrics

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-01-01 | Score minimal app | Low score | Missing docs, validation |
| V21-01-02 | Score well-defined app | High score | All dimensions green |
| V21-01-03 | Suggestions generated | Actionable | "Add description to X" |
| V21-01-04 | Consistent scoring | Deterministic | Same app = same score |

### REQ-21-02: Test Scenario Runner

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-02-01 | Run passing scenario | All steps pass | passed=true |
| V21-02-02 | Run failing scenario | Failures captured | failures list populated |
| V21-02-03 | State chains correctly | Intermediate state | Step 2 sees step 1 changes |
| V21-02-04 | Assertions checked | Final state verified | Assertion failures reported |

### REQ-21-03: Agent Evaluation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-03-01 | Track success rate | Accurate count | Matches manual count |
| V21-03-02 | Measure efficiency | Ratio calculated | optimal/actual correct |
| V21-03-03 | Detect error patterns | Patterns identified | Repeated errors flagged |

### REQ-21-04: Benchmark Suite

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-04-01 | All benchmarks exist | 5 benchmark apps | Loadable definitions |
| V21-04-02 | Benchmarks are valid | Quality score > 80 | Self-validating |
| V21-04-03 | Benchmark scenarios pass | 100% pass rate | No failures on reference |

### REQ-21-05: Regression Detection

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-05-01 | No changes | Empty report | No regressions |
| V21-05-02 | Breaking change | is_breaking=true | new_failures populated |
| V21-05-03 | Non-breaking change | is_breaking=false | Behavior unchanged |
| V21-05-04 | Performance change | Deltas calculated | latency_change_pct set |

### REQ-21-06: Coverage Analysis

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-06-01 | Action coverage | Percentage calculated | X/Y actions tested |
| V21-06-02 | Branch coverage | Both paths counted | then/else coverage % |
| V21-06-03 | Uncovered actions | Listed | "transfer never called" |
| V21-06-04 | Uncovered branches | Listed | "action:1:else not taken" |
| V21-06-05 | CFG generation | Graph built | Nodes match logic blocks |
| V21-06-06 | Path enumeration | All paths found | DFS finds all routes |
| V21-06-07 | Recommendations | Generated | "Add test for else branch" |

### REQ-21-07: Export Results

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V21-07-01 | Export JSON | Valid JSON | Parseable output |
| V21-07-02 | Export CSV | Valid CSV | Spreadsheet-compatible |
| V21-07-03 | Export includes all | Complete data | All metrics present |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `src/agentworld/apps/evaluation/quality.py` | Quality scoring |
| `src/agentworld/apps/evaluation/scenarios.py` | Scenario runner |
| `src/agentworld/apps/evaluation/agent_eval.py` | Agent evaluation |
| `src/agentworld/apps/evaluation/benchmarks.py` | Benchmark suite |
| `src/agentworld/apps/evaluation/regression.py` | Regression detection |
| `src/agentworld/api/routes/evaluation.py` | API endpoints |
| `data/benchmarks/bench_*.yaml` | Benchmark apps |
| `data/benchmarks/scenarios/*.yaml` | Test scenarios |

### Modified Files
| File | Changes |
|------|---------|
| `src/agentworld/api/routes/__init__.py` | Register evaluation routes |

---

## UI Reference

See [docs/agentworld-adr-review.jsx](../docs/agentworld-adr-review.jsx) for interactive UI mockups including:
- App Quality Dashboard with dimension scores
- Version comparison and regression detection
- Improvement suggestions view

## References

- ADR-017: Simulated Apps Framework - App execution model
- ADR-018: App Studio Backend - Dynamic app engine
- ADR-019: App Definition Schema - Logic language for apps
- ADR-020: τ-bench Evaluation Framework - Shared ExecutionEngine
