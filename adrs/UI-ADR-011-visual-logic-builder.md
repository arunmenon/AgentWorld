# UI-ADR-011: Visual Logic Builder

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **UI-ADR-010**: App Creation Wizard (action builder modal)
- **ADR-019**: App Definition Schema (logic block types, expressions)

## Context

### Problem Statement
Defining action business logic (validations, state updates, notifications) in JSON is error-prone and not intuitive. A visual flowchart builder lets users design logic without writing code, making app creation accessible to non-developers.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-11-01 | Canvas | Must | Visual canvas for logic flow |
| REQ-11-02 | Logic Blocks | Must | Draggable block components |
| REQ-11-03 | Connections | Must | Connect blocks to define flow |
| REQ-11-04 | Block Configuration | Must | Edit block properties |
| REQ-11-05 | Expression Editor | Must | Autocomplete for expressions |
| REQ-11-06 | Validation | Must | Highlight invalid logic |
| REQ-11-07 | JSON Sync | Should | Bidirectional sync with JSON |
| REQ-11-08 | Step-Through Debug | Should | Debug mode in test step |
| REQ-11-09 | Graph Constraints | Must | Enforce DAG structure, prevent cycles |
| REQ-11-10 | Library Version Lock | Must | Pin React Flow version for stability |

## Decision

### Logic Builder Interface

