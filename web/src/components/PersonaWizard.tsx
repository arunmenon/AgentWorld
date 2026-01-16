import { useState, useMemo } from 'react'
import { Check, ChevronRight, ChevronLeft, Sparkles, Copy } from 'lucide-react'
import {
  Button,
  Input,
  Label,
  Textarea,
  toast,
} from '@/components/ui'
import { cn } from '@/lib/utils'

// Types
export interface PersonaTraits {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

export interface PersonaFormData {
  name: string
  description: string
  occupation: string
  age: number | null
  location: string
  background: string
  traits: PersonaTraits
  tags: string[]
}

interface PersonaWizardProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: PersonaFormData) => void
  isSubmitting?: boolean
  initialData?: Partial<PersonaFormData>
  mode?: 'create' | 'edit'
}

// Default values
const defaultTraits: PersonaTraits = {
  openness: 0.5,
  conscientiousness: 0.5,
  extraversion: 0.5,
  agreeableness: 0.5,
  neuroticism: 0.3,
}

const defaultFormData: PersonaFormData = {
  name: '',
  description: '',
  occupation: '',
  age: null,
  location: '',
  background: '',
  traits: defaultTraits,
  tags: [],
}

// Presets configuration
const PRESETS: { name: string; traits: PersonaTraits; description: string }[] = [
  {
    name: 'Analytical',
    description: 'Logical, detail-oriented, methodical',
    traits: { openness: 0.6, conscientiousness: 0.9, extraversion: 0.3, agreeableness: 0.5, neuroticism: 0.2 },
  },
  {
    name: 'Creative',
    description: 'Imaginative, innovative, artistic',
    traits: { openness: 0.95, conscientiousness: 0.4, extraversion: 0.6, agreeableness: 0.7, neuroticism: 0.4 },
  },
  {
    name: 'Leader',
    description: 'Decisive, confident, assertive',
    traits: { openness: 0.7, conscientiousness: 0.85, extraversion: 0.9, agreeableness: 0.5, neuroticism: 0.2 },
  },
  {
    name: 'Skeptic',
    description: 'Questioning, critical, cautious',
    traits: { openness: 0.4, conscientiousness: 0.7, extraversion: 0.3, agreeableness: 0.3, neuroticism: 0.5 },
  },
  {
    name: 'Enthusiast',
    description: 'Optimistic, energetic, supportive',
    traits: { openness: 0.8, conscientiousness: 0.5, extraversion: 0.9, agreeableness: 0.9, neuroticism: 0.2 },
  },
]

// Trait Slider Component
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
        <Label className="text-sm font-medium">{label}</Label>
        <span className="text-sm font-mono text-primary">{(value * 100).toFixed(0)}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary"
      />
      <div className="flex justify-between text-xs text-foreground-muted">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  )
}

