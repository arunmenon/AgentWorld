/**
 * CoordinationAnalysis - Detailed handoff breakdown for dual-control tasks.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Shows:
 * - Individual handoff success/failure
 * - Latency analysis
 * - Communication quality metrics
 * - Failure patterns
 */

import {
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  AlertTriangle,
  MessageSquare,
  TrendingUp,
  BarChart3,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole } from '@/lib/api'

export interface HandoffResult {
  id: string
  order: number
  fromRole: AgentRole
  toRole: AgentRole
  expectedAction: string
  actualAction?: string
  success: boolean
  latencyTurns: number
  wasOptional: boolean
  instructionClarity?: number // 0-1
  userConfusionDetected: boolean
}

export interface CoordinationAnalysisProps {
  taskRunId: string
  handoffResults: HandoffResult[]
  totalTurns: number
  className?: string
}

const roleEmojis: Record<AgentRole, string> = {
  service_agent: '🎧',
  customer: '📱',
  peer: '👥',
}

function HandoffResultCard({ result }: { result: HandoffResult }) {
  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-all',
        result.success
          ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
          : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xs font-medium px-2 py-0.5 rounded',
              result.success
                ? 'bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200'
                : 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200'
            )}
          >
            #{result.order}
          </span>

          {/* From -> To */}
          <span className="text-sm flex items-center gap-1">
            <span>{roleEmojis[result.fromRole]}</span>
            <ArrowRight className="h-3 w-3 text-foreground-muted" />
            <span>{roleEmojis[result.toRole]}</span>
          </span>

          {result.wasOptional && (
            <span className="text-xs text-foreground-muted bg-background-secondary px-1.5 py-0.5 rounded">
              optional
            </span>
          )}
        </div>

        {result.success ? (
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
        ) : (
          <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
        )}
      </div>

      {/* Actions */}
      <div className="space-y-2 text-sm">
        <div className="flex items-start gap-2">
          <span className="text-foreground-muted whitespace-nowrap">Expected:</span>
          <code className="px-1.5 py-0.5 rounded bg-background text-xs">
            {result.expectedAction}
          </code>
        </div>

        {result.actualAction && result.actualAction !== result.expectedAction && (
          <div className="flex items-start gap-2">
            <span className="text-foreground-muted whitespace-nowrap">Actual:</span>
            <code
              className={cn(
                'px-1.5 py-0.5 rounded text-xs',
                result.success ? 'bg-background' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
              )}
            >
              {result.actualAction}
            </code>
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="mt-3 pt-3 border-t border-border/50 flex items-center gap-4 text-xs text-foreground-muted">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>{result.latencyTurns} turn{result.latencyTurns !== 1 ? 's' : ''}</span>
        </div>

        {result.instructionClarity !== undefined && (
          <div className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3" />
            <span>Clarity: {Math.round(result.instructionClarity * 100)}%</span>
          </div>
        )}

        {result.userConfusionDetected && (
          <div className="flex items-center gap-1 text-warning">
            <AlertTriangle className="h-3 w-3" />
            <span>Confusion detected</span>
          </div>
        )}
      </div>
    </div>
  )
}

function SummaryStats({ handoffResults }: { handoffResults: HandoffResult[] }) {
  const total = handoffResults.length
  const successful = handoffResults.filter((h) => h.success).length
  const avgLatency = total > 0
    ? handoffResults.reduce((sum, h) => sum + h.latencyTurns, 0) / total
    : 0
  const confusionCount = handoffResults.filter((h) => h.userConfusionDetected).length
  const avgClarity = handoffResults.filter((h) => h.instructionClarity !== undefined).length > 0
    ? handoffResults
        .filter((h) => h.instructionClarity !== undefined)
        .reduce((sum, h) => sum + (h.instructionClarity || 0), 0) /
      handoffResults.filter((h) => h.instructionClarity !== undefined).length
    : null

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="p-4 rounded-lg bg-background border border-border">
        <div className="text-sm text-foreground-muted mb-1">Success Rate</div>
        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
          {total > 0 ? Math.round((successful / total) * 100) : 0}%
        </div>
        <div className="text-xs text-foreground-muted mt-1">
          {successful}/{total} handoffs
        </div>
      </div>

      <div className="p-4 rounded-lg bg-background border border-border">
        <div className="text-sm text-foreground-muted mb-1">Avg Latency</div>
        <div className="text-2xl font-bold">
          {avgLatency.toFixed(1)}
        </div>
        <div className="text-xs text-foreground-muted mt-1">
          turns per handoff
        </div>
      </div>

      <div className="p-4 rounded-lg bg-background border border-border">
        <div className="text-sm text-foreground-muted mb-1">Confusion Events</div>
        <div className="text-2xl font-bold text-warning">
          {confusionCount}
        </div>
        <div className="text-xs text-foreground-muted mt-1">
          detected instances
        </div>
      </div>

      <div className="p-4 rounded-lg bg-background border border-border">
        <div className="text-sm text-foreground-muted mb-1">Instruction Clarity</div>
        <div className="text-2xl font-bold">
          {avgClarity !== null ? `${Math.round(avgClarity * 100)}%` : 'N/A'}
        </div>
        <div className="text-xs text-foreground-muted mt-1">
          average score
        </div>
      </div>
    </div>
  )
}

