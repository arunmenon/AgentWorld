# UI-ADR-010: App Creation Wizard

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **UI-ADR-009**: App Studio Library (navigation, routing)
- **ADR-018**: App Studio Backend (API endpoints)
- **ADR-019**: App Definition Schema (data structures)

## Context

### Problem Statement
Creating a simulated app requires defining identity, actions, parameters, and business logic. A multi-step wizard provides guided flow with progressive complexity, similar to the Persona Builder pattern established in UI-ADR-006.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-10-01 | Template Selection | Must | Start from template or blank |
| REQ-10-02 | Basic Info Step | Must | Name, description, category, icon |
| REQ-10-03 | Actions Step | Must | View/add/edit/remove actions |
| REQ-10-04 | Test Step | Must | Test app before saving |
| REQ-10-05 | Step Navigation | Must | Back/Next, step indicator |
| REQ-10-06 | Draft Persistence | Should | Save draft locally |
| REQ-10-07 | Validation | Must | Validate at each step |
| REQ-10-08 | Edit Mode | Must | Support editing existing apps |
| REQ-10-09 | Blank Template Flow | Must | Allow blank but block Save until ≥1 action |
| REQ-10-10 | State Schema Validation | Should | Validate state_schema against ADR-018 structure |

## Decision

### Wizard Flow

```
Step 1: Template    →   Step 2: Info    →   Step 3: Actions   →   Step 4: Test
[Select starting        [Name, desc,        [Configure          [Test actions,
 point]                  category]           actions]            save]
```

