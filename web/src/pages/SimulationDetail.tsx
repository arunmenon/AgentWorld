import { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronLeft,
  Trash2,
  Users,
  MessageSquare,
  Clock,
  DollarSign,
  Maximize2,
  Minimize2,
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
import { formatDate, formatCurrency } from '@/lib/utils'
import { api } from '@/lib/api'
import {
  useRealtimeStore,
  useIsConnected,
  useLiveMessages,
  useIsSimulationRunning,
} from '@/stores'
import {
  TopologyGraph,
  ConversationStream,
  AgentInspector,
  SimulationControls,
  type Message,
  type Memory,
} from '@/components/simulation'

function SimulationStatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
    running: 'success',
    paused: 'warning',
    completed: 'default',
    pending: 'default',
    failed: 'error',
  }
  return <Badge variant={variants[status] || 'default'}>{status}</Badge>
}

export default function SimulationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // State
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [isInspectorOpen, setIsInspectorOpen] = useState(false)
  const [isGraphExpanded, setIsGraphExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [agentFilter, setAgentFilter] = useState<string | null>(null)

  // Real-time store
  const { connect, disconnect, clearLiveData } = useRealtimeStore()
  const isConnected = useIsConnected()
  const liveMessages = useLiveMessages()
  const isSimulationRunning = useIsSimulationRunning()

  // Queries
  const { data: simulation, isLoading } = useQuery({
    queryKey: ['simulation', id],
    queryFn: () => api.getSimulation(id!),
    enabled: !!id,
    refetchInterval: isSimulationRunning ? 2000 : false, // Poll while running
  })

  const { data: agents } = useQuery({
    queryKey: ['simulation', id, 'agents'],
    queryFn: () => api.getSimulationAgents(id!),
    enabled: !!id,
  })

  const { data: messagesData, refetch: refetchMessages } = useQuery({
    queryKey: ['simulation', id, 'messages'],
    queryFn: () => api.getSimulationMessages(id!),
    enabled: !!id,
  })

  // Fetch memories for selected agent
  const { data: memoriesData, refetch: refetchMemories } = useQuery({
    queryKey: ['simulation', id, 'agent', selectedAgentId, 'memories'],
    queryFn: () => api.getAgentMemories(id!, selectedAgentId!),
    enabled: !!id && !!selectedAgentId,
  })

  // Connect to WebSocket when component mounts
  useEffect(() => {
    if (id) {
      connect(id)
    }

    return () => {
      disconnect()
      clearLiveData()
    }
  }, [id, connect, disconnect, clearLiveData])

  // Refetch messages and memories when live messages arrive
  useEffect(() => {
    if (liveMessages.length > 0) {
      refetchMessages()
      if (selectedAgentId) {
        refetchMemories()
      }
    }
  }, [liveMessages.length, refetchMessages, refetchMemories, selectedAgentId])

  // Combine API messages with live messages
  const messages: Message[] = useMemo(() => {
    const apiMessages = messagesData?.messages || []
    return apiMessages
  }, [messagesData])

  // Transform API memories to component format
  const memories: Memory[] = useMemo(() => {
    if (!memoriesData?.memories) return []
    return memoriesData.memories.map(m => ({
      id: m.id,
      agent_id: m.agent_id,
      type: m.memory_type as Memory['type'],
      content: m.content,
      importance: m.importance / 10, // API returns 0-10, component expects 0-1
      created_at: m.created_at,
    }))
  }, [memoriesData])

  // Get selected agent
  const selectedAgent = useMemo(() => {
    if (!selectedAgentId || !agents?.agents) return null
    return agents.agents.find((a) => a.id === selectedAgentId) || null
  }, [selectedAgentId, agents])

  // Mutations
  const startMutation = useMutation({
    mutationFn: () => api.startSimulation(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['simulation', id] }),
  })

  const pauseMutation = useMutation({
    mutationFn: () => api.pauseSimulation(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['simulation', id] }),
  })

  const stepMutation = useMutation({
    mutationFn: (count: number) => api.stepSimulation(id!, count),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation', id] })
      queryClient.invalidateQueries({ queryKey: ['simulation', id, 'messages'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteSimulation(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] })
      navigate('/simulations')
    },
  })

  // Inject stimulus handler
  const handleInjectStimulus = useCallback(
    async (content: string, targetAgents: string[]) => {
      await api.injectStimulus(id!, content, targetAgents)
    },
    [id]
  )

  // Agent selection handlers
  const handleAgentSelect = useCallback((agentId: string) => {
    setSelectedAgentId(agentId)
    setIsInspectorOpen(true)
  }, [])

  const handleCloseInspector = useCallback(() => {
    setIsInspectorOpen(false)
    setSelectedAgentId(null)
  }, [])

  if (isLoading) {
    return (
      <div className="p-6 text-center text-foreground-secondary">
        Loading simulation...
      </div>
    )
  }

  if (!simulation) {
    return (
      <div className="p-6 text-center text-foreground-secondary">
        Simulation not found.
      </div>
    )
  }

  const agentsList = agents?.agents || []

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/simulations')}
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{simulation.name}</h1>
              <SimulationStatusBadge status={simulation.status} />
            </div>
            <p className="text-foreground-secondary">
              Created {formatDate(simulation.created_at)}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          onClick={() => {
            if (confirm('Are you sure you want to delete this simulation?')) {
              deleteMutation.mutate()
            }
          }}
        >
          <Trash2 className="h-4 w-4 text-error" />
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-foreground-secondary">Agents</p>
              <p className="text-xl font-semibold">{simulation.agent_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center">
              <MessageSquare className="h-5 w-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-foreground-secondary">Messages</p>
              <p className="text-xl font-semibold">{simulation.message_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-success" />
            </div>
            <div>
              <p className="text-sm text-foreground-secondary">Progress</p>
              <p className="text-xl font-semibold">
                {simulation.current_step} / {simulation.total_steps}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-warning/10 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-sm text-foreground-secondary">Cost</p>
              <p className="text-xl font-semibold">
                {formatCurrency(simulation.total_cost)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: Controls + Topology */}
        <div className="space-y-6">
          {/* Simulation Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <SimulationControls
                status={simulation.status as any}
                currentStep={simulation.current_step}
                totalSteps={simulation.total_steps}
                isConnected={isConnected}
                isStepPending={stepMutation.isPending}
                agents={agentsList.map((a) => ({ id: a.id, name: a.name }))}
                onStart={() => startMutation.mutate()}
                onPause={() => pauseMutation.mutate()}
                onStep={(count = 1) => stepMutation.mutate(count)}
                onInjectStimulus={handleInjectStimulus}
              />
            </CardContent>
          </Card>

          {/* Topology Graph */}
          <Card className={isGraphExpanded ? 'lg:col-span-3' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base">Agent Topology</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsGraphExpanded(!isGraphExpanded)}
              >
                {isGraphExpanded ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </CardHeader>
            <CardContent>
              <TopologyGraph
                agents={agentsList}
                messages={messages}
                selectedAgentId={selectedAgentId || undefined}
                onAgentSelect={handleAgentSelect}
                width={isGraphExpanded ? 800 : 320}
                height={isGraphExpanded ? 400 : 250}
              />
            </CardContent>
          </Card>

          {/* Agents list */}
          <Card>
            <CardHeader>
              <CardTitle>Agents ({agentsList.length})</CardTitle>
            </CardHeader>
            <CardContent className="divide-y divide-border max-h-[300px] overflow-y-auto">
              {agentsList.map((agent) => (
                <button
                  key={agent.id}
                  className="w-full py-3 first:pt-0 last:pb-0 text-left hover:bg-secondary/50 -mx-6 px-6 transition-colors"
                  onClick={() => handleAgentSelect(agent.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1 mr-3">
                      <p className="font-medium">{agent.name}</p>
                      {agent.background && (
                        <Tooltip
                          content={agent.background}
                          position="bottom"
                          maxWidth={280}
                        >
                          <p className="text-sm text-foreground-secondary line-clamp-1 cursor-help">
                            {agent.background}
                          </p>
                        </Tooltip>
                      )}
                    </div>
                    <Badge variant="outline" className="flex-shrink-0">{agent.memory_count} memories</Badge>
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right column: Conversation stream */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Conversation</CardTitle>
            </CardHeader>
            <CardContent>
              <ConversationStream
                messages={messages}
                selectedAgentId={selectedAgentId || undefined}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                agentFilter={agentFilter}
                onAgentFilterChange={setAgentFilter}
                autoScroll={true}
                height={700}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Agent Inspector */}
      <AgentInspector
        agent={selectedAgent}
        messages={messages}
        memories={memories}
        totalSteps={simulation.total_steps}
        isOpen={isInspectorOpen}
        onClose={handleCloseInspector}
      />
    </div>
  )
}
