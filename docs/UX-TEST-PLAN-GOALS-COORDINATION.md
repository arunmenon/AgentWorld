# UX Test Plan: Goal Taxonomy & Coordination Tracker

## Overview
This test plan covers manual UI testing for:
1. Goal Taxonomy UI (all 4 goal types)
2. Simulation creation with goal-based termination
3. Coordination tracking during simulations

## Prerequisites
- Backend running: `PYTHONPATH=src uvicorn agentworld.api.main:app --reload --port 8000`
- Frontend running: `cd web && npm run dev`
- Browser open at `http://localhost:5173`

---

## Test Suite 1: Task Creation with Goals

### Test 1.1: Create Task with State Goals
**Steps:**
1. Navigate to `/tasks/new`
2. Fill in basic task info (name, description, domain)
3. Go to "Goals" step
4. Click "Add Goal Condition"
5. Select **State** category (should be default)
6. Configure:
   - Goal Type: "State Equals"
   - App: Select an app (e.g., paypal_test)
   - Field Path: "balance"
   - Expected Value: 500
7. Add another State goal with "State Greater Than"
8. Proceed to Review step
9. Verify goals display correctly with blue "State" badges

**Expected:**
- [ ] State category shows 5 sub-types (equals, contains, greater, less, exists)
- [ ] App and Field inputs appear for State goals
- [ ] Review shows goals with proper formatting

---

### Test 1.2: Create Task with Action Goals
**Steps:**
1. Navigate to `/tasks/new`
2. Fill in basic task info
3. Go to "Goals" step
4. Add Goal Condition
5. Select **Action** category (amber tab)
6. Configure:
   - Goal Type: "Action Executed"
   - App: Select an app
   - Action Name: "transfer"
7. Add another with "Action Succeeded"
8. Proceed to Review

**Expected:**
- [ ] Action category shows 2 sub-types (executed, succeeded)
- [ ] App and Action Name inputs appear
- [ ] Review shows "Execute transfer on [app]" format

---

### Test 1.3: Create Task with Coordination Goals
**Steps:**
1. Navigate to `/tasks/new`
2. Fill in basic task info
3. Go to "Handoffs" step first - add at least 2 handoffs
4. Go to "Goals" step
5. Add Goal Condition
6. Select **Coordination** category (purple tab)
7. Configure:
   - Goal Type: "Handoff Completed"
   - Select a handoff from dropdown
8. Add another with "All Handoffs Done"
9. Proceed to Review

**Expected:**
- [ ] Coordination category shows 2 sub-types
- [ ] Handoff dropdown populated with defined handoffs
- [ ] "All Handoffs Done" doesn't require handoff selection
- [ ] Review shows "Handoff #X completed" format

---

### Test 1.4: Create Task with Output Goals
**Steps:**
1. Navigate to `/tasks/new`
2. Fill in basic task info
3. Go to "Goals" step
4. Add Goal Condition
5. Select **Output** category (green tab)
6. Configure:
   - Goal Type: "Output Contains"
   - Required Phrase: "transfer complete"
7. Proceed to Review

**Expected:**
- [ ] Output category shows 1 sub-type
- [ ] Required Phrase textarea appears
- [ ] Review shows "Agent says 'transfer complete'" format

---

### Test 1.5: Create Task with Mixed Goals (All 4 Types)
**Steps:**
1. Navigate to `/tasks/new`
2. Fill in task info and add handoffs
3. Go to "Goals" step
4. Add one goal of each type:
   - State: balance equals 350
   - Action: transfer executed
   - Coordination: handoff completed
   - Output: contains "confirmed"
5. Proceed to Review
6. Submit the task

**Expected:**
- [ ] All 4 goals display with correct category badges
- [ ] Task creation succeeds (201 response)
- [ ] Task appears in task list

---

## Test Suite 2: Simulation Creation with Goals

### Test 2.1: Create Simulation from Task with Goal Termination
**Steps:**
1. Navigate to `/simulations/new`
2. Click "Select from Tasks" or similar
3. Choose a task with goals defined
4. Verify:
   - Task info loads
   - Termination mode auto-selects "Goal"
   - Steps label changes to "Max Steps"
5. Set max steps to 20
6. Create simulation

**Expected:**
- [ ] Termination mode selector appears
- [ ] Default switches to "Goal" when task selected
- [ ] Helper text: "Simulation may stop earlier if goal is achieved"
- [ ] Simulation created successfully

---

### Test 2.2: Verify Goal Spec in Simulation Response
**Steps:**
1. After creating simulation in 2.1
2. Check simulation details (GET /api/v1/simulations/{id})
3. Or view simulation detail page

