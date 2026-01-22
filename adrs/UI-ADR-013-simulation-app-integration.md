# UI-ADR-013: Simulation App Integration

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **UI-ADR-003**: Simulation Control (SimulationCreate page)
- **UI-ADR-009**: App Studio Library (app listing)
- **ADR-017**: Simulated Apps Framework (app execution)
- **ADR-018**: App Studio Backend (dynamic apps)

## Context

### Problem Statement
Users need to add apps to simulations via the web UI. The SimulationCreate page needs an "Apps" section that integrates with the App Studio, allowing users to select and configure apps for their simulations.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-13-01 | Apps Section | Must | Apps section in SimulationCreate |
| REQ-13-02 | App Picker | Must | Browse and add apps |
| REQ-13-03 | App Configuration | Must | Configure app per simulation |
| REQ-13-04 | Remove App | Must | Remove app from simulation |
| REQ-13-05 | App Instructions | Should | Show agents how to use apps |
| REQ-13-06 | Multiple Apps | Should | Support multiple apps |
| REQ-13-07 | App Validation | Should | Validate app compatibility |
| REQ-13-08 | Undo Remove | Should | Toast with undo for app removal |
| REQ-13-09 | Config Schema | Should | Dynamic form from app's config_schema |

## Decision

### SimulationCreate Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│  Create Simulation                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  BASIC INFO                                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  [Name, description, steps - existing fields]                       │
│                                                                     │
│  AGENTS                                                             │
│  ─────────────────────────────────────────────────────────────────  │
│  [Agent selection - existing]                                       │
│                                                                     │
│  APPS (Optional)                                           NEW      │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Add simulated apps that agents can interact with during the        │
│  simulation.                                                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💳 PayPal                                  [Configure] [×]   │   │
│  │ Payment app • 6 actions • Initial balance: $500              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 📧 Gmail                                   [Configure] [×]   │   │
│  │ Email app • 4 actions • Inbox: empty                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [+ Add App]                                                        │
│                                                                     │
│  ℹ️ Agents will see instructions for using these apps in their     │
│  system prompt and can interact via APP_ACTION directives.          │
│                                                                     │
│  TOPOLOGY                                                           │
│  ─────────────────────────────────────────────────────────────────  │
│  [Topology selection - existing]                                    │
│                                                                     │
│                                         [Cancel]  [Create Simulation]│
└─────────────────────────────────────────────────────────────────────┘
```

### App Picker Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│  Add App                                                      [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Search apps...                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [All] [Payments] [Shopping] [Communication] [Custom]               │
│                                                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │ 💳              │ │ 🛒              │ │ 📧              │       │
│  │ PayPal          │ │ Amazon          │ │ Gmail           │       │
│  │ 6 actions       │ │ 5 actions       │ │ 4 actions       │       │
│  │                 │ │                 │ │                 │       │
│  │ [Add]           │ │ [Add]           │ │ [Added ✓]       │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│                                                                     │
│  ┌─────────────────┐ ┌─────────────────┐                           │
│  │ 📅              │ │ 🏦              │                           │
│  │ Calendar        │ │ My Venmo        │                           │
│  │ 4 actions       │ │ 4 actions       │                           │
│  │                 │ │                 │                           │
│  │ [Add]           │ │ [Add]           │                           │
│  └─────────────────┘ └─────────────────┘                           │
│                                                                     │
│  Can't find what you need? [Create a new app →]                    │
│                                                                     │
│                                                            [Done]   │
└─────────────────────────────────────────────────────────────────────┘
```

