import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { queryClient } from '@/lib/queryClient'

// Event types matching backend EventType class
export type SimulationEventType =
  | 'connected'
  | 'disconnected'
  | 'subscribed'
  | 'ping'
  | 'pong'
  | 'simulation.created'
  | 'simulation.started'
  | 'simulation.paused'
  | 'simulation.resumed'
  | 'simulation.completed'
  | 'simulation.error'
  | 'step.started'
  | 'step.completed'
  | 'agent.thinking'
  | 'agent.responded'
  | 'message.created'
  | 'memory.created'

// Event payload interfaces
export interface BaseEvent {
  type: SimulationEventType
  simulation_id?: string
}

export interface StepEvent extends BaseEvent {
  type: 'step.started' | 'step.completed'
  step: number
  total_steps: number
  messages_generated?: number
}

export interface AgentThinkingEvent extends BaseEvent {
  type: 'agent.thinking'
  agent_id: string
  agent_name: string
}

export interface AgentRespondedEvent extends BaseEvent {
  type: 'agent.responded'
  agent_id: string
  agent_name: string
  response_preview?: string
}

export interface MessageCreatedEvent extends BaseEvent {
  type: 'message.created'
  message_id: string
  sender_id: string
  sender_name: string
  receiver_id?: string
  receiver_name?: string
  content_preview?: string
  step: number
}

export interface SimulationCompletedEvent extends BaseEvent {
  type: 'simulation.completed'
  stats?: {
    total_messages?: number
    total_tokens?: number
    total_cost?: number
  }
}

export interface SimulationErrorEvent extends BaseEvent {
  type: 'simulation.error'
  error: string
}

export type SimulationEvent =
  | BaseEvent
  | StepEvent
  | AgentThinkingEvent
  | AgentRespondedEvent
  | MessageCreatedEvent
  | SimulationCompletedEvent
  | SimulationErrorEvent

// Live message type for real-time display
export interface LiveMessage {
  id: string
  sender_id: string
  sender_name: string
  receiver_id?: string
  receiver_name?: string
  content: string
  step: number
  timestamp: Date
}

// Agent state for real-time tracking
export interface AgentState {
  id: string
  name: string
  status: 'idle' | 'thinking' | 'responded'
  lastActivity?: Date
  messageCount: number
}

interface RealtimeStore {
  // Connection state
  isConnected: boolean
  connectionError: string | null
  reconnectAttempts: number
  subscribedSimulationId: string | null
  isDisconnecting: boolean

  // WebSocket instance
  socket: WebSocket | null

  // Real-time data
  liveMessages: LiveMessage[]
  agentStates: Map<string, AgentState>
  currentStep: number
  totalSteps: number
  isSimulationRunning: boolean

  // Pending events for batching
  pendingEvents: SimulationEvent[]
  batchTimeoutId: ReturnType<typeof setTimeout> | null

  // Event history for debugging
  eventHistory: SimulationEvent[]

  // Actions
  connect: (simulationId: string) => void
  disconnect: () => void
  reconnect: () => void

  // Internal handlers
  handleEvent: (event: SimulationEvent) => void
  processBatch: () => void
  clearLiveData: () => void

  // Selectors
  getAgentState: (agentId: string) => AgentState | undefined
  getMessagesForAgent: (agentId: string) => LiveMessage[]
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const RECONNECT_DELAY = 2000
const MAX_RECONNECT_ATTEMPTS = 5
const BATCH_WINDOW_MS = 50
const MAX_LIVE_MESSAGES = 500
const MAX_EVENT_HISTORY = 100

export const useRealtimeStore = create<RealtimeStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    isConnected: false,
    connectionError: null,
    reconnectAttempts: 0,
    subscribedSimulationId: null,
    isDisconnecting: false,
    socket: null,
    liveMessages: [],
    agentStates: new Map(),
    currentStep: 0,
    totalSteps: 0,
    isSimulationRunning: false,
    pendingEvents: [],
    batchTimeoutId: null,
    eventHistory: [],

