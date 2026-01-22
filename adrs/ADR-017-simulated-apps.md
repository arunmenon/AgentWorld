# ADR-017: Simulated Application Framework

## Status
Accepted

## Date
2025-01-22

## Dependencies
- **ADR-014**: Plugin Extension (apps as plugins)
- **ADR-011**: Simulation Runtime (execution hooks)
- **ADR-012**: API/Event Schema (app interactions)
- **ADR-008**: Persistence (app data storage)

## Context

### Problem Statement
AgentWorld currently tests agents in conversational scenarios, but real AI assistants need to complete tasks across applications (payments, shopping, email). The AppWorld paper demonstrates significant value in simulating apps for agent testing and training data generation.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-01 | Agent Action Calls | Must | Agents can call app actions like `transfer_money()`, `check_balance()` |
| REQ-02 | Persistent App State | Must | App state (balances, orders) persists across simulation steps |
| REQ-03 | Realistic Outcomes | Must | Actions have realistic outcomes (e.g., insufficient balance → failure) |
| REQ-04 | Pluggable Apps | Should | Add new apps without modifying core framework |
| REQ-05 | Full Audit Trail | Should | Every action logged with timestamp, params, result |
| REQ-06 | Checkpoint Support | Should | App state included in checkpoint/restore |
| REQ-07 | Deterministic Execution | Should | Same seed produces same random outcomes |

## Decision

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATION STEP FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PERCEIVE                                                     │
│     ├─ Agent receives messages from other agents                │
│     └─ Agent receives APP OBSERVATIONS                          │
│        └─ "Your PayPal balance is $500"                         │
│        └─ "You received $50 from Bob"                           │
│                                                                  │
│  2. ACT                                                          │
│     ├─ Agent generates response text                            │
│     └─ Agent MAY include APP_ACTION directives                  │
│        └─ "APP_ACTION: paypal.transfer(to=bob, amount=25)"      │
│                                                                  │
│  3. COMMIT                                                       │
│     ├─ Message recorded in conversation                         │
│     ├─ APP ACTIONS parsed and executed                          │
│     │   ├─ Validate action (balance check, etc.)                │
│     │   ├─ Update app state (deduct/add balance)                │
│     │   └─ Record in audit log                                  │
│     └─ Events emitted for UI/webhooks                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### App Plugin Protocol

```python
@runtime_checkable
class SimulatedAppPlugin(Protocol):
    """Protocol for simulated applications."""

    @property
    def app_id(self) -> str:
        """Unique ID: 'paypal', 'amazon'"""
        ...

    @property
    def name(self) -> str:
        """Display name: 'PayPal'"""
        ...

    @property
    def description(self) -> str:
        """For agent context"""
        ...

    def get_actions(self) -> list[AppAction]:
        """Available actions with schemas"""
        ...

    async def initialize(self, sim_id: str, agents: list[str], config: dict) -> None:
        """Set up initial state (accounts, etc.)"""
        ...

    async def execute(self, agent_id: str, action: str, params: dict) -> AppResult:
        """Execute action, return result"""
        ...

    async def get_agent_state(self, agent_id: str) -> dict:
        """Get agent's view of app state"""
        ...

    async def get_observations(self, agent_id: str) -> list[AppObservation]:
        """Get pending observations for agent"""
        ...

    def get_state_snapshot(self) -> bytes:
        """Serialize full state for checkpoint"""
        ...

    def restore_state(self, snapshot: bytes) -> None:
        """Restore from checkpoint"""
        ...
```

### Data Structures

```python
@dataclass
class AppAction:
    """Definition of an app action."""
    name: str                    # "transfer"
    description: str             # "Send money to another user"
    parameters: dict[str, ParamSpec]  # {"amount": {"type": "number", "min": 0.01}}
    returns: dict[str, Any]      # {"transaction_id": "string"}

@dataclass
class AppResult:
    """Result of executing an action."""
    success: bool
    data: dict[str, Any] | None  # {"transaction_id": "tx-123", "new_balance": 450}
    error: str | None            # "Insufficient funds"

@dataclass
class AppObservation:
    """Observation injected into agent's perception."""
    app_id: str
    message: str                 # "Your balance is $500"
    data: dict[str, Any]         # Structured data
    priority: int = 0            # Higher = more important
```

