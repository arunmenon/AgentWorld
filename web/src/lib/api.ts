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
/** Goal progress information for simulations */
export interface GoalProgress {
  goal_spec?: {
    conditions: Array<{
      id?: string
      goal_type: string
      description: string
      app_id?: string
      field_path?: string
      operator?: string
      expected_value?: unknown
      handoff_id?: string
      required_phrase?: string
    }>
    success_mode: 'all' | 'any'
    description: string
  }
  goal_achieved: boolean
  goal_achieved_step?: number
  termination_mode: 'max_steps' | 'goal' | 'hybrid'
}

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
  /** τ²-bench: Task ID if this is an evaluation run */
  task_id?: string
  /** Goal-based termination info (ADR-020.1) */
  goal?: GoalProgress
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

// App Definition Types
export type AppCategory = 'payment' | 'shopping' | 'communication' | 'calendar' | 'social' | 'custom'

export interface ParamSpec {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  description?: string
  required?: boolean
  default?: unknown
  min_value?: number
  max_value?: number
  min_length?: number
  max_length?: number
  pattern?: string
  enum?: unknown[]
}

export interface LogicBlock {
  type: 'validate' | 'update' | 'notify' | 'return' | 'error' | 'branch' | 'loop'
  condition?: string
  error_message?: string
  target?: string
  operation?: 'set' | 'add' | 'subtract' | 'append' | 'remove'
  value?: unknown
  to?: string
  message?: string
  data?: Record<string, unknown>
  then?: LogicBlock[]
  else?: LogicBlock[]
  collection?: string
  item?: string
  body?: LogicBlock[]
}

export interface ActionDefinition {
  name: string
  description: string
  parameters?: Record<string, ParamSpec>
  returns?: Record<string, string>
  logic: LogicBlock[]
}

export interface StateField {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  default?: unknown
  per_agent?: boolean
  description?: string
  /** Whether user agents can see this field in state-constrained mode (τ²-bench) */
  observable?: boolean
}

/** Access control types for dual-control simulations (τ²-bench) */
export type AccessType = 'shared' | 'role_restricted' | 'per_agent'

/** Agent roles for dual-control simulations (τ²-bench) */
export type AgentRole = 'peer' | 'service_agent' | 'customer'

/** State management type */
export type StateType = 'shared' | 'per_agent'

// ==========================================================================
// Dual-Control Task Types (τ²-bench)
// ==========================================================================

export interface CoordinationHandoff {
  handoff_id: string
  from_role: AgentRole
  to_role: AgentRole
  expected_action: string
  description?: string
  instruction_pattern?: string
}

export interface DualControlTaskDefinition {
  id: string
  task_id: string
  name: string
  description: string
  domain: string
  difficulty: string
  simulation_config: Record<string, unknown>
  agent_id: string
  agent_role: AgentRole
  agent_instruction: string
  agent_apps: string[]
  agent_initial_state: Record<string, unknown>
  agent_goal_state: Record<string, unknown>
  user_id: string
  user_role: AgentRole
  user_instruction: string
  user_apps: string[]
  user_initial_state: Record<string, unknown>
  user_goal_state: Record<string, unknown>
  required_handoffs: CoordinationHandoff[]
  max_turns: number
  expected_coordination_count: number
  is_active: boolean
  tags: string[]
  created_at: string | null
  updated_at: string | null
}

export interface CreateDualControlTaskRequest {
  task_id: string
  name: string
  description: string
  domain: string
  difficulty: string
  simulation_config?: Record<string, unknown>
  agent_id: string
  agent_role: AgentRole
  agent_instruction: string
  agent_apps: string[]
  agent_initial_state?: Record<string, unknown>
  agent_goal_state?: Record<string, unknown>
  user_id: string
  user_role: AgentRole
  user_instruction: string
  user_apps: string[]
  user_initial_state?: Record<string, unknown>
  user_goal_state?: Record<string, unknown>
  required_handoffs?: CoordinationHandoff[]
  max_turns?: number
  expected_coordination_count?: number
  tags?: string[]
}

export interface UpdateDualControlTaskRequest {
  name?: string
  description?: string
  difficulty?: string
  agent_instruction?: string
  user_instruction?: string
  agent_apps?: string[]
  user_apps?: string[]
  agent_initial_state?: Record<string, unknown>
  user_initial_state?: Record<string, unknown>
  agent_goal_state?: Record<string, unknown>
  user_goal_state?: Record<string, unknown>
  required_handoffs?: CoordinationHandoff[]
  max_turns?: number
  tags?: string[]
  is_active?: boolean
}

export interface CoordinationEvent {
  id: string
  event_id: string
  trial_id: string
  task_id: string
  instructor_id: string
  instructor_role: AgentRole
  instruction_text: string
  actor_id?: string
  actor_role?: AgentRole
  action_taken?: string
  action_params?: Record<string, unknown>
  matched_handoff_id?: string
  match_confidence: number
  handoff_successful: boolean
  latency_turns: number
  timestamp: string | null
}

