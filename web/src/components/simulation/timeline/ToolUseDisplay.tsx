/**
 * ToolUseDisplay - Shows app/tool actions in the conversation timeline.
 *
 * Per ADR-020.1 Phase 10h-7: UI - Runtime Coordination
 *
 * Displays:
 * - App icon and name
 * - Action being performed
 * - Parameters (collapsible)
 * - Result status (success/error)
 * - Result data (collapsible)
 */

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Loader2,
  Play,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole } from '@/lib/api'

export type ToolUseStatus = 'pending' | 'success' | 'error'

export interface ToolUseDisplayProps {
  /** Name of the agent using the tool */
  agentName: string
  /** Role of the agent (for styling) */
  agentRole?: AgentRole
  /** App identifier */
  appId: string
  /** App display name */
  appName?: string
  /** App icon emoji */
  appIcon?: string
  /** Action being performed */
  action: string
  /** Action parameters */
  params?: Record<string, unknown>
  /** Execution status */
  status: ToolUseStatus
  /** Result data on success */
  result?: Record<string, unknown>
  /** Error message on failure */
  error?: string
  /** Simulation step number */
  step?: number
  /** Timestamp */
  timestamp?: Date | string
  /** Additional class names */
  className?: string
}

const statusConfig = {
  pending: {
    icon: Loader2,
    label: 'Executing...',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    textColor: 'text-blue-600 dark:text-blue-400',
    animate: true,
  },
  success: {
    icon: CheckCircle2,
    label: 'Success',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    borderColor: 'border-green-200 dark:border-green-800',
    textColor: 'text-green-600 dark:text-green-400',
    animate: false,
  },
  error: {
    icon: XCircle,
    label: 'Failed',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-800',
    textColor: 'text-red-600 dark:text-red-400',
    animate: false,
  },
}

const roleColors: Record<AgentRole, string> = {
  service_agent: 'text-purple-600 dark:text-purple-400',
  customer: 'text-green-600 dark:text-green-400',
  peer: 'text-blue-600 dark:text-blue-400',
}

const roleEmojis: Record<AgentRole, string> = {
  service_agent: '🎧',
  customer: '📱',
  peer: '👥',
}

function formatTimestamp(timestamp: Date | string): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function JsonPreview({ data, maxLength = 100 }: { data: unknown; maxLength?: number }) {
  const str = JSON.stringify(data, null, 2)
  if (str.length <= maxLength) {
    return <code className="text-xs">{str}</code>
  }
  return <code className="text-xs">{str.slice(0, maxLength)}...</code>
}

export function ToolUseDisplay({
  agentName,
  agentRole = 'peer',
  appId,
  appName,
  appIcon = '🔧',
  action,
  params,
  status,
  result,
  error,
  step,
  timestamp,
  className,
}: ToolUseDisplayProps) {
  const [showParams, setShowParams] = useState(false)
  const [showResult, setShowResult] = useState(false)

  const config = statusConfig[status]
  const StatusIcon = config.icon
  const hasParams = params && Object.keys(params).length > 0
  const hasResult = result && Object.keys(result).length > 0

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
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Play className="h-3 w-3 text-foreground-muted" />
          <span className={cn('text-sm font-medium', roleColors[agentRole])}>
            {roleEmojis[agentRole]} {agentName}
          </span>
          <span className="text-foreground-muted text-sm">→</span>
          <span className="text-sm">
            {appIcon} {appName || appId}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-foreground-muted">
          {step !== undefined && <span>Step {step}</span>}
          {timestamp && <span>{formatTimestamp(timestamp)}</span>}
        </div>
      </div>

      {/* Action */}
      <div className="flex items-center gap-2 mb-2">
        <code className="px-2 py-1 rounded bg-background text-sm font-mono">
          {action}
        </code>
        <div className={cn('flex items-center gap-1', config.textColor)}>
          <StatusIcon
            className={cn('h-4 w-4', config.animate && 'animate-spin')}
          />
          <span className="text-xs font-medium">{config.label}</span>
        </div>
      </div>

      {/* Parameters (collapsible) */}
      {hasParams && (
        <div className="mt-2">
          <button
            onClick={() => setShowParams(!showParams)}
            className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground-secondary transition-colors"
          >
            {showParams ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
            <span>Parameters</span>
            {!showParams && (
              <span className="text-foreground-muted ml-1">
                ({Object.keys(params).length})
              </span>
            )}
          </button>
          {showParams && (
            <div className="mt-1 p-2 rounded bg-background text-foreground-secondary">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(params, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Result (collapsible) */}
      {status === 'success' && hasResult && (
        <div className="mt-2">
          <button
            onClick={() => setShowResult(!showResult)}
            className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground-secondary transition-colors"
          >
            {showResult ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
            <span>Result</span>
            {!showResult && (
              <span className="ml-1">
                <JsonPreview data={result} maxLength={50} />
              </span>
            )}
          </button>
          {showResult && (
            <div className="mt-1 p-2 rounded bg-background text-foreground-secondary">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Error message */}
      {status === 'error' && error && (
        <div className="mt-2 p-2 rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs">
          {error}
        </div>
      )}
    </div>
  )
}

/**
 * ToolUseDisplayCompact - Inline version for message integration.
 */
export interface ToolUseDisplayCompactProps {
  appIcon?: string
  appName: string
  action: string
  status: ToolUseStatus
  className?: string
}

export function ToolUseDisplayCompact({
  appIcon = '🔧',
  appName,
  action,
  status,
  className,
}: ToolUseDisplayCompactProps) {
  const config = statusConfig[status]
  const StatusIcon = config.icon

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs',
        config.bgColor,
        className
      )}
      title={`${appName}: ${action}`}
    >
      <span>{appIcon}</span>
      <code className="font-mono">{action}</code>
      <StatusIcon
        className={cn('h-3 w-3', config.textColor, config.animate && 'animate-spin')}
      />
    </span>
  )
}

export default ToolUseDisplay
