/**
 * CoordinationMarker - Badge showing coordination handoff status.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 3.1
 *
 * States:
 * - requested: Agent has given instruction, awaiting user action
 * - complete: User successfully performed the expected action
 * - failed: User did not perform expected action or performed wrong action
 */

import { Target, CheckCircle2, XCircle, ArrowRight, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole } from '@/components/app-studio/access'

type CoordinationType = 'requested' | 'complete' | 'failed'

interface CoordinationMarkerProps {
  type: CoordinationType
  from: { id: string; role: AgentRole }
  to: { id: string; role: AgentRole }
  expectedAction: string
  actualAction?: string
  latency?: number // turns between instruction and action
  className?: string
  expanded?: boolean
  onToggleExpand?: () => void
}

const typeConfig = {
  requested: {
    icon: Target,
    label: 'COORDINATION REQUESTED',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    borderColor: 'border-yellow-300 dark:border-yellow-700',
    textColor: 'text-yellow-700 dark:text-yellow-400',
    status: 'Awaiting response',
    statusIcon: Clock,
  },
  complete: {
    icon: CheckCircle2,
    label: 'COORDINATION COMPLETE',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    borderColor: 'border-green-300 dark:border-green-700',
    textColor: 'text-green-700 dark:text-green-400',
    status: 'successful',
    statusIcon: CheckCircle2,
  },
  failed: {
    icon: XCircle,
    label: 'COORDINATION FAILED',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    borderColor: 'border-red-300 dark:border-red-700',
    textColor: 'text-red-700 dark:text-red-400',
    status: 'failed',
    statusIcon: XCircle,
  },
}

const roleIcons: Record<AgentRole, string> = {
  service_agent: '🎧',
  customer: '📱',
  peer: '👥',
}

export function CoordinationMarker({
  type,
  from,
  to,
  expectedAction,
  actualAction,
  latency,
  className,
  expanded = false,
  onToggleExpand,
}: CoordinationMarkerProps) {
  const config = typeConfig[type]
  const Icon = config.icon
  const StatusIcon = config.statusIcon

  return (
    <div
      className={cn(
        'rounded-lg border p-3',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center gap-2 cursor-pointer',
          config.textColor
        )}
        onClick={onToggleExpand}
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="font-medium text-sm">{config.label}</span>
      </div>

      {/* Divider */}
      <div
        className={cn(
          'border-t my-2',
          type === 'requested'
            ? 'border-yellow-200 dark:border-yellow-800'
            : type === 'complete'
            ? 'border-green-200 dark:border-green-800'
            : 'border-red-200 dark:border-red-800'
        )}
      />

      {/* Content */}
      <div className="space-y-2 text-sm">
        {/* From -> To */}
        <div className="flex items-center gap-2 text-foreground-secondary">
          <span>
            {roleIcons[from.role]} {from.id}
          </span>
          <ArrowRight className="h-3 w-3" />
          <span>
            {roleIcons[to.role]} {to.id}
          </span>
        </div>

        {/* Expected Action */}
        <div className="text-foreground-secondary">
          <span className="text-foreground-muted">Expected: </span>
          <code className="text-xs bg-background-secondary px-1 py-0.5 rounded">
            {expectedAction}
          </code>
        </div>

        {/* Status */}
        <div className={cn('flex items-center gap-1', config.textColor)}>
          <StatusIcon className="h-3 w-3" />
          <span>
            {type === 'requested'
              ? config.status
              : `Handoff ${config.status}`}
          </span>
          {latency !== undefined && type !== 'requested' && (
            <span className="text-foreground-muted ml-2">
              ({latency} turn{latency !== 1 ? 's' : ''})
            </span>
          )}
        </div>

        {/* Actual Action (for failed) */}
        {type === 'failed' && actualAction && (
          <div className="text-foreground-secondary">
            <span className="text-foreground-muted">Actual: </span>
            <code className="text-xs bg-background-secondary px-1 py-0.5 rounded text-red-600 dark:text-red-400">
              {actualAction}
            </code>
            <span className="text-foreground-muted ml-1">← WRONG ACTION</span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * CoordinationMarkerCompact - Inline badge version for list views.
 */
interface CoordinationMarkerCompactProps {
  type: CoordinationType
  handoffId?: string
  latency?: number
  className?: string
}

export function CoordinationMarkerCompact({
  type,
  handoffId,
  latency,
  className,
}: CoordinationMarkerCompactProps) {
  const config = typeConfig[type]
  const Icon = config.icon

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium',
        config.bgColor,
        config.textColor,
        className
      )}
      title={`${config.label}${handoffId ? `: ${handoffId}` : ''}`}
    >
      <Icon className="h-3 w-3" />
      <span>
        {type === 'requested' ? '🎯' : type === 'complete' ? '✅' : '❌'}
      </span>
      {latency !== undefined && (
        <span className="text-foreground-muted">({latency}t)</span>
      )}
    </span>
  )
}
