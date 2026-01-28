# ADR-020 Gap Analysis: AgentWorld vs τ²-bench

> **Generated:** 2026-01-27
> **Based on:** τ²-bench paper (arXiv:2506.07982) and architecture diagram

## Executive Summary

ADR-020 implemented τ-bench (2024) concepts but **misses the key innovations** from τ²-bench (2025), particularly the **dual-control environment** where both agent AND user have tools to modify shared state.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GAP SEVERITY MATRIX                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🔴 CRITICAL GAPS (missing core τ²-bench features)                         │
│   ├── Dual-Control Environment (Dec-POMDP)                                   │
│   ├── User Tools (separate from agent tools)                                 │
│   └── User Simulator with tool access                                        │
│                                                                              │
│   🟡 SIGNIFICANT GAPS (important features not implemented)                   │
│   ├── Gymnasium RL Interface                                                 │
│   ├── Compositional Task Generator                                           │
│   ├── Tool Type Annotations (READ/WRITE)                                     │
│   └── Interactive Play Mode                                                  │
│                                                                              │
│   🟢 PARTIAL GAPS (partially addressed)                                      │
│   ├── State Verification (have it, but single-side only)                     │
│   └── Policy Engine (have it, but no user-side policies)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 🔴 CRITICAL: Dual-Control Environment