    connect: (simulationId: string) => {
      const { socket } = get()

      // Reset disconnecting flag - we want to connect now
      set({ isDisconnecting: false })

      // Close existing connection cleanly
      if (socket) {
        if (socket.readyState === WebSocket.OPEN) {
          socket.close(1000, 'New connection requested')
        }
        set({ socket: null })
      }

      const wsUrl = `${WS_BASE_URL}/ws/simulations/${simulationId}`

      try {
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          // Check if we should still be connected
          if (get().isDisconnecting) {
            ws.close(1000, 'Disconnected during connection')
            return
          }
          set({
            isConnected: true,
            connectionError: null,
            reconnectAttempts: 0,
            subscribedSimulationId: simulationId,
            socket: ws,
          })
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as SimulationEvent

            // Handle ping/pong keepalive
            if (data.type === 'ping') {
              ws.send(JSON.stringify({ type: 'pong' }))
              return
            }

            get().handleEvent(data)
          } catch (e) {
            console.error('Failed to parse WebSocket message:', event.data, e)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          set({ connectionError: 'Connection error occurred' })
        }

        ws.onclose = (event) => {
          set({ isConnected: false, socket: null, isDisconnecting: false })

          // Auto-reconnect if not a clean close and not intentionally disconnecting
          if (!event.wasClean && !get().isDisconnecting && get().reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            setTimeout(() => {
              const { subscribedSimulationId, reconnectAttempts, isDisconnecting } = get()
              if (subscribedSimulationId && !isDisconnecting) {
                set({ reconnectAttempts: reconnectAttempts + 1 })
                get().connect(subscribedSimulationId)
              }
            }, RECONNECT_DELAY)
          }
        }

        set({ socket: ws })
      } catch (error) {
        set({ connectionError: `Failed to connect: ${error}` })
      }
    },

    disconnect: () => {
      const { socket, batchTimeoutId } = get()

      // Set disconnecting flag first to prevent reconnection attempts
      set({ isDisconnecting: true })

      if (batchTimeoutId) {
        clearTimeout(batchTimeoutId)
      }

      if (socket) {
        if (socket.readyState === WebSocket.OPEN) {
          socket.close(1000, 'Client disconnect')
        }
        // For CONNECTING sockets, the onopen handler will check isDisconnecting and close
      }

      // Reset state but keep isDisconnecting true - onclose will reset it
      set({
        socket: null,
        isConnected: false,
        subscribedSimulationId: null,
        reconnectAttempts: 0,
        batchTimeoutId: null,
      })

      // Reset isDisconnecting after a short delay to handle cases where onclose doesn't fire
      setTimeout(() => {
        set({ isDisconnecting: false })
      }, 100)
    },

    reconnect: () => {
      const { subscribedSimulationId, connect } = get()
      if (subscribedSimulationId) {
        connect(subscribedSimulationId)
      }
    },

    handleEvent: (event: SimulationEvent) => {
      const { pendingEvents, batchTimeoutId } = get()

      // Add to event history
      set((state) => ({
        eventHistory: [...state.eventHistory.slice(-(MAX_EVENT_HISTORY - 1)), event],
      }))

      // Add to pending batch
      set({ pendingEvents: [...pendingEvents, event] })

      // Set up batch processing if not already scheduled
      if (!batchTimeoutId) {
        const timeoutId = setTimeout(() => {
          get().processBatch()
        }, BATCH_WINDOW_MS)
        set({ batchTimeoutId: timeoutId })
      }
    },

    processBatch: () => {
      const { pendingEvents, subscribedSimulationId } = get()
      set({ pendingEvents: [], batchTimeoutId: null })

      if (pendingEvents.length === 0) return

      // Process all pending events
      let newMessages: LiveMessage[] = []
      const agentStateUpdates = new Map<string, Partial<AgentState>>()
      let stepUpdate: { current?: number; total?: number } = {}
      let isRunning = get().isSimulationRunning
      let shouldInvalidateQueries = false

      for (const event of pendingEvents) {
        switch (event.type) {
          case 'simulation.started':
            isRunning = true
            shouldInvalidateQueries = true
            break

          case 'simulation.paused':
            isRunning = false
            shouldInvalidateQueries = true
            break

          case 'simulation.resumed':
            isRunning = true
            shouldInvalidateQueries = true
            break

          case 'simulation.completed':
            isRunning = false
            shouldInvalidateQueries = true
            break

          case 'simulation.error':
            isRunning = false
            shouldInvalidateQueries = true
            break

          case 'step.started': {
            const stepEvent = event as StepEvent
            stepUpdate = {
              current: stepEvent.step,
              total: stepEvent.total_steps,
            }
            break
          }

          case 'step.completed': {
            const stepEvent = event as StepEvent
            stepUpdate = {
              current: stepEvent.step,
              total: stepEvent.total_steps,
            }
            shouldInvalidateQueries = true
            break
          }

          case 'agent.thinking': {
            const agentEvent = event as AgentThinkingEvent
            agentStateUpdates.set(agentEvent.agent_id, {
              id: agentEvent.agent_id,
              name: agentEvent.agent_name,
              status: 'thinking',
              lastActivity: new Date(),
            })
            break
          }

          case 'agent.responded': {
            const agentEvent = event as AgentRespondedEvent
            agentStateUpdates.set(agentEvent.agent_id, {
              id: agentEvent.agent_id,
              name: agentEvent.agent_name,
              status: 'responded',
              lastActivity: new Date(),
            })
            break
          }

          case 'message.created': {
            const msgEvent = event as MessageCreatedEvent
            newMessages.push({
              id: msgEvent.message_id,
              sender_id: msgEvent.sender_id,
              sender_name: msgEvent.sender_name,
              receiver_id: msgEvent.receiver_id,
              receiver_name: msgEvent.receiver_name,
              content: msgEvent.content_preview || '',
              step: msgEvent.step,
              timestamp: new Date(),
            })

            // Update agent message count
            const existingUpdate = agentStateUpdates.get(msgEvent.sender_id)
            const existingState = get().agentStates.get(msgEvent.sender_id)
            const currentCount = existingUpdate?.messageCount ?? existingState?.messageCount ?? 0
            agentStateUpdates.set(msgEvent.sender_id, {
              ...existingUpdate,
              id: msgEvent.sender_id,
              name: msgEvent.sender_name,
              status: 'idle',
              messageCount: currentCount + 1,
            })
            break
          }
        }
      }

      // Apply all updates in one state change
      set((state) => {
        const newAgentStates = new Map(state.agentStates)
        agentStateUpdates.forEach((update, id) => {
          const existing = newAgentStates.get(id) || {
            id,
            name: update.name || id,
            status: 'idle' as const,
            messageCount: 0,
          }
          newAgentStates.set(id, { ...existing, ...update } as AgentState)
        })

        // Keep only the most recent messages
        const updatedMessages = [...state.liveMessages, ...newMessages].slice(-MAX_LIVE_MESSAGES)

        return {
          liveMessages: updatedMessages,
          agentStates: newAgentStates,
          currentStep: stepUpdate.current ?? state.currentStep,
          totalSteps: stepUpdate.total ?? state.totalSteps,
          isSimulationRunning: isRunning,
        }
      })

      // Invalidate React Query cache if needed
      if (shouldInvalidateQueries && subscribedSimulationId) {
        queryClient.invalidateQueries({ queryKey: ['simulation', subscribedSimulationId] })
        queryClient.invalidateQueries({ queryKey: ['simulation', subscribedSimulationId, 'messages'] })
      }
    },

    clearLiveData: () => {
      set({
        liveMessages: [],
        agentStates: new Map(),
        currentStep: 0,
        totalSteps: 0,
        isSimulationRunning: false,
        eventHistory: [],
      })
    },

    getAgentState: (agentId: string) => {
      return get().agentStates.get(agentId)
    },

    getMessagesForAgent: (agentId: string) => {
      return get().liveMessages.filter(
        (msg) => msg.sender_id === agentId || msg.receiver_id === agentId
      )
    },
  }))
)

// Export selector hooks for common use cases
export const useIsConnected = () => useRealtimeStore((state) => state.isConnected)
export const useLiveMessages = () => useRealtimeStore((state) => state.liveMessages)
export const useCurrentStep = () => useRealtimeStore((state) => state.currentStep)
export const useIsSimulationRunning = () => useRealtimeStore((state) => state.isSimulationRunning)
export const useAgentStates = () => useRealtimeStore((state) => state.agentStates)