```
┌─────────────────────────────────────────────────────────────────────┐
│  Action Logic: transfer                           [Test] [Save]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────┐  ┌──────────────┐  │
│  │                                            │  │ BLOCKS       │  │
│  │       ┌───────────┐                        │  │              │  │
│  │       │  START    │                        │  │ ┌──────────┐ │  │
│  │       └─────┬─────┘                        │  │ │❓Validate │ │  │
│  │             │                              │  │ └──────────┘ │  │
│  │             ▼                              │  │              │  │
│  │    ┌────────────────┐                      │  │ ┌──────────┐ │  │
│  │    │ ❓ VALIDATE    │───No──┐              │  │ │📝 Update │ │  │
│  │    │ amount > 0     │       │              │  │ └──────────┘ │  │
│  │    └───────┬────────┘       │              │  │              │  │
│  │            │ Yes            │              │  │ ┌──────────┐ │  │
│  │            ▼                ▼              │  │ │🔔 Notify │ │  │
│  │    ┌────────────────┐  ┌─────────┐        │  │ └──────────┘ │  │
│  │    │ ❓ VALIDATE    │  │❌ ERROR │        │  │              │  │
│  │    │ to != self     │  │ Invalid │        │  │ ┌──────────┐ │  │
│  │    └───────┬────────┘  │ amount  │        │  │ │✅ Return │ │  │
│  │            │ Yes       └─────────┘        │  │ └──────────┘ │  │
│  │            ▼                              │  │              │  │
│  │    ┌────────────────┐                     │  │ ┌──────────┐ │  │
│  │    │ 📝 UPDATE      │                     │  │ │❌ Error  │ │  │
│  │    │ sender.balance │                     │  │ └──────────┘ │  │
│  │    │   -= amount    │                     │  │              │  │
│  │    └───────┬────────┘                     │  │ ┌──────────┐ │  │
│  │            │                              │  │ │🔀 Branch │ │  │
│  │            ▼                              │  │ └──────────┘ │  │
│  │       ┌────────────┐                      │  │              │  │
│  │       │ ✅ RETURN  │                      │  │ ┌──────────┐ │  │
│  │       │ {tx_id}    │                      │  │ │🔁 Loop   │ │  │
│  │       └────────────┘                      │  │ └──────────┘ │  │
│  │                                            │  └──────────────┘  │
│  └────────────────────────────────────────────┘                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  BLOCK CONFIGURATION                          [JSON View] [Visual]  │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Selected: VALIDATE block                                           │
│                                                                     │
│  Condition *                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ params.amount > 0                                      [?]   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Autocomplete: params. | agent. | agents[]. | state. | config.     │
│                                                                     │
│  Error Message *                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Amount must be positive                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Block Components

Each block type has a distinct visual representation:

#### VALIDATE Block
```
┌──────────────────────────┐
│ ❓ VALIDATE              │
│ ────────────────────     │
│ params.amount > 0        │
│                          │
│ ⚠ "Invalid amount"       │
│                          │
│    [Yes] ───┐   [No] ───┐│
└──────────────────────────┘
```
- Yellow/amber border
- Shows condition preview
- Shows error message preview
- Two output ports: Yes (pass) and No (fail)

#### UPDATE Block
```
┌──────────────────────────┐
│ 📝 UPDATE                │
│ ────────────────────     │
│ agent.balance            │
│ -= params.amount         │
│                          │
│    [Next] ───┐           │
└──────────────────────────┘
```
- Blue border
- Shows target and operation
- Single output port

#### NOTIFY Block
```
┌──────────────────────────┐
│ 🔔 NOTIFY                │
│ ────────────────────     │
│ To: params.to            │
│ "You received ${amount}" │
│                          │
│    [Next] ───┐           │
└──────────────────────────┘
```
- Purple border
- Shows recipient and message preview
- Single output port

#### RETURN Block
```
┌──────────────────────────┐
│ ✅ RETURN                │
│ ────────────────────     │
│ {                        │
│   transaction_id,        │
│   new_balance            │
│ }                        │
└──────────────────────────┘
```
- Green border
- Shows return value preview
- No output port (terminal)

#### ERROR Block
```
┌──────────────────────────┐
│ ❌ ERROR                 │
│ ────────────────────     │
│ "Insufficient funds"     │
│                          │
└──────────────────────────┘
```
- Red border
- Shows error message
- No output port (terminal)

#### BRANCH Block
```
┌──────────────────────────┐
│ 🔀 BRANCH                │
│ ────────────────────     │
│ agent.vip == true        │
│                          │
│    [Yes] ───┐   [No] ───┐│
└──────────────────────────┘
```
- Orange border
- Shows condition
- Two output ports: Yes and No

#### LOOP Block
```
┌──────────────────────────┐
│ 🔁 LOOP                  │
│ ────────────────────     │
│ for item in              │
│   state.pending_requests │
│                          │
│    [Body] ───┐  [Done]───┐│
└──────────────────────────┘
```
- Cyan border
- Shows collection and item variable
- Two output ports: Body (loop content) and Done (after loop)

### Expression Editor

```
┌─────────────────────────────────────────────────────────────────────┐
│  Condition *                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ params.am|                                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 📍 params.amount      number   Action parameter              │   │
│  │ 📍 params.amountType  string   (custom field)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Available:                                                         │
│  • params.to (string) - Recipient                                   │
│  • params.amount (number) - Transfer amount                         │
│  • params.note (string?) - Optional note                            │
│  • agent.id (string) - Current agent ID                             │
│  • agent.balance (number) - Current balance                         │
│  • agents[id].balance (number) - Other agent's balance              │
│  • generate_id() - Generate UUID                                    │
│  • timestamp() - Current timestamp                                  │
└─────────────────────────────────────────────────────────────────────┘
```

Features:
- Autocomplete for context variables
- Type hints for each variable
- Function signatures for built-ins
- Syntax highlighting
- Error highlighting for invalid expressions

### Graph Constraints

The logic graph **must be a Directed Acyclic Graph (DAG)**. This ensures:
- Logic can be serialized to a linear JSON array
- No infinite loops in the graph structure (runtime loop limits are separate - see ADR-018)
- Deterministic execution order

**Constraints enforced:**

| Constraint | Enforcement | User Feedback |
|------------|-------------|---------------|
| No cycles | Reject connection that creates cycle | Toast: "Cannot create circular reference" |
| Single entry | START block only | START is pre-placed, cannot be deleted |
| Terminal blocks | RETURN/ERROR must terminate paths | Warning: "Path has no terminal block" |
| No orphans | All blocks must be reachable from START | Warning: "Block is not connected" |
| Connection types | Only valid port-to-port connections | Visual feedback on drag |

**Cycle Detection Algorithm:**
```typescript
function wouldCreateCycle(
  connections: Connection[],
  newConnection: { sourceId: string; targetId: string }
): boolean {
  // Build adjacency list including proposed connection
  const graph = buildAdjacencyList(connections);
  graph.addEdge(newConnection.sourceId, newConnection.targetId);

  // DFS from target to see if we can reach source
  return hasPath(graph, newConnection.targetId, newConnection.sourceId);
}
```

**Block Limits (per ADR-018 execution safety):**
- Maximum 50 blocks per action (prevents performance issues)
- Maximum 10 nesting levels for branch/loop

### Canvas Interactions

| Interaction | Action |
|-------------|--------|
| Drag from palette | Add new block to canvas |
| Click block | Select for configuration |
| Drag block | Reposition on canvas |
| Double-click block | Open full editor |
| Click output port | Start connection |
| Click input area | Complete connection |
| Click connection | Select connection |
| Delete key | Remove selected block/connection |
| Scroll wheel | Zoom in/out |
| Click + drag canvas | Pan |
| Ctrl/Cmd + Z | Undo |
| Ctrl/Cmd + Shift + Z | Redo |

### JSON Sync

The visual builder maintains bidirectional sync with the JSON representation:

```typescript
interface LogicBuilderState {
  blocks: BlockNode[];
  connections: Connection[];
  selectedBlockId: string | null;
  selectedConnectionId: string | null;
  viewMode: 'visual' | 'json';
  jsonSource: string;
  isDirty: boolean;
}