### Step 1: Template Selection

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create New App                                    Step 1 of 4      │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  ●───────○───────○───────○                                          │
│  Template  Info    Actions  Test                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Start with a template:                                             │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │      💳         │  │      🛒         │  │      📧         │     │
│  │    Payment      │  │    Shopping     │  │     Email       │     │
│  │                 │  │                 │  │                 │     │
│  │  Transfer money │  │  Cart, orders,  │  │  Send, receive  │     │
│  │  between users  │  │  product search │  │  reply to email │     │
│  │                 │  │                 │  │                 │     │
│  │  6 actions      │  │  5 actions      │  │  4 actions      │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │      📅         │  │      💬         │  │      📝         │     │
│  │   Calendar      │  │    Messaging    │  │     Blank       │     │
│  │                 │  │                 │  │                 │     │
│  │  Events,        │  │  Send/receive   │  │  Start from     │     │
│  │  reminders      │  │  messages       │  │  scratch        │     │
│  │                 │  │                 │  │                 │     │
│  │  4 actions      │  │  3 actions      │  │  0 actions      │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│                                                                     │
│                                                      [Next: Info →] │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 2: Basic Info

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create New App                                    Step 2 of 4      │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  ○───────●───────○───────○                                          │
│  Template  Info    Actions  Test                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  App Name *                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ My Venmo Clone                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  This will be shown to agents                                       │
│                                                                     │
│  App ID *                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ my_venmo_clone                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Unique identifier (auto-generated from name)                       │
│                                                                     │
│  Description                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ A social payment app for sending money to friends with      │   │
│  │ fun emojis and notes.                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Helps agents understand what this app does                         │
│                                                                     │
│  Category                          Icon                             │
│  ┌───────────────────────┐         ┌─────────────────────────┐     │
│  │ Payment           ▼   │         │ 💸  [Change]            │     │
│  └───────────────────────┘         └─────────────────────────┘     │
│                                                                     │
│                                                                     │
│                                         [← Back]  [Next: Actions →] │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 3: Actions

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create New App                                    Step 3 of 4      │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  ○───────○───────●───────○                                          │
│  Template  Info    Actions  Test                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Actions (6)                                          [+ Add Action]│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ check_balance                                    [Edit] [×]  │   │
│  │ View your current balance                                    │   │
│  │ Parameters: (none)  •  Returns: balance                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ transfer                                         [Edit] [×]  │   │
│  │ Send money to another user                                   │   │
│  │ Parameters: to*, amount*, note  •  Returns: transaction_id   │   │
│  │ ⚠️ Has custom logic                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ request_money                                    [Edit] [×]  │   │
│  │ Request money from another user                              │   │
│  │ Parameters: from*, amount*, note  •  Returns: request_id     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ... (3 more actions, scrollable)                                   │
│                                                                     │
│  ▼ Advanced: State Schema                          (collapsed)      │
│  ▼ Advanced: Initial Configuration                 (collapsed)      │
│                                                                     │
│                                           [← Back]  [Next: Test →]  │
└─────────────────────────────────────────────────────────────────────┘
```

### Action Builder Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│  Edit Action: transfer                                        [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────┐│
│  │  DEFINITION                     │ │  LOGIC                      ││
│  │  ──────────                     │ │  ─────                      ││
│  │                                 │ │                             ││
│  │  Action Name *                  │ │  [Visual] [JSON]            ││
│  │  ┌─────────────────────────┐   │ │                             ││
│  │  │ transfer                │   │ │  This action has custom     ││
│  │  └─────────────────────────┘   │ │  logic defined.             ││
│  │                                 │ │                             ││
│  │  Description *                  │ │  ┌─────────────────────┐   ││
│  │  ┌─────────────────────────┐   │ │  │ 1. VALIDATE         │   ││
│  │  │ Send money to another   │   │ │  │    to != self       │   ││
│  │  │ user                    │   │ │  ├─────────────────────┤   ││
│  │  └─────────────────────────┘   │ │  │ 2. VALIDATE         │   ││
│  │                                 │ │  │    recipient exists │   ││
│  │  ─────────────────────────────  │ │  ├─────────────────────┤   ││
│  │  PARAMETERS                     │ │  │ 3. VALIDATE         │   ││
│  │  ──────────                     │ │  │    amount <= balance│   ││
│  │                                 │ │  ├─────────────────────┤   ││
│  │  ┌─────────────────────────┐   │ │  │ 4. UPDATE           │   ││
│  │  │ to (string) *      [×]  │   │ │  │    sender balance   │   ││
│  │  │ Recipient agent ID      │   │ │  ├─────────────────────┤   ││
│  │  └─────────────────────────┘   │ │  │ 5. UPDATE           │   ││
│  │                                 │ │  │    receiver balance │   ││
│  │  ┌─────────────────────────┐   │ │  ├─────────────────────┤   ││
│  │  │ amount (number) * [×]   │   │ │  │ 6. NOTIFY           │   ││
│  │  │ Amount to transfer      │   │ │  │    recipient        │   ││
│  │  │ Min: 0.01, Max: 10000   │   │ │  ├─────────────────────┤   ││
│  │  └─────────────────────────┘   │ │  │ 7. RETURN           │   ││
│  │                                 │ │  │    transaction_id   │   ││
│  │  ┌─────────────────────────┐   │ │  └─────────────────────┘   ││
│  │  │ note (string)      [×]  │   │ │                             ││
│  │  │ Optional note           │   │ │  [Edit Logic]               ││
│  │  └─────────────────────────┘   │ │                             ││
│  │                                 │ │                             ││
│  │  [+ Add Parameter]              │ │                             ││
│  │                                 │ │                             ││
│  │  ─────────────────────────────  │ │                             ││
│  │  RETURNS                        │ │                             ││
│  │  ───────                        │ │                             ││
│  │  transaction_id (string)        │ │                             ││
│  │  new_balance (number)           │ │                             ││
│  │                                 │ │                             ││
│  └─────────────────────────────────┘ └─────────────────────────────┘│
│                                                                     │
│                                         [Cancel]  [Save Action]     │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 4: Test & Save

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create New App                                    Step 4 of 4      │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  ○───────○───────○───────●                                          │
│  Template  Info    Actions  Test                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐  │
│  │  TEST YOUR APP               │  │  STATE                     │  │
│  │  ────────────────────────    │  │  ─────                     │  │
│  │                              │  │                            │  │
│  │  Test Agents: Alice, Bob     │  │  Alice                     │  │
│  │                              │  │    balance: $1000.00       │  │
│  │  Agent:  [Alice         ▼]   │  │    transactions: []        │  │
│  │  Action: [transfer      ▼]   │  │                            │  │
│  │                              │  │  Bob                       │  │
│  │  ─────────────────────────── │  │    balance: $1000.00       │  │
│  │  Parameters:                 │  │    transactions: []        │  │
│  │                              │  │                            │  │
│  │  to *      [bob_________]    │  │  ─────────────────────     │  │
│  │  amount *  [50__________]    │  │  EXECUTION LOG             │  │
│  │  note      [Lunch money_]    │  │                            │  │
│  │                              │  │  10:24:15 Alice              │  │
│  │  [▶ Execute Action]          │  │  ├ Action: transfer          │  │
│  │                              │  │  ├ Params: {to:"bob",        │  │
│  │  ─────────────────────────── │  │  │         amount:50}        │  │
│  │  Last Result:                │  │  ├ Result: ✓ Success         │  │
│  │  ┌────────────────────────┐  │  │  │   tx_id: tx-abc123        │  │
│  │  │ ✓ Success              │  │  │  └ State Δ:                  │  │
│  │  │ transaction_id: tx-... │  │  │      Alice.balance:         │  │
│  │  │ new_balance: $950      │  │  │        $1000 → $950 (-$50)  │  │
│  │  └────────────────────────┘  │  │      Bob.balance:           │  │
│  │                              │  │        $1000 → $1050 (+$50) │  │
│  └──────────────────────────────┘  └────────────────────────────┘  │
│                                                                     │
│                                               [← Back]  [Save App]  │
│                                                         ↑ disabled  │
│                                                           if 0      │
│                                                           actions   │
└─────────────────────────────────────────────────────────────────────┘
```

