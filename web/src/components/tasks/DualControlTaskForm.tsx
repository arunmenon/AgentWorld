/**
 * DualControlTaskForm - Form for creating dual-control evaluation tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * A dual-control task defines:
 * - Task name and description
 * - Agent and user role assignments
 * - App(s) to be used
 * - Initial state configuration
 * - Goal/success criteria
 * - Expected handoff sequence
 */

import { useState } from 'react'
import {
  Headphones,
  Smartphone,
  Target,
  FileText,
  Settings,
  HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole, AppDefinition } from '@/lib/api'
import type { GoalCondition } from '@/lib/goals'

// Re-export GoalCondition as GoalStateCondition for backwards compatibility
export type { GoalCondition as GoalStateCondition } from '@/lib/goals'

export interface DualControlTask {
  id?: string
  name: string
  description: string
  /** The role that provides guidance (typically service_agent) */
  agentRole: AgentRole
  /** The role that executes actions (typically customer) */
  userRole: AgentRole
  /** Apps available to the user role */
  userApps: string[]
  /** Apps available to the agent role (backend systems) */
  agentApps: string[]
  /** Initial state for apps */
  initialState: Record<string, Record<string, unknown>>
  /** Natural language goal description */
  goalDescription: string
  /** Structured goal state conditions (uses full GoalCondition type) */
  goalState: GoalCondition[]
  /** Expected handoff sequence */
  expectedHandoffs: ExpectedHandoff[]
  /** Maximum steps allowed */
  maxSteps: number
  /** Tags for categorization */
  tags: string[]
}

export interface ExpectedHandoff {
  id: string
  order: number
  fromRole: AgentRole
  toRole: AgentRole
  expectedAction: string
  appId?: string
  description?: string
  isOptional?: boolean
}

interface DualControlTaskFormProps {
  /** Initial values for editing */
  initialValues?: Partial<DualControlTask>
  /** Available apps to choose from */
  availableApps?: AppDefinition[]
  /** Called when form is submitted */
  onSubmit: (task: DualControlTask) => void
  /** Called when cancelled */
  onCancel?: () => void
  /** Whether form is being submitted */
  isSubmitting?: boolean
  className?: string
}

const roleOptions = [
  {
    value: 'service_agent' as AgentRole,
    icon: <Headphones className="h-4 w-4" />,
    emoji: '🎧',
    label: 'Service Agent',
    description: 'Provides guidance and has backend access',
  },
  {
    value: 'customer' as AgentRole,
    icon: <Smartphone className="h-4 w-4" />,
    emoji: '📱',
    label: 'Customer',
    description: 'Executes actions on their device',
  },
]

function SectionHeader({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description?: string
}) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <div>
        <h3 className="font-medium">{title}</h3>
        {description && (
          <p className="text-sm text-foreground-muted mt-0.5">{description}</p>
        )}
      </div>
    </div>
  )
}

