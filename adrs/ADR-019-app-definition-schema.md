# ADR-019: App Definition Schema & Logic Language

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **ADR-018**: App Studio Backend (DynamicApp, LogicEngine)
- **ADR-017**: Simulated Apps Framework (AppAction, AppResult types)

## Context

### Problem Statement
ADR-018 establishes the `DynamicApp` engine. This ADR defines the precise JSON schema for app definitions and the logic language specification that the engine executes.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-19-01 | Complete Schema | Must | JSON schema covers all app aspects |
| REQ-19-02 | Logic Block Types | Must | Support validate, update, notify, return, error, branch |
| REQ-19-03 | Expression Syntax | Must | Clear syntax for conditions and values |
| REQ-19-04 | Schema Validation | Must | Validate definitions before save |
| REQ-19-05 | Type Safety | Should | Type checking in expressions |
| REQ-19-06 | Loop Support | Should | Iteration over collections |
| REQ-19-07 | Built-in Functions | Should | Common functions (generate_id, timestamp, etc.) |
| REQ-19-08 | Error Messages | Should | Clear error messages for invalid logic |
| REQ-19-09 | Operator Precedence | Must | Clearly defined operator precedence |
| REQ-19-10 | Type Coercion Rules | Must | Explicit rules for type mismatches |
| REQ-19-11 | Loop Safeguards | Must | Iteration limits to prevent infinite loops |

## Decision

