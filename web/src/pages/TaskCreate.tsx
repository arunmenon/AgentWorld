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
  Database,
  Zap,
  RefreshCw,
  MessageSquare,
  Sparkles,
  PenTool,
  Loader2,
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
} from '@/components/tasks'
import type { GoalCondition, GoalType, GoalOperator } from '@/lib/goals'
import { getGoalTypeLabel } from '@/lib/goals'

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

/** Helper to get goal category for display */
function getGoalCategory(goalType: GoalType): 'state' | 'action' | 'coordination' | 'output' {
  if (goalType.startsWith('state_')) return 'state'
  if (goalType.startsWith('action_')) return 'action'
  if (goalType === 'handoff_completed' || goalType === 'all_handoffs_done') return 'coordination'
  if (goalType === 'output_contains') return 'output'
  return 'state'
}

/** Get category display info */
function getCategoryDisplay(category: 'state' | 'action' | 'coordination' | 'output') {
  switch (category) {
    case 'state':
      return { icon: <Database className="h-3 w-3" />, bgClass: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' }
    case 'action':
      return { icon: <Zap className="h-3 w-3" />, bgClass: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' }
    case 'coordination':
      return { icon: <RefreshCw className="h-3 w-3" />, bgClass: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' }
    case 'output':
      return { icon: <MessageSquare className="h-3 w-3" />, bgClass: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' }
  }
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
            {task.goalState.map((g, i) => {
              const goalCondition = g as GoalCondition
              const category = getGoalCategory(goalCondition.goalType)
              const categoryDisplay = getCategoryDisplay(category)

              return (
                <div
                  key={goalCondition.id}
                  className="p-3 rounded-lg bg-background-secondary/50 border border-border flex items-center gap-2 text-sm"
                >
                  <span className="text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded">
                    #{i + 1}
                  </span>

                  {/* Category badge */}
                  <span className={cn('flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium', categoryDisplay.bgClass)}>
                    {categoryDisplay.icon}
                    {getGoalTypeLabel(goalCondition.goalType)}
                  </span>

                  {/* Condition details based on type */}
                  <span className="font-mono text-foreground-muted">
                    {category === 'state' && (
                      <>
                        {goalCondition.appId}.{goalCondition.fieldPath}
                        <span className="mx-1 px-1 py-0.5 rounded bg-background">{goalCondition.operator}</span>
                        {goalCondition.operator !== 'exists' && goalCondition.operator !== 'not_exists' && (
                          <span className="text-green-600 dark:text-green-400">{JSON.stringify(goalCondition.expectedValue)}</span>
                        )}
                      </>
                    )}
                    {category === 'action' && (
                      <>
                        {goalCondition.appId} → <span className="text-amber-600 dark:text-amber-400">{goalCondition.expectedValue as string}</span>
                      </>
                    )}
                    {category === 'coordination' && (
                      goalCondition.goalType === 'all_handoffs_done' ? (
                        <span className="text-purple-600 dark:text-purple-400">All handoffs</span>
                      ) : (
                        <>
                          Handoff: <span className="text-purple-600 dark:text-purple-400">{goalCondition.handoffId}</span>
                        </>
                      )
                    )}
                    {category === 'output' && (
                      <>
                        Agent says: "<span className="text-green-600 dark:text-green-400">
                          {(goalCondition.requiredPhrase || '').substring(0, 40)}{(goalCondition.requiredPhrase?.length || 0) > 40 ? '...' : ''}
                        </span>"
                      </>
                    )}
                  </span>
                </div>
              )
            })}
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

  // AI Generation state
  const [aiMode, setAiMode] = useState(true) // Start in AI mode
  const [aiDescription, setAiDescription] = useState('')
  const [aiDomainHint, setAiDomainHint] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)

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

  // AI generation handler
  const handleGenerate = async () => {
    if (!aiDescription.trim() || aiDescription.length < 10) {
      setGenerateError('Please provide a description of at least 10 characters')
      return
    }

    setIsGenerating(true)
    setGenerateError(null)

    try {
      // Prepare available apps with their actions for AI
      const appsForAI = availableApps.map((app) => ({
        app_id: app.app_id,
        name: app.name,
        actions: (app.actions || []).map((a) => ({
          name: a.name,
          description: a.description || '',
        })),
      }))

      const response = await api.generateTask({
        description: aiDescription,
        domain_hint: aiDomainHint || undefined,
        available_apps: appsForAI.length > 0 ? appsForAI : undefined,
      })

      if (response.success && response.task) {
        const generated = response.task as Record<string, unknown>

        // Convert generated task to frontend format
        const handoffs = (generated.required_handoffs as Array<Record<string, unknown>> || []).map((h, i) => {
          const template = h.instruction_template as Record<string, unknown> | undefined
          return {
            id: (h.handoff_id as string) || `handoff_${i + 1}`,
            order: i + 1,
            fromRole: (h.from_role as 'service_agent' | 'customer') || 'service_agent',
            toRole: (h.to_role as 'service_agent' | 'customer') || 'customer',
            expectedAction: (h.expected_action as string) || '',
            appId: (h.app_id as string) || undefined, // Include app_id from AI
            description: (h.description as string) || '',
            isOptional: false,
            instructionTemplate: template ? {
              templateId: (template.template_id as string) || `template_${i + 1}`,
              keywords: (template.keywords as string[]) || [],
              targetKeywords: (template.target_keywords as string[]) || [],
            } : undefined,
          }
        })

        const goalConditions: GoalCondition[] = (generated.goal_conditions as Array<Record<string, unknown>> || []).map((g, i) => ({
          id: (g.id as string) || `goal_${i + 1}`,
          goalType: (g.goal_type as GoalType) || 'state_equals',
          description: (g.description as string) || '',
          appId: g.app_id as string | undefined,
          fieldPath: g.field_path as string | undefined,
          operator: (g.operator as GoalOperator) || 'equals',
          expectedValue: g.expected_value,
          handoffId: g.handoff_id as string | undefined,
          requiredPhrase: g.required_phrase as string | undefined,
        }))

        setTaskData({
          name: (generated.name as string) || '',
          description: (generated.description as string) || '',
          agentRole: (generated.agent_role as 'service_agent' | 'customer') || 'service_agent',
          userRole: (generated.user_role as 'service_agent' | 'customer') || 'customer',
          userApps: (generated.user_apps as string[]) || [],
          agentApps: (generated.agent_apps as string[]) || [],
          initialState: (generated.initial_state as Record<string, Record<string, unknown>>) || {},
          goalDescription: (generated.user_instruction as string) || (generated.scenario_prompt as string) || '',
          goalState: goalConditions,
          expectedHandoffs: handoffs,
          maxSteps: (generated.max_turns as number) || 10,
          tags: (generated.tags as string[]) || [(generated.domain as string) || 'general'],
        })

        // Exit AI mode and go to info step to review
        setAiMode(false)
        setCurrentStep('info')
      } else {
        setGenerateError(response.error || 'Failed to generate task. Please try again.')
      }
    } catch (error) {
      console.error('Generation failed:', error)
      setGenerateError('Failed to generate task. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleInfoSubmit = (data: DualControlTask) => {
    setTaskData((prev) => ({ ...prev, ...data }))
    setCurrentStep('handoffs')
  }

  const handleHandoffsChange = (handoffs: ExpectedHandoff[]) => {
    setTaskData((prev) => ({ ...prev, expectedHandoffs: handoffs }))
  }

  const handleGoalsChange = (goals: GoalCondition[]) => {
    setTaskData((prev) => ({ ...prev, goalState: goals }))
  }

  const handleCreate = async () => {
    setIsSubmitting(true)
    try {
      // Convert goal conditions to API format
      const goalConditions = (taskData.goalState || []).map((g) => {
        const condition = g as GoalCondition
        return {
          goal_type: condition.goalType,
          description: condition.description || '',
          app_id: condition.appId,
          field_path: condition.fieldPath,
          operator: condition.operator,
          expected_value: condition.expectedValue,
          handoff_id: condition.handoffId,
          required_phrase: condition.requiredPhrase,
        }
      })

      // Build legacy goal state for backwards compatibility
      const legacyGoalState = Object.fromEntries(
        (taskData.goalState || [])
          .filter((g) => {
            const condition = g as GoalCondition
            return condition.goalType.startsWith('state_') && condition.appId && condition.fieldPath
          })
          .map((g) => {
            const condition = g as GoalCondition
            return [`${condition.appId}.${condition.fieldPath}`, condition.expectedValue]
          })
      )

      // Convert frontend task format to API request format
      const request = {
        task_id: taskData.name?.toLowerCase().replace(/\s+/g, '-') || `task-${Date.now()}`,
        name: taskData.name || '',
        description: taskData.description || '',
        domain: taskData.tags?.[0] || 'general',
        difficulty: 'medium',
        simulation_config: {
          // Include structured goal conditions in simulation config
          goal_conditions: goalConditions,
        },
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
        user_goal_state: legacyGoalState,
        required_handoffs: (taskData.expectedHandoffs || []).map((h) => ({
          handoff_id: h.id,
          from_role: h.fromRole,
          to_role: h.toRole,
          expected_action: h.expectedAction,
          description: h.description || '',
          instruction_template: h.instructionTemplate ? {
            template_id: h.instructionTemplate.templateId,
            keywords: h.instructionTemplate.keywords,
            target_keywords: h.instructionTemplate.targetKeywords,
          } : undefined,
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

            {!aiMode && (
              <StepIndicator currentStep={currentStep} onStepClick={setCurrentStep} />
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Mode Toggle */}
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setAiMode(true)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg border transition-all',
              aiMode
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border hover:bg-background-secondary'
            )}
          >
            <Sparkles className="h-4 w-4" />
            Describe with AI
          </button>
          <button
            type="button"
            onClick={() => setAiMode(false)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg border transition-all',
              !aiMode
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border hover:bg-background-secondary'
            )}
          >
            <PenTool className="h-4 w-4" />
            Configure Manually
          </button>
        </div>

        {/* AI Generation Mode */}
        {aiMode && (
          <div className="space-y-6">
            <div className="p-6 rounded-lg border border-border bg-background-secondary/30">
              <div className="flex items-start gap-3 mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 className="font-semibold">Describe Your Scenario</h2>
                  <p className="text-sm text-foreground-muted">
                    Describe the evaluation scenario in plain English and AI will generate the task configuration.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Scenario Description *
                  </label>
                  <textarea
                    value={aiDescription}
                    onChange={(e) => setAiDescription(e.target.value)}
                    placeholder="Example: A customer wants to dispute a $50 charge on their PayPal account. The agent should help them file the dispute and confirm it was submitted successfully. The customer needs to verify their identity first before the agent can process the dispute."
                    rows={5}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                  />
                  <p className="text-xs text-foreground-muted mt-1">
                    Be specific about what the customer wants to accomplish and what actions are involved.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Domain Hint (optional)
                  </label>
                  <select
                    value={aiDomainHint}
                    onChange={(e) => setAiDomainHint(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="">Auto-detect</option>
                    <option value="paypal">PayPal / Payments</option>
                    <option value="emirates">Emirates / Airlines</option>
                    <option value="banking">Banking / Finance</option>
                    <option value="shopping">Shopping / E-commerce</option>
                    <option value="telecom">Telecom / Mobile</option>
                    <option value="general">General</option>
                  </select>
                </div>

                {generateError && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-sm">
                    {generateError}
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={isGenerating || !aiDescription.trim()}
                  className={cn(
                    'flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium transition-all',
                    isGenerating || !aiDescription.trim()
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-primary/90'
                  )}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      Generate Task
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Tips */}
            <div className="p-4 rounded-lg border border-border bg-background-secondary/30">
              <h3 className="font-medium mb-2 flex items-center gap-2">
                <span className="text-lg">💡</span> Tips for better results
              </h3>
              <ul className="text-sm text-foreground-muted space-y-1">
                <li>• Describe what the customer wants to accomplish</li>
                <li>• Mention specific actions (transfer, dispute, book, cancel, etc.)</li>
                <li>• Include amounts or details for realistic scenarios</li>
                <li>• Specify any required verification or coordination steps</li>
              </ul>
            </div>
          </div>
        )}

        {/* Manual Configuration Mode */}
        {!aiMode && currentStep === 'info' && (
          <DualControlTaskForm
            initialValues={taskData}
            availableApps={availableApps}
            onSubmit={handleInfoSubmit}
            onCancel={() => navigate(-1)}
          />
        )}

        {!aiMode && currentStep === 'handoffs' && (
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

        {!aiMode && currentStep === 'goals' && (
          <div className="space-y-6">
            <GoalStateEditor
              value={taskData.goalState || []}
              onChange={handleGoalsChange}
              availableApps={appsWithActions}
              availableHandoffs={taskData.expectedHandoffs}
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

        {!aiMode && currentStep === 'review' && (
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
