/**
 * RoleSelector - Dropdown for selecting agent role in simulation setup.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 2.1
 *
 * Roles:
 * - Peer (default): Equal access to shared apps
 * - Service Agent: Backend system access, guides users
 * - Customer: Device access, follows instructions
 */

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, HelpCircle, Headphones, Smartphone, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

export type AgentRole = 'peer' | 'service_agent' | 'customer'

interface RoleSelectorProps {
  value: AgentRole
  onChange: (role: AgentRole) => void
  disabled?: boolean
  showHelp?: boolean
  className?: string
}

interface RoleOption {
  value: AgentRole
  icon: React.ReactNode
  emoji: string
  label: string
  description: string
}

const roleOptions: RoleOption[] = [
  {
    value: 'peer',
    icon: <Users className="h-4 w-4" />,
    emoji: '👥',
    label: 'Peer (default)',
    description: 'Equal access to shared apps',
  },
  {
    value: 'service_agent',
    icon: <Headphones className="h-4 w-4" />,
    emoji: '🎧',
    label: 'Service Agent',
    description: 'Backend system access, guides users',
  },
  {
    value: 'customer',
    icon: <Smartphone className="h-4 w-4" />,
    emoji: '📱',
    label: 'Customer',
    description: 'Device access, follows instructions',
  },
]

export function RoleSelector({
  value,
  onChange,
  disabled = false,
  showHelp = true,
  className,
}: RoleSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const selectedRole = roleOptions.find((r) => r.value === value) || roleOptions[0]

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Role</label>
        {showHelp && (
          <button
            type="button"
            className="text-foreground-muted hover:text-foreground-secondary"
            title="Learn about agent roles"
          >
            <HelpCircle className="h-4 w-4" />
          </button>
        )}
      </div>

      <div ref={dropdownRef} className="relative">
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={cn(
            'w-full flex items-center justify-between gap-2 px-3 py-2',
            'border border-border rounded-lg bg-background',
            'text-left transition-colors',
            disabled
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:border-primary/40 focus:border-primary focus:ring-1 focus:ring-primary',
            isOpen && 'border-primary ring-1 ring-primary'
          )}
        >
          <div className="flex items-center gap-2">
            <span>{selectedRole.emoji}</span>
            <span className="font-medium">{selectedRole.label}</span>
          </div>
          <ChevronDown
            className={cn(
              'h-4 w-4 text-foreground-muted transition-transform',
              isOpen && 'rotate-180'
            )}
          />
        </button>

        {isOpen && (
          <div className="absolute z-50 w-full mt-1 py-1 bg-background border border-border rounded-lg shadow-lg">
            {roleOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value)
                  setIsOpen(false)
                }}
                className={cn(
                  'w-full flex items-start gap-3 px-3 py-2 text-left transition-colors',
                  option.value === value
                    ? 'bg-primary/10'
                    : 'hover:bg-background-secondary'
                )}
              >
                <span className="text-lg">{option.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{option.label}</span>
                    {option.value === value && (
                      <span className="text-xs text-primary">✓</span>
                    )}
                  </div>
                  <p className="text-xs text-foreground-muted mt-0.5">
                    {option.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * RoleBadge - Inline badge showing agent role.
 */
interface RoleBadgeProps {
  role: AgentRole
  size?: 'sm' | 'md'
  className?: string
}

export function RoleBadge({ role, size = 'md', className }: RoleBadgeProps) {
  const option = roleOptions.find((r) => r.value === role) || roleOptions[0]

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
  }

  const colorClasses = {
    peer: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    service_agent:
      'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    customer:
      'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded font-medium',
        sizeClasses[size],
        colorClasses[role],
        className
      )}
    >
      <span>{option.emoji}</span>
      <span>{option.label.replace(' (default)', '')}</span>
    </span>
  )
}