**Save Button States:**
- **Enabled**: App has ≥1 action
- **Disabled with tooltip**: "Add at least one action to save your app"

### Templates

| Template | Category | Actions | Description |
|----------|----------|---------|-------------|
| Payment | payment | check_balance, transfer, request_money, pay_request, decline_request, view_transactions | Money transfers and requests |
| Shopping | shopping | search_products, view_product, add_to_cart, view_cart, checkout | E-commerce cart flow |
| Email | communication | view_inbox, read_email, send_email, reply_email | Basic email client |
| Calendar | calendar | view_events, create_event, update_event, delete_event | Event management |
| Messaging | social | send_message, read_messages, list_conversations | Chat messaging |
| Blank | custom | (none) | Start from scratch |

### Component Architecture

```
web/src/
├── pages/
│   ├── AppCreate.tsx              # Wizard container page
│   └── AppEdit.tsx                # Edit mode wrapper
├── components/
│   └── app-studio/
│       ├── AppWizard.tsx          # Wizard state machine
│       ├── AppWizardSteps.tsx     # Step indicator
│       ├── steps/
│       │   ├── TemplateStep.tsx   # Step 1
│       │   ├── InfoStep.tsx       # Step 2
│       │   ├── ActionsStep.tsx    # Step 3
│       │   └── TestStep.tsx       # Step 4
│       ├── TemplateCard.tsx       # Template selection card
│       ├── ActionList.tsx         # Action list component
│       ├── ActionCard.tsx         # Individual action card
│       ├── ActionBuilder.tsx      # Action edit modal
│       ├── ParameterEditor.tsx    # Parameter form
│       └── IconPicker.tsx         # Emoji/icon picker
```

### Wizard State

```typescript
interface AppWizardState {
  step: 1 | 2 | 3 | 4;
  selectedTemplate: string | null;
  definition: Partial<AppDefinitionDetails>;
  validationErrors: Record<string, string>;
  isDirty: boolean;
  isLoading: boolean;
}

interface WizardContextValue {
  state: AppWizardState;
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  updateDefinition: (updates: Partial<AppDefinitionDetails>) => void;
  setTemplate: (templateId: string) => void;
  addAction: (action: ActionDefinition) => void;
  updateAction: (index: number, action: ActionDefinition) => void;
  removeAction: (index: number) => void;
  save: () => Promise<void>;
  canProceed: boolean;
}
```

### Local Draft Persistence

```typescript
const DRAFT_KEY = 'app-studio-draft';

function saveDraft(state: AppWizardState) {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({
    definition: state.definition,
    step: state.step,
    timestamp: Date.now()
  }));
}

function loadDraft(): AppWizardState | null {
  const stored = localStorage.getItem(DRAFT_KEY);
  if (!stored) return null;

  const draft = JSON.parse(stored);
  // Expire drafts after 24 hours
  if (Date.now() - draft.timestamp > 24 * 60 * 60 * 1000) {
    localStorage.removeItem(DRAFT_KEY);
    return null;
  }
  return draft;
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY);
}
```

### Validation Rules

| Step | Field | Rule | Blocking |
|------|-------|------|----------|
| 1 | template | Selection required | Next button |
| 2 | name | Required, 1-100 chars | Next button |
| 2 | app_id | Required, snake_case, 2-50 chars, unique | Next button |
| 2 | category | Required, valid enum | Next button |
| 3 | actions | Informational warning if empty | Next button (allowed) |
| 3 | action.name | Required, snake_case | Save action |
| 3 | action.description | Required | Save action |
| 3 | action.logic | At least 1 block (can be just RETURN) | Save action |
| 4 | actions | At least 1 action required | **Save App button** |

