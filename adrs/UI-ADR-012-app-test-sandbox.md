# UI-ADR-012: App Test Sandbox

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **UI-ADR-010**: App Creation Wizard (Step 4 integration)
- **ADR-018**: App Studio Backend (test endpoint)

## Context

### Problem Statement
Before deploying an app to simulations, users need to verify it works correctly. A sandbox environment allows testing actions, viewing state changes, and debugging logic without affecting real simulations.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-12-01 | Test Agents | Must | Create test agents for sandbox |
| REQ-12-02 | Action Execution | Must | Execute any action |
| REQ-12-03 | Parameter Form | Must | Dynamic form for action params |
| REQ-12-04 | Result Display | Must | Show success/error results |
| REQ-12-05 | State Viewer | Must | Show current app state |
| REQ-12-06 | State Diff | Should | Highlight state changes |
| REQ-12-07 | Execution Log | Should | Log all executed actions |
| REQ-12-08 | Reset State | Should | Reset to initial state |
| REQ-12-09 | Import State | Could | Import custom initial state |
| REQ-12-10 | Stateless API Contract | Must | Align with ADR-018 /test endpoint |
| REQ-12-11 | Payload Size Limits | Should | Warn when state approaches size limits |

## Decision

### Test Sandbox Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Test Sandbox: My Payment App                        [Reset] [Done] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │  EXECUTE ACTION             │  │  CURRENT STATE              │  │
│  │  ─────────────────────────  │  │  ───────────────────────    │  │
│  │                             │  │                             │  │
│  │  Agent:                     │  │  ┌─────────────────────┐   │  │
│  │  ┌───────────────────────┐  │  │  │ 👤 Alice            │   │  │
│  │  │ Alice              ▼  │  │  │  │   balance: $950.00  │   │  │
│  │  └───────────────────────┘  │  │  │   transactions: 1   │   │  │
│  │                             │  │  └─────────────────────┘   │  │
│  │  Action:                    │  │                             │  │
│  │  ┌───────────────────────┐  │  │  ┌─────────────────────┐   │  │
│  │  │ transfer           ▼  │  │  │  │ 👤 Bob              │   │  │
│  │  └───────────────────────┘  │  │  │   balance: $1050.00 │   │  │
│  │                             │  │  │   transactions: 1   │   │  │
│  │  ───────────────────────    │  │  └─────────────────────┘   │  │
│  │  Parameters:                │  │                             │  │
│  │                             │  │  ┌─────────────────────┐   │  │
│  │  to *                       │  │  │ 👤 Charlie          │   │  │
│  │  ┌───────────────────────┐  │  │  │   balance: $1000.00 │   │  │
│  │  │ bob                   │  │  │  │   transactions: 0   │   │  │
│  │  └───────────────────────┘  │  │  └─────────────────────┘   │  │
│  │  Recipient agent ID         │  │                             │  │
│  │                             │  │  ▼ Shared State             │  │
│  │  amount *                   │  │  (none)                     │  │
│  │  ┌───────────────────────┐  │  │                             │  │
│  │  │ 50                    │  │  │  ▼ Configuration            │  │
│  │  └───────────────────────┘  │  │  initial_balance: 1000     │  │
│  │  Min: 0.01, Max: 10000      │  │                             │  │
│  │                             │  └─────────────────────────────┘  │
│  │  note                       │                                   │
│  │  ┌───────────────────────┐  │  ┌─────────────────────────────┐  │
│  │  │ Lunch money           │  │  │  EXECUTION LOG              │  │
│  │  └───────────────────────┘  │  │  ───────────────────────    │  │
│  │  Optional                   │  │                             │  │
│  │                             │  │  10:24:15 Alice              │  │
│  │  [▶ Execute Action]         │  │  ├ Action: transfer          │  │
│  │                             │  │  ├ Params: {to:"bob",        │  │
│  │  ─────────────────────────  │  │  │         amount:50}        │  │
│  │  LAST RESULT                │  │  ├ Result: ✓ Success         │  │
│  │                             │  │  │   tx_id: tx-abc123        │  │
│  │  ┌───────────────────────┐  │  │  └ State Δ:                  │  │
│  │  │ ✓ Success             │  │  │      Alice.balance:         │  │
│  │  │                       │  │  │        $1000 → $950 (-$50)  │  │
│  │  │ transaction_id:       │  │  │      Bob.balance:           │  │
│  │  │   tx-abc12345         │  │  │        $1000 → $1050 (+$50) │  │
│  │  │ new_balance: $950.00  │  │  │                             │  │
│  │  │                       │  │  │  10:23:45 Alice              │  │
│  │  │ [Copy Result]         │  │  │  ├ Action: check_balance     │  │
│  │  └───────────────────────┘  │  │  └ Result: ✓ Success         │  │
│  │                             │  │      balance: $1000          │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Test Agents

