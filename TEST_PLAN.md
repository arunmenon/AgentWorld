# AgentWorld Comprehensive Test Plan

## Overview
This document outlines the complete testing strategy for AgentWorld, covering all features across Dashboard, Personas, Simulations, App Studio, and end-to-end scenarios.

---

## Test Scenarios

### 1. Dashboard (/)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| D-01 | Dashboard loads | Navigate to / | Shows statistics, recent simulations |
| D-02 | Stats display | Check stats cards | Shows simulation count, agent count, message count |
| D-03 | Recent simulations | View recent list | Shows last 5 simulations with status |
| D-04 | Quick actions | Check action buttons | Create simulation, create persona buttons work |
| D-05 | Navigation | Click sidebar items | All nav links route correctly |

---

### 2. Personas (/personas)

#### 2.1 Persona Library

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| P-01 | List personas | Navigate to /personas | Shows all personas in grid |
| P-02 | Search personas | Type in search box | Filters personas by name/description |
| P-03 | Filter by occupation | Select occupation filter | Shows only matching personas |
| P-04 | Empty state | Delete all personas | Shows "No personas" message |
| P-05 | Persona card display | View persona card | Shows name, traits, tags, usage count |

#### 2.2 Create Persona

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| P-06 | Open create modal | Click "Create Persona" | Modal opens with empty form |
| P-07 | Fill basic info | Enter name, description, occupation | Fields accept input |
| P-08 | Set personality traits | Adjust Big Five sliders | Values 0-100 update |
| P-09 | Add tags | Type and add tags | Tags appear as chips |
| P-10 | Save persona | Click Save | Persona created, appears in list |
| P-11 | Validation - empty name | Submit without name | Shows error message |
| P-12 | Cancel create | Click Cancel | Modal closes, no persona created |

#### 2.3 Edit/Delete Persona

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| P-13 | Edit persona | Click edit on card | Modal opens with existing data |
| P-14 | Update fields | Change name, save | Persona updated in list |
| P-15 | Delete persona | Click delete, confirm | Persona removed from list |
| P-16 | Delete cancel | Click delete, cancel | Persona remains |

#### 2.4 Collections

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| P-17 | Create collection | Click "New Collection" | Collection created |
| P-18 | Add persona to collection | Drag or select | Persona added to collection |
| P-19 | View collection | Click collection | Shows personas in collection |
| P-20 | Remove from collection | Click remove | Persona removed from collection |
| P-21 | Delete collection | Click delete | Collection deleted, personas remain |

---

### 3. Simulations

#### 3.1 Simulation List (/simulations)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| S-01 | List simulations | Navigate to /simulations | Shows all simulations |
| S-02 | Filter by status | Click status tabs | Filters to running/completed/pending |
| S-03 | Search simulations | Type in search | Filters by name |
| S-04 | Simulation card info | View card | Shows name, status, progress, agents |
| S-05 | Quick actions | Click play/pause | Controls simulation |

#### 3.2 Create Simulation (/simulations/new)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| S-06 | Template selection | View templates | Shows 6 templates (Board Meeting, etc.) |
| S-07 | Select template | Click template | Pre-fills configuration |
| S-08 | Start from scratch | Click "Start from scratch" | Empty configuration |
| S-09 | Set basic info | Enter name, steps, prompt | Fields accept input |
| S-10 | Add agent | Click "Add Agent" | New agent form appears |
| S-11 | Configure agent | Set name, background, traits | Agent configured |
| S-12 | Remove agent | Click delete on agent | Agent removed (min 2 required) |
| S-13 | Add app | Click "Add App" | App picker opens |
| S-14 | Configure app | Click Configure on app | Config modal opens |
| S-15 | Create simulation | Click Create | Simulation created, redirects |
| S-16 | Validation | Submit without name | Shows error |

#### 3.3 Simulation Detail (/simulations/:id)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| S-17 | View simulation | Navigate to detail | Shows simulation info |
| S-18 | View agents | Click Agents tab | Lists all agents with stats |
| S-19 | View messages | Click Messages tab | Shows conversation timeline |
| S-20 | Filter messages | Filter by agent/step | Filters message list |
| S-21 | Agent detail | Click agent | Shows agent memories, traits |

#### 3.4 Simulation Controls

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| S-22 | Start simulation | Click Start | Status changes to "running" |
| S-23 | Pause simulation | Click Pause | Status changes to "paused" |
| S-24 | Resume simulation | Click Resume | Continues running |
| S-25 | Step simulation | Click Step | Executes 1 step, shows new messages |
| S-26 | Inject stimulus | Enter text, inject | Stimulus sent to agents |
| S-27 | Delete simulation | Click Delete, confirm | Simulation removed |

#### 3.5 Export & Evaluation

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| S-28 | View export formats | Click Export | Shows available formats |
| S-29 | Export JSON | Select JSON, export | Downloads JSON file |
| S-30 | Export CSV | Select CSV, export | Downloads CSV file |
| S-31 | Run evaluation | Click Evaluate | Evaluations run |
| S-32 | View eval summary | View summary tab | Shows scores, pass rates |

