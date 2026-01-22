# ADR-018: App Studio Backend - Dynamic App Engine

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **ADR-017**: Simulated Apps Framework (base protocol, action execution)
- **ADR-008**: Persistence (database patterns)
- **ADR-014**: Plugin Extension (plugin registration)

## Context

### Problem Statement
ADR-017 implemented simulated apps as Python code (e.g., `PayPalApp`). To enable non-developers to create apps, we need a system that loads app definitions from JSON/database and executes them dynamically.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-18-01 | Dynamic App Loading | Must | Load app definitions from database instead of Python code |
| REQ-18-02 | Logic Engine | Must | Execute JSON-defined business logic for actions |
| REQ-18-03 | Expression Evaluation | Must | Evaluate expressions like `params.amount <= state.balance` |
| REQ-18-04 | State Management | Must | Manage per-agent and shared app state |
| REQ-18-05 | CRUD API | Must | Create, read, update, delete app definitions |
| REQ-18-06 | Test Endpoint | Should | Execute single action in isolated sandbox |
| REQ-18-07 | Migration Path | Should | Convert existing PayPal app to definition format |
| REQ-18-08 | Backward Compatibility | Should | Support both Python apps and definition-based apps |
| REQ-18-09 | Execution Safety | Must | Timeouts, iteration limits, payload size limits |
| REQ-18-10 | Version Pinning | Must | Simulations pin app version at start |
| REQ-18-11 | Built-in Governance | Must | Enforce read-only/undeletable for system apps |

## Decision

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    APP LOADING FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. REGISTRY LOOKUP                                              │
│     AppRegistry.get(app_id)                                      │
│     ├─ Check Python plugins (entry points)                       │
│     └─ Check database definitions → DynamicApp                   │
│                                                                  │
│  2. DYNAMIC APP INSTANTIATION                                    │
│     DynamicApp(definition: AppDefinition)                        │
│     ├─ Parse actions from JSON                                   │
│     ├─ Initialize state schema                                   │
│     └─ Prepare logic engine                                      │
│                                                                  │
│  3. ACTION EXECUTION                                             │
│     DynamicApp.execute(agent_id, action, params)                 │
│     ├─ Validate parameters against schema                        │
│     ├─ Execute logic steps via LogicEngine                       │
│     │   ├─ VALIDATE blocks → check conditions                    │
│     │   ├─ UPDATE blocks → modify state                          │
│     │   ├─ NOTIFY blocks → create observations                   │
│     │   └─ RETURN/ERROR blocks → produce result                  │
│     └─ Return AppResult                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- App definitions (user-created apps)
CREATE TABLE app_definitions (
    id TEXT PRIMARY KEY,
    app_id TEXT NOT NULL UNIQUE,          -- 'my_payment_app'
    name TEXT NOT NULL,                    -- 'My Payment App'
    description TEXT,
    category TEXT NOT NULL,                -- 'payment', 'shopping', 'communication', 'custom'
    icon TEXT,                             -- emoji or icon key
    version INTEGER DEFAULT 1,             -- for versioning
    definition JSON NOT NULL,              -- full AppDefinition JSON
    is_builtin INTEGER DEFAULT 0,          -- 1 for system apps
    is_active INTEGER DEFAULT 1,           -- soft delete
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT                         -- user ID if multi-user
);

-- Indexes
CREATE INDEX idx_app_def_app_id ON app_definitions(app_id);
CREATE INDEX idx_app_def_category ON app_definitions(category);
CREATE INDEX idx_app_def_active ON app_definitions(is_active);

-- App definition versions (for history)
CREATE TABLE app_definition_versions (
    id TEXT PRIMARY KEY,
    app_definition_id TEXT NOT NULL REFERENCES app_definitions(id),
    version INTEGER NOT NULL,
    definition JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(app_definition_id, version)
);
```

### Core Classes

```python
# src/agentworld/apps/dynamic.py

@dataclass
class AppDefinition:
    """JSON-serializable app definition."""
    app_id: str
    name: str
    description: str
    category: str
    icon: str
    actions: list[ActionDefinition]
    state_schema: list[StateField]
    initial_config: dict[str, Any]

@dataclass
class ActionDefinition:
    """Definition of a single action."""
    name: str
    description: str
    parameters: dict[str, ParamSpec]
    returns: dict[str, Any]
    logic: list[LogicBlock]  # Business logic steps