### App Definition Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AppDefinition",
  "type": "object",
  "required": ["app_id", "name", "category", "actions"],
  "properties": {
    "app_id": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "minLength": 2,
      "maxLength": 50,
      "description": "Unique identifier (snake_case)"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Display name"
    },
    "description": {
      "type": "string",
      "maxLength": 500
    },
    "category": {
      "type": "string",
      "enum": ["payment", "shopping", "communication", "calendar", "social", "custom"]
    },
    "icon": {
      "type": "string",
      "description": "Emoji or icon key"
    },
    "actions": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/ActionDefinition" }
    },
    "state_schema": {
      "type": "array",
      "items": { "$ref": "#/$defs/StateField" }
    },
    "initial_config": {
      "type": "object",
      "description": "Default config values"
    }
  },
  "$defs": {
    "ActionDefinition": {
      "type": "object",
      "required": ["name", "description", "logic"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z][a-z0-9_]*$"
        },
        "description": {
          "type": "string"
        },
        "parameters": {
          "type": "object",
          "additionalProperties": { "$ref": "#/$defs/ParamSpec" }
        },
        "returns": {
          "type": "object"
        },
        "logic": {
          "type": "array",
          "items": { "$ref": "#/$defs/LogicBlock" }
        }
      }
    },
    "ParamSpec": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": { "enum": ["string", "number", "boolean", "array", "object"] },
        "description": { "type": "string" },
        "required": { "type": "boolean", "default": false },
        "default": {},
        "minValue": { "type": "number" },
        "maxValue": { "type": "number" },
        "minLength": { "type": "integer" },
        "maxLength": { "type": "integer" },
        "pattern": { "type": "string" },
        "enum": { "type": "array" }
      }
    },
    "StateField": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "type": { "enum": ["string", "number", "boolean", "array", "object"] },
        "default": {},
        "perAgent": {
          "type": "boolean",
          "default": true,
          "description": "If true, stored in state.per_agent[agent_id]. If false, stored in state.shared."
        },
        "description": { "type": "string" }
      }
    },
    "LogicBlock": {
      "type": "object",
      "required": ["type"],
      "oneOf": [
        { "$ref": "#/$defs/ValidateBlock" },
        { "$ref": "#/$defs/UpdateBlock" },
        { "$ref": "#/$defs/NotifyBlock" },
        { "$ref": "#/$defs/ReturnBlock" },
        { "$ref": "#/$defs/ErrorBlock" },
        { "$ref": "#/$defs/BranchBlock" },
        { "$ref": "#/$defs/LoopBlock" }
      ]
    },
    "ValidateBlock": {
      "type": "object",
      "required": ["type", "condition", "errorMessage"],
      "properties": {
        "type": { "const": "validate" },
        "condition": { "type": "string" },
        "errorMessage": { "type": "string" }
      }
    },
    "UpdateBlock": {
      "type": "object",
      "required": ["type", "target", "operation", "value"],
      "properties": {
        "type": { "const": "update" },
        "target": { "type": "string" },
        "operation": { "enum": ["set", "add", "subtract", "append", "remove", "merge"] },
        "value": {}
      }
    },
    "NotifyBlock": {
      "type": "object",
      "required": ["type", "to", "message"],
      "properties": {
        "type": { "const": "notify" },
        "to": { "type": "string" },
        "message": { "type": "string" },
        "data": { "type": "object" }
      }
    },
    "ReturnBlock": {
      "type": "object",
      "required": ["type", "value"],
      "properties": {
        "type": { "const": "return" },
        "value": { "type": "object" }
      }
    },
    "ErrorBlock": {
      "type": "object",
      "required": ["type", "message"],
      "properties": {
        "type": { "const": "error" },
        "message": { "type": "string" }
      }
    },
    "BranchBlock": {
      "type": "object",
      "required": ["type", "condition", "then"],
      "properties": {
        "type": { "const": "branch" },
        "condition": { "type": "string" },
        "then": { "type": "array", "items": { "$ref": "#/$defs/LogicBlock" } },
        "else": { "type": "array", "items": { "$ref": "#/$defs/LogicBlock" } }
      }
    },
    "LoopBlock": {
      "type": "object",
      "required": ["type", "collection", "item", "body"],
      "properties": {
        "type": { "const": "loop" },
        "collection": { "type": "string" },
        "item": { "type": "string" },
        "body": { "type": "array", "items": { "$ref": "#/$defs/LogicBlock" } }
      }
    }
  }
}
```

### Logic Block Specifications

#### VALIDATE Block
Checks a condition and returns an error if it fails.

```json
{
  "type": "validate",
  "condition": "params.amount > 0",
  "errorMessage": "Amount must be positive"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "validate" | Yes | Block type identifier |
| condition | Expression | Yes | Boolean expression to evaluate |
| errorMessage | String/Expression | Yes | Error message if validation fails |

**Behavior:**
- Evaluates `condition` expression
- If `false`, immediately returns `AppResult(success=False, error=errorMessage)`
- If `true`, continues to next block

#### UPDATE Block
Modifies state values.

```json
{
  "type": "update",
  "target": "agent.balance",
  "operation": "subtract",
  "value": "params.amount"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "update" | Yes | Block type identifier |
| target | Path | Yes | State path to update |
| operation | Enum | Yes | `set`, `add`, `subtract`, `append`, `remove`, `merge` |
| value | Expression | Yes | Value to use in operation |

**Operations:**
- `set`: Replace value entirely
- `add`: Numeric addition (target + value)
- `subtract`: Numeric subtraction (target - value)
- `append`: Add item to array
- `remove`: Remove item from array
- `merge`: Shallow merge objects (value keys overwrite target keys)

**Merge Example:**
```json
{
  "type": "update",
  "target": "agent.preferences",
  "operation": "merge",
  "value": { "theme": "dark", "notifications": true }
}
```
If `agent.preferences` was `{"theme": "light", "locale": "en"}`, result is `{"theme": "dark", "locale": "en", "notifications": true}`.

#### NOTIFY Block
Creates an observation for another agent.

```json
{
  "type": "notify",
  "to": "params.to",
  "message": "You received ${params.amount} from ${agent.name}",
  "data": {
    "type": "received",
    "amount": "params.amount",
    "from": "agent.id"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "notify" | Yes | Block type identifier |
| to | Expression | Yes | Agent ID to notify |
| message | String (interpolated) | Yes | Human-readable message |
| data | Object | No | Structured data for observation |

**Behavior:**
- Creates an `AppObservation` for the target agent
- Interpolates `${...}` expressions in message
- Evaluates all expression values in data object

#### RETURN Block
Completes execution with success.

```json
{
  "type": "return",
  "value": {
    "transaction_id": "generate_id()",
    "new_balance": "agent.balance"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "return" | Yes | Block type identifier |
| value | Object | Yes | Return value (expressions evaluated) |

**Behavior:**
- Evaluates all expressions in `value` object
- Returns `AppResult(success=True, data=evaluated_value)`
- Stops execution immediately

#### ERROR Block
Completes execution with failure.

```json
{
  "type": "error",
  "message": "Insufficient funds"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "error" | Yes | Block type identifier |
| message | String/Expression | Yes | Error message to return |

**Behavior:**
- Interpolates expressions in message
- Returns `AppResult(success=False, error=message)`
- Stops execution immediately

#### BRANCH Block
Conditional execution path.

```json
{
  "type": "branch",
  "condition": "agent.balance >= params.amount",
  "then": [
    { "type": "update", "target": "agent.balance", "operation": "subtract", "value": "params.amount" }
  ],
  "else": [
    { "type": "error", "message": "Insufficient funds" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "branch" | Yes | Block type identifier |
| condition | Expression | Yes | Boolean condition |
| then | LogicBlock[] | Yes | Blocks to execute if true |
| else | LogicBlock[] | No | Blocks to execute if false |

**Behavior:**
- Evaluates `condition` expression
- If `true`, executes all blocks in `then`
- If `false`, executes all blocks in `else` (if present)
- If no `else` and condition is false, continues to next block

#### LOOP Block
Iterates over a collection.

```json
{
  "type": "loop",
  "collection": "state.pending_requests",
  "item": "request",
  "body": [
    { "type": "notify", "to": "request.from", "message": "Your request was processed" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | "loop" | Yes | Block type identifier |
| collection | Expression | Yes | Array to iterate |
| item | String | Yes | Variable name for current item |
| body | LogicBlock[] | Yes | Blocks to execute per item |

**Behavior:**
- Evaluates `collection` expression (must be array)
- For each item, sets `item` variable and executes `body`
- If any block returns, loop terminates and returns that result

**Safeguards (enforced per ADR-018):**
- Maximum `MAX_LOOP_ITERATIONS` (1000) iterations per loop
- Maximum `MAX_NESTED_DEPTH` (10) levels of nested loops/branches
- If limit exceeded, returns error: "Loop iteration limit exceeded"

### Expression Language Specification

#### Syntax Grammar
```
expression      := literal | path | function_call | binary_expr | unary_expr
literal         := number | string | boolean | null | object | array
path            := identifier ("." identifier | "[" expression "]")*
function_call   := identifier "(" (expression ("," expression)*)? ")"
binary_expr     := expression operator expression
unary_expr      := "!" expression

operator        := "==" | "!=" | "<" | ">" | "<=" | ">=" | "&&" | "||" | "+" | "-" | "*" | "/"
identifier      := [a-zA-Z_][a-zA-Z0-9_]*
number          := [0-9]+("." [0-9]+)?
string          := '"' [^"]* '"' | "'" [^']* "'"
boolean         := "true" | "false"
null            := "null"
object          := "{" (string ":" expression ("," string ":" expression)*)? "}"
array           := "[" (expression ("," expression)*)? "]"
```

#### Operator Precedence

Operators are evaluated in the following order (highest to lowest precedence):

| Precedence | Operator(s) | Associativity | Description |
|------------|-------------|---------------|-------------|
| 1 | `()` | - | Parentheses (grouping) |
| 2 | `.` `[]` `()` | Left-to-right | Member access, index, function call |
| 3 | `!` | Right-to-left | Logical NOT |
| 4 | `*` `/` | Left-to-right | Multiplication, division |
| 5 | `+` `-` | Left-to-right | Addition, subtraction |
| 6 | `<` `<=` `>` `>=` | Left-to-right | Relational comparison |
| 7 | `==` `!=` | Left-to-right | Equality comparison |
| 8 | `&&` | Left-to-right | Logical AND (short-circuit) |
| 9 | `||` | Left-to-right | Logical OR (short-circuit) |

**Examples:**
```
a + b * c        # Evaluates as: a + (b * c)
a || b && c      # Evaluates as: a || (b && c)
a > b && c < d   # Evaluates as: (a > b) && (c < d)
!a && b          # Evaluates as: (!a) && b
```

#### Type Coercion Rules

The expression language uses **strict typing** - no implicit coercion between incompatible types. This prevents subtle bugs and ensures predictable behavior.

| Operation | Allowed Types | Invalid Type Error |
|-----------|---------------|-------------------|
| `+` (addition) | number + number | "Cannot add {type1} and {type2}" |
| `+` (concatenation) | string + string | "Cannot add {type1} and {type2}" |
| `-`, `*`, `/` | number, number | "Cannot {op} {type1} and {type2}" |
| `<`, `<=`, `>`, `>=` | number, number OR string, string | "Cannot compare {type1} and {type2}" |
| `==`, `!=` | any, any (same type or null) | (always allowed) |
| `&&`, `||` | boolean, boolean | "Expected boolean, got {type}" |
| `!` | boolean | "Expected boolean, got {type}" |

**Null Handling:**
- `null == null` → `true`
- `null == <anything>` → `false`
- `x.missing_field` → `null` (safe navigation)
- `null + 1` → Error: "Cannot add null and number"

**Truthiness:** Only boolean `true`/`false` are valid in conditions. No implicit truthiness.
```
// VALID
if agent.active == true ...
if agent.balance > 0 ...

// INVALID (will error)
if agent.balance ...    # Error: "Expected boolean, got number"
if agent.name ...       # Error: "Expected boolean, got string"
```

#### String Interpolation
Within message strings, use `${expression}` for interpolation:
```
"You received $${params.amount} from ${agent.name}"
```
Note: Use `$$` to escape a literal `$`.

#### Context Variables
Available in all expressions. Aligned with ADR-018's canonical `AppState` structure:

| Variable | Type | Description | Maps to AppState |
|----------|------|-------------|------------------|
| `params` | Object | Action parameters from caller | (request input) |
| `agent` | Object | Calling agent's per-agent state | `state.per_agent[agent_id]` |
| `agents` | Object | All agents' per-agent states | `state.per_agent` |
| `shared` | Object | Shared state accessible to all | `state.shared` |
| `config` | Object | App configuration | (from definition) |

**Note:** The `agent` variable is a convenience shorthand. Writing to `agent.balance` is equivalent to writing to `agents[current_agent_id].balance`.

**Canonical State Structure (per ADR-018):**
```json
{
  "per_agent": {
    "alice": { "balance": 1000, "transactions": [] },
    "bob": { "balance": 1000, "transactions": [] }
  },
  "shared": {
    "total_transactions": 0,
    "fee_pool": 0
  }
}
```

#### Path Examples
```
params.amount             # Simple path to action parameter
agent.balance             # Current agent's per-agent state
agents["bob"].balance     # Other agent's per-agent state (bracket notation)
agents[params.to].name    # Dynamic key lookup
shared.fee_pool           # Shared state (all agents see same value)
shared.transactions[0]    # Array access in shared state
agent.history[-1]         # Last item (negative index)
```

#### Built-in Functions

| Function | Returns | Description | Example |
|----------|---------|-------------|---------|
| `generate_id()` | string | UUID v4 | `"tx-550e8400-e29b-..."` |
| `timestamp()` | string | ISO 8601 timestamp | `"2026-01-22T10:30:00Z"` |
| `now()` | number | Unix timestamp (ms) | `1737541800000` |
| `len(array)` | number | Array length | `len(agent.transactions)` |
| `contains(array, value)` | boolean | Array includes value | `contains(state.ids, params.id)` |
| `lower(string)` | string | Lowercase string | `lower(params.name)` |
| `upper(string)` | string | Uppercase string | `upper(params.code)` |
| `trim(string)` | string | Remove whitespace | `trim(params.input)` |
| `round(number, decimals?)` | number | Round number | `round(params.amount, 2)` |
| `min(a, b)` | number | Minimum value | `min(params.amount, agent.balance)` |
| `max(a, b)` | number | Maximum value | `max(0, result)` |
| `abs(number)` | number | Absolute value | `abs(params.delta)` |

### Complete Example: Payment Transfer Action

```json
{
  "name": "transfer",
  "description": "Send money to another user",
  "parameters": {
    "to": {
      "type": "string",
      "required": true,
      "description": "Recipient agent ID"
    },
    "amount": {
      "type": "number",
      "required": true,
      "minValue": 0.01,
      "maxValue": 10000,
      "description": "Amount to transfer"
    },
    "note": {
      "type": "string",
      "required": false,
      "maxLength": 200,
      "description": "Optional note"
    }
  },
  "returns": {
    "transaction_id": "string",
    "new_balance": "number"
  },
  "logic": [
    {
      "type": "validate",
      "condition": "params.to != agent.id",
      "errorMessage": "Cannot transfer to yourself"
    },
    {
      "type": "validate",
      "condition": "agents[params.to] != null",
      "errorMessage": "Recipient not found"
    },
    {
      "type": "validate",
      "condition": "params.amount <= agent.balance",
      "errorMessage": "Insufficient funds"
    },
    {
      "type": "update",
      "target": "agent.balance",
      "operation": "subtract",
      "value": "params.amount"
    },
    {
      "type": "update",
      "target": "agents[params.to].balance",
      "operation": "add",
      "value": "params.amount"
    },
    {
      "type": "update",
      "target": "agent.transactions",
      "operation": "append",
      "value": {
        "id": "generate_id()",
        "type": "sent",
        "to": "params.to",
        "amount": "params.amount",
        "timestamp": "timestamp()"
      }
    },
    {
      "type": "notify",
      "to": "params.to",
      "message": "You received $${params.amount} from ${agent.name}",
      "data": {
        "type": "received",
        "amount": "params.amount",
        "from": "agent.id",
        "note": "params.note"
      }
    },
    {
      "type": "return",
      "value": {
        "transaction_id": "generate_id()",
        "new_balance": "agent.balance"
      }
    }
  ]
}
```

### Complete Example: Full App Definition

```json
{
  "app_id": "simple_wallet",
  "name": "Simple Wallet",
  "description": "A simple digital wallet for transfers between users",
  "category": "payment",
  "icon": "💰",
  "state_schema": [
    {
      "name": "balance",
      "type": "number",
      "default": 1000,
      "perAgent": true,
      "description": "Account balance (stored in state.per_agent[id].balance)"
    },
    {
      "name": "transactions",
      "type": "array",
      "default": [],
      "perAgent": true,
      "description": "Transaction history (stored in state.per_agent[id].transactions)"
    },
    {
      "name": "total_transfers",
      "type": "number",
      "default": 0,
      "perAgent": false,
      "description": "Total transfers in system (stored in state.shared.total_transfers)"
    }
  ],
  "initial_config": {
    "balance": 1000
  },
  "actions": [
    {
      "name": "check_balance",
      "description": "View your current balance",
      "parameters": {},
      "returns": {
        "balance": "number"
      },
      "logic": [
        {
          "type": "return",
          "value": {
            "balance": "agent.balance"
          }
        }
      ]
    },
    {
      "name": "transfer",
      "description": "Send money to another user",
      "parameters": {
        "to": {
          "type": "string",
          "required": true,
          "description": "Recipient agent ID"
        },
        "amount": {
          "type": "number",
          "required": true,
          "minValue": 0.01,
          "description": "Amount to transfer"
        }
      },
      "returns": {
        "transaction_id": "string",
        "new_balance": "number"
      },
      "logic": [
        {
          "type": "validate",
          "condition": "params.to != agent.id",
          "errorMessage": "Cannot transfer to yourself"
        },
        {
          "type": "validate",
          "condition": "agents[params.to] != null",
          "errorMessage": "Recipient not found"
        },
        {
          "type": "validate",
          "condition": "params.amount <= agent.balance",
          "errorMessage": "Insufficient funds"
        },
        {
          "type": "update",
          "target": "agent.balance",
          "operation": "subtract",
          "value": "params.amount"
        },
        {
          "type": "update",
          "target": "agents[params.to].balance",
          "operation": "add",
          "value": "params.amount"
        },
        {
          "type": "notify",
          "to": "params.to",
          "message": "You received $${params.amount} from ${agent.name}",
          "data": {
            "type": "received",
            "amount": "params.amount",
            "from": "agent.id"
          }
        },
        {
          "type": "return",
          "value": {
            "transaction_id": "generate_id()",
            "new_balance": "agent.balance"
          }
        }
      ]
    }
  ]
}
```

## Consequences

### Positive
- Clear, documented schema enables tooling
- Logic is human-readable and auditable
- Expressions are powerful yet constrained
- Visual builder can be built on this foundation
- Schema validation catches errors before runtime

### Negative
- Schema complexity may overwhelm beginners
- Expression language is a mini-language to learn
- Some advanced logic patterns may be awkward
- Limited compared to full Python flexibility

### Neutral
- Requires documentation and examples
- Visual builder (UI-ADR-011) will hide complexity
- Templates will provide starting points

---

## Validation Checklist

### REQ-19-01: Complete Schema

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-01-01 | Validate minimal app | Valid | app_id, name, category, 1 action |
| V19-01-02 | Validate full app | Valid | All optional fields populated |
| V19-01-03 | Missing required field | Invalid | Clear error message |
| V19-01-04 | Invalid app_id format | Invalid | Pattern validation fails |
| V19-01-05 | Invalid category | Invalid | Enum validation fails |
| V19-01-06 | Empty actions array | Invalid | minItems validation fails |
| V19-01-07 | Invalid action name | Invalid | Pattern validation fails |
| V19-01-08 | Invalid param type | Invalid | Enum validation fails |

### REQ-19-02: Logic Block Types

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-02-01 | VALIDATE passes | Execution continues | Next block runs |
| V19-02-02 | VALIDATE fails | Error returned | AppResult.success=False |
| V19-02-03 | UPDATE set operation | Value replaced | state.field == newValue |
| V19-02-04 | UPDATE add operation | Value increased | state.field == old + value |
| V19-02-05 | UPDATE subtract | Value decreased | state.field == old - value |
| V19-02-06 | UPDATE append | Array extended | state.array.length++ |
| V19-02-07 | UPDATE remove | Item removed | Item not in array |
| V19-02-08 | NOTIFY creates observation | Observation queued | Recipient sees notification |
| V19-02-09 | RETURN exits with data | Execution stops | Correct data returned |
| V19-02-10 | ERROR exits with error | Execution stops | Error message returned |
| V19-02-11 | BRANCH true path | Then block runs | Correct blocks executed |
| V19-02-12 | BRANCH false path | Else block runs | Correct blocks executed |
| V19-02-13 | BRANCH no else | Continues | No error on false |

### REQ-19-03: Expression Syntax

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-03-01 | Number literal | Parsed | `42` → 42 |
| V19-03-02 | String literal | Parsed | `"hello"` → "hello" |
| V19-03-03 | Boolean literal | Parsed | `true` → true |
| V19-03-04 | Null literal | Parsed | `null` → null |
| V19-03-05 | Simple path | Resolved | `params.amount` → value |
| V19-03-06 | Nested path | Resolved | `agent.transactions[0].id` |
| V19-03-07 | Dynamic index | Resolved | `agents[params.to].balance` |
| V19-03-08 | Comparison operators | Evaluated | All ops work correctly |
| V19-03-09 | Logical AND | Evaluated | Short-circuits correctly |
| V19-03-10 | Logical OR | Evaluated | Short-circuits correctly |
| V19-03-11 | Arithmetic | Evaluated | `+`, `-`, `*`, `/` work |
| V19-03-12 | String interpolation | Interpolated | Variables replaced |
| V19-03-13 | Nested expressions | Evaluated | Complex expressions work |

### REQ-19-04: Schema Validation

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-04-01 | Valid definition | Passes validation | No errors |
| V19-04-02 | Syntax error in expression | Validation error | Clear error location |
| V19-04-03 | Invalid logic block type | Validation error | Type not in enum |
| V19-04-04 | Missing required logic field | Validation error | Field identified |
| V19-04-05 | Type mismatch in param | Validation error | Type conflict noted |

### REQ-19-05: Type Safety

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-05-01 | Number comparison with number | Works | No type error |
| V19-05-02 | String comparison with string | Works | No type error |
| V19-05-03 | Number comparison with string | Error/coercion | Defined behavior |
| V19-05-04 | Null access | Safe | Returns null, no crash |

### REQ-19-06: Loop Support

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-06-01 | Loop over array | Iterates all | Body runs for each item |
| V19-06-02 | Empty array | No iterations | Body never runs |
| V19-06-03 | Item variable accessible | Correct value | `item` has current element |
| V19-06-04 | Nested loops | Works | Inner/outer scopes correct |

### REQ-19-07: Built-in Functions

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-07-01 | generate_id() | Returns UUID | Format is valid UUID |
| V19-07-02 | timestamp() | Returns ISO string | Parseable timestamp |
| V19-07-03 | now() | Returns number | Unix ms timestamp |
| V19-07-04 | len(array) | Returns length | Correct count |
| V19-07-05 | contains(array, value) | Returns boolean | Correct membership |
| V19-07-06 | lower(string) | Returns lowercase | All lowercase |
| V19-07-07 | upper(string) | Returns uppercase | All uppercase |
| V19-07-08 | Unknown function | Error | Clear error message |

### REQ-19-08: Error Messages

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-08-01 | Undefined variable | Clear message | "Variable 'foo' is not defined" |
| V19-08-02 | Type error | Clear message | "Cannot add string and number" |
| V19-08-03 | Division by zero | Clear message | "Division by zero" |
| V19-08-04 | Array out of bounds | Clear message | "Index 5 out of range" |

### REQ-19-09: Operator Precedence

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-09-01 | Multiplication before addition | `2 + 3 * 4` → 14 | Math precedence |
| V19-09-02 | AND before OR | `true \|\| false && false` → true | Logical precedence |
| V19-09-03 | Comparison before logical | `1 < 2 && 3 > 2` → true | Relational precedence |
| V19-09-04 | Parentheses override | `(2 + 3) * 4` → 20 | Grouping works |
| V19-09-05 | NOT highest unary | `!true && false` → false | Unary precedence |
| V19-09-06 | Member access highest | `a.b + c` → a.b then + | Member precedence |

### REQ-19-10: Type Coercion Rules

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-10-01 | Number + Number | Sum | `5 + 3` → 8 |
| V19-10-02 | String + String | Concatenation | `"a" + "b"` → "ab" |
| V19-10-03 | Number + String | Type error | "Cannot add number and string" |
| V19-10-04 | Boolean in arithmetic | Type error | "Cannot add boolean and number" |
| V19-10-05 | Non-boolean in condition | Type error | "Expected boolean, got number" |
| V19-10-06 | Null comparison | Works | `null == null` → true |
| V19-10-07 | Null in arithmetic | Type error | "Cannot add null and number" |
| V19-10-08 | Safe navigation | Returns null | `agent.missing` → null |

### REQ-19-11: Loop Safeguards

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V19-11-01 | Loop under limit | Completes | 100 iterations succeeds |
| V19-11-02 | Loop at limit | Completes | 1000 iterations succeeds |
| V19-11-03 | Loop over limit | Error | "Loop iteration limit exceeded" |
| V19-11-04 | Nested loops | Limits apply per loop | Each loop has own counter |
| V19-11-05 | Deeply nested structures | Depth limit | "Maximum nesting depth exceeded" |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `src/agentworld/apps/schema.py` | JSON Schema definition and validator |
| `src/agentworld/apps/expression.py` | Expression parser and evaluator |
| `schemas/app_definition.schema.json` | Standalone JSON Schema file |

### Modified Files
| File | Changes |
|------|---------|
| `src/agentworld/apps/logic_engine.py` | Use expression evaluator |
| `src/agentworld/apps/dynamic.py` | Validate definitions against schema |

---

## JSON ↔ Python Field Mapping

Per ADR-020.1, the following table documents the canonical mapping between JSON schema field names (camelCase) and Python attribute names (snake_case):

| JSON Field | Python Attribute | Notes |
|------------|------------------|-------|
| `appId` | `app_id` | Also accepts `app_id` in JSON |
| `perAgent` | `per_agent` | StateFieldDef |
| `toolType` | `tool_type` | ActionDefinition (ADR-020.1) |
| `accessType` | `access_type` | AppDefinition (ADR-020.1) |
| `stateType` | `state_type` | AppDefinition (ADR-020.1) |
| `allowedRoles` | `allowed_roles` | AppDefinition (ADR-020.1) |
| `allowedRoleTags` | `allowed_role_tags` | AppDefinition (ADR-020.1) |
| `errorMessage` | `error_message` | ValidateBlock |
| `minValue` | `min_value` | ParamSpecDef |
| `maxValue` | `max_value` | ParamSpecDef |
| `minLength` | `min_length` | ParamSpecDef |
| `maxLength` | `max_length` | ParamSpecDef |
| `initialConfig` | `initial_config` | AppDefinition |
| `configSchema` | `config_schema` | AppDefinition |
| `stateSchema` | `state_schema` | AppDefinition |

**Serialization Rule:** When converting to JSON (`.to_dict()`), use camelCase. When parsing from JSON (`.from_dict()`), accept both camelCase and snake_case for robustness.

---

## Access Control Extension (ADR-020.1)

Per ADR-020.1, the App Definition schema is extended with access control fields for τ²-bench dual-control support:

### New Fields in AppDefinition

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `access_type` | `shared` \| `role_restricted` \| `per_agent` | `shared` | Who can access this app |
| `allowed_roles` | `string[]` | `null` | Roles that can access when role_restricted |
| `allowed_role_tags` | `string[]` | `null` | Additional tags for fine-grained access |
| `state_type` | `shared` \| `per_agent` | `shared` | How state is managed |

### New Field in ActionDefinition

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tool_type` | `read` \| `write` | `write` | Tool classification for analysis |

### Valid Access/State Combinations

| access_type | state_type | Valid | Example |
|-------------|------------|-------|---------|
| `shared` | `shared` | ✅ | Chat system |
| `shared` | `per_agent` | ✅ | Personal notepad |
| `role_restricted` | `shared` | ✅ | Backend DB |
| `role_restricted` | `per_agent` | ✅ | User device |
| `per_agent` | `shared` | ❌ | Invalid |
| `per_agent` | `per_agent` | ✅ | Personal sandbox |

---

## References

- ADR-018: App Studio Backend - Dynamic App Engine
- ADR-017: Simulated Apps Framework - Action/Result types
- ADR-020.1: Dual-Control Extension for τ²-bench Compatibility
- [JSON Schema Specification](https://json-schema.org/specification)