### App Configuration Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│  Configure: PayPal                                            [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INITIAL CONFIGURATION                                              │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Initial Balance                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 500                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Amount each agent starts with (default: 1000)                      │
│                                                                     │
│  Transaction Fee                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 0.00                                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Fee charged per transfer (default: 0)                              │
│                                                                     │
│  Daily Limit                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1000                                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Maximum transfer per day (default: 10000)                          │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  AVAILABLE ACTIONS                                                  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • check_balance - View current balance                       │   │
│  │ • transfer - Send money to another user                      │   │
│  │ • request_money - Request payment from another user          │   │
│  │ • view_transactions - See recent transactions                │   │
│  │ • pay_request - Pay a pending request                        │   │
│  │ • decline_request - Decline a pending request                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                                         [Cancel]  [Save Configuration]│
└─────────────────────────────────────────────────────────────────────┘
```

### Selected App Card

```
┌─────────────────────────────────────────────────────────────┐
│ 💳 PayPal                                  [Configure] [×]   │
│ ─────────────────────────────────────────────────────────── │
│ Payment app for sending and requesting money                │
│                                                             │
│ 6 actions: check_balance, transfer, request_money, ...      │
│                                                             │
│ Configuration:                                              │
│   Initial balance: $500                                     │
│   Transaction fee: $0.00                                    │
│   Daily limit: $1000                                        │
└─────────────────────────────────────────────────────────────┘
```

### Agent System Prompt Integration

When apps are added to a simulation, the agent system prompt is augmented:

```
You have access to the following apps:

## PayPal (payment)
A payment app for sending and requesting money.

Available actions:
- check_balance(): View your current balance
- transfer(to, amount, note?): Send money to another user
- request_money(from, amount, note?): Request payment from another user
- view_transactions(limit?): See recent transactions
- pay_request(request_id): Pay a pending request
- decline_request(request_id): Decline a pending request

To use an app, include an APP_ACTION directive in your message:
APP_ACTION: paypal.transfer(to="bob", amount=50.00, note="Lunch")

## Gmail (communication)
...
```

### Data Structures

```typescript
interface SimulationAppConfig {
  app_id: string;
  config: Record<string, unknown>;
}

interface SimulationCreatePayload {
  name: string;
  description?: string;
  agents: SimulationAgentConfig[];
  apps?: SimulationAppConfig[];  // NEW
  topology: TopologyConfig;
  max_steps: number;
}

interface AppSectionState {
  selectedApps: SimulationAppConfig[];
  isPickerOpen: boolean;
  isConfigOpen: boolean;
  configAppId: string | null;
}
```

### Component Architecture

```
web/src/components/simulation/
├── SimulationCreate.tsx       # Existing - add apps section
├── apps/
│   ├── AppsSection.tsx        # Apps section container
│   ├── AppConfigCard.tsx      # Single app config card
│   ├── AppPickerModal.tsx     # Browse/add apps modal
│   ├── AppConfigModal.tsx     # Configure app modal
│   └── AppInstructions.tsx    # Usage instructions preview
```

### App Selection Flow

```
┌──────────────┐    Click "Add App"    ┌───────────────────┐
│              │ ──────────────────────▶│                   │
│ Apps Section │                        │ App Picker Modal  │
│              │◀────────────────────── │                   │
└──────────────┘    Select app(s)      └───────────────────┘
       │
       │ Click "Configure"
       ▼
┌───────────────────┐
│                   │
│ App Config Modal  │
│                   │
└───────────────────┘
       │
       │ Save config
       ▼
