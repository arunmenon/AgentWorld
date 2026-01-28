import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Save, Sparkles } from 'lucide-react'
import { Button, toast } from '@/components/ui'
import { api, type AppCategory, type ActionDefinition, type StateField } from '@/lib/api'
import { type AppTemplate } from '@/lib/app-templates'
import { WizardSteps, type WizardStep } from './WizardSteps'
import { TemplateStep } from './TemplateStep'
import { InfoStep } from './InfoStep'
import { ActionsStep } from './ActionsStep'
import { TestStep } from './TestStep'

const DRAFT_KEY = 'app-studio-draft'

interface AppWizardProps {
  existingApp?: {
    id: string
    app_id: string
    name: string
    description: string | null
    category: AppCategory
    icon: string | null
    actions: ActionDefinition[]
    state_schema: StateField[]
    initial_config: Record<string, unknown>
    is_builtin: boolean
  }
}

interface WizardState {
  selectedTemplate: string | null
  name: string
  app_id: string
  description: string
  category: AppCategory
  icon: string
  actions: ActionDefinition[]
  state_schema: StateField[]
  initial_config: Record<string, unknown>
}

const steps: WizardStep[] = [
  { id: 'template', label: 'Template' },
  { id: 'info', label: 'Info' },
  { id: 'actions', label: 'Actions' },
  { id: 'test', label: 'Test' },
]

const initialState: WizardState = {
  selectedTemplate: null,
  name: '',
  app_id: '',
  description: '',
  category: 'custom',
  icon: '📦',
  actions: [],
  state_schema: [],
  initial_config: {},
}

