/**
 * RoleCheckboxes - Checkbox group for selecting allowed roles.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 1.1
 *
 * Only shown when access_type is 'role_restricted'.
 * Allows selecting which roles can access the app.
 */

import { Headphones, Smartphone, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

export type AgentRole = 'peer' | 'service_agent' | 'customer'

interface RoleCheckboxesProps {
  value: AgentRole[]
  onChange: (value: AgentRole[]) => void
  disabled?: boolean
  className?: string
}

interface RoleOption {
  value: AgentRole
  icon: React.ReactNode
  label: string
  description: string
}

const roleOptions: RoleOption[] = [
  {
    value: 'service_agent',
    icon: <Headphones className="h-5 w-5" />,
    label: 'Service Agent',
    description: 'Support staff, backend operators',
  },
  {
    value: 'customer',
    icon: <Smartphone className="h-5 w-5" />,
    label: 'Customer',
    description: 'End users, clients',
  },
  {
    value: 'peer',
    icon: <Users className="h-5 w-5" />,
    label: 'Peer',
    description: 'Equal participants (default role)',
  },
]

export function RoleCheckboxes({
  value,
  onChange,
  disabled = false,
  className,
}: RoleCheckboxesProps) {
  const handleToggle = (role: AgentRole) => {
    if (value.includes(role)) {
      onChange(value.filter((r) => r !== role))
    } else {
      onChange([...value, role])
    }
  }

  return (
    <div
      className={cn(
        'p-4 rounded-lg border border-border bg-background-secondary/50',
        disabled && 'opacity-50',
        className
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🔒</span>
        <h4 className="text-sm font-medium">Role-Restricted Options</h4>
      </div>

      <p className="text-sm text-foreground-muted mb-4">
        Which roles can access this app?
      </p>

      <div className="space-y-2">
        {roleOptions.map((option) => (
          <label
            key={option.value}
            className={cn(
              'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all',
              value.includes(option.value)
                ? 'bg-primary/10'
                : 'hover:bg-background-secondary',
              disabled && 'cursor-not-allowed'
            )}
          >
            <input
              type="checkbox"
              checked={value.includes(option.value)}
              onChange={() => handleToggle(option.value)}
              disabled={disabled}
              className="mt-0.5 accent-primary"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-foreground-secondary">{option.icon}</span>
                <span className="font-medium text-sm">{option.label}</span>
              </div>
              <p className="text-xs text-foreground-muted mt-0.5">
                {option.description}
              </p>
            </div>
          </label>
        ))}
      </div>

      {value.length === 0 && (
        <p className="text-xs text-warning mt-3">
          Select at least one role to access this app.
        </p>
      )}
    </div>
  )
}