Default test agents created for every sandbox session:

| Agent ID | Name | Initial State |
|----------|------|---------------|
| alice | Alice | Balance from config, empty transactions |
| bob | Bob | Balance from config, empty transactions |
| charlie | Charlie | Balance from config, empty transactions |

### State Viewer Component

```
┌─────────────────────┐
│ 👤 Alice            │
│ ───────────────     │
│                     │
│ balance:            │
│   $1000.00          │
│                     │
│ transactions:       │
│   [] (empty)        │
│                     │
│ [Expand All]        │
└─────────────────────┘
```

Expanded view for nested state:

```
┌───────────────────────────────┐
│ 👤 Alice                      │
│ ─────────────────────         │
│                               │
│ balance: $950.00              │
│                               │
│ transactions: (1 item)        │
│   ▼ [0]                       │
│     id: "tx-abc123"           │
│     type: "sent"              │
│     to: "bob"                 │
│     amount: 50                │
│     timestamp: "2026-01-22..."│
│                               │
│ pending_requests: (0 items)   │
│   (empty)                     │
│                               │
└───────────────────────────────┘
```

### State Diff Highlighting

After action execution, show changes:

```
┌─────────────────────┐
│ 👤 Alice            │
│   balance:          │
│     $1000.00        │  ← Gray (old value, strikethrough)
│     $950.00 ✓       │  ← Green (new value)
│   transactions:     │
│     + {id: tx-123,  │  ← Green (added item)
│        type: sent,  │
│        amount: 50}  │
└─────────────────────┘
```

Color coding:
- **Green background**: Added or increased value
- **Red background**: Removed or decreased value
- **Yellow background**: Modified value
- **Strikethrough**: Previous value

### Execution Log Entry

```
┌─────────────────────────────────────────────────────────────────┐
│  10:24:15 Alice                                                 │
│  ├ Action: transfer                                             │
│  ├ Params:                                                      │
│  │   to: "bob"                                                  │
│  │   amount: 50                                                 │
│  │   note: "Lunch money"                                        │
│  ├ Result: ✓ Success                                            │
│  │   transaction_id: "tx-abc12345"                              │
│  │   new_balance: 950                                           │
│  └ State Changes:                                               │
│      Alice.balance: $1000.00 → $950.00 (-$50.00)               │
│      Bob.balance: $1000.00 → $1050.00 (+$50.00)                │
│      Alice.transactions: +1 item                                │
│      Bob (observation): "You received $50 from Alice"          │
└─────────────────────────────────────────────────────────────────┘
```

### Error Result Display

```
┌───────────────────────┐
│ ✗ Error               │
│                       │
│ Insufficient funds    │
│                       │
│ The requested amount  │
│ ($2000) exceeds the   │
│ available balance     │
│ ($950).               │
│                       │
│ [Copy Error]          │
└───────────────────────┘
```

### Component Architecture

```
web/src/components/app-studio/sandbox/
├── TestSandbox.tsx           # Main sandbox container
├── AgentSelector.tsx         # Agent dropdown
├── ActionSelector.tsx        # Action dropdown
├── ParameterForm.tsx         # Dynamic parameter inputs
├── ResultDisplay.tsx         # Action result card
├── StateViewer.tsx           # State tree view
├── StateCard.tsx             # Individual agent state card
├── StateDiff.tsx             # Diff highlighting
├── ExecutionLog.tsx          # Log list
├── ExecutionLogEntry.tsx     # Single log entry
└── hooks/
    ├── useSandbox.ts         # Sandbox state management
    └── useStateDiff.ts       # State diff calculation
```

### TypeScript Interfaces

