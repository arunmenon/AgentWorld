import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Trash2,
  ChevronLeft,
  Users,
  AlertCircle,
  Sparkles,
  Building2,
  Wine,
  PenTool,
  Brain,
  Rocket,
  BookOpen,
  Target,
  X,
  ClipboardList,
  Loader2,
  Wand2,
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Textarea,
  Label,
  Badge,
  toast,
  confirm,
} from '@/components/ui'
import { cn } from '@/lib/utils'
import { api, type AgentRole, type DualControlTaskDefinition } from '@/lib/api'
import { templates, type SimulationTemplate } from '@/lib/templates'
import { AppsSection, type SimulationAppConfig } from '@/components/simulation/apps'
import { RoleSelector, RoleBadge } from '@/components/simulation/roles'

const iconMap: Record<string, React.ElementType> = {
  'building-2': Building2,
  'wine': Wine,
  'pen-tool': PenTool,
  'brain': Brain,
  'rocket': Rocket,
  'book-open': BookOpen,
}

interface AgentConfig {
  name: string
  background: string
  /** Agent role for dual-control simulations (τ²-bench) */
  role: AgentRole
  traits: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }
}

const defaultAgent: AgentConfig = {
  name: '',
  background: '',
  role: 'peer',
  traits: {
    openness: 0.5,
    conscientiousness: 0.5,
    extraversion: 0.5,
    agreeableness: 0.5,
    neuroticism: 0.3,
  },
}

function TraitSlider({
  label,
  value,
  onChange,
  lowLabel,
  highLabel,
}: {
  label: string
  value: number
  onChange: (value: number) => void
  lowLabel: string
  highLabel: string
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm">{label}</Label>
        <span className="text-sm text-foreground-muted">{(value * 100).toFixed(0)}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
      />
      <div className="flex justify-between text-xs text-foreground-muted">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  )
}

interface ValidationErrors {
  name?: string
  initialPrompt?: string
  agents?: string
}

