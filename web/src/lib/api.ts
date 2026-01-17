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

  // Export
  getExportFormats: async (simulationId: string) => {
    return request<{
      simulation_id: string
      available_formats: string[]
      message_count: number
      has_evaluations: boolean
    }>(`/simulations/${simulationId}/export/formats`)
  },

  exportSimulation: async (
    simulationId: string,
    options: {
      format: string
      redaction?: string
      anonymize?: boolean
      min_score?: number
      inline?: boolean
    }
  ) => {
    const params = new URLSearchParams()
    params.set('format', options.format)
    if (options.redaction) params.set('redaction', options.redaction)
    if (options.anonymize) params.set('anonymize', 'true')
    if (options.min_score !== undefined) params.set('min_score', options.min_score.toString())
    if (options.inline) params.set('inline', 'true')

    return request<{
      simulation_id: string
      format: string
      record_count: number
      manifest?: Record<string, unknown>
      data?: unknown[]
    }>(`/simulations/${simulationId}/export?${params.toString()}`)
  },

  downloadExport: async (simulationId: string, format: string, options?: {
    redaction?: string
    anonymize?: boolean
    min_score?: number
  }) => {
    const params = new URLSearchParams()
    params.set('format', format)
    if (options?.redaction) params.set('redaction', options.redaction)
    if (options?.anonymize) params.set('anonymize', 'true')
    if (options?.min_score !== undefined) params.set('min_score', options.min_score.toString())

    const response = await fetch(`${API_BASE}/simulations/${simulationId}/export?${params.toString()}`)
    if (!response.ok) throw new Error('Export failed')
    return response.blob()
  },

  // Evaluation
  runEvaluation: async (
    simulationId: string,
    options?: {
      evaluator_names?: string[]
      message_ids?: string[]
      async_mode?: boolean
    }
  ) => {
    return request<{
      simulation_id: string
      job_id?: string
      status: string
      evaluations_run: number
      message: string
    }>(`/simulations/${simulationId}/evaluate`, {
      method: 'POST',
      body: options || {},
    })
  },

  getEvaluations: async (
    simulationId: string,
    options?: {
      evaluator_name?: string
      min_score?: number
      max_score?: number
    }
  ) => {
    const params = new URLSearchParams()
    if (options?.evaluator_name) params.set('evaluator_name', options.evaluator_name)
    if (options?.min_score !== undefined) params.set('min_score', options.min_score.toString())
    if (options?.max_score !== undefined) params.set('max_score', options.max_score.toString())
    const query = params.toString()

    return request<{
      evaluations: Array<{
        id: string
        message_id: string
        evaluator_name: string
        score: number
        explanation: string | null
        evaluator_version: string
        passed: boolean
        created_at: string | null
      }>
      total: number
      simulation_id: string
    }>(`/simulations/${simulationId}/evaluations${query ? `?${query}` : ''}`)
  },

  getEvaluationSummary: async (simulationId: string) => {
    return request<{
      simulation_id: string
      evaluator_summaries: Record<string, {
        evaluator_name: string
        count: number
        average_score: number
        min_score: number
        max_score: number
        pass_rate: number
        total_cost_usd: number
      }>
      total_evaluations: number
      average_score: number
      pass_rate: number
      total_cost_usd: number
      total_latency_ms: number
    }>(`/simulations/${simulationId}/evaluations/summary`)
  },

  // Agent Injection
  injectAgent: async (
    simulationId: string,
    data: {
      agent_id: string
      endpoint_url: string
      api_key?: string
      timeout_seconds?: number
      privacy_tier?: string
      fallback_to_simulated?: boolean
      max_retries?: number
    }
  ) => {
    return request<{
      simulation_id: string
      agent_id: string
      success: boolean
      message: string
      is_healthy: boolean | null
    }>(`/simulations/${simulationId}/inject-agent`, {
      method: 'POST',
      body: data,
    })
  },

  removeInjectedAgent: async (simulationId: string, agentId: string) => {
    return request<{ success: boolean }>(`/simulations/${simulationId}/inject-agent/${agentId}`, {
      method: 'DELETE',
    })
  },

  getInjectedAgents: async (simulationId: string) => {
    return request<{
      simulation_id: string
      injected_agents: Array<{
        agent_id: string
        endpoint_url: string
        privacy_tier: string
        fallback_to_simulated: boolean
        circuit_state: string
        is_healthy: boolean | null
      }>
      total: number
    }>(`/simulations/${simulationId}/injected-agents`)
  },

  getInjectionMetrics: async (simulationId: string, agentId: string) => {
    return request<{
      agent_id: string
      total_calls: number
      successful_calls: number
      failed_calls: number
      error_rate: number
      timeout_rate: number
      latency_p50_ms: number
      latency_p99_ms: number
      circuit_state: string
    }>(`/simulations/${simulationId}/inject-agent/${agentId}/metrics`)
  },

  checkInjectionHealth: async (simulationId: string, agentId: string) => {
    return request<{
      agent_id: string
      endpoint_url: string
      is_healthy: boolean
      latency_ms: number | null
      error: string | null
    }>(`/simulations/${simulationId}/inject-agent/${agentId}/health-check`, {
      method: 'POST',
    })
  },
}