```typescript
interface SandboxState {
  appDefinition: AppDefinitionDetails;
  agents: string[];
  /** Canonical state per ADR-018 */
  state: AppState;
  executionLog: ExecutionLogEntry[];
  isExecuting: boolean;
  lastResult: ActionResult | null;
  /** Approximate state size in bytes */
  stateSize: number;
  /** Warning if state is large */
  stateSizeWarning?: string;
}

interface ExecutionLogEntry {
  id: string;
  timestamp: Date;
  agentId: string;
  action: string;
  params: Record<string, unknown>;
  result: ActionResult;
  stateBefore: Record<string, Record<string, unknown>>;
  stateAfter: Record<string, Record<string, unknown>>;
  observations: AppObservation[];
}

interface ActionResult {
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
}

interface StateDiff {
  agentId: string;
  changes: FieldChange[];
}

interface FieldChange {
  path: string;
  type: 'added' | 'removed' | 'modified';
  oldValue?: unknown;
  newValue?: unknown;
}

interface SandboxContextValue {
  state: SandboxState;
  selectAgent: (agentId: string) => void;
  selectAction: (actionName: string) => void;
  setParams: (params: Record<string, unknown>) => void;
  executeAction: () => Promise<void>;
  resetState: () => void;
  importState: (state: Record<string, Record<string, unknown>>) => void;
}
```

### API Integration

The test endpoint uses a **stateless model** (per ADR-018). The client owns all state and sends it with each request.

```typescript
/**
 * Execute action in sandbox (stateless - no server-side state)
 *
 * Per ADR-018, the /test endpoint:
 * - Receives full state in request
 * - Returns updated state in response
 * - Does NOT persist any changes
 */
async function testAction(
  definitionId: string,
  request: TestRequest
): Promise<TestResult> {
  const response = await fetch(`/api/v1/app-definitions/${definitionId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    if (response.status === 413) {
      throw new Error('State payload too large. Maximum size is 1MB.');
    }
    throw new Error('Test execution failed');
  }

  return response.json();
}

/**
 * Request to test an action in sandbox (per ADR-018 contract)
 */
interface TestRequest {
  /** Full state including per_agent and shared */
  state: AppState;
  /** Agent executing the action */
  agent_id: string;
  /** Action name */
  action: string;
  /** Action parameters */
  params: Record<string, unknown>;
}

/**
 * Canonical state structure (per ADR-018)
 */
interface AppState {
  per_agent: Record<string, Record<string, unknown>>;
  shared: Record<string, unknown>;
}

/**
 * Result of sandbox action execution (per ADR-018 contract)
 */
interface TestResult {
  /** Whether action succeeded */
  success: boolean;
  /** Action return data (if success) */
  data?: Record<string, unknown>;
  /** Error message (if failure) */
  error?: string;
  /** Full state after execution */
  state_after: AppState;
  /** Observations generated */
  observations: AppObservation[];
}
```

### Payload Size Limits

Per ADR-018, state payloads are limited to **1MB** (`MAX_STATE_SIZE_BYTES`). The UI should:

1. **Track state size**: Calculate approximate JSON size before sending
2. **Warn at 80%**: Show warning when state approaches limit
3. **Block at 100%**: Prevent request and show error

```typescript
const MAX_STATE_SIZE_BYTES = 1024 * 1024; // 1MB
const WARNING_THRESHOLD = 0.8;