### Database Schema

```sql
-- App instances per simulation
CREATE TABLE app_instances (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    app_id TEXT NOT NULL,
    config JSON NOT NULL,
    state JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log of all actions
CREATE TABLE app_action_log (
    id TEXT PRIMARY KEY,
    app_instance_id TEXT NOT NULL REFERENCES app_instances(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    step INTEGER NOT NULL,
    action_name TEXT NOT NULL,
    params JSON NOT NULL,
    success INTEGER NOT NULL,    -- 0 or 1
    result JSON,
    error TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_app_instances_sim ON app_instances(simulation_id);
CREATE INDEX idx_action_log_instance ON app_action_log(app_instance_id);
CREATE INDEX idx_action_log_agent ON app_action_log(agent_id);
CREATE INDEX idx_action_log_step ON app_action_log(step);
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/apps` | List active apps in simulation |
| GET | `/simulations/{id}/apps/{app_id}` | Get app state summary |
| GET | `/simulations/{id}/apps/{app_id}/agents/{agent_id}` | Get agent's app state |
| GET | `/simulations/{id}/apps/{app_id}/actions` | Get action audit log |

### Event Types

```python
class AppEventType(Enum):
    APP_INITIALIZED = "app.initialized"
    APP_ACTION_REQUESTED = "app.action.requested"
    APP_ACTION_EXECUTED = "app.action.executed"
    APP_ACTION_FAILED = "app.action.failed"
    APP_OBSERVATION_SENT = "app.observation.sent"
```

### Action Directive Syntax

Agents include actions in their messages using a specific syntax:

```
APP_ACTION: <app_id>.<action_name>(<param1>=<value1>, <param2>=<value2>)
```

Examples:
```
APP_ACTION: paypal.transfer(to="bob@email.com", amount=50.00, note="Dinner")
APP_ACTION: paypal.check_balance()
APP_ACTION: amazon.search_products(query="laptop", max_price=1000)
```

Multiple actions can be included in a single message on separate lines.

## Consequences

### Positive
- Agents can be tested on real-world task completion, not just chat
- Training data includes successful task execution patterns
- Plugin system allows community-contributed apps
- Full audit trail enables detailed analysis and debugging
- Checkpoint support allows resuming complex multi-step scenarios

### Negative
- Adds complexity to simulation loop
- State management increases checkpoint size
- Action parsing introduces potential failure points
- Agents need to learn action syntax (prompt engineering required)

### Neutral
- Requires updating agent system prompts to describe available apps/actions
- May need to iterate on action directive syntax based on LLM capabilities

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `src/agentworld/apps/__init__.py` | Package init, exports |
| `src/agentworld/apps/base.py` | Protocol + base classes + registry |
| `src/agentworld/apps/paypal.py` | PayPal app implementation |
| `src/agentworld/apps/parser.py` | Action directive parser |
| `src/agentworld/api/routes/apps.py` | API endpoints |
| `src/agentworld/api/schemas/apps.py` | API schemas |
| `tests/apps/__init__.py` | Test package |
| `tests/apps/test_paypal.py` | PayPal unit tests |
| `tests/apps/test_parser.py` | Parser unit tests |
| `tests/integration/test_app_simulation.py` | Integration test |
| `examples/paypal_simulation.yaml` | Example config |

### Modified Files
| File | Changes |
|------|---------|
| `src/agentworld/persistence/models.py` | Add `AppInstanceModel`, `AppActionLogModel` |
| `src/agentworld/simulation/runner.py` | App lifecycle integration |
| `src/agentworld/simulation/checkpoint.py` | App state in `SimulationState` |
| `src/agentworld/api/websocket.py` | App event types |
| `src/agentworld/api/app.py` | Register apps router |
| `pyproject.toml` | Add `agentworld.apps` entry point |

