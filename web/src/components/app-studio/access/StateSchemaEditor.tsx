/**
 * StateSchemaEditor - Editor for state schema fields with observable toggle.
 *
 * Per τ²-bench integration (ADR-020.1) Phase 1:
 * - Allows marking fields as observable/hidden for state-constrained user simulation
 * - Observable fields are visible to user agents in dual-control scenarios
 * - Hidden fields are only accessible to service agents (backend)
 *
 * Use case: In customer service simulations, the user agent should only
 * respond based on what they can "see" on their device (observable fields).
 */

import { Eye, EyeOff, Plus, Trash2, HelpCircle, Database, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { StateField } from '@/lib/api'

interface StateSchemaEditorProps {
  fields: StateField[]
  onChange: (fields: StateField[]) => void
  disabled?: boolean
  className?: string
}

const fieldTypes = ['string', 'number', 'boolean', 'array', 'object'] as const

export function StateSchemaEditor({
  fields,
  onChange,
  disabled = false,
  className,
}: StateSchemaEditorProps) {
  const handleFieldChange = (index: number, updates: Partial<StateField>) => {
    const newFields = [...fields]
    newFields[index] = { ...newFields[index], ...updates }
    onChange(newFields)
  }

  const handleAddField = () => {
    const newField: StateField = {
      name: `field_${fields.length + 1}`,
      type: 'string',
      default: '',
      per_agent: true,
      description: '',
      observable: true,
    }
    onChange([...fields, newField])
  }

  const handleRemoveField = (index: number) => {
    const newFields = fields.filter((_, i) => i !== index)
    onChange(newFields)
  }

  const observableCount = fields.filter((f) => f.observable !== false).length
  const hiddenCount = fields.length - observableCount

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium">State Schema</h3>
          <p className="text-xs text-foreground-muted mt-1">
            Define app state fields. Mark which fields are observable to users.
          </p>
        </div>
        <button
          type="button"
          className="text-foreground-muted hover:text-foreground-secondary"
          title="Observable fields are visible to user agents in state-constrained mode"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
      </div>

      {/* Summary badges */}
      <div className="flex gap-2 text-xs">
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-success/10 text-success">
          <Eye className="h-3 w-3" />
          {observableCount} observable
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-warning/10 text-warning">
          <EyeOff className="h-3 w-3" />
          {hiddenCount} hidden
        </span>
      </div>

      {/* Field list */}
      <div className="space-y-3">
        {fields.map((field, index) => (
          <StateFieldRow
            key={index}
            field={field}
            index={index}
            onChange={(updates) => handleFieldChange(index, updates)}
            onRemove={() => handleRemoveField(index)}
            disabled={disabled}
          />
        ))}
      </div>

      {/* Add field button */}
      <button
        type="button"
        onClick={handleAddField}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-center gap-2 p-3 rounded-lg border border-dashed',
          'text-foreground-muted hover:text-foreground-secondary hover:border-primary/40',
          'transition-colors',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <Plus className="h-4 w-4" />
        <span className="text-sm">Add State Field</span>
      </button>

      {/* Help text for observable */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-info/10 border border-info/20">
        <Database className="h-4 w-4 text-info mt-0.5 flex-shrink-0" />
        <div className="text-xs text-foreground-secondary">
          <strong>Observable Fields (τ²-bench):</strong> In dual-control simulations,
          observable fields are what user agents can "see" on their device. Hidden
          fields represent backend-only data (e.g., fraud scores, internal flags).
        </div>
      </div>
    </div>
  )
}

interface StateFieldRowProps {
  field: StateField
  index: number
  onChange: (updates: Partial<StateField>) => void
  onRemove: () => void
  disabled?: boolean
}

function StateFieldRow({
  field,
  index,
  onChange,
  onRemove,
  disabled = false,
}: StateFieldRowProps) {
  const isObservable = field.observable !== false

  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-all',
        isObservable
          ? 'border-border bg-background'
          : 'border-warning/30 bg-warning/5'
      )}
      data-testid={`state-field-row-${index}`}
    >
      <div className="flex items-start gap-4">
        {/* Observable toggle */}
        <button
          type="button"
          onClick={() => onChange({ observable: !isObservable })}
          disabled={disabled}
          className={cn(
            'mt-1 p-2 rounded-lg transition-colors',
            isObservable
              ? 'bg-success/10 text-success hover:bg-success/20'
              : 'bg-warning/10 text-warning hover:bg-warning/20',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          title={isObservable ? 'Click to hide from users' : 'Click to make observable'}
          data-testid={`observable-toggle-${index}`}
        >
          {isObservable ? (
            <Eye className="h-4 w-4" />
          ) : (
            <EyeOff className="h-4 w-4" />
          )}
        </button>

        {/* Field details */}
        <div className="flex-1 grid grid-cols-12 gap-3">
          {/* Name */}
          <div className="col-span-4">
            <label className="text-xs text-foreground-muted">Name</label>
            <input
              type="text"
              value={field.name}
              onChange={(e) => onChange({ name: e.target.value })}
              disabled={disabled}
              className={cn(
                'w-full mt-1 px-3 py-2 rounded-md border bg-background text-sm',
                'focus:outline-none focus:ring-2 focus:ring-primary/50',
                disabled && 'opacity-50'
              )}
              placeholder="field_name"
              data-testid={`field-name-${index}`}
            />
          </div>

          {/* Type */}
          <div className="col-span-3">
            <label className="text-xs text-foreground-muted">Type</label>
            <select
              value={field.type}
              onChange={(e) =>
                onChange({ type: e.target.value as StateField['type'] })
              }
              disabled={disabled}
              className={cn(
                'w-full mt-1 px-3 py-2 rounded-md border bg-background text-sm',
                'focus:outline-none focus:ring-2 focus:ring-primary/50',
                disabled && 'opacity-50'
              )}
              data-testid={`field-type-${index}`}
            >
              {fieldTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Default */}
          <div className="col-span-3">
            <label className="text-xs text-foreground-muted">Default</label>
            <input
              type="text"
              value={field.default?.toString() ?? ''}
              onChange={(e) => onChange({ default: e.target.value })}
              disabled={disabled}
              className={cn(
                'w-full mt-1 px-3 py-2 rounded-md border bg-background text-sm',
                'focus:outline-none focus:ring-2 focus:ring-primary/50',
                disabled && 'opacity-50'
              )}
              placeholder="default value"
              data-testid={`field-default-${index}`}
            />
          </div>

          {/* Per-agent checkbox */}
          <div className="col-span-2 flex items-end pb-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={field.per_agent !== false}
                onChange={(e) => onChange({ per_agent: e.target.checked })}
                disabled={disabled}
                className="accent-primary"
                data-testid={`field-per-agent-${index}`}
              />
              <span className="text-xs text-foreground-muted">Per-agent</span>
            </label>
          </div>
        </div>

        {/* Remove button */}
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          className={cn(
            'mt-1 p-2 rounded-lg text-foreground-muted hover:text-error hover:bg-error/10',
            'transition-colors',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          title="Remove field"
          data-testid={`remove-field-${index}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {/* Description row */}
      <div className="mt-3 ml-12">
        <input
          type="text"
          value={field.description ?? ''}
          onChange={(e) => onChange({ description: e.target.value })}
          disabled={disabled}
          className={cn(
            'w-full px-3 py-2 rounded-md border bg-background text-sm',
            'focus:outline-none focus:ring-2 focus:ring-primary/50',
            disabled && 'opacity-50'
          )}
          placeholder="Description (optional)"
          data-testid={`field-description-${index}`}
        />
      </div>

      {/* Hidden field indicator */}
      {!isObservable && (
        <div className="mt-2 ml-12 flex items-center gap-1 text-xs text-warning">
          <Lock className="h-3 w-3" />
          <span>Hidden from user agents in state-constrained mode</span>
        </div>
      )}
    </div>
  )
}

export default StateSchemaEditor
