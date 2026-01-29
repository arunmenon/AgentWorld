# ADR-020 Gap Analysis: AgentWorld vs τ²-bench

> **Generated:** 2026-01-27
> **Updated:** 2026-01-29
> **Based on:** τ²-bench paper (arXiv:2506.07982) and architecture diagram

## Executive Summary

ADR-020.1 defined τ²-bench features. Classes are **implemented but not fully integrated**.
This document now tracks the **integration roadmap**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION STATUS MATRIX                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✅ IMPLEMENTED (classes exist, need integration)                          │
│   ├── DualControlTaskDefinition                                              │
│   ├── CoordinationTracker (now wired into simulation runner)                 │
│   ├── CoordinationHandoff, CoordinationEvent                                 │
│   ├── SemanticMatcher, InstructionTemplate                                   │
│   └── ToolType (READ/WRITE), AppAccessType                                   │
│                                                                              │
│   🔌 INTEGRATION COMPLETE                                                    │
│   ├── Simulation Runner ↔ CoordinationTracker (DONE)                         │
│   ├── GoalEvaluator reads handoff_log (DONE)                                 │
│   ├── Coordination events persisted to database (DONE)                       │
│   └── UX fetches real metrics via API (DONE)                                 │
│                                                                              │
│   ❌ NOT YET IMPLEMENTED                                                     │
│   ├── Gymnasium RL Interface                                                 │
│   ├── Interactive Play Mode CLI                                              │
│   └── User Simulator with LLM                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Status Matrix

| Feature | Class | Exported | Simulation Hook | API | CLI | E2E Test |
|---------|-------|----------|-----------------|-----|-----|----------|
| DualControlTaskDefinition | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| DualControlAgentEnv | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| DualControlUserEnv | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| CoordinationTracker | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| CoordinationHandoff | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| SemanticMatcher | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| InstructionTemplate | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| CompositionalTaskGenerator | ✅ | ❌ | N/A | ❌ | ❌ | ❌ |
| ToolType (READ/WRITE) | ✅ | ✅ | ✅ | ✅ | N/A | ✅ |
| AppAccessType | ✅ | ✅ | ✅ | ✅ | N/A | ✅ |
| GoalEvaluator (HANDOFF_COMPLETED) | ✅ | ✅ | ✅ | ✅ | N/A | ✅ |

Legend: ✅ Complete | ⚠️ Partial | ❌ Not done | N/A Not applicable

---

## 1. Dual-Control Environment

### Implementation Status: ✅ COMPLETE

**Files:**
- `src/agentworld/tasks/dual_control.py` (~890 lines)
- `src/agentworld/tasks/coordination.py` (~386 lines)
- `src/agentworld/environments/dual_control.py` (~300 lines)

**Classes/Functions:**
- `DualControlTaskDefinition` - Task with agent/user roles and required handoffs
- `CoordinationHandoff` - Required coordination points
- `DualControlAgentEnv` - Gymnasium env for agent
- `DualControlUserEnv` - Gymnasium env for user

### Integration Status: ✅ WIRED (as of 2026-01-29)

**What's done:**
- [x] Simulation runner initializes CoordinationTracker for dual-control tasks
- [x] `on_agent_message()` called when agent speaks
- [x] `on_app_action()` called when user executes action
- [x] Successful handoffs logged via `log_handoff()`
- [x] `to_dict()` includes coordination info

**What's missing:**
- [ ] Gym environments execute real app actions
- [ ] User simulator placeholder replaced with LLM
- [ ] E2E test for full dual-control flow

---

## 2. Tool Type Annotations

### Implementation Status: ✅ COMPLETE

**Files:**
- `src/agentworld/apps/definition.py` (~400 lines)

**Classes/Functions:**
- `ToolType` enum with READ, WRITE, READ_WRITE values
- `ActionDefinition.tool_type` field
- `AppAccessType` enum for agent/user/both access

### Integration Status: ✅ INTEGRATED

**What's done:**
- [x] ToolType enum defined and exported
- [x] ActionDefinition includes tool_type
- [x] API schemas support tool_type
- [x] Tests verify tool type annotations

**What's missing:**
- [ ] Annotate all existing app actions as READ/WRITE
- [ ] Policy enforcement based on tool types

---

## 3. Gymnasium RL Interface

### Implementation Status: ✅ COMPLETE (structure)

**Files:**
- `src/agentworld/environments/dual_control.py`

**Classes/Functions:**
- `DualControlAgentEnv(gym.Env)` - Agent-side environment
- `DualControlUserEnv(gym.Env)` - User-side environment

### Integration Status: ❌ NOT INTEGRATED

**What's missing:**
- [ ] Environments execute real app actions via app_manager
- [ ] Reward functions connected to goal evaluation
- [ ] Integration with RL training frameworks

---

## 4. Compositional Task Generator

### Implementation Status: ✅ COMPLETE

**Files:**
- `src/agentworld/tasks/generator.py` (~400 lines)

**Classes/Functions:**
- `AtomicTaskComponent` - Single action building block
- `TaskComposition` - Chain of components
- `CompositionalTaskGenerator` - Generates tasks from components

### Integration Status: ❌ NOT INTEGRATED

