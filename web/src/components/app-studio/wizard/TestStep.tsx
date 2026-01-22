import { useState } from 'react'
import { Play, RotateCcw, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { Button, Card, Input, Label, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { ActionDefinition, ParamSpec, StateField } from '@/lib/api'

interface TestStepProps {
  actions: ActionDefinition[]
  stateSchema: StateField[]
  initialConfig: Record<string, unknown>
}

interface TestAgent {
  id: string
  name: string
  state: Record<string, unknown>
}

interface ExecutionLogEntry {
  id: string
  timestamp: string
  agentId: string
  agentName: string
  action: string
  params: Record<string, unknown>
  success: boolean
  result: unknown
  error?: string
  stateChanges: Array<{
    agent: string
    field: string
    oldValue: unknown
    newValue: unknown
  }>
}

function initializeAgentState(schema: StateField[]): Record<string, unknown> {
  const state: Record<string, unknown> = {}
  for (const field of schema) {
    if (field.per_agent !== false) {
      state[field.name] = field.default ?? getDefaultForType(field.type)
    }
  }
  return state
}

function getDefaultForType(type: string): unknown {
  switch (type) {
    case 'number':
      return 0
    case 'boolean':
      return false
    case 'array':
      return []
    case 'object':
      return {}
    default:
      return ''
  }
}

// Simulated action execution
function executeAction(
  action: ActionDefinition,
  _agent: TestAgent,
  _params: Record<string, unknown>,
  _allAgents: TestAgent[]
): { success: boolean; result: unknown; error?: string; stateChanges: ExecutionLogEntry['stateChanges'] } {
  const stateChanges: ExecutionLogEntry['stateChanges'] = []

  // Simulate execution based on action logic
  // For now, just return success with mock data
  try {
    // Generate mock return values based on action.returns
    const result: Record<string, unknown> = {}
    if (action.returns) {
      for (const [key, type] of Object.entries(action.returns)) {
        switch (type) {
          case 'string':
            result[key] = `mock_${key}_${Date.now()}`
            break
          case 'number':
            result[key] = Math.floor(Math.random() * 1000)
            break
          case 'boolean':
            result[key] = true
            break
          case 'array':
            result[key] = []
            break
          default:
            result[key] = null
        }
      }
    }

    return { success: true, result, stateChanges }
  } catch (err) {
    return {
      success: false,
      result: null,
      error: err instanceof Error ? err.message : 'Unknown error',
      stateChanges,
    }
  }
}

export function TestStep({ actions, stateSchema }: TestStepProps) {
  // Test agents
  const [agents, setAgents] = useState<TestAgent[]>(() => [
    { id: 'alice', name: 'Alice', state: initializeAgentState(stateSchema) },
    { id: 'bob', name: 'Bob', state: initializeAgentState(stateSchema) },
    { id: 'charlie', name: 'Charlie', state: initializeAgentState(stateSchema) },
  ])

  // Selected agent and action
  const [selectedAgentId, setSelectedAgentId] = useState('alice')
  const [selectedActionName, setSelectedActionName] = useState(actions[0]?.name || '')
  const [paramValues, setParamValues] = useState<Record<string, unknown>>({})

  // Execution log
  const [executionLog, setExecutionLog] = useState<ExecutionLogEntry[]>([])
  const [lastResult, setLastResult] = useState<{
    success: boolean
    result: unknown
    error?: string
  } | null>(null)

  const selectedAgent = agents.find((a) => a.id === selectedAgentId)
  const selectedAction = actions.find((a) => a.name === selectedActionName)

  // Reset param values when action changes
  const handleActionChange = (actionName: string) => {
    setSelectedActionName(actionName)
    setParamValues({})
  }

  // Execute action
  const handleExecute = () => {
    if (!selectedAgent || !selectedAction) return

    const result = executeAction(selectedAction, selectedAgent, paramValues, agents)
    setLastResult(result)

    // Add to log
    const logEntry: ExecutionLogEntry = {
      id: `${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      agentId: selectedAgent.id,
      agentName: selectedAgent.name,
      action: selectedAction.name,
      params: { ...paramValues },
      success: result.success,
      result: result.result,
      error: result.error,
      stateChanges: result.stateChanges,
    }
    setExecutionLog((prev) => [logEntry, ...prev])
  }

  // Reset state
  const handleReset = () => {
    setAgents([
      { id: 'alice', name: 'Alice', state: initializeAgentState(stateSchema) },
      { id: 'bob', name: 'Bob', state: initializeAgentState(stateSchema) },
      { id: 'charlie', name: 'Charlie', state: initializeAgentState(stateSchema) },
    ])
    setExecutionLog([])
    setLastResult(null)
    setParamValues({})
  }

  if (actions.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <h2 className="text-xl font-semibold mb-2">Test Your App</h2>
          <p className="text-foreground-secondary">
            Add some actions first to test your app
          </p>
        </div>
        <Card className="p-8">
          <div className="text-center text-foreground-muted">
            No actions to test. Go back and add some actions.
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Test Your App</h2>
          <p className="text-foreground-secondary">
            Execute actions and see results in real-time
          </p>
        </div>
        <Button variant="secondary" onClick={handleReset}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Execute Action */}
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Execute Action</h3>

          {/* Agent Selector */}
          <div className="space-y-2 mb-4">
            <Label>Agent</Label>
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background"
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>

          {/* Action Selector */}
          <div className="space-y-2 mb-4">
            <Label>Action</Label>
            <select
              value={selectedActionName}
              onChange={(e) => handleActionChange(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background"
            >
              {actions.map((action) => (
                <option key={action.name} value={action.name}>
                  {action.name}
                </option>
              ))}
            </select>
            {selectedAction?.description && (
              <p className="text-sm text-foreground-muted">
                {selectedAction.description}
              </p>
            )}
          </div>

          {/* Parameters */}
          {selectedAction && Object.keys(selectedAction.parameters || {}).length > 0 && (
            <div className="space-y-3 mb-4">
              <Label>Parameters</Label>
              {Object.entries(selectedAction.parameters || {}).map(([name, spec]) => (
                <div key={name} className="space-y-1">
                  <label className="text-sm font-medium">
                    {name}
                    {spec.required && <span className="text-error ml-1">*</span>}
                  </label>
                  <ParameterInput
                    name={name}
                    spec={spec}
                    value={paramValues[name]}
                    onChange={(value) =>
                      setParamValues({ ...paramValues, [name]: value })
                    }
                    agents={agents}
                  />
                  {spec.description && (
                    <p className="text-xs text-foreground-muted">{spec.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Execute Button */}
          <Button onClick={handleExecute} className="w-full">
            <Play className="h-4 w-4 mr-2" />
            Execute Action
          </Button>

          {/* Last Result */}
          {lastResult && (
            <div
              className={cn(
                'mt-4 p-4 rounded-lg border',
                lastResult.success
                  ? 'bg-success/10 border-success/30'
                  : 'bg-error/10 border-error/30'
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                {lastResult.success ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-success" />
                    <span className="font-medium text-success">Success</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-error" />
                    <span className="font-medium text-error">Error</span>
                  </>
                )}
              </div>
              <pre className="text-sm overflow-auto max-h-32">
                {lastResult.error ||
                  JSON.stringify(lastResult.result, null, 2)}
              </pre>
            </div>
          )}
        </Card>

        {/* Right: State & Log */}
        <div className="space-y-6">
          {/* Agent States */}
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Current State</h3>
            <div className="space-y-4">
              {agents.map((agent) => (
                <AgentStateCard key={agent.id} agent={agent} />
              ))}
            </div>
          </Card>

          {/* Execution Log */}
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Execution Log</h3>
            {executionLog.length === 0 ? (
              <p className="text-foreground-muted text-sm text-center py-4">
                No actions executed yet
              </p>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {executionLog.map((entry) => (
                  <LogEntry key={entry.id} entry={entry} />
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

// Parameter Input Component
function ParameterInput({
  name,
  spec,
  value,
  onChange,
  agents,
}: {
  name: string
  spec: ParamSpec
  value: unknown
  onChange: (value: unknown) => void
  agents: TestAgent[]
}) {
  // Show agent dropdown for 'to' or 'from' parameters
  if (name === 'to' || name === 'from' || name === 'recipient' || name === 'with') {
    return (
      <select
        value={String(value || '')}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-border rounded-md bg-background text-sm"
      >
        <option value="">Select agent...</option>
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
    )
  }

  switch (spec.type) {
    case 'number':
      return (
        <Input
          type="number"
          value={String(value || '')}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          min={spec.min_value}
          max={spec.max_value}
          className="text-sm"
        />
      )
    case 'boolean':
      return (
        <select
          value={String(value || 'false')}
          onChange={(e) => onChange(e.target.value === 'true')}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-sm"
        >
          <option value="false">False</option>
          <option value="true">True</option>
        </select>
      )
    default:
      return (
        <Input
          type="text"
          value={String(value || '')}
          onChange={(e) => onChange(e.target.value)}
          maxLength={spec.max_length}
          className="text-sm"
        />
      )
  }
}

// Agent State Card
function AgentStateCard({ agent }: { agent: TestAgent }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-border rounded-lg p-3">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full"
      >
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-sm font-medium text-primary">
              {agent.name.charAt(0)}
            </span>
          </div>
          <span className="font-medium">{agent.name}</span>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>
      {expanded && Object.keys(agent.state).length > 0 && (
        <div className="mt-3 pt-3 border-t border-border">
          <pre className="text-xs overflow-auto">
            {JSON.stringify(agent.state, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

// Log Entry
function LogEntry({ entry }: { entry: ExecutionLogEntry }) {
  return (
    <div className="p-3 bg-secondary/50 rounded-lg text-sm">
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium">{entry.agentName}</span>
        <span className="text-xs text-foreground-muted">{entry.timestamp}</span>
      </div>
      <div className="flex items-center gap-2">
        <code className="text-primary">{entry.action}</code>
        {entry.success ? (
          <Badge variant="outline" className="text-success border-success text-xs">
            Success
          </Badge>
        ) : (
          <Badge variant="outline" className="text-error border-error text-xs">
            Error
          </Badge>
        )}
      </div>
      {Object.keys(entry.params).length > 0 && (
        <div className="mt-1 text-xs text-foreground-muted">
          Params: {JSON.stringify(entry.params)}
        </div>
      )}
    </div>
  )
}