---

## Validation Checklist

This section provides test scenarios to verify each requirement is met.

### REQ-01: Agent Action Calls

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V01-01 | Agent message contains `APP_ACTION: paypal.check_balance()` | Action parsed and executed | Check `AppActionLog` table has entry with `action_name="check_balance"` |
| V01-02 | Agent message contains `APP_ACTION: paypal.transfer(to="bob", amount=50)` | Transfer executed, balances updated | Query both agent balances via API, verify sender -50, receiver +50 |
| V01-03 | Agent message with multiple actions | All actions executed in order | Check `AppActionLog` has multiple entries for same step |
| V01-04 | Agent message with invalid action syntax | Error logged, simulation continues | Check error in action log, simulation status remains RUNNING |
| V01-05 | Agent calls non-existent action | Error returned, logged | `AppResult.success=False`, `error="Unknown action"` |

```bash
# Verification command
curl http://localhost:8000/api/v1/simulations/{id}/apps/paypal/actions | jq '.actions[-1]'
```

### REQ-02: Persistent App State

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V02-01 | Transfer in step 1, check balance in step 3 | Balance reflects transfer | GET agent state shows updated balance |
| V02-02 | Multiple transfers across steps | Cumulative balance correct | Sum of all transfers matches final balance |
| V02-03 | Restart simulation server, query state | State preserved in DB | App instance state JSON matches expectations |
| V02-04 | Request money creates pending request | Request visible in subsequent steps | `pending_requests` array contains request |

```bash
# Verification command
curl http://localhost:8000/api/v1/simulations/{id}/apps/paypal/agents/{agent_id}
```

### REQ-03: Realistic Outcomes

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V03-01 | Transfer amount > balance | Action fails with "Insufficient funds" | `AppResult.success=False`, `error` contains "Insufficient" |
| V03-02 | Transfer to non-existent user | Action fails with "User not found" | `AppResult.success=False`, `error` contains "not found" |
| V03-03 | Transfer negative amount | Action fails validation | `AppResult.success=False`, `error` contains "positive" |
| V03-04 | Pay already-resolved request | Action fails | `AppResult.error` contains "already resolved" |
| V03-05 | Valid transfer | Success with transaction ID | `AppResult.success=True`, `data.transaction_id` exists |

```python
# Test code snippet
result = await paypal.execute(agent_id, "transfer", {"to": "bob", "amount": 99999})
assert result.success is False
assert "Insufficient" in result.error
```

### REQ-04: Pluggable Apps

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V04-01 | Register new app via entry point | App available in registry | `AppRegistry.get("new_app")` returns instance |
| V04-02 | Configure simulation with custom app | App initialized | `app_instances` table has entry |
| V04-03 | App without optional methods | Uses defaults, no crash | Simulation runs successfully |
| V04-04 | Two apps in same simulation | Both function independently | Both have separate state, both actions work |

```toml
# pyproject.toml entry point test
[project.entry-points."agentworld.apps"]
custom_app = "my_package:CustomApp"
```

### REQ-05: Full Audit Trail

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V05-01 | Execute action | Entry in `app_action_log` | Query table, verify all fields populated |
| V05-02 | Failed action | Log includes error details | `error` column contains message |
| V05-03 | Query audit via API | Returns chronological list | GET `/apps/{id}/actions` returns ordered list |
| V05-04 | Filter audit by agent | Only that agent's actions | Query with `?agent_id=X` returns filtered results |
| V05-05 | Log includes step number | Can correlate with messages | `step` field matches simulation step |

```sql
-- Verification query
SELECT * FROM app_action_log
WHERE app_instance_id = ?
ORDER BY executed_at DESC
LIMIT 10;
```