function RoleSelector({
  label,
  value,
  onChange,
  excludeRole,
}: {
  label: string
  value: AgentRole
  onChange: (role: AgentRole) => void
  excludeRole?: AgentRole
}) {
  const filteredOptions = roleOptions.filter((r) => r.value !== excludeRole)

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      <div className="grid grid-cols-2 gap-2">
        {filteredOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              'flex items-start gap-2 p-3 rounded-lg border text-left transition-all',
              value === option.value
                ? 'border-primary bg-primary/5 ring-1 ring-primary'
                : 'border-border hover:border-primary/40'
            )}
          >
            <span className="text-lg">{option.emoji}</span>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm">{option.label}</div>
              <p className="text-xs text-foreground-muted mt-0.5">
                {option.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export function DualControlTaskForm({
  initialValues,
  availableApps = [],
  onSubmit,
  onCancel,
  isSubmitting = false,
  className,
}: DualControlTaskFormProps) {
  const [formData, setFormData] = useState<Partial<DualControlTask>>({
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
    ...initialValues,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const updateField = <K extends keyof DualControlTask>(
    field: K,
    value: DualControlTask[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error when field is updated
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name?.trim()) {
      newErrors.name = 'Task name is required'
    }

    if (!formData.description?.trim()) {
      newErrors.description = 'Description is required'
    }

    if (!formData.goalDescription?.trim()) {
      newErrors.goalDescription = 'Goal description is required'
    }

    // Only require app selection if apps are available
    if (availableApps.length > 0 && (formData.userApps?.length || 0) === 0) {
      newErrors.userApps = 'Select at least one app for the user'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    onSubmit(formData as DualControlTask)
  }

  // Categorize apps by access type for easier selection
  const userFacingApps = availableApps.filter(
    (app) => !app.access_type || app.access_type === 'shared' || app.access_type === 'per_agent'
  )
  const backendApps = availableApps.filter(
    (app) => app.access_type === 'role_restricted'
  )

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-8', className)}>
      {/* Basic Info Section */}
      <section>
        <SectionHeader
          icon={<FileText className="h-4 w-4 text-primary" />}
          title="Task Information"
          description="Define what this task evaluates"
        />

        <div className="space-y-4 pl-11">
          <div className="space-y-2">
            <label className="text-sm font-medium">Task Name *</label>
            <input
              type="text"
              value={formData.name || ''}
              onChange={(e) => updateField('name', e.target.value)}
              placeholder="e.g., Flight Rebooking Assistance"
              className={cn(
                'w-full px-3 py-2 rounded-lg border bg-background',
                errors.name ? 'border-error' : 'border-border'
              )}
            />
            {errors.name && (
              <p className="text-xs text-error">{errors.name}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description *</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => updateField('description', e.target.value)}
              placeholder="Describe the task scenario and what the agent should help the user accomplish..."
              rows={3}
              className={cn(
                'w-full px-3 py-2 rounded-lg border bg-background resize-none',
                errors.description ? 'border-error' : 'border-border'
              )}
            />
            {errors.description && (
              <p className="text-xs text-error">{errors.description}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Steps</label>
              <input
                type="number"
                min={1}
                max={100}
                value={formData.maxSteps || 10}
                onChange={(e) => updateField('maxSteps', parseInt(e.target.value) || 10)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Tags</label>
              <input
                type="text"
                value={formData.tags?.join(', ') || ''}
                onChange={(e) =>
                  updateField(
                    'tags',
                    e.target.value.split(',').map((t) => t.trim()).filter(Boolean)
                  )
                }
                placeholder="airline, rebooking, complex"
                className="w-full px-3 py-2 rounded-lg border border-border bg-background"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Role Assignment Section */}
      <section>
        <SectionHeader
          icon={<Headphones className="h-4 w-4 text-primary" />}
          title="Role Assignment"
          description="Define who guides and who executes"
        />

        <div className="grid grid-cols-2 gap-6 pl-11">
          <RoleSelector
            label="Guide Role (Agent)"
            value={formData.agentRole || 'service_agent'}
            onChange={(role) => updateField('agentRole', role)}
            excludeRole={formData.userRole}
          />
          <RoleSelector
            label="Execute Role (User)"
            value={formData.userRole || 'customer'}
            onChange={(role) => updateField('userRole', role)}
            excludeRole={formData.agentRole}
          />
        </div>
      </section>

      {/* App Selection Section */}
      <section>
        <SectionHeader
          icon={<Settings className="h-4 w-4 text-primary" />}
          title="App Configuration"
          description="Select which apps each role can access"
        />

        <div className="grid grid-cols-2 gap-6 pl-11">
          {/* User Apps */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📱</span>
              <label className="text-sm font-medium">User Apps</label>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {userFacingApps.length === 0 ? (
                <p className="text-sm text-foreground-muted py-2">
                  No user-facing apps available
                </p>
              ) : (
                userFacingApps.map((app) => (
                  <label
                    key={app.id}
                    className={cn(
                      'flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors',
                      formData.userApps?.includes(app.app_id)
                        ? 'bg-primary/10'
                        : 'hover:bg-background-secondary'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={formData.userApps?.includes(app.app_id) || false}
                      onChange={(e) => {
                        const current = formData.userApps || []
                        updateField(
                          'userApps',
                          e.target.checked
                            ? [...current, app.app_id]
                            : current.filter((id) => id !== app.app_id)
                        )
                      }}
                      className="accent-primary"
                    />
                    <span>{app.icon || '🔧'}</span>
                    <span className="text-sm">{app.name}</span>
                  </label>
                ))
              )}
            </div>
            {errors.userApps && (
              <p className="text-xs text-error">{errors.userApps}</p>
            )}
          </div>

          {/* Agent Apps */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">🎧</span>
              <label className="text-sm font-medium">Agent Apps (Backend)</label>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {backendApps.length === 0 ? (
                <p className="text-sm text-foreground-muted py-2">
                  No backend apps available
                </p>
              ) : (
                backendApps.map((app) => (
                  <label
                    key={app.id}
                    className={cn(
                      'flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors',
                      formData.agentApps?.includes(app.app_id)
                        ? 'bg-primary/10'
                        : 'hover:bg-background-secondary'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={formData.agentApps?.includes(app.app_id) || false}
                      onChange={(e) => {
                        const current = formData.agentApps || []
                        updateField(
                          'agentApps',
                          e.target.checked
                            ? [...current, app.app_id]
                            : current.filter((id) => id !== app.app_id)
                        )
                      }}
                      className="accent-primary"
                    />
                    <span>{app.icon || '🔧'}</span>
                    <span className="text-sm">{app.name}</span>
                  </label>
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Goal Section */}
      <section>
        <SectionHeader
          icon={<Target className="h-4 w-4 text-primary" />}
          title="Success Criteria"
          description="Define what constitutes successful task completion"
        />

        <div className="space-y-4 pl-11">
          <div className="space-y-2">
            <label className="text-sm font-medium">Goal Description *</label>
            <textarea
              value={formData.goalDescription || ''}
              onChange={(e) => updateField('goalDescription', e.target.value)}
              placeholder="Describe the expected outcome, e.g., 'User successfully rebooks their flight to a new date with the agent's assistance'"
              rows={2}
              className={cn(
                'w-full px-3 py-2 rounded-lg border bg-background resize-none',
                errors.goalDescription ? 'border-error' : 'border-border'
              )}
            />
            {errors.goalDescription && (
              <p className="text-xs text-error">{errors.goalDescription}</p>
            )}
          </div>

          <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-start gap-2">
              <HelpCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <p className="text-sm text-foreground-secondary">
                Use the <strong>Goal State Editor</strong> and <strong>Handoff Editor</strong> below
                to define precise success conditions and expected coordination sequence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-border">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className={cn(
            'px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium transition-colors',
            isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary/90'
          )}
        >
          {isSubmitting ? 'Saving...' : 'Continue to Handoffs →'}
        </button>
      </div>
    </form>
  )
}

export default DualControlTaskForm
