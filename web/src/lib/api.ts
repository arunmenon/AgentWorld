const API_BASE = '/api/v1'

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  }

  if (body) {
    config.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(error.detail?.message || error.message || 'Request failed')
  }

  return response.json()
}

// Types
export interface Simulation {
  id: string
  name: string
  status: string
  current_step: number
  total_steps: number
  max_steps: number
  total_tokens: number
  total_cost: number
  agent_count: number
  message_count: number
  progress_percent: number | null
  created_at: string
  updated_at: string | null
}

export interface Agent {
  id: string
  simulation_id: string
  name: string
  traits: Record<string, number> | null
  background: string | null
  model: string | null
  message_count: number
  memory_count: number
  created_at: string
}

export interface Message {
  id: string
  simulation_id: string
  sender_id: string
  sender_name: string | null
  receiver_id: string | null
  receiver_name: string | null
  content: string
  step: number
  timestamp: string | null
}

export interface Persona {
  id: string
  name: string
  description: string | null
  occupation: string | null
  age: number | null
  location: string | null
  background: string | null
  traits: Record<string, number>
  tags: string[]
  usage_count: number
  created_at: string
  updated_at: string | null
}

export interface Collection {
  id: string
  name: string
  description: string | null
  tags: string[]
  member_count: number
  created_at: string
  updated_at: string | null
}