**Expected:**
- [ ] `goal` field present in response
- [ ] `goal.goal_spec.conditions` contains all defined goals
- [ ] `goal.termination_mode` is "goal"
- [ ] `goal.goal_achieved` is false initially

---

### Test 2.3: Termination Mode Selection
**Steps:**
1. Navigate to `/simulations/new`
2. Without selecting a task, verify termination mode options:
   - Max Steps (default)
   - Goal
   - Hybrid
3. Select each and verify UI changes

**Expected:**
- [ ] Three termination modes available
- [ ] "Max Steps" shows "Number of Steps" label
- [ ] "Goal"/"Hybrid" shows "Max Steps" label with helper text

---

## Test Suite 3: Simulation Execution with Goals

### Test 3.1: Run Simulation and Track Goal Progress
**Steps:**
1. Create a simulation with goals (from Test 2.1)
2. Start the simulation
3. Execute steps one at a time (POST /api/v1/simulations/{id}/step)
4. After each step, check simulation status

**Expected:**
- [ ] Simulation starts in "running" status
- [ ] `goal.goal_achieved` remains false until conditions met
- [ ] Current step increments

---

### Test 3.2: Goal Achievement Terminates Simulation
**Steps:**
1. Create a simple simulation with achievable goals
2. For testing, use Output goal with a common phrase
3. Run simulation until agent output matches
4. Check final status

**Expected:**
- [ ] When goal achieved, `goal.goal_achieved` becomes true
- [ ] `goal.goal_achieved_step` shows the step number
- [ ] Simulation status changes to "completed"
- [ ] Simulation stops before max_steps if goal achieved

---

## Test Suite 4: Coordination Tracker

### Test 4.1: Verify Coordination Events Logged
**Steps:**
1. Create a task with required handoffs
2. Create and run a simulation from that task
3. Check coordination events (GET /api/v1/dual-control-tasks/{id}/events)

**Expected:**
- [ ] Events logged as agents communicate
- [ ] Events include instructor_id, actor_id, instruction_text
- [ ] handoff_successful field populated

---

### Test 4.2: Coordination Metrics
**Steps:**
1. After running simulation in 4.1
2. Check metrics (GET /api/v1/dual-control-tasks/{id}/metrics)

**Expected:**
- [ ] `handoffs_completed` count accurate
- [ ] `coordination_success_rate` calculated
- [ ] `avg_instruction_to_action_turns` reasonable

---

## Test Suite 5: Edge Cases & Error Handling

### Test 5.1: Task with No Goals
**Steps:**
1. Create task without any goal conditions
2. Create simulation with "goal" termination mode
3. Run simulation

**Expected:**
- [ ] Simulation runs to max_steps (no goal to achieve)
- [ ] No errors in goal evaluation

---

### Test 5.2: Invalid Goal Configuration
**Steps:**
1. Try to create State goal without app selection
2. Try to create Coordination goal without handoff selection
3. Try to submit incomplete goals

**Expected:**
- [ ] Validation prevents submission
- [ ] Clear error messages shown

---

### Test 5.3: Hybrid Termination Mode
**Steps:**
1. Create simulation with hybrid mode
2. Set max_steps to 5
3. Define goal that won't be achieved quickly
4. Run simulation

**Expected:**
- [ ] Simulation stops at max_steps if goal not achieved
- [ ] OR stops early if goal achieved before max_steps

---

## Test Execution Checklist

| Test | Status | Notes |
|------|--------|-------|
| 1.1 State Goals | ⬜ | |
| 1.2 Action Goals | ⬜ | |
| 1.3 Coordination Goals | ⬜ | |
| 1.4 Output Goals | ⬜ | |
| 1.5 Mixed Goals | ⬜ | |
| 2.1 Simulation from Task | ⬜ | |
| 2.2 Goal Spec in Response | ⬜ | |
| 2.3 Termination Modes | ⬜ | |
| 3.1 Goal Progress | ⬜ | |
| 3.2 Goal Terminates Sim | ⬜ | |
| 4.1 Coordination Events | ⬜ | |
| 4.2 Coordination Metrics | ⬜ | |
| 5.1 No Goals | ⬜ | |
| 5.2 Invalid Config | ⬜ | |
| 5.3 Hybrid Mode | ⬜ | |

---

## Browser/Device Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile responsive view

---

## Notes
- Screenshots should be captured for any failures
- API responses should be logged for debugging
- Record any unexpected behaviors even if tests pass
