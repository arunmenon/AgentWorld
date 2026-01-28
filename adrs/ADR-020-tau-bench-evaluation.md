# ADR-020: τ-bench Inspired Evaluation Framework

## Status
Implemented

## Date
2026-01-26

## Dependencies
- **ADR-010**: Evaluation Metrics (existing evaluation infrastructure)
- **ADR-017**: Simulated Apps Framework (app state for verification)
- **ADR-018**: App Studio Backend (dynamic app definitions)

## Context

### Problem Statement
AgentWorld has robust behavioral evaluation (ADR-010) for measuring message quality, persona adherence, and A/B testing. However, it lacks **task-based evaluation** with:
- Deterministic success criteria (did the agent complete the task?)
- Reliability measurement (does the agent succeed consistently?)
- Structured error analysis (why did the agent fail?)
- Policy compliance verification (did the agent follow rules?)

### Research Foundation
This ADR adopts patterns from [τ-bench](https://github.com/sierra-research/tau-bench) (Sierra Research, 2024):
- **pass^k metric**: Measures consistency across multiple trials
- **Goal state verification**: Compares final DB state to expected state
- **Fault classification**: Categorizes failures by assignment and type
- **Policy system**: Explicit rules agents must follow

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-20-01 | Pass^k Metric | Must | Measure reliability across k repeated trials |
| REQ-20-02 | Goal State Verification | Must | Compare final app state to expected state |
| REQ-20-03 | Task Definitions | Must | Define tasks with ground truth outcomes |
| REQ-20-04 | Fault Classification | Must | Classify failures by assignment and type |
| REQ-20-05 | Policy Engine | Should | Evaluate agent compliance with rules |
| REQ-20-06 | Scenario Library | Should | Predefined benchmark scenarios |
| REQ-20-07 | Trajectory Export | Should | Export runs for replay/analysis |
| REQ-20-08 | Integration with ADR-010 | Must | Complement existing evaluation system |

## Decision

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EVALUATION FRAMEWORK ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      TASK LAYER                                   │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │   Task     │  │  Task Set  │  │  Scenario  │                  │   │
│  │  │ Definition │  │ (Benchmark)│  │  Library   │                  │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                  │   │
│  └────────┼───────────────┼───────────────┼─────────────────────────┘   │
│           │               │               │                              │
│           ▼               ▼               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     EXECUTION LAYER                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │   Task     │  │ Reliability│  │  State     │                  │   │
│  │  │   Runner   │  │  Evaluator │  │  Capturer  │                  │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                  │   │
│  └────────┼───────────────┼───────────────┼─────────────────────────┘   │
│           │               │               │                              │
│           ▼               ▼               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    VERIFICATION LAYER                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │   State    │  │   Fault    │  │  Policy    │                  │   │
│  │  │  Verifier  │  │ Classifier │  │  Engine    │                  │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                  │   │
│  └────────┼───────────────┼───────────────┼─────────────────────────┘   │
│           │               │               │                              │
│           ▼               ▼               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      REPORTING LAYER                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │  Pass^k    │  │   Error    │  │ Compliance │                  │   │
│  │  │  Report    │  │  Analysis  │  │   Report   │                  │   │
│  │  └────────────┘  └────────────┘  └────────────┘                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Pass^k Reliability Metric

**Concept:** Run same task k times, measure consistency.

```python
# Mathematical definition
# pass^k = C(c,k) / C(n,k)
# where n = total trials, c = successes, k = threshold

def compute_pass_k(n: int, c: int, k: int) -> float:
    """Compute pass^k = C(c,k) / C(n,k)"""
    from math import comb
    if k > n or k > c:
        return 0.0
    return comb(c, k) / comb(n, k)
```

**Interpretation:**
- `pass^1 = 0.75`: Agent succeeds 75% of the time (traditional metric)
- `pass^4 = 0.45`: 45% chance of 4 consecutive successes (reliability)
- Gap between pass^1 and pass^k exposes fragility

### 2. Goal State Verification

**Concept:** Compare final app state hash to expected state hash.

```python
@dataclass
class StateVerificationResult:
    """Result of goal state verification."""
    state_match: bool           # r_action: final state matches expected
    output_match: bool          # r_output: required outputs present
    success: bool               # r_action AND r_output
    state_diff: list[StateDiff] # Detailed differences
    missing_outputs: list[str]  # Which outputs were missing

    # Partial credit support (addresses binary outcome limitation)
    partial_credit: float       # 0.0-1.0 based on steps completed
    steps_completed: int        # How many steps completed before failure
    steps_total: int            # Total steps in task
```

#### Partial Credit Scoring

Binary pass/fail loses nuance (task failing at step 9/10 scores same as 1/10). Partial credit addresses this:

```python
def calculate_partial_credit(
    steps_completed: int,
    steps_total: int,
    state_diff: list[StateDiff]
) -> float:
    """Calculate partial credit for incomplete tasks.

    Combines:
    - Step completion ratio (50% weight)
    - State progress ratio (50% weight)
    """
    step_ratio = steps_completed / steps_total if steps_total > 0 else 0

    # Calculate how close final state is to goal state
    if not state_diff:
        state_ratio = 1.0
    else:
        total_fields = len(state_diff)
        correct_fields = sum(1 for d in state_diff if d.matches)
        state_ratio = correct_fields / total_fields

    return (step_ratio * 0.5) + (state_ratio * 0.5)
```

### 3. Task Definitions with Ground Truth

```python
@dataclass
class Checkpoint:
    """Intermediate verification point for long-running tasks."""
    checkpoint_id: str
    name: str
    after_step: int           # Verify after this step number
    expected_state: dict      # Partial state that must be true
    description: str          # What this checkpoint verifies

@dataclass
class TaskDefinition:
    """Complete task definition with ground truth."""
    task_id: str
    name: str
    description: str
    domain: str               # 'payment', 'shopping', etc.
    difficulty: str           # 'easy', 'medium', 'hard'

    # Initial conditions
    simulation_config: dict
    initial_app_states: dict[str, dict]

    # Agent instruction
    agent_instruction: str

    # Ground truth for evaluation
    expected_final_states: dict[str, dict]
    expected_actions: list[ExpectedAction]
    required_outputs: list[str]

    # Policy rules to follow
    policy_rules: list[str]

    # Checkpoints for long-running tasks (addresses visibility gap)
    checkpoints: list[Checkpoint] = field(default_factory=list)
```

#### Checkpoints for Long-Running Tasks

Long tasks have no visibility into progress before completion. Checkpoints provide intermediate verification:

```python
# Example: Multi-step payment task with checkpoints
task = TaskDefinition(
    task_id="multi_party_payment",
    name="Multi-Party Payment Split",
    # ... other fields ...
    checkpoints=[
        Checkpoint(
            checkpoint_id="balance_checked",
            name="Balance Verification",
            after_step=2,
            expected_state={"agent_checked_balance": True},
            description="Agent verified sufficient funds before split"
        ),
        Checkpoint(
            checkpoint_id="first_transfer_done",
            name="First Transfer Complete",
            after_step=5,
            expected_state={"alice.balance": 900, "bob.balance": 550},
            description="First party received their share"
        ),
        Checkpoint(
            checkpoint_id="all_notified",
            name="All Parties Notified",
            after_step=8,
            expected_state={"notifications_sent": 3},
            description="All recipients were notified"
        ),
    ]
)
```

### 4. Fault Classification

```python
class FaultAssignment(str, Enum):
    """Who is responsible for the failure."""
    AGENT = "agent"
    ENVIRONMENT = "environment"
    TASK = "task"

class FaultType(str, Enum):
    """What type of error occurred."""
    GOAL_NOT_ACHIEVED = "goal_not_achieved"
    WRONG_ACTION = "wrong_action"
    WRONG_PARAMS = "wrong_params"
    MISSING_ACTION = "missing_action"
    POLICY_VIOLATION = "policy_violation"
    REASONING_ERROR = "reasoning_error"
```

### 5. Policy Engine

```python
@dataclass
class PolicyRule:
    """A rule the agent must follow."""
    rule_id: str
    name: str
    description: str
    category: str  # 'confirmation', 'limit', 'eligibility', 'prohibition'
    trigger_actions: list[str]
    conditions: list[PolicyCondition]  # Typed conditions (see DSL below)
    requirements: list[str]
    severity: str  # 'error', 'warning'
```

#### Policy Condition DSL

Policy conditions use a defined grammar (similar to ADR-019 logic language):

```python
@dataclass
class PolicyCondition:
    """Structured policy condition with explicit operators."""
    field: str          # Path to value: "params.amount", "state.balance"
    operator: str       # One of: eq, ne, gt, gte, lt, lte, in, not_in, matches, exists
    value: Any          # Comparison value (or list for in/not_in)
    negate: bool = False  # NOT this condition

# Supported operators:
POLICY_OPERATORS = {
    "eq": lambda a, b: a == b,           # Equal
    "ne": lambda a, b: a != b,           # Not equal
    "gt": lambda a, b: a > b,            # Greater than
    "gte": lambda a, b: a >= b,          # Greater than or equal
    "lt": lambda a, b: a < b,            # Less than
    "lte": lambda a, b: a <= b,          # Less than or equal
    "in": lambda a, b: a in b,           # Value in list
    "not_in": lambda a, b: a not in b,   # Value not in list
    "matches": lambda a, b: re.match(b, str(a)),  # Regex match
    "exists": lambda a, b: a is not None,  # Field exists
    "contains": lambda a, b: b in a,     # String/list contains
}

# Example: "Confirm transfers over $100"
PolicyRule(
    rule_id="confirm_large_transfer",
    name="Confirm Large Transfers",
    trigger_actions=["transfer"],
    conditions=[
        PolicyCondition(field="params.amount", operator="gt", value=100)
    ],
    requirements=["Agent must ask for confirmation before executing"],
    severity="error"
)

# Example: "Only VIP customers can use premium features"
PolicyRule(
    rule_id="vip_only_premium",
    name="VIP-Only Premium Features",
    trigger_actions=["enable_premium", "unlock_feature"],
    conditions=[
        PolicyCondition(field="state.customer.tier", operator="in", value=["gold", "platinum"])
    ],
    requirements=["Verify customer VIP status before enabling"],
    severity="error"
)
```

#### Compound Conditions

For complex rules, use compound conditions with AND/OR logic:

```python
@dataclass
class CompoundCondition:
    """Combine multiple conditions."""
    logic: str  # "and" | "or"
    conditions: list[PolicyCondition | CompoundCondition]

# Example: "Refunds over $50 require manager approval AND reason"
PolicyRule(
    rule_id="refund_approval",
    conditions=[
        CompoundCondition(
            logic="and",
            conditions=[
                PolicyCondition(field="params.amount", operator="gt", value=50),
                CompoundCondition(
                    logic="or",
                    conditions=[
                        PolicyCondition(field="params.reason", operator="exists", value=True),
                        PolicyCondition(field="params.manager_override", operator="eq", value=True)
                    ]
                )
            ]
        )
    ]
)
```

### Database Schema

```sql
-- Task definitions
CREATE TABLE task_definitions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    domain TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    simulation_config JSON NOT NULL,
    initial_app_states JSON,
    agent_instruction TEXT NOT NULL,
    expected_final_states JSON NOT NULL,
    expected_actions JSON,
    required_outputs JSON,
    policy_rules JSON,
    estimated_steps INTEGER,
    tags JSON,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task sets (benchmarks)
CREATE TABLE task_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    task_ids JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trial results (extended with partial credit and retry tracking)
CREATE TABLE trial_results (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    trial_number INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    state_match BOOLEAN,
    output_match BOOLEAN,
    partial_credit REAL,           -- NEW: 0.0-1.0 score
    steps_completed INTEGER,       -- NEW: steps before failure
    steps_total INTEGER,           -- NEW: total steps in task
    actions_retried INTEGER,       -- NEW: retry tracking
    total_retry_count INTEGER,     -- NEW: sum of all retries
    duration_seconds REAL,
    token_count INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pass^k metrics
CREATE TABLE pass_k_metrics (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    total_trials INTEGER NOT NULL,
    successful_trials INTEGER NOT NULL,
    pass_1 REAL,
    pass_2 REAL,
    pass_4 REAL,
    pass_8 REAL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fault classifications
CREATE TABLE fault_classifications (
    id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    fault_assignment TEXT NOT NULL,
    fault_type TEXT NOT NULL,
    description TEXT,
    evidence JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policy rules
CREATE TABLE policy_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    domain TEXT,
    trigger_actions JSON,
    conditions JSON,
    requirements JSON,
    severity TEXT DEFAULT 'error',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks` | Create task definition |
| GET | `/api/v1/tasks` | List tasks |
| GET | `/api/v1/tasks/{task_id}` | Get task definition |
| POST | `/api/v1/tasks/{task_id}/run` | Run single trial |
| POST | `/api/v1/tasks/{task_id}/evaluate` | Run k trials, compute pass^k |
| GET | `/api/v1/tasks/{task_id}/results` | Get trial results |
| GET | `/api/v1/tasks/{task_id}/metrics` | Get pass^k metrics |
| GET | `/api/v1/tasks/{task_id}/faults` | Get fault classifications |
| POST | `/api/v1/task-sets` | Create benchmark task set |
| POST | `/api/v1/task-sets/{name}/run` | Run full benchmark |
| GET | `/api/v1/task-sets/{name}/report` | Get benchmark report |
| POST | `/api/v1/policies` | Create policy rule |
| POST | `/api/v1/policies/check` | Check trajectory compliance |

### File Structure

```
src/agentworld/
├── tasks/
│   ├── __init__.py           # Module exports
│   ├── definitions.py        # TaskDefinition, PolicyRule dataclasses
│   ├── runner.py             # TaskRunner execution
│   ├── repository.py         # Database operations
│   └── scenarios/            # Built-in scenarios
│       ├── __init__.py
│       ├── payment.py        # 8 payment tasks
│       └── shopping.py       # 9 shopping tasks
├── evaluation/
│   ├── reliability.py        # Pass^k computation
│   ├── state_verification.py # Goal state checking
│   ├── fault_classifier.py   # Failure categorization
│   └── policy_engine.py      # Compliance checking
└── api/
    ├── routes/tasks.py       # REST endpoints
    └── schemas/tasks.py      # Request/response models
```

### Built-in Scenarios

| Domain | Tasks | Description |
|--------|-------|-------------|
| Payment | 8 | Transfers, balance checks, multi-party, error handling |
| Shopping | 9 | Search, cart, checkout, budget constraints |

## Implementation

### Implemented Files

| File | Lines | Purpose |
|------|-------|---------|
| `tasks/__init__.py` | ~50 | Module exports |
| `tasks/definitions.py` | ~850 | Core dataclasses |
| `tasks/runner.py` | ~540 | Task execution |
| `tasks/repository.py` | ~760 | Database CRUD |
| `tasks/scenarios/payment.py` | ~425 | 8 payment tasks |
| `tasks/scenarios/shopping.py` | ~430 | 9 shopping tasks |
| `evaluation/reliability.py` | ~300 | Pass^k metrics |
| `evaluation/state_verification.py` | ~420 | State comparison |
| `evaluation/fault_classifier.py` | ~460 | Fault analysis |
| `evaluation/policy_engine.py` | ~570 | Policy compliance |
| `api/routes/tasks.py` | ~835 | API endpoints |
| `api/schemas/tasks.py` | ~430 | Pydantic schemas |
| `persistence/models.py` | +300 | Database models |

**Total: ~5,370 lines of new code**

### 6. Retry Semantics

Should a retried action count against pass^k? τ-bench allows retries within a trial. We define explicit retry behavior:

```python
@dataclass
class RetryConfig:
    """Configuration for retry behavior within trials."""
    max_retries_per_action: int = 2   # Max times to retry a failed action
    retry_delay_ms: int = 100          # Delay between retries
    count_retries_as_steps: bool = True  # Retries count toward step limit

@dataclass
class TrialResult:
    """Extended trial result with retry tracking."""
    trial_id: str
    success: bool
    partial_credit: float         # NEW: 0.0-1.0

    # Retry tracking
    actions_attempted: int
    actions_retried: int          # How many actions needed retry
    total_retry_count: int        # Sum of all retries

    # For pass^k calculation:
    # - A trial with retries can still be "successful"
    # - Excessive retries may indicate fragility even if successful
```

#### Retry Behavior Rules

| Scenario | Behavior | pass^k Impact |
|----------|----------|---------------|
| Action succeeds first try | Normal | Counts as success |
| Action succeeds after retry | Success with note | Counts as success |
| Action fails after max retries | Trial fails | Counts as failure |
| Within-trial retry | Allowed | No penalty |
| Cross-trial retry | Not allowed | Each trial independent |

```python
# Example: Action with retries
async def execute_with_retry(
    action: str,
    params: dict,
    config: RetryConfig
) -> ActionResult:
    for attempt in range(config.max_retries_per_action + 1):
        result = await execute_action(action, params)
        if result.success:
            return result.with_retry_count(attempt)
        if attempt < config.max_retries_per_action:
            await asyncio.sleep(config.retry_delay_ms / 1000)
    return result.with_failure()
```

## Consequences

### Positive
- Deterministic success criteria for benchmarking
- Reliability measurement exposes fragility (pass^k)
- Structured error analysis guides improvement
- Compatible with existing evaluation system
- Enables regression testing
- Partial credit provides nuanced scoring beyond binary pass/fail
- Checkpoints enable progress monitoring for long tasks
- Explicit retry semantics match τ-bench behavior

### Negative
- Requires task definition effort
- Policy compliance adds complexity
- Multiple trial runs increase compute cost

### Constraints

**Agent ID Immutability**

Per ADR-020.1, agent IDs are immutable within a simulation. This constraint is critical for:
- Per-agent state isolation (state keys use `{app_id}:{agent_id}`)
- Coordination tracking (handoffs reference stable agent IDs)
- Fault attribution (errors must be traceable to specific agents)

```python
# Agent IDs must not change during simulation execution
# If agent identity must change, use the migration function in ADR-020.1
# and log the change for audit purposes
```

**State Consistency**

When using per-agent state (`state_type=per_agent`):
- Each agent's state is isolated using the key format `{app_id}:{agent_id}`
- State updates by one agent never affect another agent's state
- State orphaning can occur if agent IDs change without migration

## Integration with ADR-010

ADR-020 **complements** ADR-010 (existing evaluation):

| Aspect | ADR-010 | ADR-020 |
|--------|---------|---------|
| Focus | Message quality | Task completion |
| Metrics | Behavioral, coherence | Pass^k, state match |
| Output | Quality scores (0-1) | Binary + fault analysis |
| Use case | "How good was this?" | "Did agent complete task?" |

---

## Validation Checklist

### REQ-20-01: Pass^k Metric ✅

| Test | Result |
|------|--------|
| 8 trials, 6 succeed → pass^1=0.75 | ✅ Verified |
| pass^8=0.0 when c<8 | ✅ Verified |
| Interpretation generated | ✅ "Fragile: High success rate but low reliability" |

### REQ-20-02: Goal State Verification ✅

| Test | Result |
|------|--------|
| Matching states → state_match=True | ✅ Verified |
| Hash comparison works | ✅ Verified |
| State diff generated | ✅ Verified |
| Output checking works | ✅ Verified |

### REQ-20-03: Task Definitions ✅

| Test | Result |
|------|--------|
| TaskDefinition dataclass | ✅ Implemented |
| CRUD API endpoints | ✅ Implemented |
| 17 built-in tasks | ✅ Payment + Shopping |

### REQ-20-04: Fault Classification ✅

| Test | Result |
|------|--------|
| FaultAssignment enum | ✅ agent/environment/task |
| FaultType enum | ✅ 10 fault types |
| Rule-based classifier | ✅ Implemented |
| Fault summary aggregation | ✅ Implemented |

### REQ-20-05: Policy Engine ✅

| Test | Result |
|------|--------|
| PolicyRule dataclass | ✅ Implemented |
| PAYMENT_POLICIES | ✅ 4 rules |
| SHOPPING_POLICIES | ✅ 2 rules |
| Trajectory compliance check | ✅ Verified |
| Violations detected | ✅ Confirmed |

### REQ-20-06: Scenario Library ✅

| Test | Result |
|------|--------|
| Payment scenarios | ✅ 8 tasks |
| Shopping scenarios | ✅ 9 tasks |
| Difficulty levels | ✅ easy/medium/hard |
| TaskSet benchmarks | ✅ 2 benchmark sets |

---

## Related ADRs

- **ADR-010**: Evaluation Metrics - Behavioral evaluation
- **ADR-017**: Simulated Apps - App execution
- **ADR-020.1**: Dual-Control Extension - τ²-bench compatibility (extends this ADR)
- **ADR-021**: App Benchmark & Quality - App definition evaluation (separate)

## UI Reference

See [docs/agentworld-adr-review.jsx](../docs/agentworld-adr-review.jsx) for interactive UI mockups including:
- Task Evaluation Dashboard with pass^k visualization
- Fault classification summary view
- Trial grid visualization