function checkStateSize(state: AppState): { ok: boolean; warning?: string } {
  const size = new Blob([JSON.stringify(state)]).size;
  const ratio = size / MAX_STATE_SIZE_BYTES;

  if (ratio >= 1) {
    return {
      ok: false,
      warning: `State exceeds maximum size (${formatBytes(size)} / ${formatBytes(MAX_STATE_SIZE_BYTES)})`
    };
  }

  if (ratio >= WARNING_THRESHOLD) {
    return {
      ok: true,
      warning: `State is ${Math.round(ratio * 100)}% of maximum size`
    };
  }

  return { ok: true };
}
```

**Display:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️ State size warning: 856 KB / 1 MB (86%)                         │
│  Consider reducing transaction history or resetting state.          │
└─────────────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive
- Immediate feedback on logic
- Visual state changes
- Catch errors before deployment
- Log provides audit trail
- Safe testing environment

### Negative
- Test environment may not match production exactly
- Complex state may be hard to visualize
- No persistence between sessions

### Neutral
- State is client-side only during testing
- API performs stateless validation

---

## Validation Checklist

### REQ-12-01: Test Agents

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-01-01 | Default agents exist | Alice, Bob, Charlie | Dropdown has 3 options |
| V12-01-02 | Agents have state | Initial balance shown | $1000 per agent |
| V12-01-03 | Select different agent | Dropdown works | Agent changes in form |

### REQ-12-02: Action Execution

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-02-01 | Execute valid action | Success result | ✓ shown with data |
| V12-02-02 | Execute invalid params | Error result | ✗ shown with message |
| V12-02-03 | Execute failing logic | Error result | Logic error displayed |
| V12-02-04 | Execute button disabled | While executing | Prevent double-click |

### REQ-12-03: Parameter Form

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-03-01 | Select action | Form appears | Parameters shown |
| V12-03-02 | Required params marked | Asterisk shown | Visual indicator |
| V12-03-03 | Type validation | Correct input type | Number input for numbers |
| V12-03-04 | Min/max shown | Constraints visible | Helper text shown |
| V12-03-05 | Optional params | No asterisk | Can be empty |
| V12-03-06 | Action with no params | Empty form | "No parameters" message |

### REQ-12-04: Result Display

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-04-01 | Success result | Green success | ✓ icon, data shown |
| V12-04-02 | Error result | Red error | ✗ icon, message shown |
| V12-04-03 | Copy result | Clipboard | JSON copied |
| V12-04-04 | Large result | Scrollable | JSON scrolls |

### REQ-12-05: State Viewer

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-05-01 | All agents shown | Cards for each | 3 agent cards |
| V12-05-02 | State values shown | Balance visible | Correct values |
| V12-05-03 | Nested state | Expandable | Click to expand |
| V12-05-04 | Array state | List shown | Transactions as list |

### REQ-12-06: State Diff

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-06-01 | Value changed | Old/new shown | Strikethrough + green |
| V12-06-02 | Item added | Green highlight | + indicator |
| V12-06-03 | Item removed | Red highlight | - indicator |
| V12-06-04 | No change | Normal display | No highlighting |

### REQ-12-07: Execution Log

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-07-01 | Action executed | Entry added | Log grows |
| V12-07-02 | Entry has timestamp | Time shown | HH:MM:SS format |
| V12-07-03 | Entry has details | All info shown | Agent, action, params, result |
| V12-07-04 | Entry has state diff | Changes shown | Δ values listed |
| V12-07-05 | Log scrollable | Scroll works | Many entries work |

### REQ-12-08: Reset State

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-08-01 | Click Reset | State reset | All agents at $1000 |
| V12-08-02 | Confirm dialog | Warning shown | Confirm required |
| V12-08-03 | Log cleared | Log empty | Fresh start |

### REQ-12-09: Import State

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-09-01 | Import JSON | State loaded | Custom values shown |
| V12-09-02 | Invalid JSON | Error shown | Validation message |
| V12-09-03 | Partial import | Merges with defaults | Missing fields use defaults |

### REQ-12-10: Stateless API Contract

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-10-01 | Request includes state | State in request body | Full AppState sent |
| V12-10-02 | Response has state_after | State returned | Full AppState received |
| V12-10-03 | Sequential actions | State chains | state_after becomes next state |
| V12-10-04 | Server has no state | Stateless | Same request = same result |
| V12-10-05 | Observations returned | In response | observations array populated |

### REQ-12-11: Payload Size Limits

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V12-11-01 | State under limit | No warning | Normal operation |
| V12-11-02 | State at 80% | Warning shown | Yellow warning banner |
| V12-11-03 | State over 100% | Blocked | Cannot execute, red error |
| V12-11-04 | Reset clears large state | Size reduced | Warning removed |
| V12-11-05 | Size displayed | Visible | "856 KB / 1 MB" shown |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `web/src/components/app-studio/sandbox/TestSandbox.tsx` | Main container |
| `web/src/components/app-studio/sandbox/AgentSelector.tsx` | Agent dropdown |
| `web/src/components/app-studio/sandbox/ActionSelector.tsx` | Action dropdown |
| `web/src/components/app-studio/sandbox/ParameterForm.tsx` | Dynamic form |
| `web/src/components/app-studio/sandbox/ResultDisplay.tsx` | Result card |
| `web/src/components/app-studio/sandbox/StateViewer.tsx` | State tree |
| `web/src/components/app-studio/sandbox/StateCard.tsx` | Agent state card |
| `web/src/components/app-studio/sandbox/StateDiff.tsx` | Diff display |
| `web/src/components/app-studio/sandbox/ExecutionLog.tsx` | Log list |
| `web/src/components/app-studio/sandbox/ExecutionLogEntry.tsx` | Log entry |
| `web/src/components/app-studio/sandbox/hooks/useSandbox.ts` | State hook |
| `web/src/components/app-studio/sandbox/hooks/useStateDiff.ts` | Diff hook |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/components/app-studio/steps/TestStep.tsx` | Integrate sandbox |

---

## References

- UI-ADR-010: App Creation Wizard - Step 4 context
- ADR-018: App Studio Backend - Test endpoint
- ADR-019: App Definition Schema - State structure