### Blank Template Flow

When user selects the "Blank" template:

1. **Step 1 → 2**: Allowed to proceed (blank is a valid selection)
2. **Step 2 → 3**: Allowed to proceed after filling name/category
3. **Step 3 → 4**: Allowed to proceed even with 0 actions (show info message)
4. **Step 4 Save**: **BLOCKED** until at least 1 action exists

This flow allows users to explore the wizard and understand the structure before committing to action creation, while ensuring no app can be saved without functionality.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Actions (Blank template)                                   │
│                                                                     │
│  Actions (0)                                          [+ Add Action]│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  📝 No actions yet                                           │   │
│  │                                                               │   │
│  │  Add at least one action to define what your app can do.     │   │
│  │                                                               │   │
│  │  [+ Add Your First Action]                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ⚠️ You need at least 1 action to save your app.                   │
│                                                                     │
│                                            [← Back]  [Next: Test →] │
│                                            ↑ enabled even with 0    │
└─────────────────────────────────────────────────────────────────────┘
```

### State Schema Validation

State schema fields defined in the wizard must align with ADR-018's canonical `AppState` structure:

```typescript
// Each state field maps to either per_agent or shared
interface StateFieldUI {
  name: string;           // Field name
  type: ParamType;        // string | number | boolean | array | object
  default: unknown;       // Default value
  perAgent: boolean;      // true → state.per_agent[id].{name}
                          // false → state.shared.{name}
  description?: string;
}
```

**Validation:**
- Field names must be valid identifiers (no spaces, start with letter)
- `perAgent: true` fields are duplicated per agent on initialization
- `perAgent: false` fields are shared and visible to all agents
- Default values must match the declared type

**Example mapping to runtime state (per ADR-018):**
```json
// Definition:
{ "name": "balance", "type": "number", "default": 1000, "perAgent": true }
{ "name": "fee_pool", "type": "number", "default": 0, "perAgent": false }