export interface CreateCoordinationEventRequest {
  event_id: string
  trial_id: string
  instructor_id: string
  instructor_role: AgentRole
  instruction_text: string
  actor_id?: string
  actor_role?: AgentRole
  action_taken?: string
  action_params?: Record<string, unknown>
  matched_handoff_id?: string
  match_confidence?: number
  handoff_successful?: boolean
  latency_turns?: number
}

export interface CoordinationMetrics {
  task_id: string
  trial_id?: string
  total_handoffs_required: number
  handoffs_completed: number
  coordination_success_rate: number
  avg_instruction_to_action_turns: number
  unnecessary_user_actions: number
  instruction_clarity_score?: number
  user_confusion_count: number
  computed_at: string
}

export interface SoloDualComparisonResult {
  id: string
  task_id: string
  solo_trials: number
  solo_successes: number
  solo_pass_1: number
  solo_avg_steps: number
  dual_trials: number
  dual_successes: number
  dual_pass_1: number
  dual_avg_steps: number
  performance_drop: number
  step_increase: number
  computed_at: string | null
}

export interface AppDefinition {
  id: string
  app_id: string
  name: string
  description: string | null
  category: AppCategory
  icon: string | null
  version: number
  actions: ActionDefinition[]
  state_schema: StateField[]
  initial_config: Record<string, unknown>
  is_builtin: boolean
  is_active: boolean
  created_at: string
  updated_at: string | null
  /** Access control: who can use this app (τ²-bench) */
  access_type?: AccessType
  /** Roles allowed to access when access_type is 'role_restricted' */
  allowed_roles?: AgentRole[]
  /** State management type */
  state_type?: StateType
}

export interface AppDefinitionCreate {
  app_id: string
  name: string
  description?: string
  category: AppCategory
  icon?: string
  actions: ActionDefinition[]
  state_schema?: StateField[]
  initial_config?: Record<string, unknown>
  /** Access control: who can use this app (τ²-bench) */
  access_type?: AccessType
  /** Roles allowed to access when access_type is 'role_restricted' */
  allowed_roles?: AgentRole[]
  /** State management type */
  state_type?: StateType
}

export interface AppDefinitionUpdate {
  name?: string
  description?: string
  category?: AppCategory
  icon?: string
  actions?: ActionDefinition[]
  state_schema?: StateField[]
  initial_config?: Record<string, unknown>
  /** Access control: who can use this app (τ²-bench) */
  access_type?: AccessType
  /** Roles allowed to access when access_type is 'role_restricted' */
  allowed_roles?: AgentRole[]
  /** State management type */
  state_type?: StateType
}

export interface TestActionRequest {
  action: string
  agent_id: string
  params: Record<string, unknown>
  state: {
    per_agent: Record<string, Record<string, unknown>>
    shared: Record<string, unknown>
  }
}

export interface TestActionResponse {
  success: boolean
  data?: Record<string, unknown>
  error?: string
  state_after: {
    per_agent: Record<string, Record<string, unknown>>
    shared: Record<string, unknown>
  }
  observations: Array<{
    to: string
    message: string
    data?: Record<string, unknown>
  }>
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

  /** Get coordination metrics for a simulation (ADR-020.1) */
  getSimulationCoordinationMetrics: async (simulationId: string) => {
    return request<CoordinationMetrics>(`/simulations/${simulationId}/coordination-metrics`)
  },

