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
| REQ-21-06 | Coverage Analysis | Could | Measure action/logic coverage |
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
| **State Safety** | 10% | No unbounded state growth | Heuristic analysis |
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

```python
@dataclass
class ScenarioResult:
    scenario_name: str
    passed: bool
    steps_passed: int
    steps_total: int
    failures: list[StepFailure]
    duration_ms: float

@dataclass
class StepFailure:
    step_name: str
    expected: dict
    actual: dict
    error: str

class ScenarioRunner:
    """Executes test scenarios against apps."""

    def __init__(self, app: DynamicApp):
        self.app = app

    async def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        state = scenario.setup.initial_state
        failures = []
        steps_passed = 0

        for step in scenario.steps:
            result = await self.app.execute(
                agent_id=step.agent,
                action=step.action,
                params=step.params,
                state=state
            )

            passed, failure = self._check_expectations(
                step, result, state
            )

            if passed:
                steps_passed += 1
                state = result.state_after  # Chain state
            else:
                failures.append(failure)
                if scenario.stop_on_failure:
                    break

        # Run final assertions
        assertion_failures = self._check_assertions(
            scenario.assertions, state
        )
        failures.extend(assertion_failures)

        return ScenarioResult(
            scenario_name=scenario.name,
            passed=len(failures) == 0,
            steps_passed=steps_passed,
            steps_total=len(scenario.steps),
            failures=failures,
            duration_ms=elapsed
        )
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

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/app-definitions/:id/quality` | Get quality score |
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
| V21-06-02 | Logic path coverage | Branches counted | Branch coverage % |
| V21-06-03 | Uncovered actions | Listed | "transfer never called" |

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

## References

- ADR-017: Simulated Apps Framework - App execution model
- ADR-018: App Studio Backend - Dynamic app engine
- ADR-019: App Definition Schema - Logic language for apps