### REQ-06: Checkpoint Support

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V06-01 | Create checkpoint after transfers | App state in checkpoint | Checkpoint blob contains `app_states` key |
| V06-02 | Restore checkpoint | App state restored | Balances match checkpoint state |
| V06-03 | Continue simulation after restore | Actions use restored state | New transfers work with restored balances |
| V06-04 | Multiple apps in checkpoint | All apps restored | Each app's state matches checkpoint |

```python
# Test code snippet
checkpoint = create_checkpoint(simulation)
assert "app_states" in checkpoint.state.to_dict()
assert "paypal" in checkpoint.state.to_dict()["app_states"]

# Restore and verify
restore_checkpoint(checkpoint)
state = await paypal.get_agent_state(agent_id)
assert state["balance"] == expected_balance
```

### REQ-07: Deterministic Execution

| Test ID | Test Scenario | Expected Result | How to Verify |
|---------|---------------|-----------------|---------------|
| V07-01 | Same seed, same initial balances | Balances identical | Run twice with seed, compare initial state |
| V07-02 | Random elements (if any) use seed | Reproducible | Transaction IDs or random delays match |
| V07-03 | Different seeds | Different results | States differ between runs |

```bash
# Run twice with same seed
agentworld run config.yaml --seed 12345
agentworld run config.yaml --seed 12345
# Compare final states
```

### End-to-End Test Scenarios

| Test ID | Scenario | Steps | Verification |
|---------|----------|-------|--------------|
| E2E-01 | Bill splitting | 1. Alice has $100, Bob has $100<br>2. Alice: "I'll pay for dinner" + `transfer(to=bob, amount=30)`<br>3. Bob receives observation "You received $30"<br>4. Bob: "Thanks!" | Alice=$70, Bob=$130, audit log has 1 entry |
| E2E-02 | Payment request flow | 1. Alice requests $50 from Bob<br>2. Bob receives observation<br>3. Bob pays request<br>4. Alice receives notification | Request resolved, balances updated |
| E2E-03 | Insufficient funds recovery | 1. Alice tries to send $200 (has $100)<br>2. Fails with error<br>3. Alice sends $50 instead<br>4. Success | First action failed, second succeeded |

---

## PayPal App Specification

### App ID
`paypal`

### Actions

| Action | Description | Parameters | Returns | Validations |
|--------|-------------|------------|---------|-------------|
| `check_balance` | View current balance | - | `{balance: number}` | Agent must exist |
| `transfer` | Send money | `to: string, amount: number, note?: string` | `{transaction_id, new_balance}` | amount > 0, amount <= balance, recipient exists |
| `request_money` | Request payment | `from: string, amount: number, note?: string` | `{request_id}` | amount > 0, target exists |
| `view_transactions` | Recent transactions | `limit?: number` | `{transactions: [...]}` | limit <= 100 |
| `pay_request` | Pay pending request | `request_id: string` | `{transaction_id, new_balance}` | request exists, is pending, payer has funds |
| `decline_request` | Decline request | `request_id: string` | `{success: bool}` | request exists, is pending |

### Initial Configuration

```yaml
apps:
  - id: paypal
    config:
      initial_balance: 1000.00
      transaction_fee: 0.00
      daily_limit: 10000.00
```

### Observations Generated

| Trigger | Observation Message | Data |
|---------|---------------------|------|
| Received transfer | "You received ${amount} from {sender}" | `{type: "received", amount, from, transaction_id}` |
| New money request | "{requester} requested ${amount} from you: '{note}'" | `{type: "request", request_id, amount, from, note}` |
| Request paid | "{payer} paid your ${amount} request" | `{type: "request_paid", request_id, amount}` |
| Request declined | "{decliner} declined your ${amount} request" | `{type: "request_declined", request_id}` |

---

## References

- [AppWorld Paper](https://arxiv.org/abs/2407.18901) - Inspiration for simulated app testing
- ADR-011: Simulation Runtime - Three-phase execution model
- ADR-014: Plugin Extension - Plugin registration pattern
