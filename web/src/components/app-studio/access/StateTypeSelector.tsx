/**
 * StateTypeSelector - Radio group for app state management selection.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 1.1
 *
 * Options:
 * - Shared State: All agents share a single state
 * - Per-Agent State: Each agent has isolated state
 *
 * GATING RULE: If access_type is 'per_agent', this is forced to 'per_agent'.
 */

import { Globe, User, HelpCircle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AccessType } from './AccessTypeSelector'

export type StateType = 'shared' | 'per_agent'

interface StateTypeSelectorProps {
  value: StateType
  onChange: (value: StateType) => void
  accessType: AccessType // For gating logic
  disabled?: boolean
  className?: string
}

interface StateOption {
  value: StateType
  icon: React.ReactNode
  label: string
  description: string
}

const stateOptions: StateOption[] = [
  {
    value: 'shared',
    icon: <Globe className="h-5 w-5" />,
    label: 'Shared State',
    description:
      'Single state shared by all agents (e.g., customer DB). Changes by one agent are visible to all.',
  },
  {
    value: 'per_agent',
    icon: <User className="h-5 w-5" />,
    label: 'Per-Agent State',
    description:
      "Each agent has isolated state (e.g., personal device). Agent A's changes don't affect Agent B's state.",
  },
]

export function StateTypeSelector({
  value,
  onChange,
  accessType,
  disabled = false,
  className,
}: StateTypeSelectorProps) {
  // Gating rule: per_agent access forces per_agent state
  const isForced = accessType === 'per_agent'
  const effectiveValue = isForced ? 'per_agent' : value
  const isDisabled = disabled || isForced

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">How should app state be managed?</h3>
        <button
          type="button"
          className="text-foreground-muted hover:text-foreground-secondary"
          title="Learn about state types"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-2">
        {stateOptions.map((option) => {
          const isSelected = effectiveValue === option.value
          const isOptionDisabled =
            isDisabled || (isForced && option.value !== 'per_agent')

          return (
            <label
              key={option.value}
              className={cn(
                'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all',
                isSelected
                  ? 'border-primary bg-primary/5 ring-1 ring-primary'
                  : 'border-border hover:border-primary/40',
                isOptionDisabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input
                type="radio"
                name="state_type"
                value={option.value}
                checked={isSelected}
                onChange={() => onChange(option.value)}
                disabled={isOptionDisabled}
                className="mt-1 accent-primary"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-foreground-secondary">{option.icon}</span>
                  <span className="font-medium">{option.label}</span>
                </div>
                <p className="text-sm text-foreground-muted mt-1">
                  {option.description}
                </p>
              </div>
            </label>
          )
        })}
      </div>

      {isForced && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-info/10 border border-info/20">
          <AlertCircle className="h-4 w-4 text-info mt-0.5 flex-shrink-0" />
          <p className="text-xs text-foreground-secondary">
            <strong>GATING RULE:</strong> If "Per-Agent Instance" is selected
            above, this selector is disabled and forced to "Per-Agent State".
          </p>
        </div>
      )}
    </div>
  )
}