// Runtime AppState:
{
  "per_agent": {
    "alice": { "balance": 1000 },
    "bob": { "balance": 1000 }
  },
  "shared": {
    "fee_pool": 0
  }
}
```

## Consequences

### Positive
- Guided flow reduces cognitive load
- Templates accelerate creation
- Testing before save catches errors
- Consistent with PersonaWizard pattern
- Draft persistence prevents data loss

### Negative
- 4 steps may feel long for simple apps
- Template customization may be limited
- Modal-heavy experience for action editing

### Neutral
- Requires maintaining template definitions
- Edit mode skips template step

---

## Validation Checklist

### REQ-10-01: Template Selection

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-01-01 | Display templates | All templates shown | 6 template cards visible |
| V10-01-02 | Select template | Template highlighted | Visual selection state |
| V10-01-03 | Select blank | Blank highlighted | Can proceed with no actions |
| V10-01-04 | None selected | Next disabled | Cannot proceed without selection |
| V10-01-05 | Template preview | Shows action count | "6 actions" label accurate |

### REQ-10-02: Basic Info Step

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-02-01 | Empty name | Validation error | "Name required" message |
| V10-02-02 | Invalid app_id | Validation error | Pattern validation shown |
| V10-02-03 | Auto-generate app_id | ID from name | "My App" → "my_app" |
| V10-02-04 | Select category | Value saved | Category in form state |
| V10-02-05 | Select icon | Icon shown | Emoji picker works |
| V10-02-06 | Edit mode pre-fills | Fields populated | Existing values shown |

### REQ-10-03: Actions Step

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-03-01 | Show template actions | Actions listed | All template actions shown |
| V10-03-02 | Add new action | Opens builder | Modal opens |
| V10-03-03 | Edit action | Opens builder with data | Pre-filled form |
| V10-03-04 | Delete action | Removes from list | Action no longer in list |
| V10-03-05 | Reorder actions | Drag and drop | Order changes |
| V10-03-06 | No actions (blank) | Empty state | "Add your first action" |
| V10-03-07 | Action validation | Shows errors | Invalid actions marked |

### REQ-10-04: Test Step

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-04-01 | Test agents exist | Alice, Bob shown | Dropdown has options |
| V10-04-02 | Select action | Params shown | Parameter form appears |
| V10-04-03 | Execute action | Result shown | Success/error displayed |
| V10-04-04 | State updates | State panel updates | Balance changes visible |
| V10-04-05 | Execution log | Entry added | Log shows action details |
| V10-04-06 | Reset state | State reset | Balances return to initial |

### REQ-10-05: Step Navigation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-05-01 | Click Next | Advances step | Step indicator updates |
| V10-05-02 | Click Back | Goes back | Previous step shown |
| V10-05-03 | Click step indicator | Jumps to step | Direct navigation works |
| V10-05-04 | Invalid step | Next disabled | Cannot skip validation |
| V10-05-05 | Keyboard nav | Shortcuts work | Enter advances, Esc cancels |

### REQ-10-06: Draft Persistence

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-06-01 | Close tab mid-wizard | Draft saved | localStorage has draft |
| V10-06-02 | Reopen /apps/new | Prompt to restore | "Continue where you left off?" |
| V10-06-03 | Accept restore | Draft loaded | Previous state restored |
| V10-06-04 | Decline restore | Fresh start | Blank wizard |
| V10-06-05 | Save app | Draft cleared | localStorage empty |

### REQ-10-07: Validation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-07-01 | Step 1: no selection | Cannot proceed | Next button disabled |
| V10-07-02 | Step 2: empty name | Error shown | Inline validation message |
| V10-07-03 | Step 3: invalid action | Error shown | Action card shows warning |
| V10-07-04 | Step 4: save fails | Error toast | API error displayed |
| V10-07-05 | Duplicate app_id | Error on save | Conflict error shown |

### REQ-10-08: Edit Mode

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-08-01 | Navigate to /apps/:id | Edit mode | Existing app loaded |
| V10-08-02 | Fields pre-filled | All data shown | Name, desc, actions visible |
| V10-08-03 | Skip template step | Start at step 2 | Template step hidden |
| V10-08-04 | Save updates app | PATCH called | Existing app updated |
| V10-08-05 | Edit built-in | Read-only | Cannot save changes |

### REQ-10-09: Blank Template Flow

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-09-01 | Select blank template | Proceeds to step 2 | No error, allowed |
| V10-09-02 | Step 3 with 0 actions | Can proceed to step 4 | Next enabled with warning |
| V10-09-03 | Step 4 with 0 actions | Save disabled | Button grayed + tooltip |
| V10-09-04 | Add 1 action | Save enabled | Button becomes active |
| V10-09-05 | Warning shown | Info message visible | "Add at least 1 action" |

### REQ-10-10: State Schema Validation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V10-10-01 | Valid field name | Accepted | No error |
| V10-10-02 | Invalid field name (spaces) | Error shown | "Invalid field name" |
| V10-10-03 | Type/default mismatch | Error shown | "Default must be number" |
| V10-10-04 | perAgent true | Maps to per_agent | Preview shows structure |
| V10-10-05 | perAgent false | Maps to shared | Preview shows structure |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `web/src/pages/AppCreate.tsx` | Wizard container page |
| `web/src/pages/AppEdit.tsx` | Edit mode wrapper |
| `web/src/components/app-studio/AppWizard.tsx` | Wizard state machine |
| `web/src/components/app-studio/AppWizardSteps.tsx` | Step indicator |
| `web/src/components/app-studio/steps/TemplateStep.tsx` | Step 1 |
| `web/src/components/app-studio/steps/InfoStep.tsx` | Step 2 |
| `web/src/components/app-studio/steps/ActionsStep.tsx` | Step 3 |
| `web/src/components/app-studio/steps/TestStep.tsx` | Step 4 |
| `web/src/components/app-studio/TemplateCard.tsx` | Template card |
| `web/src/components/app-studio/ActionList.tsx` | Action list |
| `web/src/components/app-studio/ActionCard.tsx` | Action card |
| `web/src/components/app-studio/ActionBuilder.tsx` | Action modal |
| `web/src/components/app-studio/ParameterEditor.tsx` | Parameter form |
| `web/src/components/app-studio/IconPicker.tsx` | Icon picker |
| `web/src/lib/templates/index.ts` | Template definitions |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/App.tsx` | Add /apps/new and /apps/:id routes |

---

## References

- UI-ADR-006: Persona Builder - Wizard pattern
- UI-ADR-009: App Studio Library - Navigation context
- ADR-018: App Studio Backend - API integration
- ADR-019: App Definition Schema - Data validation
