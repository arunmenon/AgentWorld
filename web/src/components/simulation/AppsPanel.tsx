import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ChevronDown,
  ChevronRight,
  Wallet,
  CheckCircle,
  XCircle,
  Activity,
  RefreshCw,
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Tooltip,
} from '@/components/ui'
import { api } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

interface Agent {
  id: string
  name: string
}

interface AppsPanelProps {
  simulationId: string
  agents: Agent[]
  isRunning?: boolean
}

interface AppInstance {
  id: string
  simulation_id: string
  app_id: string
  config: Record<string, unknown>
  state: Record<string, unknown>
  created_at: string | null
  updated_at: string | null
}

export function AppsPanel({ simulationId, agents, isRunning }: AppsPanelProps) {
  const [expandedApps, setExpandedApps] = useState<Set<string>>(new Set())

  // Fetch simulation apps
  const { data: appsData, refetch: refetchApps, isLoading: loadingApps } = useQuery({
    queryKey: ['simulation', simulationId, 'apps'],
    queryFn: () => api.getSimulationApps(simulationId),
    enabled: !!simulationId,
    refetchInterval: isRunning ? 3000 : false,
  })

  // Fetch action log
  const { data: actionsData } = useQuery({
    queryKey: ['simulation', simulationId, 'actions'],
    queryFn: () => api.getSimulationAppActions(simulationId, { limit: 20 }),
    enabled: !!simulationId,
    refetchInterval: isRunning ? 3000 : false,
  })

  const apps = appsData?.apps || []
  const actions = actionsData?.actions || []

  const toggleExpand = (appId: string) => {
    setExpandedApps((prev) => {
      const next = new Set(prev)
      if (next.has(appId)) {
        next.delete(appId)
      } else {
        next.add(appId)
      }
      return next
    })
  }

  const getAgentName = (agentId: string) => {
    const agent = agents.find((a) => a.id === agentId)
    return agent?.name || agentId.slice(0, 8)
  }

  const getAgentStates = (app: AppInstance) => {
    const state = app.state || {}
    const innerState = (state.state || state) as Record<string, unknown>
    const accounts = (innerState.accounts || {}) as Record<string, Record<string, unknown>>

    return Object.entries(accounts).map(([agentId, agentState]) => ({
      agentId,
      agentName: getAgentName(agentId),
      state: agentState,
    }))
  }

  const getAppActions = (appInstanceId: string) => {
    return actions.filter((a) => a.app_instance_id === appInstanceId)
  }

  if (loadingApps) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            Apps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-foreground-muted text-center py-4">
            Loading apps...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (apps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            Apps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-foreground-muted text-center py-4">
            No apps configured for this simulation
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-4 w-4" />
          Apps ({apps.length})
        </CardTitle>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => refetchApps()}
          className="h-8 w-8"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {apps.map((app) => {
          const isExpanded = expandedApps.has(app.app_id)
          const agentStates = getAgentStates(app)
          const appActions = getAppActions(app.id)
          const recentActions = appActions.slice(0, 5)
          const successCount = appActions.filter((a) => a.success).length
          const failCount = appActions.filter((a) => !a.success).length

          return (
            <div
              key={app.id}
              className="border border-border rounded-lg overflow-hidden"
            >
              {/* App header */}
              <button
                className="w-full flex items-center justify-between p-3 hover:bg-secondary/50 transition-colors text-left"
                onClick={() => toggleExpand(app.app_id)}
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-foreground-muted" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-foreground-muted" />
                  )}
                  <span className="font-medium">{app.app_id}</span>
                </div>
                <div className="flex items-center gap-2">
                  {appActions.length > 0 && (
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-success">{successCount}</span>
                      <span className="text-foreground-muted">/</span>
                      <span className="text-error">{failCount}</span>
                    </div>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {agentStates.length} agents
                  </Badge>
                </div>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="border-t border-border">
                  {/* Agent states */}
                  <div className="p-3 bg-secondary/30">
                    <h4 className="text-xs font-medium text-foreground-muted mb-2 uppercase">
                      Agent Balances
                    </h4>
                    <div className="space-y-1">
                      {agentStates.length === 0 ? (
                        <p className="text-xs text-foreground-muted">
                          No agent state yet
                        </p>
                      ) : (
                        agentStates.map(({ agentId, agentName, state }) => (
                          <div
                            key={agentId}
                            className="flex items-center justify-between text-sm"
                          >
                            <span className="text-foreground-secondary">
                              {agentName}
                            </span>
                            <span className="font-mono font-medium">
                              {typeof state.balance === 'number'
                                ? formatCurrency(state.balance)
                                : JSON.stringify(state.balance || state)}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Recent actions */}
                  <div className="p-3">
                    <h4 className="text-xs font-medium text-foreground-muted mb-2 uppercase flex items-center gap-1">
                      <Activity className="h-3 w-3" />
                      Recent Actions
                    </h4>
                    <div className="space-y-2">
                      {recentActions.length === 0 ? (
                        <p className="text-xs text-foreground-muted">
                          No actions yet
                        </p>
                      ) : (
                        recentActions.map((action) => (
                          <div
                            key={action.id}
                            className="flex items-start gap-2 text-xs"
                          >
                            {action.success ? (
                              <CheckCircle className="h-3.5 w-3.5 text-success mt-0.5 flex-shrink-0" />
                            ) : (
                              <XCircle className="h-3.5 w-3.5 text-error mt-0.5 flex-shrink-0" />
                            )}
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1">
                                <span className="font-medium">
                                  {getAgentName(action.agent_id)}
                                </span>
                                <span className="text-foreground-muted">→</span>
                                <span className="font-mono text-primary">
                                  {action.action_name}
                                </span>
                              </div>
                              {action.params && Object.keys(action.params).length > 0 && (
                                <Tooltip
                                  content={JSON.stringify(action.params, null, 2)}
                                  position="bottom"
                                >
                                  <p className="text-foreground-muted truncate cursor-help">
                                    {formatParams(action.params, agents)}
                                  </p>
                                </Tooltip>
                              )}
                              {action.error && (
                                <p className="text-error truncate">{action.error}</p>
                              )}
                            </div>
                            <span className="text-foreground-muted flex-shrink-0">
                              Step {action.step}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

function formatParams(params: Record<string, unknown>, agents: Agent[]): string {
  const parts: string[] = []

  for (const [key, value] of Object.entries(params)) {
    if (key === 'to' && typeof value === 'string') {
      const agent = agents.find((a) => a.id === value)
      parts.push(`to: ${agent?.name || value.slice(0, 8)}`)
    } else if (key === 'amount' && typeof value === 'number') {
      parts.push(`$${value}`)
    } else if (typeof value === 'string' && value.length > 20) {
      parts.push(`${key}: "${value.slice(0, 20)}..."`)
    } else if (typeof value === 'string') {
      parts.push(`${key}: "${value}"`)
    } else {
      parts.push(`${key}: ${JSON.stringify(value)}`)
    }
  }

  return parts.join(', ')
}