// API Functions
export const api = {
  // Simulations
  getSimulations: async (params?: { status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.limit) searchParams.set('per_page', params.limit.toString())
    const query = searchParams.toString()
    return request<{ simulations: Simulation[]; total: number }>(
      `/simulations${query ? `?${query}` : ''}`
    )
  },

  getSimulation: async (id: string) => {
    return request<Simulation>(`/simulations/${id}`)
  },

  createSimulation: async (data: {
    name: string
    steps: number
    initial_prompt?: string
    model?: string
    agents?: Array<{
      name: string
      background?: string
      traits?: Record<string, number>
      model?: string
    }>
  }) => {
    return request<Simulation>('/simulations', { method: 'POST', body: data })
  },

  deleteSimulation: async (id: string) => {
    return request<{ success: boolean }>(`/simulations/${id}`, { method: 'DELETE' })
  },

  startSimulation: async (id: string) => {
    return request<{ simulation_id: string; status: string; message: string }>(
      `/simulations/${id}/start`,
      { method: 'POST' }
    )
  },

  pauseSimulation: async (id: string) => {
    return request<{ simulation_id: string; status: string; message: string }>(
      `/simulations/${id}/pause`,
      { method: 'POST' }
    )
  },

  resumeSimulation: async (id: string) => {
    return request<{ simulation_id: string; status: string; message: string }>(
      `/simulations/${id}/resume`,
      { method: 'POST' }
    )
  },

  stepSimulation: async (id: string, count: number = 1) => {
    return request<{
      simulation_id: string
      steps_executed: number
      current_step: number
      total_steps: number
      messages_generated: number
      status: string
    }>(`/simulations/${id}/step`, { method: 'POST', body: { count } })
  },

  injectStimulus: async (id: string, content: string, targetAgents?: string[]) => {
    return request<{
      simulation_id: string
      injected: boolean
      content: string
      affected_agents: number
    }>(`/simulations/${id}/inject`, {
      method: 'POST',
      body: { content, target_agents: targetAgents },
    })
  },

  // Agents
  getSimulationAgents: async (simulationId: string) => {
    return request<{ agents: Agent[]; total: number }>(
      `/simulations/${simulationId}/agents`
    )
  },

  getAgent: async (simulationId: string, agentId: string) => {
    return request<Agent>(`/simulations/${simulationId}/agents/${agentId}`)
  },

  getAgentMemories: async (
    simulationId: string,
    agentId: string,
    params?: { memory_type?: string; limit?: number }
  ) => {
    const searchParams = new URLSearchParams()
    if (params?.memory_type) searchParams.set('memory_type', params.memory_type)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return request<{
      memories: Array<{
        id: string
        agent_id: string
        memory_type: string
        content: string
        importance: number
        source: string | null
        created_at: string
      }>
      total: number
    }>(`/simulations/${simulationId}/agents/${agentId}/memories${query ? `?${query}` : ''}`)
  },

  // Messages
  getSimulationMessages: async (
    simulationId: string,
    params?: { step?: number; sender_id?: string; limit?: number }
  ) => {
    const searchParams = new URLSearchParams()
    if (params?.step) searchParams.set('step', params.step.toString())
    if (params?.sender_id) searchParams.set('sender_id', params.sender_id)
    if (params?.limit) searchParams.set('per_page', params.limit.toString())
    const query = searchParams.toString()
    return request<{ messages: Message[]; total: number }>(
      `/simulations/${simulationId}/messages${query ? `?${query}` : ''}`
    )
  },

  // Personas
  getPersonas: async (params?: { occupation?: string; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.occupation) searchParams.set('occupation', params.occupation)
    if (params?.limit) searchParams.set('per_page', params.limit.toString())
    const query = searchParams.toString()
    return request<{ personas: Persona[]; total: number }>(
      `/personas${query ? `?${query}` : ''}`
    )
  },

  searchPersonas: async (query: string, limit?: number) => {
    const searchParams = new URLSearchParams({ q: query })
    if (limit) searchParams.set('limit', limit.toString())
    return request<{ personas: Persona[]; total: number }>(
      `/personas/search?${searchParams.toString()}`
    )
  },

  getPersona: async (id: string) => {
    return request<Persona>(`/personas/${id}`)
  },

  createPersona: async (data: {
    name: string
    description?: string
    occupation?: string
    age?: number
    location?: string
    background?: string
    traits?: {
      openness: number
      conscientiousness: number
      extraversion: number
      agreeableness: number
      neuroticism: number
    }
    tags?: string[]
  }) => {
    return request<Persona>('/personas', { method: 'POST', body: data })
  },

  updatePersona: async (
    id: string,
    data: Partial<{
      name: string
      description: string
      occupation: string
      age: number
      location: string
      background: string
      traits: {
        openness: number
        conscientiousness: number
        extraversion: number
        agreeableness: number
        neuroticism: number
      }
      tags: string[]
    }>
  ) => {
    return request<Persona>(`/personas/${id}`, { method: 'PATCH', body: data })
  },

  deletePersona: async (id: string) => {
    return request<{ success: boolean }>(`/personas/${id}`, { method: 'DELETE' })
  },

  // Collections
  getCollections: async () => {
    return request<{ collections: Collection[]; total: number }>('/collections')
  },

  getCollection: async (id: string) => {
    return request<Collection>(`/collections/${id}`)
  },

  createCollection: async (data: {
    name: string
    description?: string
    tags?: string[]
  }) => {
    return request<Collection>('/collections', { method: 'POST', body: data })
  },

  deleteCollection: async (id: string) => {
    return request<{ success: boolean }>(`/collections/${id}`, { method: 'DELETE' })
  },

  getCollectionPersonas: async (collectionId: string) => {
    return request<{ personas: Persona[]; total: number }>(
      `/collections/${collectionId}/personas`
    )
  },

  addPersonaToCollection: async (collectionId: string, personaId: string) => {
    return request<{ success: boolean }>(
      `/collections/${collectionId}/personas`,
      { method: 'POST', body: { persona_id: personaId } }
    )
  },

  removePersonaFromCollection: async (collectionId: string, personaId: string) => {
    return request<{ success: boolean }>(
      `/collections/${collectionId}/personas/${personaId}`,
      { method: 'DELETE' }
    )
  },

  // Health
  checkHealth: async () => {
    return request<{ status: string; version: string; api_version: string }>('/health')
  },
}