  createSimulation: async (data: {
    name: string
    steps: number
    initial_prompt?: string
    model?: string
    agents?: Array<{
      name: string
      background?: string
      role?: AgentRole
      traits?: Record<string, number>
      model?: string
    }>
    apps?: Array<{
      app_id: string
      config?: Record<string, unknown>
    }>
    /** τ²-bench: Optional task ID for evaluation mode */
    task_id?: string
    /** Goal-based termination mode (ADR-020.1) */
    termination_mode?: 'max_steps' | 'goal' | 'hybrid'
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

  // App Definitions
  getAppDefinitions: async (params?: {
    category?: AppCategory
    search?: string
    page?: number
    per_page?: number
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.per_page) searchParams.set('per_page', params.per_page.toString())
    const query = searchParams.toString()
    return request<{ definitions: AppDefinition[]; total: number }>(
      `/app-definitions${query ? `?${query}` : ''}`
    )
  },

  getAppDefinition: async (id: string) => {
    return request<AppDefinition>(`/app-definitions/${id}`)
  },

  createAppDefinition: async (data: AppDefinitionCreate) => {
    return request<AppDefinition>('/app-definitions', { method: 'POST', body: data })
  },

  updateAppDefinition: async (id: string, data: AppDefinitionUpdate) => {
    return request<AppDefinition>(`/app-definitions/${id}`, { method: 'PATCH', body: data })
  },

  deleteAppDefinition: async (id: string) => {
    return request<{ success: boolean }>(`/app-definitions/${id}`, { method: 'DELETE' })
  },

  duplicateAppDefinition: async (id: string, data: { new_app_id: string; new_name: string }) => {
    return request<AppDefinition>(`/app-definitions/${id}/duplicate`, { method: 'POST', body: data })
  },

  testAppDefinition: async (id: string, data: TestActionRequest) => {
    return request<TestActionResponse>(`/app-definitions/${id}/test`, { method: 'POST', body: data })
  },

  // Simulation Apps (runtime state)
  getSimulationApps: async (simulationId: string) => {
    return request<{
      apps: Array<{
        id: string
        simulation_id: string
        app_id: string
        config: Record<string, unknown>
        state: Record<string, unknown>
        created_at: string | null
        updated_at: string | null
      }>
      total: number
    }>(`/simulations/${simulationId}/apps`)
  },

  getSimulationAppState: async (simulationId: string, appId: string) => {
    return request<{
      id: string
      simulation_id: string
      app_id: string
      config: Record<string, unknown>
      state: Record<string, unknown>
      created_at: string | null
      updated_at: string | null
    }>(`/simulations/${simulationId}/apps/${appId}`)
  },

  getSimulationAppActions: async (
    simulationId: string,
    params?: {
      app_id?: string
      agent_id?: string
      limit?: number
    }
  ) => {
    const searchParams = new URLSearchParams()
    if (params?.app_id) searchParams.set('app_id', params.app_id)
    if (params?.agent_id) searchParams.set('agent_id', params.agent_id)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return request<{
      actions: Array<{
        id: string
        app_instance_id: string
        agent_id: string
        step: number
        action_name: string
        params: Record<string, unknown>
        success: boolean
        result: Record<string, unknown> | null
        error: string | null
        executed_at: string | null
      }>
      total: number
    }>(`/simulations/${simulationId}/actions${query ? `?${query}` : ''}`)
  },

  getAvailableApps: async () => {
    return request<{
      apps: Array<{
        app_id: string
        name: string
        description: string
        actions: Array<{
          name: string
          description: string
          parameters: Record<string, unknown>
          returns: Record<string, string>
        }>
      }>
    }>('/apps/available')
  },

  // ==========================================================================
  // Dual-Control Tasks (τ²-bench)
  // ==========================================================================

  getDualControlTasks: async (params?: {
    domain?: string
    difficulty?: string
    tags?: string
    search?: string
    page?: number
    per_page?: number
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.domain) searchParams.set('domain', params.domain)
    if (params?.difficulty) searchParams.set('difficulty', params.difficulty)
    if (params?.tags) searchParams.set('tags', params.tags)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.per_page) searchParams.set('per_page', params.per_page.toString())
    const query = searchParams.toString()
    return request<{ tasks: DualControlTaskDefinition[]; total: number }>(
      `/dual-control-tasks${query ? `?${query}` : ''}`
    )
  },

  getDualControlTask: async (taskId: string) => {
    return request<DualControlTaskDefinition>(`/dual-control-tasks/${taskId}`)
  },

  createDualControlTask: async (data: CreateDualControlTaskRequest) => {
    return request<DualControlTaskDefinition>('/dual-control-tasks', {
      method: 'POST',
      body: data,
    })
  },

  updateDualControlTask: async (taskId: string, data: UpdateDualControlTaskRequest) => {
    return request<DualControlTaskDefinition>(`/dual-control-tasks/${taskId}`, {
      method: 'PATCH',
      body: data,
    })
  },

  deleteDualControlTask: async (taskId: string, hard?: boolean) => {
    const params = hard ? '?hard=true' : ''
    return request<void>(`/dual-control-tasks/${taskId}${params}`, {
      method: 'DELETE',
    })
  },

  getDualControlTaskStats: async () => {
    return request<{
      total_tasks: number
      total_coordination_events: number
      successful_handoffs: number
      handoff_success_rate: number
      total_comparisons: number
    }>('/dual-control-tasks/stats')
  },

  getDualControlDomains: async () => {
    return request<{ domains: string[]; count: number }>('/dual-control-tasks/domains/list')
  },

  // Coordination Events
  getCoordinationEvents: async (taskId: string, params?: {
    trial_id?: string
    limit?: number
    offset?: number
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    const query = searchParams.toString()
    return request<{ events: CoordinationEvent[]; total: number }>(
      `/dual-control-tasks/${taskId}/events${query ? `?${query}` : ''}`
    )
  },

  createCoordinationEvent: async (taskId: string, event: CreateCoordinationEventRequest) => {
    return request<CoordinationEvent>(`/dual-control-tasks/${taskId}/events`, {
      method: 'POST',
      body: event,
    })
  },

  // Coordination Metrics
  getCoordinationMetrics: async (taskId: string, trialId?: string) => {
    const params = trialId ? `?trial_id=${trialId}` : ''
    return request<CoordinationMetrics>(`/dual-control-tasks/${taskId}/metrics${params}`)
  },

  // Solo vs Dual Comparison
  getSoloDualComparison: async (taskId: string) => {
    return request<SoloDualComparisonResult>(`/dual-control-tasks/${taskId}/comparison`)
  },

  runSoloDualComparison: async (taskId: string, numTrials: number) => {
    return request<{
      comparison: SoloDualComparisonResult
      insight: string
    }>(`/dual-control-tasks/${taskId}/compare`, {
      method: 'POST',
      body: { num_trials: numTrials },
    })
  },
}
