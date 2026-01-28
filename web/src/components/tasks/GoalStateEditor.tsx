/**
 * GoalStateEditor - Define success criteria for dual-control tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Goal state conditions define verifiable criteria for task success:
 * - Field value checks (equals, contains, gt, lt, etc.)
 * - Existence checks
 * - Multiple conditions can be combined (all must pass)
 */

import { useState } from 'react'
import { Plus, Trash2, Target, CheckCircle2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { GoalStateCondition } from './DualControlTaskForm'

interface GoalStateEditorProps {
  value: GoalStateCondition[]
  onChange: (conditions: GoalStateCondition[]) => void
  /** Available apps with their state schemas */
  availableApps?: Array<{
    id: string
    name: string
    icon?: string
    stateFields?: Array<{
      name: string
      type: string
      description?: string
    }>
  }>
  className?: string
}

type Operator = GoalStateCondition['operator']

const operators: Array<{ value: Operator; label: string; description: string }> = [
  { value: 'equals', label: '=', description: 'Equals' },
  { value: 'contains', label: '∋', description: 'Contains' },
  { value: 'gt', label: '>', description: 'Greater than' },
  { value: 'lt', label: '<', description: 'Less than' },
  { value: 'gte', label: '≥', description: 'Greater or equal' },
  { value: 'lte', label: '≤', description: 'Less or equal' },
  { value: 'exists', label: '∃', description: 'Exists (not null)' },
]

function generateId(): string {
  return `condition-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function GoalStateEditor({
  value,
  onChange,
  availableApps = [],
  className,
}: GoalStateEditorProps) {
  const [expandedCondition, setExpandedCondition] = useState<string | null>(null)

  const addCondition = () => {
    const defaultApp = availableApps[0]
    const defaultField = defaultApp?.stateFields?.[0]?.name || ''

    const newCondition: GoalStateCondition = {
      id: generateId(),
      appId: defaultApp?.id || '',
      field: defaultField,
      operator: 'equals',
      value: '',
      description: '',
    }
    onChange([...value, newCondition])
    setExpandedCondition(newCondition.id)
  }

  const updateCondition = (id: string, updates: Partial<GoalStateCondition>) => {
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

  const getFieldsForApp = (appId: string) => {
    const app = availableApps.find((a) => a.id === appId)
    return app?.stateFields || []
  }

  const getFieldType = (appId: string, fieldName: string): string => {
    const fields = getFieldsForApp(appId)
    return fields.find((f) => f.name === fieldName)?.type || 'string'
  }

  const isConditionValid = (condition: GoalStateCondition): boolean => {
    if (!condition.appId || !condition.field) return false
    if (condition.operator !== 'exists' && condition.value === '') return false
    return true
  }

  const validConditions = value.filter(isConditionValid)
  const invalidConditions = value.filter((c) => !isConditionValid(c))

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" />
            Goal State Conditions
          </h3>
          <p className="text-sm text-foreground-muted mt-0.5">
            Define verifiable conditions for task success
          </p>
        </div>
        <button
          type="button"
          onClick={addCondition}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 transition-colors text-sm"
        >
          <Plus className="h-4 w-4" />
          Add Condition
        </button>
      </div>

      {/* Empty State */}
      {value.length === 0 && (
        <div className="p-6 rounded-lg border border-dashed border-border text-center">
          <CheckCircle2 className="h-8 w-8 text-foreground-muted mx-auto mb-2" />
          <p className="text-foreground-muted">No goal conditions defined</p>
          <p className="text-sm text-foreground-muted mt-1">
            Add conditions to define verifiable success criteria
          </p>
          <button
            type="button"
            onClick={addCondition}
            className="mt-4 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Add First Condition
          </button>
        </div>
      )}

      {/* Conditions List */}
      {value.length > 0 && (
        <div className="space-y-3">
          {value.map((condition, index) => {
            const isValid = isConditionValid(condition)
            const fields = getFieldsForApp(condition.appId)
            const fieldType = getFieldType(condition.appId, condition.field)
            const app = availableApps.find((a) => a.id === condition.appId)

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
                      expandedCondition === condition.id ? null : condition.id
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
                  <div className="flex-1 flex items-center gap-2 text-sm font-mono">
                    <span className="text-foreground-muted">
                      {app?.icon || '🔧'} {condition.appId || '?'}
                    </span>
                    <span className="text-foreground-muted">.</span>
                    <span className="text-primary">{condition.field || '?'}</span>
                    <span className="px-1.5 py-0.5 rounded bg-background-secondary text-foreground-muted">
                      {operators.find((o) => o.value === condition.operator)?.label || '?'}
                    </span>
                    {condition.operator !== 'exists' && (
                      <span className="text-green-600 dark:text-green-400">
                        {JSON.stringify(condition.value)}
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeCondition(condition.id)
                    }}
                    className="p-1.5 rounded hover:bg-error/10 text-foreground-muted hover:text-error transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {/* Expanded Editor */}
                {expandedCondition === condition.id && (
                  <div className="p-4 pt-0 space-y-4 border-t border-border">
                    <div className="grid grid-cols-4 gap-3">
                      {/* App */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-foreground-muted">
                          App
                        </label>
                        <select
                          value={condition.appId}
                          onChange={(e) => {
                            const newAppId = e.target.value
                            const newFields = getFieldsForApp(newAppId)
                            updateCondition(condition.id, {
                              appId: newAppId,
                              field: newFields[0]?.name || '',
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
                        <label className="text-xs font-medium text-foreground-muted">
                          Field
                        </label>
                        {fields.length > 0 ? (
                          <select
                            value={condition.field}
                            onChange={(e) =>
                              updateCondition(condition.id, { field: e.target.value })
                            }
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
                            value={condition.field}
                            onChange={(e) =>
                              updateCondition(condition.id, { field: e.target.value })
                            }
                            placeholder="field_name"
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                          />
                        )}
                      </div>

                      {/* Operator */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-foreground-muted">
                          Operator
                        </label>
                        <select
                          value={condition.operator}
                          onChange={(e) =>
                            updateCondition(condition.id, {
                              operator: e.target.value as Operator,
                            })
                          }
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                        >
                          {operators.map((op) => (
                            <option key={op.value} value={op.value}>
                              {op.label} {op.description}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Value */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-foreground-muted">
                          Value
                        </label>
                        {condition.operator === 'exists' ? (
                          <div className="px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm text-foreground-muted">
                            (checks existence)
                          </div>
                        ) : fieldType === 'number' ? (
                          <input
                            type="number"
                            value={condition.value as number}
                            onChange={(e) =>
                              updateCondition(condition.id, {
                                value: parseFloat(e.target.value) || 0,
                              })
                            }
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                          />
                        ) : fieldType === 'boolean' ? (
                          <select
                            value={String(condition.value)}
                            onChange={(e) =>
                              updateCondition(condition.id, {
                                value: e.target.value === 'true',
                              })
                            }
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                          >
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        ) : (
                          <input
                            type="text"
                            value={condition.value as string}
                            onChange={(e) =>
                              updateCondition(condition.id, { value: e.target.value })
                            }
                            placeholder="Expected value"
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                          />
                        )}
                      </div>
                    </div>

                    {/* Description */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-foreground-muted">
                        Description (optional)
                      </label>
                      <input
                        type="text"
                        value={condition.description || ''}
                        onChange={(e) =>
                          updateCondition(condition.id, { description: e.target.value })
                        }
                        placeholder="e.g., User's balance should be reduced by transfer amount"
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                      />
                    </div>
                  </div>
                )}
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
        </div>
      )}
    </div>
  )
}

export default GoalStateEditor