@dataclass
class LogicBlock:
    """A single logic step."""
    type: Literal["validate", "update", "notify", "return", "error", "branch", "loop"]
    # Type-specific fields...

@dataclass
class AppState:
    """Canonical runtime state structure."""
    per_agent: dict[str, dict[str, Any]]  # {agent_id: {field: value}}
    shared: dict[str, Any]                 # {field: value} - accessible to all agents

class DynamicApp(BaseSimulatedApp):
    """App loaded from JSON definition."""

    def __init__(self, definition: AppDefinition):
        self._definition = definition
        self._logic_engine = LogicEngine()
        self._state = AppState(per_agent={}, shared={})

    @property
    def app_id(self) -> str:
        return self._definition.app_id

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    def get_actions(self) -> list[AppAction]:
        return [
            AppAction(
                name=action.name,
                description=action.description,
                parameters=action.parameters,
                returns=action.returns
            )
            for action in self._definition.actions
        ]

    async def initialize(self, sim_id: str, agents: list[str], config: dict) -> None:
        """Initialize state for all agents based on state_schema."""
        # Initialize per-agent state
        for agent_id in agents:
            self._state.per_agent[agent_id] = self._create_initial_state(config, per_agent=True)
        # Initialize shared state
        self._state.shared = self._create_initial_state(config, per_agent=False)

    async def execute(self, agent_id: str, action: str, params: dict) -> AppResult:
        action_def = self._get_action(action)
        if not action_def:
            return AppResult(success=False, error=f"Unknown action: {action}")

        # Validate parameters
        validation = self._validate_params(params, action_def.parameters)
        if not validation.valid:
            return AppResult(success=False, error=validation.error)

        # Execute logic with canonical context
        # Expression context variables:
        #   - params: action parameters
        #   - agent: current agent's per-agent state (shorthand for state.per_agent[agent_id])
        #   - agents: all agents' per-agent state (state.per_agent)
        #   - shared: shared app state (state.shared)
        #   - config: app configuration
        context = ExecutionContext(
            agent_id=agent_id,
            params=params,
            agent=self._state.per_agent.get(agent_id, {}),
            agents=self._state.per_agent,
            shared=self._state.shared,
            config=self._definition.initial_config,
            observations=[]
        )
        return await self._logic_engine.execute(action_def.logic, context)

    def _get_action(self, name: str) -> ActionDefinition | None:
        for action in self._definition.actions:
            if action.name == name:
                return action
        return None

    def _create_initial_state(self, config: dict, per_agent: bool) -> dict:
        """Create initial state, filtering by perAgent flag."""
        state = {}
        for field in self._definition.state_schema:
            # Only include fields matching the per_agent filter
            if field.perAgent != per_agent:
                continue
            if field.name in config:
                state[field.name] = config[field.name]
            else:
                state[field.name] = field.default
        return state

