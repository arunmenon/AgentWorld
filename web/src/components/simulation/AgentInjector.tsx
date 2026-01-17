import { memo, useState, useEffect } from 'react'
import {
  Plug,
  Unplug,
  Activity,
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
  Settings,
  Trash2,
} from 'lucide-react'
import { Button, Badge, Card, Input, Modal, ModalHeader } from '@/components/ui'
import { api, type Agent } from '@/lib/api'
import { cn } from '@/lib/utils'

interface AgentInjectorProps {
  simulationId: string
  agents: Agent[]
  className?: string
}

interface InjectedAgent {
  agent_id: string
  endpoint_url: string
  privacy_tier: string
  fallback_to_simulated: boolean
  circuit_state: string
  is_healthy: boolean | null
}

interface InjectionMetrics {
  agent_id: string
  total_calls: number
  successful_calls: number
  failed_calls: number
  error_rate: number
  timeout_rate: number
  latency_p50_ms: number
  latency_p99_ms: number
  circuit_state: string
}

const PRIVACY_TIERS = [
  { id: 'minimal', name: 'Minimal', description: 'Only persona ID and hash' },
  { id: 'basic', name: 'Basic', description: 'Name and traits (no background)' },
  { id: 'full', name: 'Full', description: 'Complete persona including background' },
]

