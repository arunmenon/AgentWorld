/**
 * AccessTypeSelector - Radio group for app access type selection.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 1.1
 *
 * Options:
 * - Shared (default): All agents can access
 * - Role-Restricted: Only specific roles can access
 * - Per-Agent Instance: Each agent gets own instance
 */

import { HelpCircle, Users, Lock, User } from 'lucide-react'
import { cn } from '@/lib/utils'

export type AccessType = 'shared' | 'role_restricted' | 'per_agent'

interface AccessTypeSelectorProps {
  value: AccessType
  onChange: (value: AccessType) => void
  disabled?: boolean
  className?: string
}

interface AccessOption {
  value: AccessType
  icon: React.ReactNode
  label: string
  description: string
  bestFor: string
}

const accessOptions: AccessOption[] = [
  {
    value: 'shared',
    icon: <Users className="h-5 w-5" />,
    label: 'Shared (Default)',
    description: 'All agents in the simulation can access this app.',
    bestFor: 'Chat systems, shared resources',
  },
  {
    value: 'role_restricted',
    icon: <Lock className="h-5 w-5" />,
    label: 'Role-Restricted',
    description: 'Only agents with specific roles can access this app.',
    bestFor: 'Backend systems, admin tools',
  },
  {
    value: 'per_agent',
    icon: <User className="h-5 w-5" />,
    label: 'Per-Agent Instance',
    description: 'Each agent gets their own isolated copy of this app.',
    bestFor: 'Personal devices, individual accounts',
  },
]

export function AccessTypeSelector({
  value,
  onChange,
  disabled = false,
  className,
}: AccessTypeSelectorProps) {
  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Who can access this app?</h3>
        <button
          type="button"
          className="text-foreground-muted hover:text-foreground-secondary"
          title="Learn about access types"
        >
          <HelpCircle className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-2">
        {accessOptions.map((option) => (
          <label
            key={option.value}
            className={cn(
              'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all',
              value === option.value
                ? 'border-primary bg-primary/5 ring-1 ring-primary'
                : 'border-border hover:border-primary/40',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input
              type="radio"
              name="access_type"
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              disabled={disabled}
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
              <p className="text-xs text-foreground-muted mt-1">
                <span className="text-foreground-secondary">Best for:</span>{' '}
                {option.bestFor}
              </p>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
