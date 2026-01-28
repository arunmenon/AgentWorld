/**
 * ToolTypeBadge - Badge component showing action tool type.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 1.2
 *
 * - READ: Query only, no modifications (blue/gray)
 * - WRITE: Modifies state (orange)
 */

import { BookOpen, Pencil } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToolType = 'read' | 'write'

interface ToolTypeBadgeProps {
  type: ToolType
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5 gap-1',
  md: 'text-sm px-2 py-1 gap-1.5',
  lg: 'text-base px-3 py-1.5 gap-2',
}

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
}

export function ToolTypeBadge({
  type,
  showLabel = true,
  size = 'md',
  className,
}: ToolTypeBadgeProps) {
  const isRead = type === 'read'

  return (
    <span
      className={cn(
        'inline-flex items-center rounded font-medium',
        sizeClasses[size],
        isRead
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
          : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
        className
      )}
      title={isRead ? 'Query only, no modifications' : 'Modifies state'}
    >
      {isRead ? (
        <BookOpen className={iconSizes[size]} />
      ) : (
        <Pencil className={iconSizes[size]} />
      )}
      {showLabel && <span>{isRead ? 'READ' : 'WRITE'}</span>}
    </span>
  )
}

/**
 * ToolTypeSelector - Dropdown for selecting tool type.
 *
 * Per UI-WIREFRAMES-DUAL-CONTROL.md Section 1.3
 */

interface ToolTypeSelectorProps {
  value: ToolType
  onChange: (value: ToolType) => void
  disabled?: boolean
  className?: string
}

export function ToolTypeSelector({
  value,
  onChange,
  disabled = false,
  className,
}: ToolTypeSelectorProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <label className="text-sm font-medium">Tool Type</label>

      <div className="space-y-2">
        <label
          className={cn(
            'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all',
            value === 'read'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/40',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <input
            type="radio"
            name="tool_type"
            value="read"
            checked={value === 'read'}
            onChange={() => onChange('read')}
            disabled={disabled}
            className="mt-0.5 accent-primary"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <ToolTypeBadge type="read" size="sm" />
            </div>
            <p className="text-xs text-foreground-muted mt-1">
              This action only queries/reads data
            </p>
            <p className="text-xs text-foreground-muted">
              Example: get_balance, search_products, view_history
            </p>
          </div>
        </label>

        <label
          className={cn(
            'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all',
            value === 'write'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/40',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <input
            type="radio"
            name="tool_type"
            value="write"
            checked={value === 'write'}
            onChange={() => onChange('write')}
            disabled={disabled}
            className="mt-0.5 accent-primary"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <ToolTypeBadge type="write" size="sm" />
            </div>
            <p className="text-xs text-foreground-muted mt-1">
              This action creates, updates, or deletes data
            </p>
            <p className="text-xs text-foreground-muted">
              Example: transfer_money, add_to_cart, send_message
            </p>
          </div>
        </label>
      </div>
    </div>
  )
}