### τ²-bench Architecture (from diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       τ²-bench DUAL-CONTROL MODEL                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐            ┌─────────────────────────┐         │
│  │    AGENT DOMAIN POLICY  │            │    USER INSTRUCTION     │         │
│  │                         │            │                         │         │
│  │  "As a telecom agent,   │            │  "Your mobile data is   │         │
│  │   you can help users    │            │   not working. Fix it." │         │
│  │   with technical        │            │                         │         │
│  │   support."             │            │                         │         │
│  └───────────┬─────────────┘            └───────────┬─────────────┘         │
│              │                                      │                        │
│              ▼                                      ▼                        │
│  ┌─────────────────────────┐            ┌─────────────────────────┐         │
│  │         AGENT           │◄──────────►│          USER           │         │
│  │                         │  dialogue  │                         │         │
│  └───────────┬─────────────┘            └───────────┬─────────────┘         │
│              │                                      │                        │
│              │ Agent Tools                          │ User Tools             │
│              │ ┌───────────────────┐               │ ┌───────────────────┐  │
│              │ │ @is_tool(READ)    │               │ │ @is_tool(READ)    │  │
│              │ │ get_customer_by_id│               │ │ get_status_bar()  │  │
│              │ │ get_details_by_id │               │ │ check_settings()  │  │
│              │ └───────────────────┘               │ └───────────────────┘  │
│              │ ┌───────────────────┐               │ ┌───────────────────┐  │
│              │ │ @is_tool(WRITE)   │               │ │ @is_tool(WRITE)   │  │
│              │ │ enable_roaming()  │               │ │ toggle_data()     │  │
│              │ │ change_plan()     │               │ │ toggle_airplane() │  │
│              │ └───────────────────┘               │ └───────────────────┘  │
│              │                                      │                        │
│              ▼                                      ▼                        │
│  ┌─────────────────────────┐            ┌─────────────────────────┐         │
│  │       AGENT DB          │            │        USER DB          │         │
│  │  ┌─────────────────┐    │            │  ┌─────────────────┐    │         │
│  │  │ [[customers]]   │    │            │  │ [device]        │    │         │
│  │  │ customer_id     │    │◄═══════════►  │ sim_card_status │    │         │
│  │  │ full_name       │    │   SHARED   │  │ airplane_mode   │    │         │
│  │  │ phone_number    │    │   WORLD    │  │ battery_level   │    │         │
│  │  │ ...             │    │            │  │ data_enabled    │    │         │
│  │  └─────────────────┘    │            │  └─────────────────┘    │         │
│  └─────────────────────────┘            └─────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ADR-020 Current Architecture (SINGLE-CONTROL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADR-020 SINGLE-CONTROL MODEL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐                                                │
│  │    AGENT INSTRUCTION    │                                                │
│  │                         │                                                │
│  │  "Transfer $50 from     │       ❌ NO USER INSTRUCTION                   │
│  │   Alice to Bob"         │       ❌ NO USER TOOLS                         │
│  │                         │       ❌ NO USER DB                            │
│  └───────────┬─────────────┘                                                │
│              │                                                              │
│              ▼                                                              │
│  ┌─────────────────────────┐                                                │
│  │      AGENT (Alice)      │                                                │
│  │                         │                                                │
│  └───────────┬─────────────┘                                                │
│              │                                                              │
│              │ App Actions (agent only)                                     │
│              │ ┌───────────────────┐                                        │
│              │ │ check_balance()   │    ❌ No READ/WRITE distinction        │
│              │ │ transfer()        │                                        │
│              │ │ get_transactions()│                                        │
│              │ └───────────────────┘                                        │
│              │                                                              │
│              ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         APP STATE                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ { "Alice": { "balance": 1000 }, "Bob": { "balance": 500 } } │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gap Details

| Aspect | τ²-bench | ADR-020 | Gap |
|--------|----------|---------|-----|
| Control Model | **Dual** (agent + user) | Single (agent only) | 🔴 Missing |
| User Tools | Yes (`toggle_data`, etc.) | No | 🔴 Missing |
| User Instruction | Yes (explicit goal) | No | 🔴 Missing |
| Separate DBs | Agent DB + User DB | Single app state | 🔴 Missing |
| Dec-POMDP | Yes (partial observability) | No (full observability) | 🔴 Missing |

### Impact

Without dual-control:
- **Cannot test coordination** between agent and user
- **Cannot measure communication quality** (agent guiding user)
- **Cannot detect the -25 point performance drop** seen in τ²-bench research
- **Cannot model real tech support** scenarios

---

## 2. 🔴 CRITICAL: Tool Type Annotations

### τ²-bench Pattern

```python
# τ²-bench tool definitions
@is_tool(ToolType.READ)
def get_customer_by_id(customer_id: str) -> Customer:
    """Retrieves a customer directly by their unique ID."""
    ...

@is_tool(ToolType.WRITE)
def toggle_airplane_mode() -> str:
    """Turns Airplane Mode ON or OFF. When ON, it disconnects
    all wireless communications including cellular, Wi-Fi, and Bluetooth."""
    ...
```

### ADR-020/ADR-017 Pattern

```python
# Current AgentWorld app actions - no READ/WRITE distinction
class PayPalApp(BaseSimulatedApp):
    def execute(self, agent_id: str, action: str, params: dict) -> AppResult:
        match action:
            case "check_balance":    # Is this READ or WRITE? Unknown
                ...
            case "transfer":         # Is this READ or WRITE? Unknown
                ...
```

### Why It Matters

- **Ablation studies**: τ²-bench can test "READ-only agent" vs "full agent"
- **Policy enforcement**: "User can only use WRITE tools after agent confirms"
- **Safety analysis**: Track which actions modify state vs query state

---

## 3. 🟡 SIGNIFICANT: Gymnasium RL Interface

### τ²-bench Implementation

```python
# τ²-bench Gymnasium environments
from tau2.gym import AgentGymEnv, UserGymEnv

# Train agent with RL
env = AgentGymEnv(domain="telecom")
obs, info = env.reset()
while not done:
    action = agent.select_action(obs)
    obs, reward, done, truncated, info = env.step(action)

# Train user simulator with RL
env = UserGymEnv(domain="telecom", agent_llm="gpt-4.1")
```

### ADR-020 Status

**Not implemented.** No Gymnasium interface exists.

### Recommendation

```python
# Proposed for AgentWorld
class AgentWorldGymEnv(gym.Env):
    """Gymnasium wrapper for AgentWorld simulations."""

    def __init__(self, app_id: str, task_id: str):
        self.app = AppRegistry.get(app_id)
        self.task = TaskRepository.get(task_id)

    def step(self, action: dict) -> tuple:
        result = self.app.execute(self.agent_id, action["name"], action["params"])
        reward = self._compute_reward(result)
        done = self._check_goal_state()
        return self._get_obs(), reward, done, False, {}
```

---

## 4. 🟡 SIGNIFICANT: Compositional Task Generator

### τ²-bench Approach

```python
# τ²-bench generates tasks from atomic components
atomic_actions = [
    "toggle_mobile_data",
    "check_data_limit",
    "enable_roaming",
    "verify_sim_status"
]

# Compositional generator creates complex tasks
task = compose_task(
    preconditions=["data_disabled", "sim_active"],
    goal_state=["data_enabled", "roaming_on"],
    max_steps=5
)
# Output: Verified task with automatic ground truth
```

### ADR-020 Approach

```python
# Manual task definitions only
PAYMENT_SCENARIOS = [
    TaskDefinition(
        task_id="payment_simple_transfer",
        name="Simple Transfer",
        # ... manually specified everything ...
        expected_final_states={"paypal": {"Alice": {"balance": 450}, ...}},
        expected_actions=[ExpectedAction(...)],  # Manually listed
    )
]
```

### Recommendation

Implement a compositional task generator:

```python
class TaskComposer:
    """Generate tasks from atomic action components."""

    def compose(self, app: BaseSimulatedApp, complexity: int) -> TaskDefinition:
        # 1. Get available actions from app
        actions = app.get_actions()

        # 2. Generate random valid initial state
        initial = self._random_valid_state(app.state_schema)

        # 3. Select action sequence of given complexity
        action_seq = self._select_actions(actions, complexity)

        # 4. Compute expected final state by simulation
        expected = self._simulate(initial, action_seq)

        # 5. Return verified task definition
        return TaskDefinition(
            task_id=f"auto_{uuid4()}",
            initial_app_states=initial,
            expected_final_states=expected,
            expected_actions=action_seq,
            # Automatically verified!
        )
```

---

## 5. 🟡 SIGNIFICANT: Interactive Play Mode

### τ²-bench CLI

```bash
# Interactive debugging
$ tau2 play

? Select mode: (Use arrow keys)
 ❯ Agent (control the agent, LLM plays user)
   User (control the user, LLM plays agent)
   Spectator (watch LLM vs LLM)

[Agent] > check_customer_by_id("C1001")
{customer_id: "C1001", full_name: "John Smith", ...}

[User says] My mobile data is not working. It is very slow.

[Agent] > What would you like to say?
```

### ADR-020 Status

**No interactive mode.** Only batch evaluation via API.

### Recommendation

```bash
# Proposed for AgentWorld
$ agentworld play --app paypal --task payment_simple_transfer

? Select role: Agent | User | Spectator

[Simulation: payment_simple_transfer]
Initial State:
  Alice: {balance: $500}
  Bob: {balance: $100}

[Alice] What action? > check_balance
Result: {balance: 500}

[Alice] What action? > transfer --to bob --amount 50
Result: {success: true, new_balance: 450}
...
```

---

## 6. Gap Summary Table

| Feature | τ²-bench | ADR-020 | Priority | Effort |
|---------|----------|---------|----------|--------|
| Dual-Control (Dec-POMDP) | ✅ | ❌ | 🔴 Critical | High |
| User Tools | ✅ | ❌ | 🔴 Critical | High |
| User Instruction | ✅ | ❌ | 🔴 Critical | Medium |
| Tool READ/WRITE Types | ✅ | ❌ | 🟡 Significant | Low |
| Gymnasium RL Interface | ✅ | ❌ | 🟡 Significant | Medium |
| Compositional Task Gen | ✅ | ❌ | 🟡 Significant | Medium |
| Interactive Play Mode | ✅ | ❌ | 🟡 Significant | Medium |
| Public Leaderboard | ✅ | ❌ | 🟢 Nice-to-have | High |
| Train/Test Splits | ✅ | ⚠️ Partial | 🟢 Nice-to-have | Low |

---

## 7. Proposed ADR-020.1: Dual-Control Extension

### Overview

Extend ADR-020 to support τ²-bench style dual-control environments.

### New Data Structures

```python
@dataclass
class DualControlTaskDefinition(TaskDefinition):
    """Extended task definition for dual-control scenarios."""

    # User-side additions
    user_instruction: str           # What the user is trying to accomplish
    user_tools: list[ToolDefinition]  # Tools available to user
    user_initial_state: dict        # User's device/context state

    # Separate DBs
    agent_db_schema: dict           # Agent-accessible state
    user_db_schema: dict            # User-accessible state (device)
    shared_state_schema: dict       # Both can observe

    # Coordination requirements
    required_coordination: list[str]  # e.g., ["agent_instructs_user_toggle"]

class ToolType(Enum):
    READ = "read"
    WRITE = "write"

@dataclass
class ToolDefinition:
    """Tool with READ/WRITE annotation."""
    name: str
    description: str
    tool_type: ToolType
    parameters: dict
    returns: dict
    owner: Literal["agent", "user", "both"]
```

### Architecture Update

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADR-020.1 DUAL-CONTROL MODEL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐            ┌─────────────────────────┐         │
│  │    AGENT (LLM)          │◄──────────►│    USER SIMULATOR       │         │
│  │    + Agent Policy       │  dialogue  │    + User Instruction   │         │
│  └───────────┬─────────────┘            └───────────┬─────────────┘         │
│              │                                      │                        │
│              │ Agent Tools                          │ User Tools             │
│              │ (READ/WRITE)                         │ (READ/WRITE)           │
│              ▼                                      ▼                        │
│  ┌─────────────────────────┐            ┌─────────────────────────┐         │
│  │    AGENT-SIDE STATE     │◄═══════════►    USER-SIDE STATE     │         │
│  │    (account, plans)     │   SHARED   │    (device settings)   │         │
│  └─────────────────────────┘   WORLD    └─────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Metrics

```python
@dataclass
class DualControlMetrics:
    """Extended metrics for dual-control evaluation."""

    # Standard pass^k
    pass_k: dict[int, float]

    # Dual-control specific
    coordination_success: float    # Did agent successfully guide user?
    user_action_efficiency: float  # User actions / minimum required
    communication_clarity: float   # LLM-judged instruction quality

    # Ablation comparisons
    solo_mode_pass_1: float       # Agent with full info
    dual_mode_pass_1: float       # Agent must guide user
    performance_drop: float       # solo - dual (expect ~25 points)
```

---

## 8. Implementation Roadmap

### Phase 1: Tool Type Annotations (1-2 days)
- Add `ToolType` enum to ADR-017/ADR-018
- Annotate existing app actions as READ/WRITE
- Update API schemas

### Phase 2: User Simulator Framework (3-5 days)
- Create `UserSimulator` class with tool access
- Add `user_instruction` to `TaskDefinition`
- Implement user-side state management

### Phase 3: Dual-Control Environment (5-7 days)
- Implement Dec-POMDP style partial observability
- Add agent DB / user DB separation
- Create coordination tracking

### Phase 4: Interactive Play Mode (2-3 days)
- Add `agentworld play` CLI command
- Support agent/user/spectator modes
- Real-time state visualization

### Phase 5: Gymnasium Interface (3-4 days)
- Implement `AgentWorldGymEnv`
- Add reward functions
- Support RL training workflows

### Phase 6: Compositional Task Generator (3-4 days)
- Implement atomic action library
- Build task composer
- Auto-generate ground truth

---

## 9. Conclusion

ADR-020 provides a solid foundation with pass^k, state verification, and fault classification. However, it was based on τ-bench (2024) and **misses the key dual-control innovation** from τ²-bench (2025).

The -25 point performance drop when agents shift from solo to dual-control mode is a **critical finding** that AgentWorld cannot currently measure or study.

**Recommendation:** Prioritize implementing dual-control support (Phases 1-3) before RL interface and task generation.
