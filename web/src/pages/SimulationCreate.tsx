import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ChevronLeft, Users, AlertCircle } from 'lucide-react'
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
  toast,
  confirm,
} from '@/components/ui'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'

interface AgentConfig {
  name: string
  background: string
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
    { ...defaultAgent, name: 'Alice' },
    { ...defaultAgent, name: 'Bob' },
  ])
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [showPersonaPicker, setShowPersonaPicker] = useState(false)

  // Fetch personas for the picker
  const { data: personasData } = useQuery({
    queryKey: ['personas'],
    queryFn: () => api.getPersonas(),
  })
  const personas = personasData?.personas || []

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

  const addPersonaAsAgent = (persona: { name: string; background?: string; traits?: AgentConfig['traits'] }) => {
    setAgents([...agents, {
      name: persona.name,
      background: persona.background || '',
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
        traits: a.traits,
      })),
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
              <Label htmlFor="steps">Number of Steps</Label>
              <Input
                id="steps"
                type="number"
                min="1"
                max="100"
                value={steps}
                onChange={(e) => setSteps(parseInt(e.target.value) || 1)}
              />
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
                  <h4 className="font-medium">Agent {index + 1}</h4>
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

                <div className="grid gap-4 md:grid-cols-2">
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
    </div>
  )
}