---

### 4. App Studio

#### 4.1 App Library (/apps)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| A-01 | List apps | Navigate to /apps | Shows all app definitions |
| A-02 | Search apps | Type in search | Filters by name/description |
| A-03 | Filter by category | Click category tab | Shows only category apps |
| A-04 | App card display | View card | Shows icon, name, actions count |
| A-05 | Grid/List toggle | Click view buttons | Switches layout |

#### 4.2 Create App (/apps/new)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| A-06 | Step 1: Templates | View templates | Shows 6 templates + blank |
| A-07 | Select template | Click template | Template selected |
| A-08 | Step 2: Info | Fill name, desc | App ID auto-generates |
| A-09 | Select category | Click category | Category selected |
| A-10 | Select icon | Click icon | Icon selected |
| A-11 | Step 3: Actions | View actions | Shows template actions |
| A-12 | Add action | Click Add Action | Action builder opens |
| A-13 | Edit action | Click Edit | Action builder with data |
| A-14 | Delete action | Click Delete | Action removed |
| A-15 | Reorder actions | Use up/down arrows | Order changes |

#### 4.3 Visual Logic Builder

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| A-16 | Open builder | Click Visual Builder | Canvas opens |
| A-17 | View nodes | See canvas | Start → Return nodes visible |
| A-18 | Drag block | Drag from palette | New block added |
| A-19 | Connect blocks | Drag edge | Connection created |
| A-20 | Select block | Click block | Config panel shows |
| A-21 | Edit block config | Change condition | Block updates |
| A-22 | Delete block | Click Delete Block | Block removed |
| A-23 | JSON view | Click JSON tab | Shows JSON representation |
| A-24 | Apply changes | Click Apply | Changes saved to action |

#### 4.4 Test Sandbox

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| A-25 | Step 4: Test | Navigate to test | Sandbox loads |
| A-26 | Select agent | Choose from dropdown | Agent selected |
| A-27 | Select action | Choose action | Parameters form shows |
| A-28 | Fill parameters | Enter values | Values accepted |
| A-29 | Execute action | Click Execute | Result displayed |
| A-30 | View state | Check state panel | Agent states shown |
| A-31 | Execution log | View log | Shows action history |
| A-32 | Reset state | Click Reset | State returns to initial |

#### 4.5 Save & Edit App

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| A-33 | Save app | Click Save App | App created, in library |
| A-34 | Edit app | Click Edit on card | Opens at step 2 |
| A-35 | Update app | Change name, save | App updated |
| A-36 | Delete app | Click delete, confirm | App removed |
| A-37 | Duplicate app | Click duplicate | Copy created |

---

### 5. Settings (/settings)

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| ST-01 | View settings | Navigate to /settings | Settings page loads |
| ST-02 | API configuration | View API settings | Shows model settings |
| ST-03 | Theme toggle | Click theme switch | Theme changes |

---

### 6. End-to-End Scenarios

#### 6.1 Complete Simulation Flow

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| E2E-01 | Create persona → Use in simulation | 1. Create persona with traits<br>2. Create simulation<br>3. Add persona as agent<br>4. Run simulation | Persona traits affect agent behavior |

#### 6.2 App Integration Flow

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| E2E-02 | Create app → Use in simulation | 1. Create payment app<br>2. Create simulation with app<br>3. Run simulation<br>4. Agent uses app actions | App actions appear in messages |

#### 6.3 Full Workflow

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| E2E-03 | Complete workflow | 1. Create 2 personas<br>2. Create payment app<br>3. Create simulation with personas + app<br>4. Run 5 steps<br>5. Export results | All components work together |

---

### 7. Error Handling

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| ERR-01 | Network error | Disable network | Error message shown |
| ERR-02 | 404 page | Navigate to /invalid | 404 page shown |
| ERR-03 | API error | Trigger backend error | Toast notification |
| ERR-04 | Validation errors | Submit invalid data | Field-level errors |

---

### 8. API Health

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| API-01 | Health endpoint | GET /api/v1/health | Returns healthy status |
| API-02 | Personas CRUD | Test all endpoints | All return correct data |
| API-03 | Simulations CRUD | Test all endpoints | All return correct data |
| API-04 | App Definitions CRUD | Test all endpoints | All return correct data |

---

## Test Execution Checklist

- [ ] Dashboard (5 tests)
- [ ] Personas (21 tests)
- [ ] Simulations (32 tests)
- [ ] App Studio (37 tests)
- [ ] Settings (3 tests)
- [ ] End-to-End (3 tests)
- [ ] Error Handling (4 tests)
- [ ] API Health (4 tests)

**Total: 109 test scenarios**

---

## Test Environment

- Backend: http://127.0.0.1:8000
- Frontend: http://127.0.0.1:5173
- Browser: Playwright (Chromium)