interface BlockNode {
  id: string;
  type: LogicBlockType;
  position: { x: number; y: number };
  data: LogicBlock;
}

interface Connection {
  id: string;
  sourceId: string;
  sourcePort: 'yes' | 'no' | 'next' | 'body' | 'done';
  targetId: string;
}

// Convert visual to JSON
function visualToJson(state: LogicBuilderState): LogicBlock[] {
  // Topological sort from START block
  // Inline branch/loop bodies
  // Return ordered logic array
}

// Convert JSON to visual
function jsonToVisual(logic: LogicBlock[]): LogicBuilderState {
  // Create blocks with auto-layout
  // Create connections from flow
  // Handle nested branch/loop structures
}
```

### Validation Display

```
┌─────────────────────────────────────────────────────────────────────┐
│  VALIDATION ISSUES (3)                                        [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⚠️ Block 3 (VALIDATE): Invalid expression syntax                   │
│     "params.amount >" - unexpected end of expression                │
│     [Go to block]                                                   │
│                                                                     │
│  ⚠️ Block 5 (NOTIFY): Unconnected output                           │
│     Block has no connection to next step                            │
│     [Go to block]                                                   │
│                                                                     │
│  ❌ No terminal block: Logic must end with RETURN or ERROR         │
│     Add a RETURN or ERROR block to complete the flow                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Step-Through Debug Mode

```
┌─────────────────────────────────────────────────────────────────────┐
│  DEBUG MODE                              [Step] [Run] [Reset] [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Current Block: VALIDATE (3)                     Step 2 of ?        │
│  Condition: params.amount <= agent.balance                          │
│  Result: true ✓                                                     │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  CONTEXT                                                            │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  params:                                                            │
│    to: "bob"                                                        │
│    amount: 50                                                       │
│    note: "Lunch"                                                    │
│                                                                     │
│  agent:                                                             │
│    id: "alice"                                                      │
│    balance: 1000  → (will be 950 after UPDATE)                     │
│    transactions: []                                                 │
│                                                                     │
│  agents.bob:                                                        │
│    balance: 500  → (will be 550 after UPDATE)                      │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  EXECUTION TRACE                                                    │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  ✓ 1. VALIDATE: params.to != agent.id → true                       │
│  ● 2. VALIDATE: params.amount <= agent.balance → true (current)    │
│  ○ 3. UPDATE: agent.balance -= 50                                  │
│  ○ 4. UPDATE: agents[bob].balance += 50                            │
│  ○ 5. NOTIFY: bob                                                  │
│  ○ 6. RETURN: {transaction_id, new_balance}                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
web/src/components/app-studio/logic-builder/
├── LogicCanvas.tsx          # Main canvas with drag/drop
├── LogicBlock.tsx           # Generic block container
├── blocks/
│   ├── ValidateBlock.tsx    # VALIDATE block component
│   ├── UpdateBlock.tsx      # UPDATE block component
│   ├── NotifyBlock.tsx      # NOTIFY block component
│   ├── ReturnBlock.tsx      # RETURN block component
│   ├── ErrorBlock.tsx       # ERROR block component
│   ├── BranchBlock.tsx      # BRANCH block component
│   └── LoopBlock.tsx        # LOOP block component
├── BlockPalette.tsx         # Draggable block palette
├── BlockConnection.tsx      # SVG connection lines
├── BlockConfigPanel.tsx     # Selected block configuration
├── ExpressionEditor.tsx     # Expression input with autocomplete
├── ExpressionAutocomplete.tsx # Autocomplete dropdown
├── LogicValidator.tsx       # Logic validation display
├── JsonEditor.tsx           # JSON view editor
├── DebugPanel.tsx           # Step-through debug UI
└── hooks/
    ├── useLogicBuilder.ts   # State management
    ├── useAutoLayout.ts     # Auto-layout algorithm
    ├── useUndoRedo.ts       # Undo/redo stack
    └── useExpressionParser.ts # Expression parsing
```

### TypeScript Interfaces

```typescript
type LogicBlockType = 'validate' | 'update' | 'notify' | 'return' | 'error' | 'branch' | 'loop';

interface BlockNode {
  id: string;
  type: LogicBlockType;
  position: { x: number; y: number };
  data: LogicBlock;
  isSelected: boolean;
  hasError: boolean;
  errorMessage?: string;
}

interface Connection {
  id: string;
  sourceId: string;
  sourcePort: string;
  targetId: string;
  isSelected: boolean;
}

interface LogicBuilderProps {
  logic: LogicBlock[];
  onChange: (logic: LogicBlock[]) => void;
  actionParameters: Record<string, ParamSpec>;
  stateSchema: StateField[];
  readOnly?: boolean;
}

interface ExpressionEditorProps {
  value: string;
  onChange: (value: string) => void;
  context: ExpressionContext;
  placeholder?: string;
  multiline?: boolean;
  error?: string;
}

interface ExpressionContext {
  params: Record<string, ParamSpec>;
  stateFields: StateField[];
  builtinFunctions: FunctionSignature[];
}

interface ValidationIssue {
  blockId?: string;
  severity: 'error' | 'warning';
  message: string;
  details?: string;
}
```

## Consequences

### Positive
- No-code logic definition
- Visual debugging
- Clear data flow visualization
- Prevents syntax errors
- Accessible to non-developers
- Undo/redo support

### Negative
- Complex UI implementation
- Canvas performance with many blocks
- Learning curve for flowchart paradigm
- Auto-layout can be imperfect

### Neutral
- JSON view provides escape hatch for advanced users
- Requires maintaining two representations (visual + JSON)

---

## Validation Checklist

### REQ-11-01: Canvas

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-01-01 | Canvas renders | Empty canvas shown | START block visible |
| V11-01-02 | Pan canvas | Canvas moves | Drag to pan works |
| V11-01-03 | Zoom canvas | Canvas scales | Scroll to zoom works |
| V11-01-04 | Reset view | Returns to default | Fit-to-view button |
| V11-01-05 | Canvas persists | Layout saved | Reload preserves positions |

### REQ-11-02: Logic Blocks

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-02-01 | Drag block from palette | Block added to canvas | Block appears at drop point |
| V11-02-02 | Select block | Block highlighted | Config panel shows |
| V11-02-03 | Move block | Position changes | Connections follow |
| V11-02-04 | Delete block | Block removed | Connections removed |
| V11-02-05 | Duplicate block | Copy created | New block with same config |
| V11-02-06 | All block types render | Each type works | 7 block types functional |

### REQ-11-03: Connections

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-03-01 | Connect blocks | Line drawn | SVG path visible |
| V11-03-02 | Delete connection | Line removed | Click connection to delete |
| V11-03-03 | Invalid connection | Rejected | Cannot connect incompatible |
| V11-03-04 | Branch connections | Two outputs | Yes/No paths |
| V11-03-05 | Curved connections | Bezier paths | Aesthetically pleasing |

### REQ-11-04: Block Configuration

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-04-01 | Select VALIDATE | Shows condition + error | Config panel updates |
| V11-04-02 | Select UPDATE | Shows target + operation | Config panel updates |
| V11-04-03 | Select NOTIFY | Shows to + message + data | Config panel updates |
| V11-04-04 | Edit config | Block updates | Changes reflected in block |
| V11-04-05 | Invalid config | Shows error | Inline validation |

### REQ-11-05: Expression Editor

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-05-01 | Type "params." | Autocomplete shows | Parameter list displayed |
| V11-05-02 | Type "agent." | Autocomplete shows | State fields displayed |
| V11-05-03 | Type "generate" | Function shown | Built-in functions listed |
| V11-05-04 | Select suggestion | Text inserted | Autocomplete works |
| V11-05-05 | Invalid expression | Error shown | Syntax error highlighted |
| V11-05-06 | Help tooltip | Documentation shown | Click [?] shows help |

### REQ-11-06: Validation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-06-01 | Missing connection | Warning shown | Unconnected block highlighted |
| V11-06-02 | Invalid expression | Error shown | Block shows error badge |
| V11-06-03 | No RETURN/ERROR | Warning shown | Flow must terminate |
| V11-06-04 | Circular reference | Error shown | Infinite loop detected |
| V11-06-05 | Validation summary | All errors listed | Panel shows all issues |

### REQ-11-07: JSON Sync

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-07-01 | Visual → JSON | JSON updates | Live sync on edit |
| V11-07-02 | JSON → Visual | Canvas updates | Manual JSON edit reflects |
| V11-07-03 | Toggle view mode | Both views accessible | Tab switch works |
| V11-07-04 | JSON validation | Errors shown | Invalid JSON flagged |

### REQ-11-08: Step-Through Debug

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-08-01 | Enable debug mode | Stepping available | Debug button appears |
| V11-08-02 | Step through | Block highlighted | Current block shown |
| V11-08-03 | Variable inspection | Values shown | Context variables visible |
| V11-08-04 | Step into branch | Correct path taken | Follows condition result |
| V11-08-05 | Breakpoints | Pause at breakpoint | Click to set breakpoint |

### REQ-11-09: Graph Constraints

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-09-01 | Attempt cycle | Connection rejected | Toast error shown |
| V11-09-02 | Delete START | Not allowed | START undeletable |
| V11-09-03 | Orphan block | Warning shown | Block highlighted yellow |
| V11-09-04 | No terminal | Warning shown | "Path has no terminal" |
| V11-09-05 | Max blocks exceeded | Cannot add more | "Maximum 50 blocks" |
| V11-09-06 | Max nesting exceeded | Error shown | "Maximum nesting depth" |

### REQ-11-10: Library Version Lock

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V11-10-01 | Check package.json | Exact version pinned | No `^` or `~` prefix |
| V11-10-02 | Canvas renders | React Flow works | Basic operations functional |
| V11-10-03 | Custom nodes | Registered correctly | All block types render |
| V11-10-04 | Version mismatch | Build fails | CI catches version drift |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `web/src/components/app-studio/logic-builder/LogicCanvas.tsx` | Main canvas |
| `web/src/components/app-studio/logic-builder/LogicBlock.tsx` | Block container |
| `web/src/components/app-studio/logic-builder/blocks/*.tsx` | Block components |
| `web/src/components/app-studio/logic-builder/BlockPalette.tsx` | Block palette |
| `web/src/components/app-studio/logic-builder/BlockConnection.tsx` | Connections |
| `web/src/components/app-studio/logic-builder/BlockConfigPanel.tsx` | Config panel |
| `web/src/components/app-studio/logic-builder/ExpressionEditor.tsx` | Expression input |
| `web/src/components/app-studio/logic-builder/LogicValidator.tsx` | Validation |
| `web/src/components/app-studio/logic-builder/JsonEditor.tsx` | JSON view |
| `web/src/components/app-studio/logic-builder/DebugPanel.tsx` | Debug UI |
| `web/src/components/app-studio/logic-builder/hooks/*.ts` | Custom hooks |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/components/app-studio/ActionBuilder.tsx` | Integrate logic builder |

---

## Technology Stack

### React Flow Version Lock

The visual logic builder uses [React Flow](https://reactflow.dev/) for the canvas implementation. **The version must be pinned** to prevent breaking changes:

```json
// package.json
{
  "dependencies": {
    "@xyflow/react": "12.3.x"
  }
}
```

**Rationale:**
- React Flow has had breaking changes between major versions
- Canvas behavior, node/edge APIs, and styling can change significantly
- Pinning ensures consistent behavior across environments
- Upgrades should be explicit and tested

**Update Policy:**
1. Do not auto-update React Flow via `^` or `~` ranges
2. Test thoroughly before upgrading (manual QA of all interactions)
3. Document breaking changes and migration steps
4. Consider migration guide for stored graph state if format changes

**Locked Features Used:**
- `ReactFlow` component with custom nodes
- `useNodesState` / `useEdgesState` hooks
- Custom node types registration
- Edge connection validation
- Viewport controls (zoom, pan)

---

## References

- UI-ADR-010: App Creation Wizard - Action builder context
- ADR-019: App Definition Schema - Logic block types
- [React Flow](https://reactflow.dev/) - Canvas library (version 12.x)