export const AgentInjector = memo(function AgentInjector({
  simulationId,
  agents,
  className,
}: AgentInjectorProps) {
  const [injectedAgents, setInjectedAgents] = useState<InjectedAgent[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showInjectModal, setShowInjectModal] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [endpointUrl, setEndpointUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [privacyTier, setPrivacyTier] = useState('basic')
  const [fallbackEnabled, setFallbackEnabled] = useState(true)
  const [timeoutSeconds, setTimeoutSeconds] = useState(30)
  const [selectedMetrics, setSelectedMetrics] = useState<InjectionMetrics | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadInjectedAgents = async () => {
    try {
      const result = await api.getInjectedAgents(simulationId)
      setInjectedAgents(result.injected_agents)
    } catch (error) {
      console.error('Failed to load injected agents:', error)
    }
  }

  useEffect(() => {
    loadInjectedAgents()
  }, [simulationId])

  const handleInject = async () => {
    if (!selectedAgent || !endpointUrl) return

    setIsLoading(true)
    setError(null)

    try {
      await api.injectAgent(simulationId, {
        agent_id: selectedAgent,
        endpoint_url: endpointUrl,
        api_key: apiKey || undefined,
        timeout_seconds: timeoutSeconds,
        privacy_tier: privacyTier,
        fallback_to_simulated: fallbackEnabled,
      })

      await loadInjectedAgents()
      setShowInjectModal(false)
      resetForm()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Injection failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemove = async (agentId: string) => {
    setIsLoading(true)
    try {
      await api.removeInjectedAgent(simulationId, agentId)
      await loadInjectedAgents()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Removal failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleHealthCheck = async (agentId: string) => {
    try {
      const result = await api.checkInjectionHealth(simulationId, agentId)
      // Update the agent's health status
      setInjectedAgents(prev =>
        prev.map(a =>
          a.agent_id === agentId
            ? { ...a, is_healthy: result.is_healthy }
            : a
        )
      )
    } catch (error) {
      console.error('Health check failed:', error)
    }
  }

  const handleViewMetrics = async (agentId: string) => {
    try {
      const metrics = await api.getInjectionMetrics(simulationId, agentId)
      setSelectedMetrics(metrics)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }

  const resetForm = () => {
    setSelectedAgent('')
    setEndpointUrl('')
    setApiKey('')
    setPrivacyTier('basic')
    setFallbackEnabled(true)
    setTimeoutSeconds(30)
  }

  const availableAgents = agents.filter(
    a => !injectedAgents.some(ia => ia.agent_id === a.id)
  )

  const getCircuitStateColor = (state: string) => {
    switch (state) {
      case 'CLOSED':
        return 'text-success'
      case 'OPEN':
        return 'text-error'
      case 'HALF_OPEN':
        return 'text-warning'
      default:
        return 'text-foreground-muted'
    }
  }

  return (
    <Card className={cn('p-4 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Plug className="h-4 w-4" />
          <h3 className="font-medium">Agent Injection</h3>
        </div>
        <Button
          size="sm"
          onClick={() => setShowInjectModal(true)}
          disabled={availableAgents.length === 0}
        >
          <Plug className="h-4 w-4 mr-1" />
          Inject Agent
        </Button>
      </div>

      {/* Injected Agents List */}
      {injectedAgents.length === 0 ? (
        <div className="text-center py-8 text-foreground-muted">
          <Unplug className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No agents injected</p>
          <p className="text-xs mt-1">
            Inject an external agent to test against simulated personas
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {injectedAgents.map((injected) => {
            const agentInfo = agents.find(a => a.id === injected.agent_id)
            return (
              <div
                key={injected.agent_id}
                className="p-3 rounded-lg border border-border bg-secondary/30"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {agentInfo?.name || injected.agent_id}
                    </span>
                    {injected.is_healthy === true && (
                      <CheckCircle className="h-4 w-4 text-success" />
                    )}
                    {injected.is_healthy === false && (
                      <AlertCircle className="h-4 w-4 text-error" />
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge variant="default" className={getCircuitStateColor(injected.circuit_state)}>
                      {injected.circuit_state}
                    </Badge>
                    <Badge variant="default">{injected.privacy_tier}</Badge>
                  </div>
                </div>

                <p className="text-xs text-foreground-muted mb-3 truncate">
                  {injected.endpoint_url}
                </p>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleHealthCheck(injected.agent_id)}
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Health
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleViewMetrics(injected.agent_id)}
                  >
                    <Activity className="h-3 w-3 mr-1" />
                    Metrics
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-error hover:text-error"
                    onClick={() => handleRemove(injected.agent_id)}
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Remove
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-3 rounded-lg bg-error/10 text-error text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Inject Modal */}
      <Modal
        open={showInjectModal}
        onClose={() => {
          setShowInjectModal(false)
          resetForm()
        }}
      >
        <ModalHeader onClose={() => { setShowInjectModal(false); resetForm() }}>
          Inject External Agent
        </ModalHeader>
        <div className="space-y-4">
          {/* Agent Selection */}
          <div className="space-y-2">
            <label className="text-sm text-foreground-secondary">Select Agent</label>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background"
            >
              <option value="">Select an agent...</option>
              {availableAgents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>

          {/* Endpoint URL */}
          <div className="space-y-2">
            <label className="text-sm text-foreground-secondary">Endpoint URL</label>
            <Input
              type="url"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              placeholder="https://your-agent.example.com/respond"
            />
          </div>

          {/* API Key (optional) */}
          <div className="space-y-2">
            <label className="text-sm text-foreground-secondary">API Key (optional)</label>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Bearer token or API key"
            />
          </div>

          {/* Privacy Tier */}
          <div className="space-y-2">
            <label className="text-sm text-foreground-secondary">Privacy Tier</label>
            <div className="flex gap-2">
              {PRIVACY_TIERS.map((tier) => (
                <button
                  key={tier.id}
                  onClick={() => setPrivacyTier(tier.id)}
                  className={cn(
                    'px-3 py-2 rounded-lg border text-sm transition-colors flex-1',
                    privacyTier === tier.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-border-hover'
                  )}
                  title={tier.description}
                >
                  {tier.name}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <div className="space-y-3 pt-2 border-t border-border">
            <div className="flex items-center gap-2 text-sm text-foreground-muted">
              <Settings className="h-4 w-4" />
              Advanced Options
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm">Timeout (seconds)</label>
              <Input
                type="number"
                min="1"
                max="300"
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(parseInt(e.target.value) || 30)}
                className="w-20 h-8"
              />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={fallbackEnabled}
                onChange={(e) => setFallbackEnabled(e.target.checked)}
                className="rounded border-border"
              />
              Fall back to simulated agent on failure
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowInjectModal(false)
                resetForm()
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleInject}
              disabled={!selectedAgent || !endpointUrl || isLoading}
              className="flex-1"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plug className="h-4 w-4 mr-2" />
              )}
              Inject
            </Button>
          </div>
        </div>
      </Modal>

      {/* Metrics Modal */}
      <Modal
        open={selectedMetrics !== null}
        onClose={() => setSelectedMetrics(null)}
      >
        <ModalHeader onClose={() => setSelectedMetrics(null)}>
          Injection Metrics
        </ModalHeader>
        {selectedMetrics && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-secondary/50">
                <p className="text-xs text-foreground-muted">Total Calls</p>
                <p className="text-xl font-bold">{selectedMetrics.total_calls}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/50">
                <p className="text-xs text-foreground-muted">Success Rate</p>
                <p className="text-xl font-bold">
                  {((1 - selectedMetrics.error_rate) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/50">
                <p className="text-xs text-foreground-muted">P50 Latency</p>
                <p className="text-xl font-bold">{selectedMetrics.latency_p50_ms}ms</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/50">
                <p className="text-xs text-foreground-muted">P99 Latency</p>
                <p className="text-xl font-bold">{selectedMetrics.latency_p99_ms}ms</p>
              </div>
            </div>

            <div className="flex justify-between text-sm">
              <span className="text-foreground-muted">Circuit State</span>
              <span className={getCircuitStateColor(selectedMetrics.circuit_state)}>
                {selectedMetrics.circuit_state}
              </span>
            </div>

            <div className="flex justify-between text-sm">
              <span className="text-foreground-muted">Timeout Rate</span>
              <span>{(selectedMetrics.timeout_rate * 100).toFixed(1)}%</span>
            </div>

            <Button
              variant="outline"
              onClick={() => setSelectedMetrics(null)}
              className="w-full"
            >
              Close
            </Button>
          </div>
        )}
      </Modal>
    </Card>
  )
})

export default AgentInjector