┌──────────────────────────────────┐
│ Updated app card with config     │
└──────────────────────────────────┘
```

### Undo Toast for App Removal

When a user removes an app, show a toast with undo option instead of immediate permanent removal:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✓ PayPal removed                                      [Undo] [×]   │
└─────────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- App is removed from UI immediately (optimistic update)
- Toast appears for 5 seconds
- "Undo" restores the app with its configuration intact
- After timeout or navigation, removal is finalized
- If user clicks [×], removal is finalized immediately

```typescript
function removeApp(appId: string) {
  const removed = selectedApps.find(a => a.app_id === appId);
  setSelectedApps(apps => apps.filter(a => a.app_id !== appId));

  toast({
    title: `${removed.name} removed`,
    action: (
      <ToastAction onClick={() => restoreApp(removed)}>
        Undo
      </ToastAction>
    ),
    duration: 5000,
  });
}
```

### Config Schema Support

Apps can define a `config_schema` that describes their configurable fields. The configuration modal dynamically generates form fields from this schema.

**Config Schema Definition (in AppDefinition):**

```typescript
interface ConfigField {
  name: string;           // Field key (e.g., "initial_balance")
  label: string;          // Display label (e.g., "Initial Balance")
  type: 'string' | 'number' | 'boolean' | 'select';
  description?: string;   // Help text
  default?: unknown;      // Default value
  required?: boolean;
  // Type-specific constraints
  min?: number;           // For numbers
  max?: number;
  step?: number;
  options?: Array<{       // For select type
    value: string;
    label: string;
  }>;
  pattern?: string;       // For strings (regex)
}

interface AppDefinition {
  // ... other fields
  config_schema?: ConfigField[];
}
```

**Example Config Schema (PayPal):**

```json
{
  "config_schema": [
    {
      "name": "initial_balance",
      "label": "Initial Balance",
      "type": "number",
      "description": "Amount each agent starts with",
      "default": 1000,
      "min": 0,
      "max": 1000000,
      "step": 100
    },
    {
      "name": "transaction_fee",
      "label": "Transaction Fee",
      "type": "number",
      "description": "Fee charged per transfer",
      "default": 0,
      "min": 0,
      "max": 100,
      "step": 0.01
    },
    {
      "name": "daily_limit",
      "label": "Daily Limit",
      "type": "number",
      "description": "Maximum transfer per day",
      "default": 10000,
      "min": 0
    },
    {
      "name": "currency",
      "label": "Currency",
      "type": "select",
      "default": "USD",
      "options": [
        { "value": "USD", "label": "US Dollar ($)" },
        { "value": "EUR", "label": "Euro (€)" },
        { "value": "GBP", "label": "British Pound (£)" }
      ]
    }
  ]
}
```

**Dynamic Form Rendering:**

```typescript
function ConfigModalForm({ schema, values, onChange }: ConfigFormProps) {
  return (
    <form>
      {schema.map(field => (
        <FormField key={field.name}>
          <FormLabel>{field.label}{field.required && ' *'}</FormLabel>
          {renderFieldByType(field, values[field.name], onChange)}
          {field.description && (
            <FormDescription>{field.description}</FormDescription>
          )}
        </FormField>
      ))}
    </form>
  );
}

function renderFieldByType(field: ConfigField, value: unknown, onChange: Fn) {
  switch (field.type) {
    case 'number':
      return <Input type="number" min={field.min} max={field.max} step={field.step} ... />;
    case 'boolean':
      return <Switch checked={value as boolean} ... />;
    case 'select':
      return <Select options={field.options} value={value} ... />;
    default:
      return <Input type="text" pattern={field.pattern} ... />;
  }
}
```

**Fallback for Apps Without Schema:**

Apps without a `config_schema` show a JSON editor for raw config input:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Configure: Legacy App                                        [×]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  This app doesn't have a configuration schema.                      │
│  Enter configuration as JSON:                                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ {                                                            │   │
│  │   "custom_setting": 123                                      │   │
│  │ }                                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                                         [Cancel]  [Save Configuration]│
└─────────────────────────────────────────────────────────────────────┘
```

### Validation Rules

| Rule | Description |
|------|-------------|
| Unique apps | Cannot add same app twice |
| Valid config | Config values must pass app's schema validation |
| Active apps | Only active (non-deleted) apps can be added |
| Compatible agents | Warn if app expects more agents than selected |
| Required fields | Config schema required fields must be filled |

## Consequences

### Positive
- Seamless integration with simulation flow
- Visual configuration
- Clear app capabilities shown
- Link to App Studio for creation
- Consistent with existing form patterns

### Negative
- SimulationCreate form becomes longer
- Configuration options vary by app
- Must maintain sync between app definitions and config forms

