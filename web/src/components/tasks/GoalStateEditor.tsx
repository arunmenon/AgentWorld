/**
 * GoalStateEditor - Define success criteria for dual-control tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Supports the full goal taxonomy:
 * - State goals: Check app data values
 * - Action goals: Check what user did
 * - Coordination goals: Check agent-user interaction
 * - Output goals: Check what agent said
 */

import { useState } from 'react'
import { Plus, Trash2, Target, CheckCircle2, AlertCircle, Database, Zap, RefreshCw, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { GoalCondition, GoalType, GoalOperator } from '@/lib/goals'
import { getGoalTypeLabel } from '@/lib/goals'
import type { ExpectedHandoff } from './DualControlTaskForm'

/** Goal category for UI grouping */
type GoalCategory = 'state' | 'action' | 'coordination' | 'output'

interface GoalStateEditorProps {
  value: GoalCondition[]
  onChange: (conditions: GoalCondition[]) => void
  /** Available apps with their state schemas */
  availableApps?: Array<{
    id: string
    name: string
    icon?: string
    actions?: string[]
    stateFields?: Array<{
      name: string
      type: string
      description?: string
    }>
  }>
  /** Available handoffs for coordination goals */
  availableHandoffs?: ExpectedHandoff[]
  className?: string
}

/** Category metadata for display */
const categories: Array<{
  id: GoalCategory
  label: string
  description: string
  icon: React.ReactNode
  goalTypes: GoalType[]
}> = [
  {
    id: 'state',
    label: 'State',
    description: 'Check app data values',
    icon: <Database className="h-4 w-4" />,
    goalTypes: ['state_equals', 'state_contains', 'state_greater', 'state_less', 'state_exists'],
  },
  {
    id: 'action',
    label: 'Action',
    description: 'Check what user did',
    icon: <Zap className="h-4 w-4" />,
    goalTypes: ['action_executed', 'action_succeeded'],
  },
  {
    id: 'coordination',
    label: 'Coordination',
    description: 'Check handoff sequence',
    icon: <RefreshCw className="h-4 w-4" />,
    goalTypes: ['handoff_completed', 'all_handoffs_done'],
  },
  {
    id: 'output',
    label: 'Output',
    description: 'Check what agent said',
    icon: <MessageSquare className="h-4 w-4" />,
    goalTypes: ['output_contains'],
  },
]

/** Operators for state goals */
const stateOperators: Array<{ value: GoalOperator; label: string; description: string }> = [
  { value: 'equals', label: '=', description: 'Equals' },
  { value: 'not_equals', label: '≠', description: 'Not equals' },
  { value: 'contains', label: '∋', description: 'Contains' },
  { value: 'not_contains', label: '∌', description: 'Does not contain' },
  { value: 'gt', label: '>', description: 'Greater than' },
  { value: 'lt', label: '<', description: 'Less than' },
  { value: 'gte', label: '≥', description: 'Greater or equal' },
  { value: 'lte', label: '≤', description: 'Less or equal' },
  { value: 'exists', label: '∃', description: 'Exists (not null)' },
  { value: 'not_exists', label: '∄', description: 'Does not exist' },
]

function generateId(): string {
  return `condition-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function getCategoryForGoalType(goalType: GoalType): GoalCategory {
  if (goalType.startsWith('state_')) return 'state'
  if (goalType.startsWith('action_')) return 'action'
  if (goalType === 'handoff_completed' || goalType === 'all_handoffs_done') return 'coordination'
  if (goalType === 'output_contains') return 'output'
  return 'state'
}

function getDefaultGoalType(category: GoalCategory): GoalType {
  switch (category) {
    case 'state': return 'state_equals'
    case 'action': return 'action_executed'
    case 'coordination': return 'handoff_completed'
    case 'output': return 'output_contains'
  }
}

export function GoalStateEditor({
  value,
  onChange,
  availableApps = [],
  availableHandoffs = [],
  className,
}: GoalStateEditorProps) {
  const [expandedCondition, setExpandedCondition] = useState<string | null>(null)

  const addCondition = (category: GoalCategory = 'state') => {
    const defaultGoalType = getDefaultGoalType(category)
    const defaultApp = availableApps[0]
    const defaultField = defaultApp?.stateFields?.[0]?.name || ''
    const defaultHandoff = availableHandoffs[0]

    const newCondition: GoalCondition = {
      id: generateId(),
      goalType: defaultGoalType,
      description: '',
      appId: category === 'state' || category === 'action' ? defaultApp?.id : undefined,
      fieldPath: category === 'state' ? defaultField : undefined,
      operator: category === 'state' ? 'equals' : undefined,
      expectedValue: category === 'state' || category === 'action' ? '' : undefined,
      handoffId: category === 'coordination' && defaultHandoff ? defaultHandoff.id : undefined,
      requiredPhrase: category === 'output' ? '' : undefined,
    }
    onChange([...value, newCondition])
    setExpandedCondition(newCondition.id!)
  }

  const updateCondition = (id: string, updates: Partial<GoalCondition>) => {
    onChange(
      value.map((c) => (c.id === id ? { ...c, ...updates } : c))
    )
  }

  const removeCondition = (id: string) => {
    onChange(value.filter((c) => c.id !== id))
    if (expandedCondition === id) {
      setExpandedCondition(null)
    }
  }

  const changeConditionCategory = (id: string, newCategory: GoalCategory) => {
    const condition = value.find((c) => c.id === id)
    if (!condition) return

    const newGoalType = getDefaultGoalType(newCategory)
    const defaultApp = availableApps[0]
    const defaultField = defaultApp?.stateFields?.[0]?.name || ''
    const defaultHandoff = availableHandoffs[0]

    // Reset fields based on new category
    const updates: Partial<GoalCondition> = {
      goalType: newGoalType,
      appId: newCategory === 'state' || newCategory === 'action' ? defaultApp?.id : undefined,
      fieldPath: newCategory === 'state' ? defaultField : undefined,
      operator: newCategory === 'state' ? 'equals' : undefined,
      expectedValue: newCategory === 'state' || newCategory === 'action' ? '' : undefined,
      handoffId: newCategory === 'coordination' && defaultHandoff ? defaultHandoff.id : undefined,
      requiredPhrase: newCategory === 'output' ? '' : undefined,
    }

    updateCondition(id, updates)
  }

  const getFieldsForApp = (appId: string | undefined) => {
    if (!appId) return []
    const app = availableApps.find((a) => a.id === appId)
    return app?.stateFields || []
  }

  const getActionsForApp = (appId: string | undefined) => {
    if (!appId) return []
    const app = availableApps.find((a) => a.id === appId)
    return app?.actions || []
  }

  const getFieldType = (appId: string | undefined, fieldName: string | undefined): string => {
    if (!appId || !fieldName) return 'string'
    const fields = getFieldsForApp(appId)
    return fields.find((f) => f.name === fieldName)?.type || 'string'
  }

  const isConditionValid = (condition: GoalCondition): boolean => {
    const category = getCategoryForGoalType(condition.goalType)

    switch (category) {
      case 'state':
        if (!condition.appId || !condition.fieldPath) return false
        if (condition.operator !== 'exists' && condition.operator !== 'not_exists' && !condition.expectedValue) return false
        return true
      case 'action':
        if (!condition.appId || !condition.expectedValue) return false
        return true
      case 'coordination':
        if (condition.goalType === 'all_handoffs_done') return true
        if (!condition.handoffId) return false
        return true
      case 'output':
        if (!condition.requiredPhrase) return false
        return true
      default:
        return false
    }
  }

  const validConditions = value.filter(isConditionValid)
  const invalidConditions = value.filter((c) => !isConditionValid(c))

  /** Render condition preview text */
  const renderConditionPreview = (condition: GoalCondition) => {
    const category = getCategoryForGoalType(condition.goalType)
    const app = availableApps.find((a) => a.id === condition.appId)
    const handoff = availableHandoffs.find((h) => h.id === condition.handoffId)
    const categoryInfo = categories.find((c) => c.id === category)

    return (
      <div className="flex-1 flex items-center gap-2 text-sm">
        {/* Category badge */}
        <span className={cn(
          'flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium',
          category === 'state' && 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
          category === 'action' && 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
          category === 'coordination' && 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
          category === 'output' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
        )}>
          {categoryInfo?.icon}
          <span className="hidden sm:inline">{categoryInfo?.label}</span>
        </span>

        {/* Condition details */}
        <span className="font-mono text-foreground-muted truncate">
          {category === 'state' && (
            <>
              {app?.icon || '🔧'} {condition.appId || '?'}.{condition.fieldPath || '?'}
              <span className="mx-1 px-1 py-0.5 rounded bg-background-secondary">
                {stateOperators.find((o) => o.value === condition.operator)?.label || '?'}
              </span>
              {condition.operator !== 'exists' && condition.operator !== 'not_exists' && (
                <span className="text-green-600 dark:text-green-400">
                  {JSON.stringify(condition.expectedValue)}
                </span>
              )}
            </>
          )}
          {category === 'action' && (
            <>
              {app?.icon || '🔧'} {condition.appId || '?'} →
              <span className="text-amber-600 dark:text-amber-400 ml-1">
                {condition.expectedValue as string || '?'}
              </span>
              {condition.goalType === 'action_succeeded' && (
                <span className="ml-1 text-xs text-foreground-muted">(must succeed)</span>
              )}
            </>
          )}
          {category === 'coordination' && (
            condition.goalType === 'all_handoffs_done' ? (
              <span className="text-purple-600 dark:text-purple-400">All handoffs completed</span>
            ) : (
              <>
                Handoff: <span className="text-purple-600 dark:text-purple-400">
                  {handoff ? `#${handoff.order} ${handoff.expectedAction}` : condition.handoffId || '?'}
                </span>
              </>
            )
          )}
          {category === 'output' && (
            <>
              Agent says: "<span className="text-green-600 dark:text-green-400">
                {(condition.requiredPhrase || '').substring(0, 30)}{(condition.requiredPhrase?.length || 0) > 30 ? '...' : ''}
              </span>"
            </>
          )}
        </span>
      </div>
    )
  }

  /** Render fields based on goal category */
  const renderConditionFields = (condition: GoalCondition) => {
    const category = getCategoryForGoalType(condition.goalType)
    const fields = getFieldsForApp(condition.appId)
    const actions = getActionsForApp(condition.appId)
    const fieldType = getFieldType(condition.appId, condition.fieldPath)
    const categoryGoalTypes = categories.find((c) => c.id === category)?.goalTypes || []

    return (
      <div className="p-4 pt-0 space-y-4 border-t border-border">
        {/* Category tabs */}
        <div className="flex gap-1 pt-4">
          {categories.map((cat) => {
            const isActive = category === cat.id
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => changeConditionCategory(condition.id!, cat.id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background-secondary text-foreground-muted hover:text-foreground hover:bg-background-secondary/80'
                )}
              >
                {cat.icon}
                {cat.label}
              </button>
            )
          })}
        </div>

        {/* Goal type selector within category */}
        {categoryGoalTypes.length > 1 && (
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground-muted">Goal Type</label>
            <select
              value={condition.goalType}
              onChange={(e) => updateCondition(condition.id!, { goalType: e.target.value as GoalType })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
            >
              {categoryGoalTypes.map((gt) => (
                <option key={gt} value={gt}>{getGoalTypeLabel(gt)}</option>
              ))}
            </select>
          </div>
        )}

        {/* State goal fields */}
        {category === 'state' && (
          <div className="grid grid-cols-4 gap-3">
            {/* App */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">App</label>
              <select
                value={condition.appId || ''}
                onChange={(e) => {
                  const newAppId = e.target.value
                  const newFields = getFieldsForApp(newAppId)
                  updateCondition(condition.id!, {
                    appId: newAppId,
                    fieldPath: newFields[0]?.name || '',
                  })
                }}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
              >
                <option value="">Select app...</option>
                {availableApps.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.icon || '🔧'} {app.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">Field</label>
              {fields.length > 0 ? (
                <select
                  value={condition.fieldPath || ''}
                  onChange={(e) => updateCondition(condition.id!, { fieldPath: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">Select field...</option>
                  {fields.map((field) => (
                    <option key={field.name} value={field.name}>
                      {field.name} ({field.type})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={condition.fieldPath || ''}
                  onChange={(e) => updateCondition(condition.id!, { fieldPath: e.target.value })}
                  placeholder="field_name"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                />
              )}
            </div>

            {/* Operator */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">Operator</label>
              <select
                value={condition.operator || 'equals'}
                onChange={(e) => updateCondition(condition.id!, { operator: e.target.value as GoalOperator })}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
              >
                {stateOperators.map((op) => (
                  <option key={op.value} value={op.value}>
                    {op.label} {op.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Value */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">Value</label>
              {condition.operator === 'exists' || condition.operator === 'not_exists' ? (
                <div className="px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm text-foreground-muted">
                  (checks existence)
                </div>
              ) : fieldType === 'number' ? (
                <input
                  type="number"
                  value={condition.expectedValue as number || ''}
                  onChange={(e) => updateCondition(condition.id!, { expectedValue: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                />
              ) : fieldType === 'boolean' ? (
                <select
                  value={String(condition.expectedValue)}
                  onChange={(e) => updateCondition(condition.id!, { expectedValue: e.target.value === 'true' })}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              ) : (
                <input
                  type="text"
                  value={condition.expectedValue as string || ''}
                  onChange={(e) => updateCondition(condition.id!, { expectedValue: e.target.value })}
                  placeholder="Expected value"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                />
              )}
            </div>
          </div>
        )}

        {/* Action goal fields */}
        {category === 'action' && (
          <div className="grid grid-cols-3 gap-3">
            {/* App */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">App</label>
              <select
                value={condition.appId || ''}
                onChange={(e) => updateCondition(condition.id!, { appId: e.target.value, expectedValue: '' })}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
              >
                <option value="">Select app...</option>
                {availableApps.map((app) => (
                  <option key={app.id} value={app.id}>
                    {app.icon || '🔧'} {app.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Action */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">Action</label>
              {actions.length > 0 ? (
                <select
                  value={condition.expectedValue as string || ''}
                  onChange={(e) => updateCondition(condition.id!, { expectedValue: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">Select action...</option>
                  {actions.map((action) => (
                    <option key={action} value={action}>{action}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={condition.expectedValue as string || ''}
                  onChange={(e) => updateCondition(condition.id!, { expectedValue: e.target.value })}
                  placeholder="action_name"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                />
              )}
            </div>

            {/* Must succeed checkbox */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">Options</label>
              <label className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background text-sm cursor-pointer hover:bg-background-secondary">
                <input
                  type="checkbox"
                  checked={condition.goalType === 'action_succeeded'}
                  onChange={(e) => updateCondition(condition.id!, {
                    goalType: e.target.checked ? 'action_succeeded' : 'action_executed'
                  })}
                  className="accent-primary"
                />
                Must succeed
              </label>
            </div>
          </div>
        )}

        {/* Coordination goal fields */}
        {category === 'coordination' && (
          <div className="grid grid-cols-2 gap-3">
            {/* Handoff selector or All Done */}
            {condition.goalType === 'all_handoffs_done' ? (
              <div className="col-span-2 p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
                <p className="text-sm text-purple-700 dark:text-purple-300">
                  This goal is met when all defined handoffs have been completed successfully.
                </p>
                {availableHandoffs.length === 0 && (
                  <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                    Note: No handoffs defined yet. Add handoffs in the previous step.
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground-muted">Handoff</label>
                {availableHandoffs.length > 0 ? (
                  <select
                    value={condition.handoffId || ''}
                    onChange={(e) => updateCondition(condition.id!, { handoffId: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="">Select handoff...</option>
                    {availableHandoffs.map((h) => (
                      <option key={h.id} value={h.id}>
                        #{h.order}: {h.expectedAction} ({h.fromRole} → {h.toRole})
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="px-3 py-2 rounded-lg border border-warning/50 bg-warning/10 text-sm text-foreground-muted">
                    No handoffs defined. Add handoffs in the previous step.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Output goal fields */}
        {category === 'output' && (
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground-muted">Required Phrase</label>
            <textarea
              value={condition.requiredPhrase || ''}
              onChange={(e) => updateCondition(condition.id!, { requiredPhrase: e.target.value })}
              placeholder="Enter a phrase that the agent must include in their response..."
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
            />
            <p className="text-xs text-foreground-muted">
              The agent's response must contain this phrase (case-insensitive substring match).
            </p>
          </div>
        )}

        {/* Description */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-foreground-muted">Description (optional)</label>
          <input
            type="text"
            value={condition.description || ''}
            onChange={(e) => updateCondition(condition.id!, { description: e.target.value })}
            placeholder="e.g., User's balance should be reduced by transfer amount"
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
          />
        </div>
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" />
            Goal Conditions
          </h3>
          <p className="text-sm text-foreground-muted mt-0.5">
            Define verifiable conditions for task success
          </p>
        </div>

        {/* Add condition dropdown */}
        <div className="relative group">
          <button
            type="button"
            onClick={() => addCondition('state')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 transition-colors text-sm"
          >
            <Plus className="h-4 w-4" />
            Add Condition
          </button>

          {/* Dropdown menu for category selection */}
          <div className="absolute right-0 top-full mt-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
            <div className="bg-background border border-border rounded-lg shadow-lg p-1 min-w-[180px]">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => addCondition(cat.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-left hover:bg-background-secondary transition-colors"
                >
                  {cat.icon}
                  <div>
                    <div className="font-medium">{cat.label}</div>
                    <div className="text-xs text-foreground-muted">{cat.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Empty State */}
      {value.length === 0 && (
        <div className="p-6 rounded-lg border border-dashed border-border text-center">
          <CheckCircle2 className="h-8 w-8 text-foreground-muted mx-auto mb-2" />
          <p className="text-foreground-muted">No goal conditions defined</p>
          <p className="text-sm text-foreground-muted mt-1">
            Add conditions to define verifiable success criteria
          </p>
          <div className="flex justify-center gap-2 mt-4 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => addCondition(cat.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 transition-colors text-sm"
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Conditions List */}
      {value.length > 0 && (
        <div className="space-y-3">
          {value.map((condition, index) => {
            const isValid = isConditionValid(condition)

            return (
              <div
                key={condition.id}
                className={cn(
                  'rounded-lg border transition-all',
                  !isValid
                    ? 'border-warning bg-warning/5'
                    : 'border-border bg-background hover:border-primary/30'
                )}
              >
                {/* Condition Summary Row */}
                <div
                  className="flex items-center gap-3 p-3 cursor-pointer"
                  onClick={() =>
                    setExpandedCondition(
                      expandedCondition === condition.id ? null : condition.id!
                    )
                  }
                >
                  <span
                    className={cn(
                      'text-xs font-medium px-2 py-0.5 rounded',
                      isValid
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-warning/20 text-warning'
                    )}
                  >
                    {index + 1}
                  </span>

                  {/* Condition preview */}
                  {renderConditionPreview(condition)}

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeCondition(condition.id!)
                    }}
                    className="p-1.5 rounded hover:bg-error/10 text-foreground-muted hover:text-error transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {/* Expanded Editor */}
                {expandedCondition === condition.id && renderConditionFields(condition)}
              </div>
            )
          })}
        </div>
      )}

      {/* Summary */}
      {value.length > 0 && (
        <div className="p-3 rounded-lg bg-background-secondary/50 border border-border">
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-muted">
              Total conditions: <strong>{value.length}</strong>
            </span>
            <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-3 w-3" />
              Valid: <strong>{validConditions.length}</strong>
            </span>
            {invalidConditions.length > 0 && (
              <span className="flex items-center gap-1 text-warning">
                <AlertCircle className="h-3 w-3" />
                Incomplete: <strong>{invalidConditions.length}</strong>
              </span>
            )}
          </div>

          {/* Category breakdown */}
          <div className="flex gap-3 mt-2 pt-2 border-t border-border">
            {categories.map((cat) => {
              const count = value.filter((c) => getCategoryForGoalType(c.goalType) === cat.id).length
              if (count === 0) return null
              return (
                <span key={cat.id} className="flex items-center gap-1 text-xs text-foreground-muted">
                  {cat.icon}
                  {cat.label}: {count}
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default GoalStateEditor