export default function SimulationCreate() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState('')
  const [steps, setSteps] = useState(10)
  const [initialPrompt, setInitialPrompt] = useState('')
  const [agents, setAgents] = useState<AgentConfig[]>([
    { ...defaultAgent, name: 'Alice', role: 'peer' },
    { ...defaultAgent, name: 'Bob', role: 'peer' },
  ])
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [showPersonaPicker, setShowPersonaPicker] = useState(false)
  const [apps, setApps] = useState<SimulationAppConfig[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [showTemplates, setShowTemplates] = useState(true)
  const [selectedTask, setSelectedTask] = useState<DualControlTaskDefinition | null>(null)
  const [showTaskPicker, setShowTaskPicker] = useState(false)
  const [terminationMode, setTerminationMode] = useState<'max_steps' | 'goal' | 'hybrid'>('max_steps')

  // AI Generation state
  const [showAiGenerator, setShowAiGenerator] = useState(false)
  const [aiDescription, setAiDescription] = useState('')
  const [aiNumAgents, setAiNumAgents] = useState<number | undefined>(undefined)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)

  // Apply a template to the form
  const applyTemplate = (template: SimulationTemplate) => {
    setName(template.name)
    setSteps(template.steps)
    setInitialPrompt(template.initialPrompt)
    setAgents(template.agents.map(a => ({
      name: a.name,
      background: a.background,
      role: (a as { role?: AgentRole }).role || 'peer',
      traits: a.traits,
    })))
    setSelectedTemplate(template.id)
    setShowTemplates(false)
    setErrors({})
    setTouched({})
    toast.success('Template applied', `"${template.name}" configuration loaded.`)
  }

  // Clear template and reset to blank
  const clearTemplate = () => {
    setName('')
    setSteps(10)
    setInitialPrompt('')
    setAgents([
      { ...defaultAgent, name: 'Alice', role: 'peer' },
      { ...defaultAgent, name: 'Bob', role: 'peer' },
    ])
    setApps([])
    setSelectedTemplate(null)
    setShowTemplates(true)
    setErrors({})
    setTouched({})
  }

  // Apply a dual-control task for evaluation
  const applyTask = (task: DualControlTaskDefinition) => {
    setName(`${task.name} - Trial`)
    setSteps(task.max_turns)
    // Priority for initial prompt:
    // 1. Task's simulation_config.scenario_prompt (if explicitly defined)
    // 2. Fallback to agent_instruction (describes what the scenario is about)
    const scenarioPrompt = (task.simulation_config as Record<string, unknown>)?.scenario_prompt as string | undefined
    setInitialPrompt(scenarioPrompt || task.agent_instruction)

    // Set up agents based on task roles
    const taskAgents: AgentConfig[] = [
      {
        ...defaultAgent,
        name: 'Service Agent',
        background: task.agent_instruction,
        role: task.agent_role as AgentRole,
      },
      {
        ...defaultAgent,
        name: 'Customer',
        background: task.user_instruction,
        role: task.user_role as AgentRole,
      },
    ]
    setAgents(taskAgents)

    // Note: Apps should be added manually through the Apps section
    // The task defines which apps are needed: agent_apps and user_apps
    // Clearing apps to let user add them via the picker
    setApps([])

    setSelectedTask(task)
    setSelectedTemplate(null)
    setShowTemplates(false)
    setShowTaskPicker(false)
    // Default to goal-based termination when a task is selected
    setTerminationMode('goal')
    setErrors({})
    setTouched({})
    toast.success('Task applied', `"${task.name}" configuration loaded for evaluation.`)
  }

  // Clear task selection
  const clearTask = () => {
    setSelectedTask(null)
    setTerminationMode('max_steps')
  }

  // AI generation handler
  const handleGenerateSimulation = async () => {
    if (!aiDescription.trim() || aiDescription.length < 10) {
      setGenerateError('Please provide a description of at least 10 characters')
      return
    }

    setIsGenerating(true)
    setGenerateError(null)

    try {
      const response = await api.generateSimulation({
        description: aiDescription,
        num_agents: aiNumAgents,
      })

      if (response.success && response.config) {
        const config = response.config

        // Apply generated config to form
        setName(config.name || 'Generated Simulation')
        setSteps(config.steps || 10)
        setInitialPrompt(config.initial_prompt || '')

        // Convert agents
        const generatedAgents: AgentConfig[] = (config.agents || []).map((a) => ({
          name: a.name || 'Agent',
          background: a.background || '',
          role: a.role || 'peer',
          traits: a.traits || defaultAgent.traits,
        }))

        if (generatedAgents.length >= 2) {
          setAgents(generatedAgents)
        }

        // Clear other selections
        setSelectedTemplate(null)
        setSelectedTask(null)
        setShowAiGenerator(false)
        setShowTemplates(false)
        setErrors({})
        setTouched({})

        toast.success('Simulation generated', 'Review and modify the configuration as needed.')
      } else {
        setGenerateError(response.error || 'Failed to generate simulation. Please try again.')
      }
    } catch (error) {
      console.error('Generation failed:', error)
      setGenerateError('Failed to generate simulation. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  // Fetch personas for the picker
  const { data: personasData } = useQuery({
    queryKey: ['personas'],
    queryFn: () => api.getPersonas(),
  })
  const personas = personasData?.personas || []

  // Fetch dual-control tasks for evaluation mode
  const { data: tasksData } = useQuery({
    queryKey: ['dual-control-tasks'],
    queryFn: () => api.getDualControlTasks({ per_page: 50 }),
  })
  const availableTasks = tasksData?.tasks || []

  const createMutation = useMutation({
    mutationFn: api.createSimulation,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['simulations'] })
      toast.success('Simulation created', 'Your simulation is now running.')
      navigate(`/simulations/${data.id}`)
    },
    onError: () => {
      toast.error('Failed to create simulation', 'Please check your inputs and try again.')
    },
  })

  // Validation
  const validate = (): boolean => {
    const newErrors: ValidationErrors = {}

    if (!name.trim()) {
      newErrors.name = 'Simulation name is required'
    } else if (name.length < 3) {
      newErrors.name = 'Name must be at least 3 characters'
    }

    if (!initialPrompt.trim()) {
      newErrors.initialPrompt = 'Initial prompt is required'
    }

    const emptyAgents = agents.filter(a => !a.name.trim())
    if (emptyAgents.length > 0) {
      newErrors.agents = 'All agents must have names'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const addAgent = () => {
    setAgents([...agents, { ...defaultAgent, name: `Agent ${agents.length + 1}` }])
  }

  const addPersonaAsAgent = (persona: { name: string; background?: string; role?: AgentRole; traits?: AgentConfig['traits'] }) => {
    setAgents([...agents, {
      name: persona.name,
      background: persona.background || '',
      role: persona.role || 'peer',
      traits: persona.traits || defaultAgent.traits,
    }])
    setShowPersonaPicker(false)
    toast.success('Persona added', `${persona.name} has been added as an agent.`)
  }

  const removeAgent = async (index: number) => {
    if (agents.length <= 2) {
      toast.warning('Cannot remove agent', 'Simulations require at least 2 agents.')
      return
    }

    const confirmed = await confirm({
      type: 'warning',
      title: `Remove ${agents[index].name}?`,
      description: 'This agent will be removed from the simulation.',
      confirmLabel: 'Remove',
    })

    if (confirmed) {
      setAgents(agents.filter((_, i) => i !== index))
    }
  }

  const updateAgent = (index: number, updates: Partial<AgentConfig>) => {
    setAgents(
      agents.map((agent, i) => (i === index ? { ...agent, ...updates } : agent))
    )
  }

  const updateAgentTrait = (
    index: number,
    trait: keyof AgentConfig['traits'],
    value: number
  ) => {
    setAgents(
      agents.map((agent, i) =>
        i === index
          ? { ...agent, traits: { ...agent.traits, [trait]: value } }
          : agent
      )
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTouched({ name: true, initialPrompt: true, agents: true })

    if (!validate()) {
      toast.error('Validation failed', 'Please fix the errors before submitting.')
      return
    }

    createMutation.mutate({
      name,
      steps,
      initial_prompt: initialPrompt,
      agents: agents.map((a) => ({
        name: a.name,
        background: a.background,
        role: a.role,
        traits: a.traits,
      })),
      apps: apps.length > 0 ? apps.map((a) => ({
        app_id: a.app_id,
        config: a.config,
      })) : undefined,
      // Include task_id for evaluation mode (τ²-bench)
      task_id: selectedTask?.task_id,
      // Include termination mode
      termination_mode: terminationMode,
    })
  }

  const handleBlur = (field: string) => {
    setTouched({ ...touched, [field]: true })
    validate()
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Button
        variant="ghost"
        className="mb-4"
        onClick={() => navigate('/simulations')}
      >
        <ChevronLeft className="h-4 w-4 mr-2" />
        Back to Simulations
      </Button>

      {/* Template Picker */}
      {showTemplates && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle>Start from a Template</CardTitle>
            </div>
            <CardDescription>
              Choose a pre-built scenario or start from scratch
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => {
                const Icon = iconMap[template.icon] || Building2
                return (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => applyTemplate(template)}
                    className={cn(
                      'p-4 rounded-lg border border-border text-left transition-all',
                      'hover:border-primary/50 hover:bg-primary/5',
                      'focus:outline-none focus:ring-2 focus:ring-primary/50'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-sm">{template.name}</h4>
                          <Badge variant="outline" className="text-xs">
                            {template.agents.length} agents
                          </Badge>
                        </div>
                        <p className="text-xs text-foreground-secondary line-clamp-2">
                          {template.description}
                        </p>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
            <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
              <button
                type="button"
                onClick={() => setShowTemplates(false)}
                className="text-sm text-foreground-secondary hover:text-foreground transition-colors"
              >
                Or start from scratch
              </button>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowAiGenerator(true)
                    setShowTemplates(false)
                  }}
                >
                  <Wand2 className="h-4 w-4 mr-2" />
                  Describe with AI
                </Button>
                {availableTasks.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowTaskPicker(true)}
                  >
                    <Target className="h-4 w-4 mr-2" />
                    Run Evaluation Task
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Generation Card */}
      {showAiGenerator && (
        <Card className="mb-6 border-primary/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-primary" />
                <CardTitle>Describe Your Simulation</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowAiGenerator(false)
                  setShowTemplates(true)
                }}
              >
                <X className="h-4 w-4 mr-1" />
                Cancel
              </Button>
            </div>
            <CardDescription>
              Describe the simulation in plain English and AI will generate the configuration.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="ai-description">Description *</Label>
              <Textarea
                id="ai-description"
                value={aiDescription}
                onChange={(e) => setAiDescription(e.target.value)}
                placeholder="Example: A panel discussion between three experts debating the future of renewable energy. Include a moderator who is organized and neutral, and two experts with opposing viewpoints - one optimistic and one skeptical."
                rows={4}
                className="mt-1.5"
              />
              <p className="text-xs text-foreground-muted mt-1">
                Be specific about the number of agents, their roles, and what they should discuss.
              </p>
            </div>

            <div>
              <Label htmlFor="ai-num-agents">Number of Agents (optional)</Label>
              <Input
                id="ai-num-agents"
                type="number"
                min={2}
                max={10}
                value={aiNumAgents || ''}
                onChange={(e) => setAiNumAgents(e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="Auto-detect"
                className="mt-1.5 w-32"
              />
            </div>

            {generateError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-sm">
                {generateError}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleGenerateSimulation}
                disabled={isGenerating || !aiDescription.trim()}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Simulation
                  </>
                )}
              </Button>
            </div>

            {/* Tips */}
            <div className="pt-3 border-t border-border">
              <p className="text-sm font-medium mb-2">Tips for better results:</p>
              <ul className="text-xs text-foreground-muted space-y-1">
                <li>• Describe distinct personalities (creative, analytical, skeptical, etc.)</li>
                <li>• Mention the context or topic of discussion</li>
                <li>• Specify relationships between agents if relevant</li>
                <li>• Include desired interaction style (formal, casual, debate-style)</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Template Banner */}
      {selectedTemplate && !showTemplates && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-primary/10 border border-primary/20 mb-6">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm">
              Using template: <strong>{templates.find(t => t.id === selectedTemplate)?.name}</strong>
            </span>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => setShowTemplates(true)}>
              Change Template
            </Button>
            <Button variant="ghost" size="sm" onClick={clearTemplate}>
              Start Fresh
            </Button>
          </div>
        </div>
      )}

      {/* Show templates button when hidden */}
      {!showTemplates && !selectedTemplate && !selectedTask && !showAiGenerator && (
        <div className="flex gap-2 mb-6">
          <Button
            variant="outline"
            onClick={() => setShowTemplates(true)}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Browse Templates
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowAiGenerator(true)}
          >
            <Wand2 className="h-4 w-4 mr-2" />
            Describe with AI
          </Button>
          {availableTasks.length > 0 && (
            <Button
              variant="outline"
              onClick={() => setShowTaskPicker(true)}
            >
              <Target className="h-4 w-4 mr-2" />
              Run Evaluation Task
            </Button>
          )}
        </div>
      )}

      {/* Selected Task Banner */}
      {selectedTask && (
        <Card className="mb-6 border-green-500/30 bg-green-500/5">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <Target className="h-5 w-5 text-green-500" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">{selectedTask.name}</span>
                    <Badge variant="outline" className="text-xs bg-green-500/10 text-green-600 border-green-500/30">
                      τ²-bench Evaluation
                    </Badge>
                  </div>
                  <p className="text-sm text-foreground-muted mb-2">
                    {selectedTask.domain} • {selectedTask.difficulty} • {selectedTask.required_handoffs.length} handoffs
                  </p>
                  <div className="text-xs text-foreground-muted space-y-1">
                    <p>
                      <strong>Recommended Apps:</strong>{' '}
                      {[...selectedTask.agent_apps, ...selectedTask.user_apps]
                        .filter((v, i, a) => a.indexOf(v) === i)
                        .join(', ') || 'None specified'}
                    </p>
                    <p>
                      <strong>Roles:</strong> 🎧 {selectedTask.agent_role} guides 📱 {selectedTask.user_role}
                    </p>
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={clearTask}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle>Create Simulation</CardTitle>
            <CardDescription>
              Configure your multi-agent simulation settings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Simulation Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onBlur={() => handleBlur('name')}
                placeholder="My Simulation"
                className={cn(touched.name && errors.name && 'border-error focus:ring-error')}
              />
              {touched.name && errors.name && (
                <p className="text-sm text-error flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.name}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="steps">
                {terminationMode === 'max_steps' ? 'Number of Steps' : 'Max Steps'}
              </Label>
              <Input
                id="steps"
                type="number"
                min="1"
                max="100"
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value) || 1)}
              />
              {terminationMode !== 'max_steps' && (
                <p className="text-xs text-foreground-muted">
                  Simulation may stop earlier if goal is achieved
                </p>
              )}
            </div>

            {/* Termination Mode */}
            <div className="space-y-3">
              <Label>Termination Mode</Label>
              <div className="space-y-2">
                <label className="flex items-start gap-3 p-3 rounded-lg border border-border cursor-pointer hover:bg-background-secondary transition-colors">
                  <input
                    type="radio"
                    name="termination"
                    value="max_steps"
                    checked={terminationMode === 'max_steps'}
                    onChange={() => setTerminationMode('max_steps')}
                    className="mt-0.5 accent-primary"
                  />
                  <div>
                    <span className="font-medium text-sm">Run for max steps</span>
                    <p className="text-xs text-foreground-muted">
                      Simulation runs for exactly {steps} steps
                    </p>
                  </div>
                </label>
                <label className={cn(
                  'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                  !selectedTask
                    ? 'border-border/50 opacity-60 cursor-not-allowed'
                    : 'border-border hover:bg-background-secondary'
                )}>
                  <input
                    type="radio"
                    name="termination"
                    value="goal"
                    checked={terminationMode === 'goal'}
                    onChange={() => setTerminationMode('goal')}
                    disabled={!selectedTask}
                    className="mt-0.5 accent-primary"
                  />
                  <div>
                    <span className="font-medium text-sm">Stop when goal achieved</span>
                    <p className="text-xs text-foreground-muted">
                      Simulation stops early if task goal is met
                    </p>
                    {!selectedTask && (
                      <p className="text-xs text-warning mt-1">
                        Select an evaluation task to enable goal-based termination
                      </p>
                    )}
                  </div>
                </label>
                <label className={cn(
                  'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                  !selectedTask
                    ? 'border-border/50 opacity-60 cursor-not-allowed'
                    : 'border-border hover:bg-background-secondary'
                )}>
                  <input
                    type="radio"
                    name="termination"
                    value="hybrid"
                    checked={terminationMode === 'hybrid'}
                    onChange={() => setTerminationMode('hybrid')}
                    disabled={!selectedTask}
                    className="mt-0.5 accent-primary"
                  />
                  <div>
                    <span className="font-medium text-sm">Hybrid</span>
                    <p className="text-xs text-foreground-muted">
                      Stops at goal OR max steps, whichever comes first
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="prompt">Initial Prompt *</Label>
              <Textarea
                id="prompt"
                value={initialPrompt}
                onChange={(e) => setInitialPrompt(e.target.value)}
                onBlur={() => handleBlur('initialPrompt')}
                placeholder="What should the agents discuss?"
                rows={3}
                className={cn(touched.initialPrompt && errors.initialPrompt && 'border-error focus:ring-error')}
              />
              {touched.initialPrompt && errors.initialPrompt && (
                <p className="text-sm text-error flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.initialPrompt}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Agents */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Agents ({agents.length})</CardTitle>
              <CardDescription>
                Configure the agents that will participate in the simulation.
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {personas.length > 0 && (
                <Button type="button" variant="outline" onClick={() => setShowPersonaPicker(true)}>
                  <Users className="h-4 w-4 mr-2" />
                  From Library
                </Button>
              )}
              <Button type="button" variant="outline" onClick={addAgent}>
                <Plus className="h-4 w-4 mr-2" />
                Add Agent
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {errors.agents && touched.agents && (
              <p className="text-sm text-error flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {errors.agents}
              </p>
            )}
            {agents.map((agent, index) => (
              <div
                key={index}
                className="p-4 rounded-lg border border-border space-y-4 group relative"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <h4 className="font-medium">Agent {index + 1}</h4>
                    <RoleBadge role={agent.role} size="sm" />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeAgent(index)}
                    className={cn(
                      "transition-opacity",
                      agents.length <= 2 ? "opacity-30 cursor-not-allowed" : "opacity-60 hover:opacity-100"
                    )}
                    title={agents.length <= 2 ? "Minimum 2 agents required" : "Remove agent"}
                  >
                    <Trash2 className="h-4 w-4 text-error" />
                  </Button>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={agent.name}
                      onChange={(e) =>
                        updateAgent(index, { name: e.target.value })
                      }
                      placeholder="Agent name"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <RoleSelector
                      value={agent.role}
                      onChange={(role) => updateAgent(index, { role })}
                      showHelp={index === 0}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Background</Label>
                    <Input
                      value={agent.background}
                      onChange={(e) =>
                        updateAgent(index, { background: e.target.value })
                      }
                      placeholder="Brief background"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <h5 className="text-sm font-medium text-foreground-secondary">
                    Personality Traits (Big Five)
                  </h5>
                  <div className="grid gap-4 md:grid-cols-2">
                    <TraitSlider
                      label="Openness"
                      value={agent.traits.openness}
                      onChange={(v) => updateAgentTrait(index, 'openness', v)}
                      lowLabel="Practical"
                      highLabel="Creative"
                    />
                    <TraitSlider
                      label="Conscientiousness"
                      value={agent.traits.conscientiousness}
                      onChange={(v) =>
                        updateAgentTrait(index, 'conscientiousness', v)
                      }
                      lowLabel="Flexible"
                      highLabel="Organized"
                    />
                    <TraitSlider
                      label="Extraversion"
                      value={agent.traits.extraversion}
                      onChange={(v) => updateAgentTrait(index, 'extraversion', v)}
                      lowLabel="Reserved"
                      highLabel="Outgoing"
                    />
                    <TraitSlider
                      label="Agreeableness"
                      value={agent.traits.agreeableness}
                      onChange={(v) =>
                        updateAgentTrait(index, 'agreeableness', v)
                      }
                      lowLabel="Challenging"
                      highLabel="Cooperative"
                    />
                    <TraitSlider
                      label="Neuroticism"
                      value={agent.traits.neuroticism}
                      onChange={(v) => updateAgentTrait(index, 'neuroticism', v)}
                      lowLabel="Calm"
                      highLabel="Sensitive"
                    />
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Apps Section */}
        <AppsSection
          apps={apps}
          onChange={setApps}
          agentRoles={agents.map((a) => a.role)}
        />

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate('/simulations')}
          >
            Cancel
          </Button>
          <Button type="submit" loading={createMutation.isPending}>
            Create Simulation
          </Button>
        </div>

      </form>

      {/* Persona Picker Modal */}
      {showPersonaPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowPersonaPicker(false)}
          />
          <div className="relative z-50 w-full max-w-lg rounded-lg border border-border bg-background-secondary p-6 shadow-lg animate-in">
            <h3 className="text-lg font-semibold mb-4">Add from Persona Library</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {personas.map((persona) => (
                <button
                  key={persona.id}
                  type="button"
                  onClick={() => addPersonaAsAgent({
                    name: persona.name,
                    background: persona.background || undefined,
                    traits: persona.traits as AgentConfig['traits'],
                  })}
                  className="w-full p-3 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors text-left flex items-center gap-3"
                >
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 text-primary font-semibold">
                    {persona.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{persona.name}</p>
                    <p className="text-sm text-foreground-secondary truncate">
                      {persona.occupation || 'No occupation'}
                    </p>
                  </div>
                </button>
              ))}
              {personas.length === 0 && (
                <p className="text-center text-foreground-muted py-4">
                  No personas in library
                </p>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="ghost" onClick={() => setShowPersonaPicker(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Task Picker Modal */}
      {showTaskPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowTaskPicker(false)}
          />
          <div className="relative z-50 w-full max-w-2xl rounded-lg border border-border bg-background-secondary p-6 shadow-lg animate-in">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Target className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Select Evaluation Task</h3>
                <p className="text-sm text-foreground-muted">
                  Run a τ²-bench dual-control evaluation scenario
                </p>
              </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {availableTasks.map((task) => (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => applyTask(task)}
                  className="w-full p-4 rounded-lg border border-border hover:border-green-500/50 hover:bg-green-500/5 transition-colors text-left"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium">{task.name}</h4>
                      <p className="text-sm text-foreground-muted mt-0.5 line-clamp-2">
                        {task.description}
                      </p>
                    </div>
                    <Badge variant="outline" className="ml-2 flex-shrink-0">
                      {task.difficulty}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-foreground-muted mt-2">
                    <span className="flex items-center gap-1">
                      <ClipboardList className="h-3 w-3" />
                      {task.domain}
                    </span>
                    <span>
                      🎧 {task.agent_role} → 📱 {task.user_role}
                    </span>
                    <span>
                      {task.required_handoffs.length} handoffs
                    </span>
                    <span>
                      Max {task.max_turns} turns
                    </span>
                  </div>
                  {task.tags.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {task.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </button>
              ))}
              {availableTasks.length === 0 && (
                <div className="text-center py-8">
                  <Target className="h-12 w-12 text-foreground-muted mx-auto mb-3" />
                  <p className="text-foreground-muted">No evaluation tasks available</p>
                  <p className="text-sm text-foreground-muted mt-1">
                    Create a task at <code>/tasks/new</code> first
                  </p>
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-border flex justify-end">
              <Button variant="ghost" onClick={() => setShowTaskPicker(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
