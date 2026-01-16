import { create } from 'zustand'

interface SimulationEvent {
  type: string
  simulation_id?: string
  [key: string]: unknown
}

interface SimulationState {
  // WebSocket connection
  socket: WebSocket | null
  connected: boolean
  connectionError: string | null

  // Active simulation
  activeSimulationId: string | null
  setActiveSimulation: (id: string | null) => void

  // Events
  events: SimulationEvent[]
  addEvent: (event: SimulationEvent) => void
  clearEvents: () => void

  // Connection management
  connect: (simulationId?: string) => void
  disconnect: () => void
  subscribe: (simulationId: string) => void
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  socket: null,
  connected: false,
  connectionError: null,
  activeSimulationId: null,
  events: [],

  setActiveSimulation: (id) => set({ activeSimulationId: id }),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events.slice(-99), event], // Keep last 100 events
    })),

  clearEvents: () => set({ events: [] }),

  connect: (simulationId) => {
    const { socket } = get()

    // Close existing connection
    if (socket) {
      socket.close()
    }

    const wsUrl = simulationId
      ? `ws://localhost:8000/ws/simulations/${simulationId}`
      : 'ws://localhost:8000/ws'

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      set({ connected: true, connectionError: null })
      if (simulationId) {
        set({ activeSimulationId: simulationId })
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        get().addEvent(data)
      } catch {
        console.error('Failed to parse WebSocket message:', event.data)
      }
    }

    ws.onerror = () => {
      set({ connectionError: 'Connection error' })
    }

    ws.onclose = () => {
      set({ connected: false, socket: null })
    }

    set({ socket: ws })
  },

  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.close()
      set({ socket: null, connected: false, activeSimulationId: null })
    }
  },

  subscribe: (simulationId) => {
    const { socket, connected } = get()
    if (socket && connected) {
      socket.send(
        JSON.stringify({
          type: 'subscribe',
          simulation_id: simulationId,
        })
      )
      set({ activeSimulationId: simulationId })
    }
  },
}))