### Neutral
- Apps are optional, won't break existing simulations
- Can be added/removed without affecting other settings

---

## Validation Checklist

### REQ-13-01: Apps Section

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-01-01 | Section visible | Apps section shown | In SimulationCreate |
| V13-01-02 | Section optional | No apps required | Can create without apps |
| V13-01-03 | Section position | After agents | Before topology |
| V13-01-04 | Help text shown | Explanation visible | "Agents can interact..." |

### REQ-13-02: App Picker

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-02-01 | Click Add App | Modal opens | Picker modal visible |
| V13-02-02 | Apps listed | All apps shown | System + user apps |
| V13-02-03 | Search works | Filtered results | Search by name |
| V13-02-04 | Categories work | Filtered results | Category tabs |
| V13-02-05 | Add app | App added | Appears in section |
| V13-02-06 | Already added | Disabled | "Added ✓" state |

### REQ-13-03: App Configuration

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-03-01 | Click Configure | Modal opens | Config form visible |
| V13-03-02 | Default values | Pre-filled | App defaults shown |
| V13-03-03 | Edit values | Values saved | Config updates |
| V13-03-04 | Actions listed | Read-only | Available actions shown |
| V13-03-05 | Save config | Modal closes | Values persisted |

### REQ-13-04: Remove App

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-04-01 | Click remove | App removed + toast | No longer in section |
| V13-04-02 | Toast shows undo | Undo button visible | Can restore app |
| V13-04-03 | Can re-add | App available | Back in picker |

### REQ-13-05: App Instructions

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-05-01 | Info text | Instructions shown | How agents use apps |
| V13-05-02 | Expand preview | Full instructions | System prompt preview |

### REQ-13-06: Multiple Apps

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-06-01 | Add second app | Both shown | Two app cards |
| V13-06-02 | Different configs | Independent | Each has own config |
| V13-06-03 | Order preserved | Consistent | Same order on reload |

### REQ-13-07: App Validation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-07-01 | Invalid config | Error shown | Validation message |
| V13-07-02 | Missing app | Warning | App was deleted |

### REQ-13-08: Undo Remove

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-08-01 | Remove shows toast | Toast appears | "App removed" message |
| V13-08-02 | Click Undo | App restored | Back in list with config |
| V13-08-03 | Toast timeout | Finalized | App stays removed |
| V13-08-04 | Close toast | Finalized | [×] closes toast |
| V13-08-05 | Multiple undos | Each tracked | Multiple toasts work |

### REQ-13-09: Config Schema

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V13-09-01 | App has schema | Form generated | Dynamic fields shown |
| V13-09-02 | Number field | Number input | min/max/step work |
| V13-09-03 | Boolean field | Toggle/switch | Checkbox renders |
| V13-09-04 | Select field | Dropdown | Options shown |
| V13-09-05 | Required field | Asterisk + validation | Cannot save empty |
| V13-09-06 | No schema | JSON editor | Fallback to raw JSON |
| V13-09-07 | Default values | Pre-filled | Schema defaults used |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `web/src/components/simulation/apps/AppsSection.tsx` | Apps section |
| `web/src/components/simulation/apps/AppConfigCard.tsx` | Config card |
| `web/src/components/simulation/apps/AppPickerModal.tsx` | Picker modal |
| `web/src/components/simulation/apps/AppConfigModal.tsx` | Config modal |
| `web/src/components/simulation/apps/AppInstructions.tsx` | Instructions |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/pages/SimulationCreate.tsx` | Add apps section |
| `web/src/lib/api/simulations.ts` | Include apps in payload |
| `src/agentworld/api/schemas/simulations.py` | Add apps field |

---

## References

- UI-ADR-003: Simulation Control - SimulationCreate context
- UI-ADR-009: App Studio Library - App listing patterns
- ADR-017: Simulated Apps Framework - App execution
- ADR-018: App Studio Backend - App definitions
