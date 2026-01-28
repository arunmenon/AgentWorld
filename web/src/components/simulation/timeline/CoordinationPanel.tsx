/**
 * CoordinationPanel - Metrics sidebar for coordination tracking.
 *
 * Per ADR-020.1 and UI-WIREFRAMES-DUAL-CONTROL.md Section 3.1
 *
 * Shows:
 * - Handoffs (required, completed, success rate)
 * - Efficiency (avg latency, extra actions)
 * - Communication quality (clarity, confusion)
 */

import {
  ArrowRightLeft,
  Clock,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface CoordinationMetrics {
  // Handoffs
  totalHandoffsRequired: number
  handoffsCompleted: number
  coordinationSuccessRate: number

  // Efficiency
  avgInstructionToActionTurns: number
  unnecessaryUserActions: number

  // Communication quality
  instructionClarityScore?: number // 0-1, LLM-judged
  userConfusionCount: number
}

interface CoordinationPanelProps {
  metrics: CoordinationMetrics
  className?: string
}

function MetricCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-foreground-secondary">{title}</h4>
      <div className="p-3 rounded-lg bg-background-secondary/50 border border-border">
        {children}
      </div>
    </div>
  )
}

function ProgressBar({
  value,
  max = 100,
  color = 'primary',
}: {
  value: number
  max?: number
  color?: 'primary' | 'success' | 'warning' | 'error'
}) {
  const percentage = Math.min((value / max) * 100, 100)
  const colorClasses = {
    primary: 'bg-primary',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  }

  return (
    <div className="h-2 bg-background-secondary rounded-full overflow-hidden">
      <div
        className={cn('h-full rounded-full transition-all', colorClasses[color])}
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}

export function CoordinationPanel({
  metrics,
  className,
}: CoordinationPanelProps) {
  const successPercentage = Math.round(metrics.coordinationSuccessRate * 100)

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <ArrowRightLeft className="h-4 w-4 text-foreground-secondary" />
        <h3 className="font-medium">COORDINATION METRICS</h3>
      </div>

      {/* Handoffs */}
      <MetricCard title="Handoffs">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-foreground-muted">Required:</span>
            <span className="font-medium">{metrics.totalHandoffsRequired}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-foreground-muted">Completed:</span>
            <span className="font-medium flex items-center gap-1">
              {metrics.handoffsCompleted}
              {metrics.handoffsCompleted === metrics.totalHandoffsRequired && (
                <CheckCircle2 className="h-3 w-3 text-green-500" />
              )}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-foreground-muted">Success:</span>
            <span className="font-medium">{successPercentage}%</span>
          </div>
        </div>
      </MetricCard>

      {/* Efficiency */}
      <MetricCard title="Efficiency">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-3 w-3 text-foreground-muted" />
            <span className="text-foreground-muted">Avg Latency:</span>
            <span className="font-medium">
              {metrics.avgInstructionToActionTurns.toFixed(1)} turns
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-3 w-3 text-foreground-muted" />
            <span className="text-foreground-muted">Extra Actions:</span>
            <span className="font-medium">
              {metrics.unnecessaryUserActions}
            </span>
          </div>
        </div>
      </MetricCard>

      {/* Communication */}
      <MetricCard title="Communication">
        {metrics.instructionClarityScore !== undefined ? (
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-foreground-muted flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Clarity:
                </span>
                <span className="font-medium">
                  {Math.round(metrics.instructionClarityScore * 100)}%
                </span>
              </div>
              <ProgressBar
                value={metrics.instructionClarityScore * 100}
                color={
                  metrics.instructionClarityScore >= 0.8
                    ? 'success'
                    : metrics.instructionClarityScore >= 0.6
                    ? 'warning'
                    : 'error'
                }
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <MessageSquare className="h-3 w-3 text-foreground-muted" />
              <span className="text-foreground-muted">Confusion:</span>
              <span className="font-medium">{metrics.userConfusionCount}</span>
            </div>
          </div>
        ) : (
          <div className="text-sm text-foreground-muted text-center py-2">
            Clarity scoring not available
          </div>
        )}
      </MetricCard>
    </div>
  )
}

/**
 * CoordinationSummary - Compact summary for task cards.
 */
interface CoordinationSummaryProps {
  metrics: CoordinationMetrics
  className?: string
}

export function CoordinationSummary({
  metrics,
  className,
}: CoordinationSummaryProps) {
  const successPercentage = Math.round(metrics.coordinationSuccessRate * 100)

  return (
    <div className={cn('flex items-center gap-4 text-sm', className)}>
      <div className="flex items-center gap-1">
        <ArrowRightLeft className="h-3 w-3 text-foreground-muted" />
        <span className="text-foreground-muted">Handoffs:</span>
        <span className="font-medium">
          {metrics.handoffsCompleted}/{metrics.totalHandoffsRequired}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <TrendingUp className="h-3 w-3 text-foreground-muted" />
        <span className="text-foreground-muted">Success:</span>
        <span
          className={cn(
            'font-medium',
            successPercentage >= 80
              ? 'text-green-500'
              : successPercentage >= 50
              ? 'text-yellow-500'
              : 'text-red-500'
          )}
        >
          {successPercentage}%
        </span>
      </div>
    </div>
  )
}