function LatencyDistribution({ handoffResults }: { handoffResults: HandoffResult[] }) {
  // Group by latency buckets
  const buckets = [
    { label: '1 turn', min: 0, max: 1 },
    { label: '2-3 turns', min: 2, max: 3 },
    { label: '4-5 turns', min: 4, max: 5 },
    { label: '6+ turns', min: 6, max: Infinity },
  ]

  const distribution = buckets.map((bucket) => ({
    ...bucket,
    count: handoffResults.filter(
      (h) => h.latencyTurns >= bucket.min && h.latencyTurns <= bucket.max
    ).length,
  }))

  const maxCount = Math.max(...distribution.map((d) => d.count), 1)

  return (
    <div className="p-4 rounded-lg bg-background border border-border">
      <div className="text-sm text-foreground-muted mb-3 flex items-center gap-2">
        <BarChart3 className="h-4 w-4" />
        Latency Distribution
      </div>

      <div className="space-y-2">
        {distribution.map((bucket) => (
          <div key={bucket.label} className="flex items-center gap-3">
            <span className="w-20 text-xs text-foreground-muted">{bucket.label}</span>
            <div className="flex-1 h-4 bg-background-secondary rounded overflow-hidden">
              <div
                className="h-full bg-primary rounded transition-all"
                style={{ width: `${(bucket.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="w-8 text-xs text-right">{bucket.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function FailurePatterns({ handoffResults }: { handoffResults: HandoffResult[] }) {
  const failures = handoffResults.filter((h) => !h.success)

  if (failures.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
        <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
          <CheckCircle2 className="h-5 w-5" />
          <span className="font-medium">All handoffs successful!</span>
        </div>
        <p className="text-sm text-green-600 dark:text-green-500 mt-1">
          No failure patterns to analyze.
        </p>
      </div>
    )
  }

  // Analyze failure patterns
  const wrongAction = failures.filter((f) => f.actualAction && f.actualAction !== f.expectedAction)
  const noAction = failures.filter((f) => !f.actualAction)
  const withConfusion = failures.filter((f) => f.userConfusionDetected)

  return (
    <div className="p-4 rounded-lg bg-background border border-border">
      <div className="text-sm text-foreground-muted mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        Failure Patterns ({failures.length} failures)
      </div>

      <div className="space-y-3">
        {wrongAction.length > 0 && (
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 mt-1.5" />
            <div>
              <div className="text-sm font-medium">Wrong Action ({wrongAction.length})</div>
              <p className="text-xs text-foreground-muted">
                User performed a different action than expected
              </p>
            </div>
          </div>
        )}

        {noAction.length > 0 && (
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 rounded-full bg-orange-500 mt-1.5" />
            <div>
              <div className="text-sm font-medium">No Action ({noAction.length})</div>
              <p className="text-xs text-foreground-muted">
                User did not perform the expected action
              </p>
            </div>
          </div>
        )}

        {withConfusion.length > 0 && (
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500 mt-1.5" />
            <div>
              <div className="text-sm font-medium">With Confusion ({withConfusion.length})</div>
              <p className="text-xs text-foreground-muted">
                User showed signs of confusion before failing
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function CoordinationAnalysis({
  taskRunId,
  handoffResults,
  totalTurns,
  className,
}: CoordinationAnalysisProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Coordination Analysis
        </h2>
        <p className="text-sm text-foreground-muted mt-0.5">
          Run {taskRunId} • {handoffResults.length} handoffs • {totalTurns} total turns
        </p>
      </div>

      {/* Summary Stats */}
      <SummaryStats handoffResults={handoffResults} />

      {/* Analysis Cards */}
      <div className="grid grid-cols-2 gap-4">
        <LatencyDistribution handoffResults={handoffResults} />
        <FailurePatterns handoffResults={handoffResults} />
      </div>

      {/* Individual Handoff Results */}
      <div>
        <h3 className="font-medium mb-3">Handoff Timeline</h3>
        <div className="space-y-3">
          {handoffResults.map((result) => (
            <HandoffResultCard key={result.id} result={result} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default CoordinationAnalysis