export function AppWizard({ existingApp }: AppWizardProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // For edit mode, skip template step and start at step 1 (info)
  const isEditMode = !!existingApp
  const startStep = isEditMode ? 1 : 0

  const [currentStep, setCurrentStep] = useState(startStep)
  const [state, setState] = useState<WizardState>(() => {
    if (existingApp) {
      return {
        selectedTemplate: null,
        name: existingApp.name,
        app_id: existingApp.app_id,
        description: existingApp.description || '',
        category: existingApp.category,
        icon: existingApp.icon || '📦',
        actions: existingApp.actions,
        state_schema: existingApp.state_schema,
        initial_config: existingApp.initial_config,
      }
    }

    // Check for draft
    try {
      const draft = localStorage.getItem(DRAFT_KEY)
      if (draft) {
        return JSON.parse(draft)
      }
    } catch {
      // Ignore
    }
    return initialState
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [showDraftPrompt, setShowDraftPrompt] = useState(false)

  // Check for draft on mount
  useEffect(() => {
    if (!isEditMode) {
      try {
        const draft = localStorage.getItem(DRAFT_KEY)
        if (draft) {
          const parsed = JSON.parse(draft)
          if (parsed.name || parsed.actions.length > 0) {
            setShowDraftPrompt(true)
          }
        }
      } catch {
        // Ignore
      }
    }
  }, [isEditMode])

  // Save draft on state changes
  useEffect(() => {
    if (!isEditMode && (state.name || state.actions.length > 0)) {
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(state))
      } catch {
        // Ignore
      }
    }
  }, [state, isEditMode])

  // Clear draft
  const clearDraft = () => {
    try {
      localStorage.removeItem(DRAFT_KEY)
    } catch {
      // Ignore
    }
  }

  // Create mutation
  const createMutation = useMutation({
    mutationFn: api.createAppDefinition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-definitions'] })
      clearDraft()
      toast.success('App created', 'Your app is ready to use.')
      navigate('/apps')
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to create app'
      toast.error('Error', message)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.updateAppDefinition>[1] }) =>
      api.updateAppDefinition(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-definitions'] })
      toast.success('App updated', 'Changes saved successfully.')
      navigate('/apps')
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Failed to update app'
      toast.error('Error', message)
    },
  })

  // Apply template
  const handleSelectTemplate = (template: AppTemplate) => {
    setState({
      ...state,
      selectedTemplate: template.id,
      category: template.category,
      icon: template.icon,
      actions: template.actions,
      state_schema: template.state_schema,
      initial_config: template.initial_config,
      // Don't override name if user already entered one
      name: state.name || '',
      app_id: state.app_id || '',
      description: state.description || template.description,
    })
  }

  // Update info
  const handleInfoChange = (updates: Partial<WizardState>) => {
    setState({ ...state, ...updates })
  }

  // Update actions
  const handleActionsChange = (actions: ActionDefinition[]) => {
    setState({ ...state, actions })
  }

  // Validation
  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {}

    if (step === 0) {
      // Template - no validation needed, can proceed without selection
      return true
    }

    if (step === 1) {
      if (!state.name.trim()) {
        newErrors.name = 'Name is required'
      } else if (state.name.length < 2) {
        newErrors.name = 'Name must be at least 2 characters'
      }

      if (!state.app_id.trim()) {
        newErrors.app_id = 'App ID is required'
      } else if (!/^[a-z][a-z0-9_]*$/.test(state.app_id)) {
        newErrors.app_id = 'App ID must start with a letter and contain only lowercase letters, numbers, and underscores'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle blur for validation
  const handleBlur = (field: string) => {
    setTouched({ ...touched, [field]: true })
  }

  // Navigation
  const canGoNext = () => {
    if (currentStep === 0) return true // Template step always allows next
    if (currentStep === 1) return !!state.name.trim() && !!state.app_id.trim()
    if (currentStep === 2) return state.actions.length > 0
    return true
  }

  const handleNext = () => {
    if (!validateStep(currentStep)) {
      toast.error('Validation Error', 'Please fix the errors before continuing.')
      return
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > startStep) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleStepClick = (stepIndex: number) => {
    if (stepIndex < currentStep || (stepIndex === currentStep + 1 && canGoNext())) {
      setCurrentStep(stepIndex)
    }
  }

  // Save
  const handleSave = () => {
    if (!validateStep(1)) {
      setCurrentStep(1)
      toast.error('Validation Error', 'Please fix the errors.')
      return
    }

    const data = {
      app_id: state.app_id,
      name: state.name,
      description: state.description || undefined,
      category: state.category,
      icon: state.icon,
      actions: state.actions,
      state_schema: state.state_schema,
      initial_config: state.initial_config,
    }

    if (isEditMode && existingApp) {
      updateMutation.mutate({ id: existingApp.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  // Restore or discard draft
  const handleRestoreDraft = () => {
    setShowDraftPrompt(false)
    // State already has draft loaded
  }

  const handleDiscardDraft = () => {
    setShowDraftPrompt(false)
    clearDraft()
    setState(initialState)
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const isReadOnly = existingApp?.is_builtin

  // Steps to display (skip template for edit mode)
  const displaySteps = isEditMode ? steps.slice(1) : steps
  const displayStepIndex = isEditMode ? currentStep - 1 : currentStep

  return (
    <div className="space-y-8">
      {/* Draft Prompt */}
      {showDraftPrompt && (
        <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="font-medium">Continue where you left off?</span>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={handleDiscardDraft}>
                Start Fresh
              </Button>
              <Button size="sm" onClick={handleRestoreDraft}>
                Restore Draft
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Read-only banner for built-in apps */}
      {isReadOnly && (
        <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
          <p className="text-sm text-warning">
            This is a built-in app and cannot be modified. You can view its configuration but cannot save changes.
          </p>
        </div>
      )}

      {/* Step Indicator */}
      <WizardSteps
        steps={displaySteps}
        currentStep={displayStepIndex}
        onStepClick={(index) => handleStepClick(isEditMode ? index + 1 : index)}
      />

      {/* Step Content */}
      <div className="min-h-[400px]">
        {currentStep === 0 && !isEditMode && (
          <TemplateStep
            selectedTemplate={state.selectedTemplate}
            onSelectTemplate={handleSelectTemplate}
          />
        )}

        {currentStep === 1 && (
          <InfoStep
            data={{
              name: state.name,
              app_id: state.app_id,
              description: state.description,
              category: state.category,
              icon: state.icon,
              state_schema: state.state_schema,
            }}
            onChange={handleInfoChange}
            errors={errors}
            touched={touched}
            onBlur={handleBlur}
          />
        )}

        {currentStep === 2 && (
          <ActionsStep
            actions={state.actions}
            onChange={handleActionsChange}
          />
        )}

        {currentStep === 3 && (
          <TestStep
            actions={state.actions}
            stateSchema={state.state_schema}
            initialConfig={state.initial_config}
            definitionId={existingApp?.id}
          />
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-border">
        <div>
          {currentStep > startStep ? (
            <Button variant="ghost" onClick={handleBack}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => navigate('/apps')}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          )}
        </div>

        <div className="flex gap-3">
          {currentStep < steps.length - 1 ? (
            <Button onClick={handleNext} disabled={!canGoNext()}>
              Next
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleSave}
              disabled={isPending || isReadOnly}
              loading={isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {isEditMode ? 'Save Changes' : 'Save App'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