class LogicEngine:
    """Executes JSON-defined logic."""

    def __init__(self):
        self._evaluator = ExpressionEvaluator()

    async def execute(self, logic: list[LogicBlock], ctx: ExecutionContext) -> AppResult:
        for block in logic:
            result = await self._execute_block(block, ctx)
            if result.should_return:
                return result.value
        return AppResult(success=True, data={})

    async def _execute_block(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        match block.type:
            case "validate":
                return self._execute_validate(block, ctx)
            case "update":
                return self._execute_update(block, ctx)
            case "notify":
                return self._execute_notify(block, ctx)
            case "return":
                return self._execute_return(block, ctx)
            case "error":
                return self._execute_error(block, ctx)
            case "branch":
                return await self._execute_branch(block, ctx)
            case "loop":
                return await self._execute_loop(block, ctx)
            case _:
                raise ValueError(f"Unknown block type: {block.type}")

    def _execute_validate(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        condition = self._evaluator.evaluate(block.condition, ctx)
        if not condition:
            error_msg = self._evaluator.interpolate(block.errorMessage, ctx)
            return BlockResult(should_return=True, value=AppResult(success=False, error=error_msg))
        return BlockResult(should_return=False)

    def _execute_update(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        target_path = block.target
        value = self._evaluator.evaluate(block.value, ctx)

        match block.operation:
            case "set":
                self._set_path(ctx, target_path, value)
            case "add":
                current = self._get_path(ctx, target_path)
                self._set_path(ctx, target_path, current + value)
            case "subtract":
                current = self._get_path(ctx, target_path)
                self._set_path(ctx, target_path, current - value)
            case "append":
                current = self._get_path(ctx, target_path)
                current.append(value)
            case "remove":
                current = self._get_path(ctx, target_path)
                current.remove(value)

        return BlockResult(should_return=False)

    def _execute_notify(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        to = self._evaluator.evaluate(block.to, ctx)
        message = self._evaluator.interpolate(block.message, ctx)
        data = self._evaluator.evaluate_object(block.data, ctx) if block.data else {}

        ctx.observations.append(AppObservation(
            app_id=ctx.app_id,
            agent_id=to,
            message=message,
            data=data
        ))
        return BlockResult(should_return=False)

    def _execute_return(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        value = self._evaluator.evaluate_object(block.value, ctx)
        return BlockResult(
            should_return=True,
            value=AppResult(success=True, data=value, observations=ctx.observations)
        )

    def _execute_error(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        message = self._evaluator.interpolate(block.message, ctx)
        return BlockResult(
            should_return=True,
            value=AppResult(success=False, error=message)
        )

    async def _execute_branch(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        condition = self._evaluator.evaluate(block.condition, ctx)
        branch = block.then if condition else block.get("else", [])

        for sub_block in branch:
            result = await self._execute_block(sub_block, ctx)
            if result.should_return:
                return result
        return BlockResult(should_return=False)

    async def _execute_loop(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        collection = self._evaluator.evaluate(block.collection, ctx)
        item_name = block.item

        for item in collection:
            ctx.loop_vars[item_name] = item
            for sub_block in block.body:
                result = await self._execute_block(sub_block, ctx)
                if result.should_return:
                    return result

        return BlockResult(should_return=False)
```

### API Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/app-definitions` | List all app definitions | `?category=payment&search=pay` | `AppDefinition[]` |
| POST | `/api/v1/app-definitions` | Create new app definition | `AppDefinition` | `AppDefinition` |
| GET | `/api/v1/app-definitions/:id` | Get single app definition | - | `AppDefinition` |
| PATCH | `/api/v1/app-definitions/:id` | Update app definition | Partial `AppDefinition` | `AppDefinition` |
| DELETE | `/api/v1/app-definitions/:id` | Soft-delete app definition | - | `{success: bool}` |
| POST | `/api/v1/app-definitions/:id/test` | Test action in sandbox | `TestRequest` | `TestResult` |
| GET | `/api/v1/app-definitions/:id/versions` | Get version history | - | `Version[]` |
| POST | `/api/v1/app-definitions/:id/duplicate` | Duplicate app | `{new_name}` | `AppDefinition` |

### Test Endpoint Contract (Stateless)

The test endpoint uses a **stateless model** where state is passed in the request and returned in the response. This enables UI-side state management, reset, and import features.

```python
@dataclass
class TestRequest:
    """Request to test an action in sandbox."""
    state: AppState                    # Full state (per_agent + shared)
    agent_id: str                      # Agent executing the action
    action: str                        # Action name
    params: dict[str, Any]             # Action parameters

@dataclass
class TestResult:
    """Result of sandbox action execution."""
    success: bool
    data: dict[str, Any] | None        # Action return data (if success)
    error: str | None                  # Error message (if failure)
    state_after: AppState              # Full state after execution
    observations: list[AppObservation] # Observations generated
```

**Payload limits:**
- Maximum `state` size: 1 MB
- Request timeout: 5 seconds

### File Structure

```
src/agentworld/
├── apps/
│   ├── __init__.py          # Add DynamicApp export
│   ├── base.py              # Unchanged
│   ├── paypal.py            # Unchanged (Python version)
│   ├── parser.py            # Unchanged
│   ├── dynamic.py           # NEW: DynamicApp class
│   ├── logic_engine.py      # NEW: Logic execution engine
│   ├── expression.py        # NEW: Expression evaluator
│   └── definition.py        # NEW: AppDefinition dataclass
├── api/
│   ├── routes/
│   │   ├── apps.py          # Existing (runtime app state)
│   │   └── app_definitions.py  # NEW: CRUD endpoints
│   └── schemas/
│       ├── apps.py          # Existing
│       └── app_definitions.py  # NEW: API schemas
└── persistence/
    └── models.py            # Add AppDefinitionModel
```

### Execution Safety Limits

To prevent runaway execution and resource exhaustion, the LogicEngine enforces these limits:

| Limit | Value | Scope |
|-------|-------|-------|
| `MAX_LOOP_ITERATIONS` | 1000 | Per LOOP block |
| `MAX_NESTED_DEPTH` | 10 | BRANCH/LOOP nesting |
| `EXPRESSION_TIMEOUT_MS` | 100 | Single expression evaluation |
| `ACTION_TIMEOUT_MS` | 5000 | Total action execution |
| `MAX_STATE_SIZE_BYTES` | 1 MB | Per test request |
| `MAX_OBSERVATIONS` | 100 | Per action execution |

```python
class LogicEngine:
    MAX_LOOP_ITERATIONS = 1000
    MAX_NESTED_DEPTH = 10
    EXPRESSION_TIMEOUT_MS = 100
    ACTION_TIMEOUT_MS = 5000

    async def _execute_loop(self, block: LogicBlock, ctx: ExecutionContext) -> BlockResult:
        collection = self._evaluator.evaluate(block.collection, ctx)
        item_name = block.item

        iterations = 0
        for item in collection:
            iterations += 1
            if iterations > self.MAX_LOOP_ITERATIONS:
                return BlockResult(
                    should_return=True,
                    value=AppResult(success=False, error=f"Loop exceeded maximum iterations ({self.MAX_LOOP_ITERATIONS})")
                )
            # ... execute body
```

### Hot Reload Semantics

App definitions can be edited at any time, but **simulations pin to a specific version** at start:

| Scenario | Behavior |
|----------|----------|
| Edit app while simulation running | No effect on running simulation |
| Start new simulation | Uses latest active version |
| Restore checkpoint | Uses version from checkpoint |

```python
# When simulation starts, capture app version
class SimulationRunner:
    async def start(self, config: SimulationConfig):
        for app_config in config.apps:
            # Load and pin the current version
            app_def = await self.db.get_app_definition(app_config.app_id)
            self.pinned_apps[app_config.app_id] = {
                "version": app_def.version,
                "definition": app_def.definition
            }
```

### Built-in App Governance

System apps (marked `is_builtin=1`) have special protections:

| Operation | Built-in Apps | User Apps |
|-----------|---------------|-----------|
| Read | Allowed | Allowed |
| Update | **Denied (403)** | Allowed |
| Delete | **Denied (403)** | Allowed (soft-delete) |
| Duplicate | Allowed | Allowed |
| View in UI | Read-only mode | Full edit |

```python
# Backend enforcement (not just UI)
@router.patch("/app-definitions/{id}")
async def update_app_definition(id: str, updates: AppDefinitionUpdate):
    app = await db.get_app_definition(id)
    if app.is_builtin:
        raise HTTPException(403, "Cannot modify built-in apps")
    # ... proceed with update

@router.delete("/app-definitions/{id}")
async def delete_app_definition(id: str):
    app = await db.get_app_definition(id)
    if app.is_builtin:
        raise HTTPException(403, "Cannot delete built-in apps")
    # ... proceed with soft-delete
```

## Consequences

### Positive
- Non-developers can create apps via UI
- Apps can be versioned and rolled back
- Hot-reload of app definitions (no server restart)
- Enables app marketplace/sharing in future
- Execution safety prevents resource exhaustion

### Negative
- Logic engine adds execution overhead vs native Python
- JSON logic less flexible than Python code
- Need to maintain two app paradigms (Python + Dynamic)

### Neutral
- Existing Python apps continue to work unchanged
- Registry checks Python plugins first, then database

---

## Validation Checklist

### REQ-18-01: Dynamic App Loading

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-01-01 | Create app definition in DB | App loadable via registry | `AppRegistry.get("custom_app")` returns `DynamicApp` |
| V18-01-02 | Load app with actions | All actions accessible | `app.get_actions()` returns defined actions |
| V18-01-03 | Load app with state schema | State initialized correctly | Agent state has schema fields |
| V18-01-04 | Load non-existent app | Returns None gracefully | `AppRegistry.get("nonexistent")` returns `None` |
| V18-01-05 | Load inactive app | Returns None | Soft-deleted apps not loadable |

```python
# Verification code
def test_dynamic_app_loading():
    # Insert definition into DB
    db.insert_app_definition(test_definition)

    # Load via registry
    app = AppRegistry.get("test_app")
    assert isinstance(app, DynamicApp)
    assert app.app_id == "test_app"
    assert len(app.get_actions()) == 2
```

### REQ-18-02: Logic Engine

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-02-01 | Execute VALIDATE block (pass) | Continues to next block | No error, execution proceeds |
| V18-02-02 | Execute VALIDATE block (fail) | Returns error | `AppResult.success=False` |
| V18-02-03 | Execute UPDATE block | State modified | `state["agent"].field` changed |
| V18-02-04 | Execute NOTIFY block | Observation created | `context.observations` has entry |
| V18-02-05 | Execute RETURN block | Returns success with data | `AppResult.success=True, data={...}` |
| V18-02-06 | Execute ERROR block | Returns failure | `AppResult.success=False` |
| V18-02-07 | Execute BRANCH (true path) | Takes yes branch | Correct logic executed |
| V18-02-08 | Execute BRANCH (false path) | Takes no branch | Correct logic executed |
| V18-02-09 | Empty logic | Returns success | Default success result |
| V18-02-10 | Sequential blocks | All executed in order | State reflects all changes |

```python
# Verification code
async def test_logic_engine_validate():
    engine = LogicEngine()
    logic = [
        LogicBlock(type="validate", condition="params.amount > 0", errorMessage="Amount must be positive"),
        LogicBlock(type="return", value={"success": True})
    ]

    # Valid params
    result = await engine.execute(logic, context_with(params={"amount": 50}))
    assert result.success

    # Invalid params
    result = await engine.execute(logic, context_with(params={"amount": -10}))
    assert not result.success
    assert "positive" in result.error
```

### REQ-18-03: Expression Evaluation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-03-01 | Access params | Returns param value | `eval("params.amount")` → 50 |
| V18-03-02 | Access agent state | Returns state value | `eval("agent.balance")` → 1000 |
| V18-03-03 | Access other agent state | Returns other state | `eval("agents['bob'].balance")` → 500 |
| V18-03-04 | Comparison operators | Correct boolean | `eval("params.amount > 0")` → True |
| V18-03-05 | Logical operators | Correct boolean | `eval("a && b")` → True/False |
| V18-03-06 | String interpolation | Correct string | `"Hello ${agent.name}"` → "Hello Alice" |
| V18-03-07 | Built-in functions | Correct result | `generate_id()` → "tx-123..." |
| V18-03-08 | Invalid expression | Graceful error | Returns `EvaluationError` |
| V18-03-09 | Null-safe access | No crash on missing | `eval("agent.missing")` → None |
| V18-03-10 | Arithmetic | Correct math | `eval("agent.balance - params.amount")` |

```python
# Verification code
def test_expression_evaluation():
    evaluator = ExpressionEvaluator()
    context = {"params": {"amount": 50}, "agent": {"balance": 1000, "name": "Alice"}}

    assert evaluator.evaluate("params.amount", context) == 50
    assert evaluator.evaluate("params.amount <= agent.balance", context) == True
    assert evaluator.evaluate("agent.balance - params.amount", context) == 950
```

### REQ-18-04: State Management

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-04-01 | Initialize agent state | State created from schema | Agent has all schema fields |
| V18-04-02 | Update state | State persisted | Value reflects update |
| V18-04-03 | Multiple agents | Independent state | Agent A change doesn't affect B |
| V18-04-04 | Shared state | Shared state works | `state.shared` accessible to all |
| V18-04-05 | State snapshot | Full state serialized | All agents in snapshot |
| V18-04-06 | State restore | State restored correctly | Balances match snapshot |
| V18-04-07 | State diff | Only changes recorded | Diff is minimal |

### REQ-18-05: CRUD API

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-05-01 | Create app definition | Returns created app | `POST /app-definitions` → 201 |
| V18-05-02 | Create with invalid schema | Returns validation error | 400 with error details |
| V18-05-03 | Create duplicate app_id | Returns conflict | 409 |
| V18-05-04 | List all definitions | Returns array | `GET /app-definitions` → [] |
| V18-05-05 | List with category filter | Filtered results | Only matching category |
| V18-05-06 | List with search | Search results | Matches name/description |
| V18-05-07 | Get single definition | Returns definition | `GET /app-definitions/:id` → {} |
| V18-05-08 | Get non-existent | Returns 404 | 404 |
| V18-05-09 | Update definition | Returns updated | `PATCH` → updated fields |
| V18-05-10 | Update read-only fields | Ignored/error | `app_id` can't change |
| V18-05-11 | Delete definition | Soft-deleted | `is_active=0`, still in DB |
| V18-05-12 | Delete builtin | Error | Can't delete system apps |

```bash
# Verification commands
# Create
curl -X POST http://localhost:8000/api/v1/app-definitions \
  -H "Content-Type: application/json" \
  -d '{"app_id": "test", "name": "Test App", ...}'

# List
curl http://localhost:8000/api/v1/app-definitions?category=payment

# Get
curl http://localhost:8000/api/v1/app-definitions/{id}

# Update
curl -X PATCH http://localhost:8000/api/v1/app-definitions/{id} \
  -d '{"name": "Updated Name"}'

# Delete
curl -X DELETE http://localhost:8000/api/v1/app-definitions/{id}
```

### REQ-18-06: Test Endpoint

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-06-01 | Test valid action | Returns success | `POST /test` → success result |
| V18-06-02 | Test with invalid params | Returns validation error | Error details in response |
| V18-06-03 | Test shows state changes | Before/after state | Response includes state diff |
| V18-06-04 | Test shows observations | Observations in response | `observations` array populated |
| V18-06-05 | Test is isolated | No persistent changes | App state unchanged after test |
| V18-06-06 | Test multiple agents | Multi-agent scenario | Test Bob→Alice transfer |

### REQ-18-07: Migration Path

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-07-01 | Export PayPal to JSON | Valid definition | JSON passes schema validation |
| V18-07-02 | Import PayPal definition | Works identically | All actions produce same results |
| V18-07-03 | Side-by-side comparison | Identical behavior | Run same scenarios, compare |

### REQ-18-08: Backward Compatibility

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-08-01 | Python app still works | No regression | All PayPal tests pass |
| V18-08-02 | Mixed simulation | Both app types work | Python + Dynamic in same sim |
| V18-08-03 | Registry priority | Python takes precedence | If both exist, Python wins |

### REQ-18-09: Execution Safety

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-09-01 | Loop exceeds max iterations | Error returned | "Loop exceeded maximum iterations" |
| V18-09-02 | Deeply nested branches | Error returned | "Maximum nesting depth exceeded" |
| V18-09-03 | Expression timeout | Error returned | Execution halts gracefully |
| V18-09-04 | Action timeout | Error returned | Total execution time limited |
| V18-09-05 | Large state payload | Rejected (413) | Payload size enforced |
| V18-09-06 | Too many observations | Capped | Max 100 observations per action |

### REQ-18-10: Version Pinning

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-10-01 | Edit app during simulation | No effect | Running sim uses pinned version |
| V18-10-02 | Start new simulation | Uses latest | New sim gets current version |
| V18-10-03 | Restore checkpoint | Uses checkpoint version | Version matches checkpoint |

### REQ-18-11: Built-in Governance

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V18-11-01 | Update built-in app | 403 Forbidden | Backend rejects update |
| V18-11-02 | Delete built-in app | 403 Forbidden | Backend rejects delete |
| V18-11-03 | Duplicate built-in app | Success | Can duplicate to user app |
| V18-11-04 | UI shows read-only | Correct | Edit button disabled for built-in |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `src/agentworld/apps/dynamic.py` | DynamicApp class |
| `src/agentworld/apps/logic_engine.py` | Logic execution engine |
| `src/agentworld/apps/expression.py` | Expression evaluator |
| `src/agentworld/apps/definition.py` | AppDefinition dataclasses |
| `src/agentworld/api/routes/app_definitions.py` | CRUD API endpoints |
| `src/agentworld/api/schemas/app_definitions.py` | API schemas |
| `tests/apps/test_dynamic.py` | DynamicApp unit tests |
| `tests/apps/test_logic_engine.py` | Logic engine unit tests |
| `tests/apps/test_expression.py` | Expression evaluator tests |

### Modified Files
| File | Changes |
|------|---------|
| `src/agentworld/apps/__init__.py` | Export DynamicApp |
| `src/agentworld/apps/base.py` | Update registry to check DB |
| `src/agentworld/persistence/models.py` | Add AppDefinitionModel |
| `src/agentworld/api/app.py` | Register app_definitions router |

---

## References

- ADR-017: Simulated Apps Framework - Base protocol
- ADR-008: Persistence - Database patterns
- ADR-014: Plugin Extension - Plugin registration