**What's missing:**
- [ ] Export in `__init__.py`
- [ ] `POST /api/v1/tasks/generate` endpoint
- [ ] `agentworld generate-task` CLI command

---

## 5. Interactive Play Mode

### Implementation Status: ❌ NOT IMPLEMENTED

**What's needed:**
- `agentworld play` CLI command
- Support agent/user/spectator modes
- Real-time state visualization

---

## 6. Coordination Tracking

### Implementation Status: ✅ COMPLETE

**Files:**
- `src/agentworld/tasks/coordination.py` (~386 lines)

**Classes/Functions:**
- `CoordinationTracker` - Monitors instruction→action handoffs
- `PendingInstruction` - Tracks awaited actions
- `analyze_coordination()` - Analysis utilities

### Integration Status: ✅ WIRED (as of 2026-01-29)

**Changes made to `simulation/runner.py`:**
```python
# New field
_coordination_tracker: "CoordinationTracker | None" = field(default=None, repr=False)

# Called in run():
self._initialize_coordination_tracker()

# Called in _step_sequential():
self._track_agent_message(agent.id, message.content)
self._track_app_action(agent_id, app_id, action_name, params)

# New methods:
_initialize_coordination_tracker()
get_coordination_metrics() -> CoordinationMetrics | None
_track_agent_message(agent_id, message_text)
_track_app_action(agent_id, app_id, action_name, params)
```

---

## 7. Goal-Based Termination

### Implementation Status: ✅ COMPLETE

**Files:**
- `src/agentworld/goals/types.py`
- `src/agentworld/goals/evaluator.py`

**Classes/Functions:**
- `GoalType` with HANDOFF_COMPLETED, COORDINATION_SUCCESS types
- `GoalEvaluator.evaluate()` reads `handoff_log`

### Integration Status: ✅ INTEGRATED

**What's done:**
- [x] GoalEvaluator reads _handoff_log
- [x] HANDOFF_COMPLETED goal type evaluates correctly
- [x] Simulation terminates when coordination goals met

---

## Integration Roadmap

### Phase 1: Simulation ↔ Dual-Control Wiring ✅ COMPLETE
- [x] Simulation runner calls CoordinationTracker.on_agent_message()
- [x] Simulation runner calls CoordinationTracker.on_app_action()
- [x] Successful handoffs populate _handoff_log
- [x] get_coordination_metrics() method available

### Phase 2: UX Real Data Connection ✅ COMPLETE
- [x] `GET /api/v1/simulations/{id}/coordination-metrics` endpoint
- [x] CoordinationPanel fetches real metrics via useQuery
- [x] Remove hardcoded estimates in SimulationDetail.tsx
- [x] Coordination events persisted to database via _persist_coordination_event()

### Phase 3: Gym Environment Integration
- [ ] Gym environments execute real app actions
- [ ] User simulator placeholder replaced with LLM
- [ ] RL training workflow tested

### Phase 4: Task Generator Integration
- [ ] Export CompositionalTaskGenerator in __init__.py
- [ ] Add `POST /api/v1/tasks/generate` endpoint
- [ ] Add `agentworld generate-task` CLI command

### Phase 5: End-to-End Testing
- [ ] Integration test: run dual-control task through simulation
- [ ] Verify coordination events automatically tracked
- [ ] Verify metrics computed correctly

### Phase 6: Interactive Play Mode
- [ ] Add `agentworld play` CLI command
- [ ] Support agent/user/spectator modes
- [ ] Real-time state visualization

---

## 8. Gap Summary Table (Updated)

| Feature | τ²-bench | ADR-020.1 | Status |
|---------|----------|-----------|--------|
| Dual-Control Task Definition | ✅ | ✅ | Implemented |
| User Instruction | ✅ | ✅ | Implemented |
| User Tools | ✅ | ✅ | Implemented |
| Tool READ/WRITE Types | ✅ | ✅ | Implemented |
| Coordination Tracking | ✅ | ✅ | **Fully integrated (runner + API + UX)** |
| Goal-based Termination | ✅ | ✅ | Integrated |
| Gymnasium RL Interface | ✅ | ⚠️ | Structure only |
| Compositional Task Gen | ✅ | ✅ | Not exported |
| Interactive Play Mode | ✅ | ❌ | Not implemented |
| User Simulator (LLM) | ✅ | ❌ | Placeholder only |

---

## 9. Conclusion

ADR-020.1 classes are **fully implemented**. As of 2026-01-29:

**Phase 1 ✅ CoordinationTracker wired into simulation runner:**
1. Automatic detection of agent instructions matching required handoffs
2. Tracking when users complete expected actions
3. Populating `_handoff_log` for goal evaluation
4. Coordination metrics available via `get_coordination_metrics()`

**Phase 2 ✅ UX connected to real coordination data:**
1. Coordination events persisted to database via `_persist_coordination_event()`
2. `GET /simulations/{id}/coordination-metrics` API endpoint
3. Frontend fetches real metrics (no more hardcoded estimates)
4. CoordinationPanel displays live data with polling during simulation

**Next priority:** Gym environment integration (Phase 3) - execute real app actions.

The -25 point performance drop when agents shift from solo to dual-control mode can now be measured once the full dual-control simulation flow is exercised.
