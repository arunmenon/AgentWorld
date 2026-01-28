/**
 * TaskCreate - Page for creating dual-control evaluation tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Multi-step wizard:
 * 1. Basic Info & Role Assignment
 * 2. Handoff Sequence Definition
 * 3. Goal State Conditions
 * 4. Review & Create
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  FileText,
  ArrowRightLeft,
  Target,
  Eye,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import type { AppDefinition } from '@/lib/api'
import {
  DualControlTaskForm,
  HandoffEditor,
  GoalStateEditor,
} from '@/components/tasks'
import type {
  DualControlTask,
  ExpectedHandoff,
  GoalStateCondition,
} from '@/components/tasks'

type WizardStep = 'info' | 'handoffs' | 'goals' | 'review'

const steps: Array<{ id: WizardStep; label: string; icon: React.ReactNode }> = [
  { id: 'info', label: 'Task Info', icon: <FileText className="h-4 w-4" /> },
  { id: 'handoffs', label: 'Handoffs', icon: <ArrowRightLeft className="h-4 w-4" /> },
  { id: 'goals', label: 'Goals', icon: <Target className="h-4 w-4" /> },
  { id: 'review', label: 'Review', icon: <Eye className="h-4 w-4" /> },
]

function StepIndicator({
  currentStep,
  onStepClick,
}: {
  currentStep: WizardStep
  onStepClick: (step: WizardStep) => void
}) {
  const currentIndex = steps.findIndex((s) => s.id === currentStep)

  return (
    <div className="flex items-center gap-2">
      {steps.map((step, index) => {
        const isComplete = index < currentIndex
        const isCurrent = step.id === currentStep
        const isClickable = index <= currentIndex

        return (
          <div key={step.id} className="flex items-center">
            <button
              type="button"
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all',
                isCurrent
                  ? 'bg-primary text-primary-foreground'
                  : isComplete
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 cursor-pointer hover:bg-green-200 dark:hover:bg-green-900/50'
                  : 'bg-background-secondary text-foreground-muted cursor-not-allowed'
              )}
            >
              {isComplete ? (
                <Check className="h-4 w-4" />
              ) : (
                step.icon
              )}
              <span className="text-sm font-medium">{step.label}</span>
            </button>

            {index < steps.length - 1 && (
              <div
                className={cn(
                  'w-8 h-0.5 mx-2',
                  index < currentIndex ? 'bg-green-500' : 'bg-border'
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

function ReviewStep({ task }: { task: Partial<DualControlTask> }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium mb-2">Task Information</h3>
        <div className="p-4 rounded-lg bg-background-secondary/50 border border-border space-y-2">
          <div>
            <span className="text-sm text-foreground-muted">Name:</span>
            <span className="ml-2 font-medium">{task.name}</span>
          </div>
          <div>
            <span className="text-sm text-foreground-muted">Description:</span>
            <p className="mt-1 text-sm">{task.description}</p>
          </div>
          <div className="flex gap-6">
            <div>
              <span className="text-sm text-foreground-muted">Max Steps:</span>
              <span className="ml-2">{task.maxSteps}</span>
            </div>
            <div>
              <span className="text-sm text-foreground-muted">Tags:</span>
              <span className="ml-2">{task.tags?.join(', ') || 'None'}</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-2">Roles & Apps</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-background-secondary/50 border border-border">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎧</span>
              <span className="font-medium">Agent Role</span>
            </div>
            <p className="text-sm text-foreground-muted capitalize">{task.agentRole}</p>
            <div className="mt-2">
              <span className="text-xs text-foreground-muted">Apps:</span>
              <p className="text-sm">{task.agentApps?.join(', ') || 'None'}</p>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-background-secondary/50 border border-border">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">📱</span>
              <span className="font-medium">User Role</span>
            </div>
            <p className="text-sm text-foreground-muted capitalize">{task.userRole}</p>
            <div className="mt-2">
              <span className="text-xs text-foreground-muted">Apps:</span>
              <p className="text-sm">{task.userApps?.join(', ') || 'None'}</p>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-2">Expected Handoffs ({task.expectedHandoffs?.length || 0})</h3>
        {task.expectedHandoffs && task.expectedHandoffs.length > 0 ? (
          <div className="space-y-2">
            {task.expectedHandoffs.map((h, i) => (
              <div
                key={h.id}
                className="p-3 rounded-lg bg-background-secondary/50 border border-border flex items-center gap-3"
              >
                <span className="text-xs font-medium bg-primary/10 text-primary px-2 py-0.5 rounded">
                  #{i + 1}
                </span>
                <span className="text-sm">
                  {h.fromRole === 'service_agent' ? '🎧' : '📱'} →{' '}
                  {h.toRole === 'customer' ? '📱' : '🎧'}
                </span>
                <code className="text-sm px-2 py-0.5 rounded bg-background">
                  {h.expectedAction}
                </code>
                {h.isOptional && (
                  <span className="text-xs text-foreground-muted">(optional)</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-foreground-muted">No handoffs defined</p>
        )}
      </div>

      <div>
        <h3 className="font-medium mb-2">Goal Conditions ({task.goalState?.length || 0})</h3>
        {task.goalState && task.goalState.length > 0 ? (
          <div className="space-y-2">
            {task.goalState.map((g, i) => (
              <div
                key={g.id}
                className="p-3 rounded-lg bg-background-secondary/50 border border-border flex items-center gap-2 font-mono text-sm"
              >
                <span className="text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded">
                  #{i + 1}
                </span>
                <span>{g.appId}.{g.field}</span>
                <span className="px-1.5 py-0.5 rounded bg-background">{g.operator}</span>
                {g.operator !== 'exists' && (
                  <span className="text-green-600">{JSON.stringify(g.value)}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-foreground-muted">No goal conditions defined</p>
        )}
      </div>

      <div>
        <h3 className="font-medium mb-2">Goal Description</h3>
        <p className="p-4 rounded-lg bg-background-secondary/50 border border-border text-sm">
          {task.goalDescription || 'No description provided'}
        </p>
      </div>
    </div>
  )
}

export function TaskCreate() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<WizardStep>('info')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [availableApps, setAvailableApps] = useState<AppDefinition[]>([])

  const [taskData, setTaskData] = useState<Partial<DualControlTask>>({
    name: '',
    description: '',
    agentRole: 'service_agent',
    userRole: 'customer',
    userApps: [],
    agentApps: [],
    initialState: {},
    goalDescription: '',
    goalState: [],
    expectedHandoffs: [],
    maxSteps: 10,
    tags: [],
  })

  // Load available apps
  useEffect(() => {
    api.getAvailableApps()
      .then((response) => setAvailableApps(response.apps as AppDefinition[]))
      .catch(console.error)
  }, [])

  const handleInfoSubmit = (data: DualControlTask) => {
    setTaskData((prev) => ({ ...prev, ...data }))
    setCurrentStep('handoffs')
  }

  const handleHandoffsChange = (handoffs: ExpectedHandoff[]) => {
    setTaskData((prev) => ({ ...prev, expectedHandoffs: handoffs }))
  }

  const handleGoalsChange = (goals: GoalStateCondition[]) => {
    setTaskData((prev) => ({ ...prev, goalState: goals }))
  }

  const handleCreate = async () => {
    setIsSubmitting(true)
    try {
      // Convert frontend task format to API request format
      const request = {
        task_id: taskData.name?.toLowerCase().replace(/\s+/g, '-') || `task-${Date.now()}`,
        name: taskData.name || '',
        description: taskData.description || '',
        domain: taskData.tags?.[0] || 'general',
        difficulty: 'medium',
        simulation_config: {},
        agent_id: 'agent-1',
        agent_role: taskData.agentRole || 'service_agent',
        agent_instruction: `Guide the user to complete: ${taskData.goalDescription}`,
        agent_apps: taskData.agentApps || [],
        agent_initial_state: {},
        agent_goal_state: {},
        user_id: 'user-1',
        user_role: taskData.userRole || 'customer',
        user_instruction: taskData.goalDescription || '',
        user_apps: taskData.userApps || [],
        user_initial_state: taskData.initialState || {},
        user_goal_state: Object.fromEntries(
          (taskData.goalState || []).map((g) => [`${g.appId}.${g.field}`, g.value])
        ),
        required_handoffs: (taskData.expectedHandoffs || []).map((h) => ({
          handoff_id: h.id,
          from_role: h.fromRole,
          to_role: h.toRole,
          expected_action: h.expectedAction,
          description: h.description || '',
        })),
        max_turns: taskData.maxSteps || 10,
        expected_coordination_count: taskData.expectedHandoffs?.length || 0,
        tags: taskData.tags || [],
      }

      await api.createDualControlTask(request)
      navigate('/simulations') // Navigate to simulations for now (tasks list TBD)
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const goBack = () => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep)
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1].id)
    }
  }

  const goNext = () => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep)
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1].id)
    }
  }

  // Prepare apps data for editors
  const appsWithActions = availableApps.map((app) => ({
    id: app.app_id,
    name: app.name,
    icon: app.icon ?? undefined,
    actions: app.actions?.map((a) => a.name) || [],
    stateFields: app.state_schema?.map((s) => ({
      name: s.name,
      type: s.type as string,
      description: s.description,
    })) || [],
  }))

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 rounded-lg hover:bg-background-secondary transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-xl font-semibold">Create Dual-Control Task</h1>
                <p className="text-sm text-foreground-muted">
                  Define a task for evaluating agent-user coordination
                </p>
              </div>
            </div>

            <StepIndicator currentStep={currentStep} onStepClick={setCurrentStep} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {currentStep === 'info' && (
          <DualControlTaskForm
            initialValues={taskData}
            availableApps={availableApps}
            onSubmit={handleInfoSubmit}
            onCancel={() => navigate(-1)}
          />
        )}

        {currentStep === 'handoffs' && (
          <div className="space-y-6">
            <HandoffEditor
              value={taskData.expectedHandoffs || []}
              onChange={handleHandoffsChange}
              availableApps={appsWithActions}
              agentRole={taskData.agentRole}
              userRole={taskData.userRole}
            />

            <div className="flex justify-between pt-4 border-t border-border">
              <button
                type="button"
                onClick={goBack}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={goNext}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Continue to Goals
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {currentStep === 'goals' && (
          <div className="space-y-6">
            <GoalStateEditor
              value={taskData.goalState || []}
              onChange={handleGoalsChange}
              availableApps={appsWithActions}
            />

            <div className="flex justify-between pt-4 border-t border-border">
              <button
                type="button"
                onClick={goBack}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={goNext}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Review Task
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {currentStep === 'review' && (
          <div className="space-y-6">
            <ReviewStep task={taskData} />

            <div className="flex justify-between pt-4 border-t border-border">
              <button
                type="button"
                onClick={goBack}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={handleCreate}
                disabled={isSubmitting}
                className={cn(
                  'flex items-center gap-2 px-6 py-2 rounded-lg bg-green-600 text-white font-medium transition-colors',
                  isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-green-700'
                )}
              >
                <Check className="h-4 w-4" />
                {isSubmitting ? 'Creating...' : 'Create Task'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TaskCreate
