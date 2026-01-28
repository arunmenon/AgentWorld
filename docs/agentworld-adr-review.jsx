import React, { useState } from 'react';

const AgentWorldADRReview = () => {
  const [activeTab, setActiveTab] = useState('review');
  const [activeADR, setActiveADR] = useState('020');
  const [mockupView, setMockupView] = useState('app-studio');

  // Review content
  const critiques = {
    '020': {
      title: 'ADR-020: τ-bench Evaluation Framework',
      status: 'Implemented',
      strengths: [
        { text: 'Strong theoretical foundation', detail: 'Direct adoption of pass^k metric provides statistical rigor for reliability measurement beyond simple success rates.' },
        { text: 'Excellent fault taxonomy', detail: 'FaultAssignment (agent/environment/task) + FaultType creates actionable debugging categories.' },
        { text: 'Comprehensive policy engine', detail: 'Category-based policies (confirmation, limit, eligibility, prohibition) cover real-world compliance needs.' },
        { text: 'Good integration story', detail: 'Clean separation from ADR-010 behavioral evaluation - complements rather than replaces.' }
      ],
      weaknesses: [
        { text: 'Binary success loses nuance', detail: 'A task that fails on step 9/10 scores same as failing on step 1/10. Consider partial success scoring.', severity: 'medium' },
        { text: 'No intermediate checkpoints', detail: 'Long tasks have no visibility into progress before completion. Add milestone verification.', severity: 'medium' },
        { text: 'Policy conditions are opaque', detail: 'JSON conditions in policy_rules need a clear DSL spec. What operators are valid?', severity: 'high' },
        { text: 'Missing retry semantics', detail: 'Should a retried action count against pass^k? τ-bench allows retries within a trial.', severity: 'low' }
      ],
      suggestions: [
        'Add `partial_credit: float` field to TrialResult for nuanced scoring',
        'Define explicit grammar for policy conditions (similar to ADR-019 logic language)',
        'Add `checkpoints: list[Checkpoint]` to TaskDefinition for long-running tasks',
        'Document retry behavior explicitly - within-trial vs cross-trial'
      ]
    },
    '020.1': {
      title: 'ADR-020.1: Dual-Control Extension',
      status: 'Proposed',
      strengths: [
        { text: 'Research-backed motivation', detail: 'Direct citation of τ²-bench ~25pt performance drop gives clear success criteria.' },
        { text: 'Elegant access model', detail: 'AppAccessType × AppStateType matrix with validity rules is well thought out.' },
        { text: 'Coordination tracking', detail: 'CoordinationEvent with instruction→action matching enables precise handoff analysis.' },
        { text: 'Comprehensive UI spec', detail: 'Section 11 component architecture shows implementation thought-through.' }
      ],
      weaknesses: [
        { text: 'Complexity explosion', detail: 'Adding access_type, state_type, tool_type, roles to every app/action is heavy. UX burden high.', severity: 'high' },
        { text: 'Instruction matching is hard', detail: 'Detecting "toggle your data" → toggle_mobile_data requires NLU. How accurate is this?', severity: 'high' },
        { text: 'Role rigidity', detail: 'Binary service_agent/customer roles. Real scenarios have supervisors, multiple service tiers.', severity: 'medium' },
        { text: 'Per-agent state key collision', detail: 'Key format `{app_id}:{agent_id}` - what about agent_id changes mid-simulation?', severity: 'low' }
      ],
      suggestions: [
        'Default most apps to SHARED/SHARED - only require configuration for dual-control scenarios',
        'Add explicit instruction template matching rather than free-form NLU',
        'Make roles hierarchical or tag-based rather than fixed enum',
        'Add agent_id immutability constraint or state migration strategy'
      ]
    },
    '021': {
      title: 'ADR-021: App Benchmark & Evaluation',
      status: 'Proposed',
      strengths: [
        { text: 'Holistic quality dimensions', detail: '6 weighted dimensions (completeness, docs, validation, error handling, state safety, consistency) cover app hygiene well.' },
        { text: 'Scenario chaining', detail: 'State flows between steps allows realistic multi-action test sequences.' },
        { text: 'Regression detection', detail: 'Comparing versions with is_breaking flag is critical for CI/CD.' },
        { text: 'Benchmark suite concept', detail: 'Standard bench_* apps enable cross-implementation comparison.' }
      ],
      weaknesses: [
        { text: 'Overlap with ADR-020', detail: 'Both have scenario runners, state verification, metrics. Unclear when to use which.', severity: 'high' },
        { text: 'Quality metrics are shallow', detail: '"State Safety" via heuristic analysis is vague. What heuristics? How reliable?', severity: 'medium' },
        { text: 'No semantic testing', detail: 'Scenarios are syntactic (action→expected). No "does this app make sense?" validation.', severity: 'medium' },
        { text: 'Coverage analysis undefined', detail: 'REQ-21-06 is marked "Could" but implementation is completely undefined.', severity: 'low' }
      ],
      suggestions: [
        'Merge scenario runner with ADR-020 TaskRunner - single execution engine',
        'Define specific state safety rules (max array size, no recursive state, etc.)',
        'Add LLM-based semantic coherence check for action descriptions',
        'Promote coverage analysis to "Should" with specific path enumeration algorithm'
      ]
    }
  };

  const crossCuttingConcerns = [
    {
      title: 'Fragmented Execution Engines',
      detail: 'ADR-020 has TaskRunner, ADR-021 has ScenarioRunner. Both execute actions against apps and verify state. Should be unified.',
      recommendation: 'Create single ExecutionEngine in ADR-017 (Simulated Apps), have both evaluation frameworks use it.'
    },
    {
      title: 'Schema Evolution Risk',
      detail: 'AppDefinition now has: actions, state_schema, initial_config (ADR-017) + access_type, allowed_roles, state_type (ADR-020.1) + quality metadata (ADR-021). Growing unbounded.',
      recommendation: 'Split into AppDefinition (core) + AppAccessConfig + AppQualityMetadata. Use composition.'
    },
    {
      title: 'Missing End-to-End Example',
      detail: 'No ADR shows a complete flow: create app → define task → run dual-control evaluation → analyze results. Hard to validate integration.',
      recommendation: 'Add ADR-022: Integration Walkthrough with concrete telecom support example soup-to-nuts.'
    },
    {
      title: 'UI Complexity Budget',
      detail: 'ADR-020.1 Section 11 adds 13-16 days of UI work. Combined with App Studio, Simulation View, Task Creation - UX sprawl risk.',
      recommendation: 'Define "complexity budget" - what features are hidden behind Advanced mode? Progressive disclosure.'
    }
  ];

  // Mockup components
  const AppStudioMockup = () => (
    <div className="bg-[#0a0a0f] min-h-[600px] text-white font-mono">
      {/* Header */}
      <div className="border-b border-white/10 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center text-xs font-bold">AW</div>
          <span className="text-lg tracking-wide">AgentWorld</span>
          <span className="text-white/40 text-sm">/ App Studio</span>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 text-sm bg-white/5 rounded border border-white/10 hover:bg-white/10 transition">Preview</button>
          <button className="px-3 py-1.5 text-sm bg-cyan-500 text-black rounded font-medium hover:bg-cyan-400 transition">Publish</button>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar - Steps */}
        <div className="w-56 border-r border-white/10 p-4">
          <div className="text-xs uppercase tracking-wider text-white/40 mb-3">Creation Steps</div>
          {['Basic Info', 'Access Control', 'State Schema', 'Actions', 'Review'].map((step, i) => (
            <div key={step} className={`flex items-center gap-3 p-2 rounded mb-1 cursor-pointer transition ${i === 1 ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 text-white/60'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${i < 1 ? 'bg-cyan-500 text-black' : i === 1 ? 'border-2 border-cyan-400' : 'border border-white/20'}`}>
                {i < 1 ? '✓' : i + 1}
              </div>
              <span className="text-sm">{step}</span>
            </div>
          ))}
        </div>

        {/* Main Content - Access Control */}
        <div className="flex-1 p-6">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-light mb-1">Access Control</h2>
            <p className="text-white/50 text-sm mb-8">Define who can access this app and how state is managed</p>

            {/* Access Type */}
            <div className="mb-8">
              <label className="block text-sm text-white/70 mb-3">Access Type</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'shared', label: 'Shared', desc: 'All agents', icon: '👥' },
                  { id: 'role', label: 'Role-Restricted', desc: 'Specific roles', icon: '🔐' },
                  { id: 'per-agent', label: 'Per-Agent', desc: 'Isolated instances', icon: '👤' }
                ].map((type, i) => (
                  <div key={type.id} className={`p-4 rounded-lg border cursor-pointer transition ${i === 1 ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/10 hover:border-white/30'}`}>
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <div className="font-medium">{type.label}</div>
                    <div className="text-xs text-white/50">{type.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Allowed Roles */}
            <div className="mb-8 p-4 bg-cyan-500/5 border border-cyan-500/30 rounded-lg">
              <label className="block text-sm text-cyan-400 mb-3">Allowed Roles</label>
              <div className="flex flex-wrap gap-2">
                {['service_agent', 'customer', 'supervisor', 'admin'].map((role, i) => (
                  <label key={role} className={`flex items-center gap-2 px-3 py-2 rounded border cursor-pointer transition ${i === 0 ? 'border-cyan-500 bg-cyan-500/20' : 'border-white/10 hover:border-white/30'}`}>
                    <input type="checkbox" defaultChecked={i === 0} className="accent-cyan-500" />
                    <span className="text-sm">{role}</span>
                  </label>
                ))}
                <button className="px-3 py-2 rounded border border-dashed border-white/20 text-white/40 text-sm hover:border-white/40 transition">+ Add Role</button>
              </div>
            </div>

            {/* State Type */}
            <div className="mb-8">
              <label className="block text-sm text-white/70 mb-3">State Type</label>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-lg border border-cyan-500 bg-cyan-500/10 cursor-pointer">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">🗄️</span>
                    <span className="font-medium">Shared State</span>
                  </div>
                  <p className="text-xs text-white/50">Single state for all agents (e.g., backend DB)</p>
                </div>
                <div className="p-4 rounded-lg border border-white/10 cursor-pointer hover:border-white/30 transition">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">📱</span>
                    <span className="font-medium">Per-Agent State</span>
                  </div>
                  <p className="text-xs text-white/50">Each agent has isolated state (e.g., device)</p>
                </div>
              </div>
            </div>

            {/* Warning */}
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex gap-3">
              <span className="text-amber-400 text-xl">⚠️</span>
              <div>
                <div className="font-medium text-amber-400 text-sm">Dual-Control Configuration</div>
                <p className="text-xs text-white/60 mt-1">Role-restricted apps with shared state are typical for backend systems in dual-control scenarios. Agents with this role can modify state that affects other participants.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const TaskRunnerMockup = () => (
    <div className="bg-[#0a0a0f] min-h-[600px] text-white font-mono">
      {/* Header */}
      <div className="border-b border-white/10 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center text-xs font-bold">AW</div>
          <span className="text-lg tracking-wide">AgentWorld</span>
          <span className="text-white/40 text-sm">/ Task Evaluation</span>
        </div>
        <div className="flex gap-2 text-sm">
          <button className="px-3 py-1.5 bg-white/5 rounded border border-white/10">Export</button>
          <button className="px-3 py-1.5 bg-red-500/80 rounded">Stop All</button>
        </div>
      </div>

      <div className="flex">
        {/* Task List */}
        <div className="w-72 border-r border-white/10 p-4">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs uppercase tracking-wider text-white/40">Task Set: Payment</span>
            <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded">8 tasks</span>
          </div>
          {[
            { name: 'basic_transfer', status: 'pass', pass1: 0.87 },
            { name: 'multi_party_split', status: 'pass', pass1: 0.75 },
            { name: 'insufficient_funds', status: 'running', pass1: null },
            { name: 'self_transfer_block', status: 'pending', pass1: null },
            { name: 'concurrent_transfers', status: 'pending', pass1: null },
          ].map((task, i) => (
            <div key={task.name} className={`p-3 rounded-lg mb-2 cursor-pointer transition ${i === 2 ? 'bg-cyan-500/10 border border-cyan-500/50' : 'hover:bg-white/5'}`}>
              <div className="flex items-center justify-between">
                <span className="text-sm">{task.name}</span>
                {task.status === 'pass' && <span className="text-green-400 text-xs">✓</span>}
                {task.status === 'running' && <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />}
                {task.status === 'pending' && <span className="w-2 h-2 rounded-full bg-white/20" />}
              </div>
              {task.pass1 && <div className="text-xs text-white/40 mt-1">pass¹ = {task.pass1}</div>}
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-light">insufficient_funds</h2>
              <p className="text-white/50 text-sm">Test transfer failure on insufficient balance</p>
            </div>
            <div className="flex gap-4 text-center">
              <div>
                <div className="text-2xl font-light text-cyan-400">6/8</div>
                <div className="text-xs text-white/40">Trials</div>
              </div>
              <div>
                <div className="text-2xl font-light text-green-400">0.75</div>
                <div className="text-xs text-white/40">pass¹</div>
              </div>
              <div>
                <div className="text-2xl font-light text-amber-400">0.42</div>
                <div className="text-xs text-white/40">pass⁴</div>
              </div>
            </div>
          </div>

          {/* Trials Grid */}
          <div className="grid grid-cols-8 gap-2 mb-8">
            {[1,1,0,1,1,0,null,null].map((result, i) => (
              <div key={i} className={`aspect-square rounded-lg flex items-center justify-center text-sm ${
                result === 1 ? 'bg-green-500/20 border border-green-500/50 text-green-400' :
                result === 0 ? 'bg-red-500/20 border border-red-500/50 text-red-400' :
                'bg-white/5 border border-white/10 text-white/30'
              }`}>
                {result === 1 ? '✓' : result === 0 ? '✗' : i + 1}
              </div>
            ))}
          </div>

          {/* Current Trial */}
          <div className="bg-white/5 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-white/60">Trial 7 / 8</span>
              <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded animate-pulse">Running...</span>
            </div>
            <div className="space-y-2">
              {[
                { action: 'get_balance', result: 'success', time: '42ms' },
                { action: 'transfer', result: 'success', time: '156ms' },
                { action: 'verify_error', result: 'pending', time: '...' },
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs ${
                    step.result === 'success' ? 'bg-green-500' :
                    step.result === 'pending' ? 'bg-cyan-500 animate-pulse' : 'bg-white/20'
                  }`}>
                    {step.result === 'success' ? '✓' : ''}
                  </span>
                  <span className="text-white/80 font-mono">{step.action}</span>
                  <span className="text-white/30">{step.time}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Fault Summary */}
          <div>
            <h3 className="text-sm text-white/60 mb-3">Fault Classification</h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <div className="text-lg font-light text-red-400">2</div>
                <div className="text-xs text-white/50">Agent Errors</div>
                <div className="text-xs text-red-400/60 mt-1">wrong_params</div>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                <div className="text-lg font-light text-amber-400">0</div>
                <div className="text-xs text-white/50">Environment</div>
              </div>
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3">
                <div className="text-lg font-light text-purple-400">0</div>
                <div className="text-xs text-white/50">Task Issues</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const DualControlMockup = () => (
    <div className="bg-[#0a0a0f] min-h-[600px] text-white font-mono">
      {/* Header */}
      <div className="border-b border-white/10 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center text-xs font-bold">AW</div>
          <span className="text-lg tracking-wide">AgentWorld</span>
          <span className="text-white/40 text-sm">/ Dual-Control Simulation</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">τ²-bench Compatible</span>
          <button className="px-3 py-1.5 text-sm bg-cyan-500 text-black rounded font-medium">Run Comparison</button>
        </div>
      </div>

      <div className="flex">
        {/* Agent Panel - Service Agent */}
        <div className="w-80 border-r border-white/10 p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">🎧</div>
            <div>
              <div className="font-medium">TechSupport</div>
              <div className="text-xs text-blue-400">service_agent</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="text-xs text-white/40 mb-2">Available Apps</div>
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <span>🗄️</span>
                <span className="text-sm font-medium">Telecom Backend</span>
              </div>
              <div className="space-y-1">
                {[
                  { name: 'get_customer_by_id', type: '📖' },
                  { name: 'enable_roaming', type: '✏️' },
                  { name: 'change_plan', type: '✏️' },
                ].map(tool => (
                  <div key={tool.name} className="flex items-center gap-2 text-xs text-white/60">
                    <span>{tool.type}</span>
                    <span>{tool.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="text-xs text-white/40 mb-2">Recent Actions</div>
          <div className="space-y-2">
            <div className="bg-white/5 rounded p-2 text-sm">
              <code className="text-blue-300">get_customer_by_id("john123")</code>
              <div className="text-xs text-green-400 mt-1">✓ Customer found</div>
            </div>
            <div className="bg-white/5 rounded p-2 text-sm">
              <code className="text-blue-300">enable_roaming("john123")</code>
              <div className="text-xs text-green-400 mt-1">✓ Roaming enabled</div>
            </div>
          </div>
        </div>

        {/* Timeline Center */}
        <div className="flex-1 p-4 border-r border-white/10">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-white/60">Conversation Timeline</span>
            <div className="flex gap-2">
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">3 handoffs</span>
              <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded">2 successful</span>
            </div>
          </div>

          <div className="space-y-3">
            {/* Message */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-sm flex-shrink-0">🎧</div>
              <div className="flex-1 bg-blue-500/10 rounded-lg p-3 text-sm">
                I've enabled international roaming on your account. Now, could you please toggle off airplane mode on your device?
              </div>
            </div>

            {/* Coordination Event */}
            <div className="flex items-center gap-2 text-xs text-purple-400 ml-11">
              <div className="h-px flex-1 bg-purple-500/30" />
              <span className="bg-purple-500/20 px-2 py-0.5 rounded">↓ HANDOFF: toggle_airplane_mode</span>
              <div className="h-px flex-1 bg-purple-500/30" />
            </div>

            {/* User Response */}
            <div className="flex gap-3 justify-end">
              <div className="flex-1 bg-green-500/10 rounded-lg p-3 text-sm text-right">
                Okay, I'm turning off airplane mode now.
              </div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center text-sm flex-shrink-0">👤</div>
            </div>

            {/* Action Marker */}
            <div className="flex items-center gap-2 text-xs text-green-400 mr-11 justify-end">
              <span className="bg-green-500/20 px-2 py-0.5 rounded">✓ toggle_airplane_mode(false)</span>
            </div>

            {/* Another message */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-sm flex-shrink-0">🎧</div>
              <div className="flex-1 bg-blue-500/10 rounded-lg p-3 text-sm">
                Great! Now please check your status bar - do you see the roaming indicator?
              </div>
            </div>

            {/* Pending handoff */}
            <div className="flex items-center gap-2 text-xs text-amber-400 ml-11">
              <div className="h-px flex-1 bg-amber-500/30" />
              <span className="bg-amber-500/20 px-2 py-0.5 rounded animate-pulse">⏳ AWAITING: get_status_bar</span>
              <div className="h-px flex-1 bg-amber-500/30" />
            </div>
          </div>
        </div>

        {/* Agent Panel - Customer */}
        <div className="w-80 p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">👤</div>
            <div>
              <div className="font-medium">John</div>
              <div className="text-xs text-green-400">customer</div>
            </div>
          </div>

          <div className="mb-4">
            <div className="text-xs text-white/40 mb-2">Available Apps</div>
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <span>📱</span>
                <span className="text-sm font-medium">User Device</span>
              </div>
              <div className="space-y-1">
                {[
                  { name: 'get_status_bar', type: '📖' },
                  { name: 'toggle_airplane_mode', type: '✏️' },
                  { name: 'toggle_mobile_data', type: '✏️' },
                  { name: 'restart_device', type: '✏️' },
                ].map(tool => (
                  <div key={tool.name} className="flex items-center gap-2 text-xs text-white/60">
                    <span>{tool.type}</span>
                    <span>{tool.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="text-xs text-white/40 mb-2">Device State</div>
          <div className="bg-white/5 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-white/60">Airplane Mode</span>
              <span className="text-red-400">OFF</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-white/60">Mobile Data</span>
              <span className="text-green-400">ON</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-white/60">Roaming</span>
              <span className="text-green-400">ACTIVE</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-white/60">Signal</span>
              <span className="text-cyan-400">████░░</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const QualityDashMockup = () => (
    <div className="bg-[#0a0a0f] min-h-[600px] text-white font-mono">
      {/* Header */}
      <div className="border-b border-white/10 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center text-xs font-bold">AW</div>
          <span className="text-lg tracking-wide">AgentWorld</span>
          <span className="text-white/40 text-sm">/ App Quality Dashboard</span>
        </div>
      </div>

      <div className="p-6">
        <div className="flex gap-6">
          {/* Quality Score Card */}
          <div className="w-64 bg-gradient-to-br from-cyan-500/20 to-purple-500/20 rounded-xl p-6 border border-white/10">
            <div className="text-sm text-white/60 mb-2">Overall Quality</div>
            <div className="text-6xl font-light text-cyan-400 mb-2">82</div>
            <div className="text-sm text-green-400">● Good</div>
            <div className="mt-4 text-xs text-white/40">PayPal App v2.3</div>
          </div>

          {/* Dimension Scores */}
          <div className="flex-1">
            <h3 className="text-sm text-white/60 mb-4">Quality Dimensions</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { name: 'Completeness', score: 95, weight: '25%', color: 'cyan' },
                { name: 'Documentation', score: 70, weight: '20%', color: 'purple' },
                { name: 'Validation', score: 85, weight: '20%', color: 'green' },
                { name: 'Error Handling', score: 90, weight: '15%', color: 'blue' },
                { name: 'State Safety', score: 75, weight: '10%', color: 'amber' },
                { name: 'Consistency', score: 80, weight: '10%', color: 'pink' },
              ].map(dim => (
                <div key={dim.name} className="bg-white/5 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm">{dim.name}</span>
                    <span className="text-xs text-white/40">{dim.weight}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                      <div className={`h-full bg-${dim.color}-500`} style={{width: `${dim.score}%`}} />
                    </div>
                    <span className={`text-sm text-${dim.color}-400`}>{dim.score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Suggestions */}
        <div className="mt-6">
          <h3 className="text-sm text-white/60 mb-4">Improvement Suggestions</h3>
          <div className="space-y-2">
            {[
              { type: 'warning', text: 'Add description to action "process_refund"', impact: '+5 Documentation' },
              { type: 'info', text: 'Consider adding VALIDATE block for amount parameter', impact: '+3 Validation' },
              { type: 'info', text: 'Action "get_balance" uses camelCase, others use snake_case', impact: '+2 Consistency' },
            ].map((sug, i) => (
              <div key={i} className={`flex items-center gap-3 p-3 rounded-lg ${sug.type === 'warning' ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-cyan-500/10 border border-cyan-500/30'}`}>
                <span>{sug.type === 'warning' ? '⚠️' : '💡'}</span>
                <span className="flex-1 text-sm">{sug.text}</span>
                <span className="text-xs text-white/40">{sug.impact}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Regression Comparison */}
        <div className="mt-6 grid grid-cols-2 gap-6">
          <div className="bg-white/5 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm text-white/60">Version Comparison</h3>
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">No Breaking Changes</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-2xl font-light text-white/40">v2.2</div>
                <div className="text-sm text-white/30">previous</div>
              </div>
              <div className="flex-1 flex items-center justify-center">
                <span className="text-2xl">→</span>
              </div>
              <div className="text-center">
                <div className="text-2xl font-light text-cyan-400">v2.3</div>
                <div className="text-sm text-white/30">current</div>
              </div>
            </div>
            <div className="mt-4 text-center text-sm text-green-400">Quality: 78 → 82 (+4)</div>
          </div>

          <div className="bg-white/5 rounded-lg p-4">
            <h3 className="text-sm text-white/60 mb-4">Test Scenarios</h3>
            <div className="space-y-2">
              {[
                { name: 'basic_transfer', status: 'pass' },
                { name: 'error_handling', status: 'pass' },
                { name: 'concurrent_ops', status: 'pass' },
                { name: 'edge_cases', status: 'pass' },
              ].map(test => (
                <div key={test.name} className="flex items-center justify-between text-sm">
                  <span className="text-white/60">{test.name}</span>
                  <span className="text-green-400">✓ pass</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const mockups = {
    'app-studio': { title: 'App Studio: Access Control', component: <AppStudioMockup /> },
    'task-runner': { title: 'Task Evaluation Dashboard', component: <TaskRunnerMockup /> },
    'dual-control': { title: 'Dual-Control Simulation', component: <DualControlMockup /> },
    'quality': { title: 'App Quality Dashboard', component: <QualityDashMockup /> }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Navigation */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-light tracking-wide">AgentWorld ADR Review</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('review')}
              className={`px-4 py-2 rounded-lg transition ${activeTab === 'review' ? 'bg-cyan-500 text-black' : 'bg-white/5 hover:bg-white/10'}`}
            >
              📋 Review
            </button>
            <button
              onClick={() => setActiveTab('mockups')}
              className={`px-4 py-2 rounded-lg transition ${activeTab === 'mockups' ? 'bg-cyan-500 text-black' : 'bg-white/5 hover:bg-white/10'}`}
            >
              🎨 UI Mockups
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'review' ? (
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* ADR Selector */}
          <div className="flex gap-3 mb-8">
            {Object.entries(critiques).map(([id, adr]) => (
              <button
                key={id}
                onClick={() => setActiveADR(id)}
                className={`flex-1 p-4 rounded-xl border transition ${
                  activeADR === id 
                    ? 'border-cyan-500 bg-cyan-500/10' 
                    : 'border-white/10 bg-white/5 hover:border-white/30'
                }`}
              >
                <div className="text-lg font-medium">ADR-{id}</div>
                <div className="text-sm text-white/50 truncate">{adr.title.split(':')[1]}</div>
                <div className={`text-xs mt-2 px-2 py-0.5 rounded inline-block ${
                  adr.status === 'Implemented' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  {adr.status}
                </div>
              </button>
            ))}
          </div>

          {/* Current ADR Review */}
          <div className="grid grid-cols-2 gap-6 mb-8">
            {/* Strengths */}
            <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-6">
              <h3 className="text-green-400 font-medium mb-4 flex items-center gap-2">
                <span>✓</span> Strengths
              </h3>
              <div className="space-y-4">
                {critiques[activeADR].strengths.map((s, i) => (
                  <div key={i}>
                    <div className="font-medium text-green-300">{s.text}</div>
                    <div className="text-sm text-white/50 mt-1">{s.detail}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Weaknesses */}
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6">
              <h3 className="text-red-400 font-medium mb-4 flex items-center gap-2">
                <span>✗</span> Weaknesses
              </h3>
              <div className="space-y-4">
                {critiques[activeADR].weaknesses.map((w, i) => (
                  <div key={i}>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-red-300">{w.text}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        w.severity === 'high' ? 'bg-red-500/30 text-red-300' :
                        w.severity === 'medium' ? 'bg-amber-500/30 text-amber-300' :
                        'bg-white/10 text-white/50'
                      }`}>
                        {w.severity}
                      </span>
                    </div>
                    <div className="text-sm text-white/50 mt-1">{w.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Suggestions */}
          <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-6 mb-8">
            <h3 className="text-cyan-400 font-medium mb-4 flex items-center gap-2">
              <span>💡</span> Recommendations
            </h3>
            <ul className="space-y-2">
              {critiques[activeADR].suggestions.map((s, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-cyan-500 mt-1">→</span>
                  <span className="text-white/80">{s}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Cross-Cutting Concerns */}
          <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-6">
            <h3 className="text-purple-400 font-medium mb-4 flex items-center gap-2">
              <span>🔗</span> Cross-Cutting Concerns
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {crossCuttingConcerns.map((c, i) => (
                <div key={i} className="bg-white/5 rounded-lg p-4">
                  <div className="font-medium text-purple-300 mb-2">{c.title}</div>
                  <div className="text-sm text-white/50 mb-3">{c.detail}</div>
                  <div className="text-sm text-purple-400">
                    <span className="text-white/30">→</span> {c.recommendation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Mockup Selector */}
          <div className="flex gap-3 mb-6">
            {Object.entries(mockups).map(([id, mock]) => (
              <button
                key={id}
                onClick={() => setMockupView(id)}
                className={`px-4 py-2 rounded-lg transition text-sm ${
                  mockupView === id 
                    ? 'bg-cyan-500 text-black' 
                    : 'bg-white/5 hover:bg-white/10'
                }`}
              >
                {mock.title}
              </button>
            ))}
          </div>

          {/* Mockup Display */}
          <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl">
            {mockups[mockupView].component}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentWorldADRReview;