// Step Indicator Component
function StepIndicator({ currentStep, steps }: { currentStep: number; steps: string[] }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {steps.map((step, index) => {
        const stepNum = index + 1
        const isActive = stepNum === currentStep
        const isCompleted = stepNum < currentStep

        return (
          <div key={step} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                  isActive && 'bg-primary text-primary-foreground',
                  isCompleted && 'bg-success text-success-foreground',
                  !isActive && !isCompleted && 'bg-slate-700 text-foreground-muted'
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : stepNum}
              </div>
              <span
                className={cn(
                  'text-sm hidden sm:block',
                  isActive && 'text-foreground font-medium',
                  !isActive && 'text-foreground-muted'
                )}
              >
                {step}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className={cn(
                'w-8 h-0.5 mx-2',
                isCompleted ? 'bg-success' : 'bg-slate-700'
              )} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// Persona Card Preview
function PersonaCardPreview({ data }: { data: PersonaFormData }) {
  const traitLabels = [
    { key: 'openness', label: 'O', color: 'bg-violet-500' },
    { key: 'conscientiousness', label: 'C', color: 'bg-blue-500' },
    { key: 'extraversion', label: 'E', color: 'bg-orange-500' },
    { key: 'agreeableness', label: 'A', color: 'bg-emerald-500' },
    { key: 'neuroticism', label: 'N', color: 'bg-rose-500' },
  ]

  return (
    <div className="p-4 rounded-lg border border-border bg-background">
      <div className="flex items-start gap-3">
        <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-lg">
          {data.name ? data.name.charAt(0).toUpperCase() : '?'}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold">{data.name || 'Unnamed Persona'}</h4>
          <p className="text-sm text-foreground-secondary">{data.occupation || 'No occupation'}</p>
          {data.age && <p className="text-xs text-foreground-muted">Age {data.age}</p>}
          {data.location && <p className="text-xs text-foreground-muted">{data.location}</p>}
        </div>
      </div>

      {data.description && (
        <p className="mt-3 text-sm text-foreground-secondary">{data.description}</p>
      )}

      <div className="mt-4 flex gap-1">
        {traitLabels.map(({ key, label, color }) => {
          const value = data.traits[key as keyof PersonaTraits]
          return (
            <div key={key} className="flex-1">
              <div className="text-xs text-center text-foreground-muted mb-1">{label}</div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all', color)}
                  style={{ width: `${value * 100}%` }}
                />
              </div>
              <div className="text-xs text-center text-foreground-muted mt-1">
                {(value * 100).toFixed(0)}%
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Generate prompt preview
function generatePromptPreview(data: PersonaFormData): string {
  const { name, occupation, age, location, description, background, traits } = data

  const traitDescriptions: string[] = []

  if (traits.openness >= 0.7) {
    traitDescriptions.push('highly creative and curious, open to new experiences')
  } else if (traits.openness <= 0.3) {
    traitDescriptions.push('practical and conventional, preferring familiar approaches')
  }

  if (traits.conscientiousness >= 0.7) {
    traitDescriptions.push('organized and disciplined, attention to detail')
  } else if (traits.conscientiousness <= 0.3) {
    traitDescriptions.push('flexible and spontaneous, adaptable to change')
  }

  if (traits.extraversion >= 0.7) {
    traitDescriptions.push('outgoing and energetic, enjoys social interaction')
  } else if (traits.extraversion <= 0.3) {
    traitDescriptions.push('reserved and reflective, prefers smaller groups')
  }

  if (traits.agreeableness >= 0.7) {
    traitDescriptions.push('cooperative and trusting, values harmony')
  } else if (traits.agreeableness <= 0.3) {
    traitDescriptions.push('competitive and skeptical, maintains strong opinions')
  }

  if (traits.neuroticism >= 0.7) {
    traitDescriptions.push('emotionally sensitive, may experience stress')
  } else if (traits.neuroticism <= 0.3) {
    traitDescriptions.push('emotionally stable and calm under pressure')
  }

  let prompt = `You are ${name || '[Name]'}`
  if (age) prompt += `, a ${age}-year-old`
  if (occupation) prompt += ` ${occupation}`
  if (location) prompt += ` from ${location}`
  prompt += '.\n\n'

  if (traitDescriptions.length > 0) {
    prompt += 'Your personality:\n'
    traitDescriptions.forEach(desc => {
      prompt += `- ${desc}\n`
    })
    prompt += '\n'
  }

  if (description) {
    prompt += `Background: ${description}\n\n`
  }

  if (background) {
    prompt += `Additional context: ${background}\n`
  }

  return prompt.trim()
}

// Main Wizard Component
export function PersonaWizard({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
  initialData,
  mode = 'create',
}: PersonaWizardProps) {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState<PersonaFormData>(() => ({
    ...defaultFormData,
    ...initialData,
    traits: { ...defaultTraits, ...initialData?.traits },
  }))

  const steps = ['Traits', 'Identity', 'Preview']

  // Reset when modal opens/closes
  const handleClose = () => {
    setStep(1)
    setFormData({ ...defaultFormData, ...initialData, traits: { ...defaultTraits, ...initialData?.traits } })
    onClose()
  }

  const updateTrait = (trait: keyof PersonaTraits, value: number) => {
    setFormData(prev => ({
      ...prev,
      traits: { ...prev.traits, [trait]: value },
    }))
  }

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setFormData(prev => ({
      ...prev,
      traits: { ...preset.traits },
    }))
    toast.success(`Applied "${preset.name}" preset`, preset.description)
  }

  const canProceed = useMemo(() => {
    if (step === 1) return true // Traits step always valid
    if (step === 2) return formData.name.trim().length >= 2
    return true
  }, [step, formData.name])

  const handleNext = () => {
    if (step < 3) setStep(step + 1)
  }

  const handleBack = () => {
    if (step > 1) setStep(step - 1)
  }

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error('Name required', 'Please enter a name for the persona.')
      setStep(2)
      return
    }
    onSubmit(formData)
  }

  const promptPreview = useMemo(() => generatePromptPreview(formData), [formData])
  const tokenEstimate = useMemo(() => Math.ceil(promptPreview.length / 4), [promptPreview])

  const copyPrompt = () => {
    navigator.clipboard.writeText(promptPreview)
    toast.success('Copied', 'Prompt copied to clipboard.')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />

      {/* Modal */}
      <div className="relative z-50 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg border border-border bg-background-secondary shadow-lg animate-in">
        {/* Header */}
        <div className="sticky top-0 bg-background-secondary border-b border-border p-4 z-10">
          <h2 className="text-lg font-semibold text-center">
            {mode === 'edit' ? 'Edit Persona' : 'Create New Persona'}
          </h2>
          <StepIndicator currentStep={step} steps={steps} />
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Step 1: Traits */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide mb-4">
                  Personality Traits (Big Five)
                </h3>
                <div className="grid gap-6 md:grid-cols-2">
                  <TraitSlider
                    label="Openness"
                    value={formData.traits.openness}
                    onChange={(v) => updateTrait('openness', v)}
                    lowLabel="Practical"
                    highLabel="Creative"
                  />
                  <TraitSlider
                    label="Conscientiousness"
                    value={formData.traits.conscientiousness}
                    onChange={(v) => updateTrait('conscientiousness', v)}
                    lowLabel="Flexible"
                    highLabel="Organized"
                  />
                  <TraitSlider
                    label="Extraversion"
                    value={formData.traits.extraversion}
                    onChange={(v) => updateTrait('extraversion', v)}
                    lowLabel="Reserved"
                    highLabel="Outgoing"
                  />
                  <TraitSlider
                    label="Agreeableness"
                    value={formData.traits.agreeableness}
                    onChange={(v) => updateTrait('agreeableness', v)}
                    lowLabel="Competitive"
                    highLabel="Cooperative"
                  />
                  <TraitSlider
                    label="Neuroticism"
                    value={formData.traits.neuroticism}
                    onChange={(v) => updateTrait('neuroticism', v)}
                    lowLabel="Calm"
                    highLabel="Sensitive"
                  />
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide mb-3">
                  Presets
                </h3>
                <div className="flex flex-wrap gap-2">
                  {PRESETS.map((preset) => (
                    <button
                      key={preset.name}
                      type="button"
                      onClick={() => applyPreset(preset)}
                      className="px-3 py-1.5 text-sm rounded-full border border-border hover:border-primary hover:bg-primary/10 transition-colors"
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Identity */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide mb-4">
                Basic Information
              </h3>

              <div className="space-y-2">
                <Label htmlFor="persona-name">Name *</Label>
                <Input
                  id="persona-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Lisa Chen"
                  autoFocus
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="persona-occupation">Occupation</Label>
                  <Input
                    id="persona-occupation"
                    value={formData.occupation}
                    onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                    placeholder="e.g., Software Engineer"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="persona-age">Age</Label>
                  <Input
                    id="persona-age"
                    type="number"
                    min="0"
                    max="120"
                    value={formData.age || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        age: e.target.value ? parseInt(e.target.value) : null,
                      })
                    }
                    placeholder="32"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="persona-location">Location</Label>
                <Input
                  id="persona-location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  placeholder="e.g., San Francisco, CA"
                />
              </div>

              <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide mt-6 mb-4">
                Background & Context
              </h3>

              <div className="space-y-2">
                <Label htmlFor="persona-description">Brief Description</Label>
                <Textarea
                  id="persona-description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Tech-savvy professional who values efficiency..."
                  rows={2}
                />
                <p className="text-xs text-foreground-muted text-right">
                  {formData.description.length}/500
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="persona-background">Additional Background (Optional)</Label>
                <Textarea
                  id="persona-background"
                  value={formData.background}
                  onChange={(e) => setFormData({ ...formData, background: e.target.value })}
                  placeholder="Detailed background, goals, motivations..."
                  rows={3}
                />
              </div>
            </div>
          )}

          {/* Step 3: Preview */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide mb-3">
                    Persona Card Preview
                  </h3>
                  <PersonaCardPreview data={formData} />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wide">
                      Live Prompt Preview
                    </h3>
                    <Button variant="ghost" size="sm" onClick={copyPrompt}>
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-800/50 border border-border font-mono text-xs whitespace-pre-wrap max-h-64 overflow-y-auto">
                    {promptPreview}
                  </div>
                  <p className="text-xs text-foreground-muted mt-2">
                    Estimated tokens: ~{tokenEstimate}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-background-secondary border-t border-border p-4 flex items-center justify-between">
          <div>
            {step > 1 && (
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={handleClose}>
              Cancel
            </Button>
            {step < 3 ? (
              <Button onClick={handleNext} disabled={!canProceed}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button onClick={handleSubmit} loading={isSubmitting}>
                <Sparkles className="h-4 w-4 mr-1" />
                {mode === 'edit' ? 'Save Changes' : 'Save to Library'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
