/**
 * HandoffEditor - Define expected handoffs for dual-control tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * A handoff represents a coordination point where:
 * - The agent (service_agent) gives an instruction
 * - The user (customer) is expected to perform an action
 */

import { useState } from 'react'
import {
  Plus,
  Trash2,
  GripVertical,
  ArrowRight,
  AlertCircle,
  HelpCircle,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole } from '@/lib/api'
import type { ExpectedHandoff } from './DualControlTaskForm'

interface HandoffEditorProps {
  value: ExpectedHandoff[]
  onChange: (handoffs: ExpectedHandoff[]) => void
  /** Available apps for action selection */
  availableApps?: Array<{ id: string; name: string; icon?: string; actions?: string[] }>
  /** The role that gives instructions */
  agentRole?: AgentRole
  /** The role that executes actions */
  userRole?: AgentRole
  className?: string
}

const roleEmojis: Record<AgentRole, string> = {
  service_agent: '🎧',
  customer: '📱',
  peer: '👥',
}

const roleLabels: Record<AgentRole, string> = {
  service_agent: 'Service Agent',
  customer: 'Customer',
  peer: 'Peer',
}

function generateId(): string {
  return `handoff-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function HandoffEditor({
  value,
  onChange,
  availableApps = [],
  agentRole = 'service_agent',
  userRole = 'customer',
  className,
}: HandoffEditorProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)

  const addHandoff = () => {
    const newHandoff: ExpectedHandoff = {
      id: generateId(),
      order: value.length + 1,
      fromRole: agentRole,
      toRole: userRole,
      expectedAction: '',
      appId: availableApps[0]?.id,
      description: '',
      isOptional: false,
    }
    onChange([...value, newHandoff])
  }

  const updateHandoff = (index: number, updates: Partial<ExpectedHandoff>) => {
    onChange(
      value.map((h, i) => (i === index ? { ...h, ...updates } : h))
    )
  }

  const removeHandoff = (index: number) => {
    const updated = value.filter((_, i) => i !== index)
    // Reorder remaining handoffs
    onChange(updated.map((h, i) => ({ ...h, order: i + 1 })))
  }

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return

    const newValue = [...value]
    const [draggedItem] = newValue.splice(draggedIndex, 1)
    newValue.splice(index, 0, draggedItem)

    // Update order numbers
    onChange(newValue.map((h, i) => ({ ...h, order: i + 1 })))
    setDraggedIndex(index)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
  }

  // Get actions for selected app
  const getAppActions = (appId?: string): string[] => {
    if (!appId) return []
    const app = availableApps.find((a) => a.id === appId)
    return app?.actions || []
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium flex items-center gap-2">
            <ArrowRight className="h-4 w-4 text-primary" />
            Expected Handoffs
          </h3>
          <p className="text-sm text-foreground-muted mt-0.5">
            Define the coordination sequence between agent and user
          </p>
        </div>
        <button
          type="button"
          onClick={addHandoff}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 transition-colors text-sm"
        >
          <Plus className="h-4 w-4" />
          Add Handoff
        </button>
      </div>

      {/* Empty State */}
      {value.length === 0 && (
        <div className="p-6 rounded-lg border border-dashed border-border text-center">
          <ArrowRight className="h-8 w-8 text-foreground-muted mx-auto mb-2" />
          <p className="text-foreground-muted">No handoffs defined</p>
          <p className="text-sm text-foreground-muted mt-1">
            Add handoffs to define the expected coordination sequence
          </p>
          <button
            type="button"
            onClick={addHandoff}
            className="mt-4 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Add First Handoff
          </button>
        </div>
      )}

      {/* Handoff List */}
      {value.length > 0 && (
        <div className="space-y-3">
          {value.map((handoff, index) => (
            <div
              key={handoff.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={cn(
                'p-4 rounded-lg border bg-background transition-all',
                draggedIndex === index
                  ? 'border-primary ring-2 ring-primary/20 opacity-50'
                  : 'border-border hover:border-primary/30'
              )}
            >
              {/* Handoff Header */}
              <div className="flex items-center gap-3 mb-3">
                <div className="cursor-grab hover:bg-background-secondary p-1 rounded">
                  <GripVertical className="h-4 w-4 text-foreground-muted" />
                </div>

                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs font-medium bg-primary/10 text-primary px-2 py-0.5 rounded">
                    #{handoff.order}
                  </span>

                  {/* From -> To display */}
                  <span className="flex items-center gap-1 text-sm">
                    <span>{roleEmojis[handoff.fromRole]}</span>
                    <span className="text-foreground-muted">{roleLabels[handoff.fromRole]}</span>
                  </span>
                  <ArrowRight className="h-3 w-3 text-foreground-muted" />
                  <span className="flex items-center gap-1 text-sm">
                    <span>{roleEmojis[handoff.toRole]}</span>
                    <span className="text-foreground-muted">{roleLabels[handoff.toRole]}</span>
                  </span>
                </div>

                {/* Optional toggle */}
                <label className="flex items-center gap-1.5 text-xs text-foreground-muted">
                  <input
                    type="checkbox"
                    checked={handoff.isOptional || false}
                    onChange={(e) =>
                      updateHandoff(index, { isOptional: e.target.checked })
                    }
                    className="accent-primary"
                  />
                  Optional
                </label>

                <button
                  type="button"
                  onClick={() => removeHandoff(index)}
                  className="p-1.5 rounded hover:bg-error/10 text-foreground-muted hover:text-error transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Handoff Details */}
              <div className="grid grid-cols-2 gap-4 ml-8">
                {/* App Selection */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground-muted">App</label>
                  <select
                    value={handoff.appId || ''}
                    onChange={(e) => updateHandoff(index, { appId: e.target.value })}
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

                {/* Expected Action */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground-muted">
                    Expected Action *
                  </label>
                  {getAppActions(handoff.appId).length > 0 ? (
                    <select
                      value={handoff.expectedAction}
                      onChange={(e) =>
                        updateHandoff(index, { expectedAction: e.target.value })
                      }
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                    >
                      <option value="">Select action...</option>
                      {getAppActions(handoff.appId).map((action) => (
                        <option key={action} value={action}>
                          {action}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={handoff.expectedAction}
                      onChange={(e) =>
                        updateHandoff(index, { expectedAction: e.target.value })
                      }
                      placeholder="e.g., transfer, check_balance"
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                    />
                  )}
                </div>

                {/* Description */}
                <div className="col-span-2 space-y-1.5">
                  <label className="text-xs font-medium text-foreground-muted">
                    Description (optional)
                  </label>
                  <input
                    type="text"
                    value={handoff.description || ''}
                    onChange={(e) =>
                      updateHandoff(index, { description: e.target.value })
                    }
                    placeholder="e.g., User transfers money after agent confirms details"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                  />
                </div>

                {/* Instruction Template */}
                <div className="col-span-2 p-3 rounded-lg bg-background-secondary/50 border border-border/50 space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    <span className="text-xs font-medium">Instruction Detection</span>
                    <div className="relative group">
                      <HelpCircle className="h-3.5 w-3.5 text-foreground-muted cursor-help" />
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 rounded-lg bg-foreground text-background text-xs opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 shadow-lg">
                        <p className="font-medium mb-1">How instruction detection works:</p>
                        <p className="mb-2">During simulation, when the agent speaks, the system looks for these keywords to detect when an instruction is given.</p>
                        <p className="text-background/80">Example: If agent says "Please <strong>verify</strong> your <strong>identity</strong>", the system matches "verify" (keyword) + "identity" (target) → Instruction detected!</p>
                        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-foreground"></div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs text-foreground-muted">
                        Action Keywords
                      </label>
                      <input
                        type="text"
                        value={handoff.instructionTemplate?.keywords?.join(', ') || ''}
                        onChange={(e) => {
                          const keywords = e.target.value.split(',').map(k => k.trim()).filter(Boolean)
                          updateHandoff(index, {
                            instructionTemplate: {
                              templateId: handoff.instructionTemplate?.templateId || handoff.id,
                              keywords,
                              targetKeywords: handoff.instructionTemplate?.targetKeywords || [],
                            }
                          })
                        }}
                        placeholder="verify, confirm, check"
                        className="w-full px-2.5 py-1.5 rounded border border-border bg-background text-xs"
                      />
                      <p className="text-[10px] text-foreground-muted">Verbs the agent might use</p>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-foreground-muted">
                        Target Keywords
                      </label>
                      <input
                        type="text"
                        value={handoff.instructionTemplate?.targetKeywords?.join(', ') || ''}
                        onChange={(e) => {
                          const targetKeywords = e.target.value.split(',').map(k => k.trim()).filter(Boolean)
                          updateHandoff(index, {
                            instructionTemplate: {
                              templateId: handoff.instructionTemplate?.templateId || handoff.id,
                              keywords: handoff.instructionTemplate?.keywords || [],
                              targetKeywords,
                            }
                          })
                        }}
                        placeholder="identity, ID, account"
                        className="w-full px-2.5 py-1.5 rounded border border-border bg-background text-xs"
                      />
                      <p className="text-[10px] text-foreground-muted">Nouns the instruction refers to</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validation warning */}
              {!handoff.expectedAction && (
                <div className="mt-3 ml-8 flex items-center gap-1.5 text-xs text-warning">
                  <AlertCircle className="h-3 w-3" />
                  Expected action is required
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {value.length > 0 && (
        <div className="p-3 rounded-lg bg-background-secondary/50 border border-border">
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-muted">
              Total handoffs: <strong>{value.length}</strong>
            </span>
            <span className="text-foreground-muted">
              Optional:{' '}
              <strong>{value.filter((h) => h.isOptional).length}</strong>
            </span>
            <span className="text-foreground-muted">
              Required:{' '}
              <strong>{value.filter((h) => !h.isOptional).length}</strong>
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default HandoffEditor
