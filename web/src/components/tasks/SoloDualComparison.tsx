/**
 * SoloDualComparison - Compare solo vs dual-control task performance.
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Shows side-by-side comparison of:
 * - Success rates (pass^k metrics)
 * - Step counts
 * - Error categories
 * - Efficiency metrics
 */

import {
  TrendingUp,
  TrendingDown,
  Minus,
  User,
  Users,
  AlertTriangle,
  Target,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface TaskRunResult {
  taskId: string
  mode: 'solo' | 'dual'
  success: boolean
  steps: number
  maxSteps: number
  handoffsCompleted?: number
  handoffsRequired?: number
  errorCategory?: 'reasoning' | 'communication' | 'execution' | null
  goalConditionsMet: number
  goalConditionsTotal: number
  executionTimeMs?: number
}

export interface SoloDualComparisonProps {
  taskName: string
  soloRuns: TaskRunResult[]
  dualRuns: TaskRunResult[]
  className?: string
}

interface MetricCardProps {
  label: string
  soloValue: string | number
  dualValue: string | number
  unit?: string
  higherIsBetter?: boolean
  showTrend?: boolean
}

function MetricCard({
  label,
  soloValue,
  dualValue,
  unit = '',
  higherIsBetter = true,
  showTrend = true,
}: MetricCardProps) {
  const soloNum = typeof soloValue === 'number' ? soloValue : parseFloat(soloValue) || 0
  const dualNum = typeof dualValue === 'number' ? dualValue : parseFloat(dualValue) || 0
  const diff = dualNum - soloNum
  const percentDiff = soloNum !== 0 ? ((diff / soloNum) * 100) : 0

  const isBetter = higherIsBetter ? diff > 0 : diff < 0
  const isEqual = Math.abs(diff) < 0.001

  return (
    <div className="p-4 rounded-lg border border-border bg-background">
      <div className="text-sm text-foreground-muted mb-3">{label}</div>

      <div className="grid grid-cols-3 gap-4">
        {/* Solo */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-foreground-muted mb-1">
            <User className="h-3 w-3" />
            <span className="text-xs">Solo</span>
          </div>
          <div className="text-2xl font-bold">
            {soloValue}
            {unit && <span className="text-sm font-normal text-foreground-muted">{unit}</span>}
          </div>
        </div>

        {/* Trend indicator */}
        {showTrend && (
          <div className="flex flex-col items-center justify-center">
            {isEqual ? (
              <Minus className="h-5 w-5 text-foreground-muted" />
            ) : isBetter ? (
              <TrendingUp className="h-5 w-5 text-green-500" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-500" />
            )}
            {!isEqual && (
              <span
                className={cn(
                  'text-xs font-medium mt-1',
                  isBetter ? 'text-green-500' : 'text-red-500'
                )}
              >
                {diff > 0 ? '+' : ''}{percentDiff.toFixed(1)}%
              </span>
            )}
          </div>
        )}

        {/* Dual */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-foreground-muted mb-1">
            <Users className="h-3 w-3" />
            <span className="text-xs">Dual</span>
          </div>
          <div className="text-2xl font-bold">
            {dualValue}
            {unit && <span className="text-sm font-normal text-foreground-muted">{unit}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

function PassAtKChart({
  soloRuns,
  dualRuns,
  k = 5,
}: {
  soloRuns: TaskRunResult[]
  dualRuns: TaskRunResult[]
  k?: number
}) {
  // Calculate pass@k for different k values
  const calculatePassAtK = (runs: TaskRunResult[], kVal: number): number => {
    if (runs.length === 0) return 0
    const successes = runs.filter((r) => r.success).length
    // Simplified pass@k calculation
    const passRate = successes / runs.length
    // pass@k = 1 - (1 - passRate)^k
    return 1 - Math.pow(1 - passRate, kVal)
  }

  const kValues = [1, 2, 3, 5, 10].filter((v) => v <= Math.max(soloRuns.length, dualRuns.length, k))

  return (
    <div className="p-4 rounded-lg border border-border bg-background">
      <div className="text-sm text-foreground-muted mb-3">Pass@k Reliability</div>

      <div className="space-y-2">
        {kValues.map((kVal) => {
          const soloPassK = calculatePassAtK(soloRuns, kVal)
          const dualPassK = calculatePassAtK(dualRuns, kVal)

          return (
            <div key={kVal} className="flex items-center gap-3">
              <span className="w-16 text-xs text-foreground-muted">pass@{kVal}</span>

              {/* Solo bar */}
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 h-2 bg-background-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${soloPassK * 100}%` }}
                  />
                </div>
                <span className="w-12 text-xs text-right">{(soloPassK * 100).toFixed(0)}%</span>
              </div>

              {/* Dual bar */}
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 h-2 bg-background-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full transition-all"
                    style={{ width: `${dualPassK * 100}%` }}
                  />
                </div>
                <span className="w-12 text-xs text-right">{(dualPassK * 100).toFixed(0)}%</span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="flex items-center justify-center gap-6 mt-4 text-xs text-foreground-muted">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500" />
          <span>Solo</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-purple-500" />
          <span>Dual-Control</span>
        </div>
      </div>
    </div>
  )
}

function ErrorBreakdown({
  soloRuns,
  dualRuns,
}: {
  soloRuns: TaskRunResult[]
  dualRuns: TaskRunResult[]
}) {
  const countErrors = (runs: TaskRunResult[]) => {
    const failed = runs.filter((r) => !r.success)
    return {
      reasoning: failed.filter((r) => r.errorCategory === 'reasoning').length,
      communication: failed.filter((r) => r.errorCategory === 'communication').length,
      execution: failed.filter((r) => r.errorCategory === 'execution').length,
      unknown: failed.filter((r) => !r.errorCategory).length,
    }
  }

  const soloErrors = countErrors(soloRuns)
  const dualErrors = countErrors(dualRuns)

  const categories = [
    { key: 'reasoning', label: 'Reasoning', color: 'bg-yellow-500' },
    { key: 'communication', label: 'Communication', color: 'bg-orange-500' },
    { key: 'execution', label: 'Execution', color: 'bg-red-500' },
  ] as const

  return (
    <div className="p-4 rounded-lg border border-border bg-background">
      <div className="text-sm text-foreground-muted mb-3 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        Error Breakdown
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Solo errors */}
        <div>
          <div className="text-xs text-foreground-muted mb-2 flex items-center gap-1">
            <User className="h-3 w-3" />
            Solo Failures
          </div>
          <div className="space-y-1.5">
            {categories.map((cat) => (
              <div key={cat.key} className="flex items-center gap-2">
                <div className={cn('w-2 h-2 rounded-full', cat.color)} />
                <span className="text-xs flex-1">{cat.label}</span>
                <span className="text-xs font-medium">
                  {soloErrors[cat.key]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Dual errors */}
        <div>
          <div className="text-xs text-foreground-muted mb-2 flex items-center gap-1">
            <Users className="h-3 w-3" />
            Dual Failures
          </div>
          <div className="space-y-1.5">
            {categories.map((cat) => (
              <div key={cat.key} className="flex items-center gap-2">
                <div className={cn('w-2 h-2 rounded-full', cat.color)} />
                <span className="text-xs flex-1">{cat.label}</span>
                <span className="text-xs font-medium">
                  {dualErrors[cat.key]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export function SoloDualComparison({
  taskName,
  soloRuns,
  dualRuns,
  className,
}: SoloDualComparisonProps) {
  // Calculate aggregate metrics
  const calcMetrics = (runs: TaskRunResult[]) => {
    if (runs.length === 0) {
      return {
        successRate: 0,
        avgSteps: 0,
        avgGoalCompletion: 0,
      }
    }

    const successes = runs.filter((r) => r.success).length
    const totalSteps = runs.reduce((sum, r) => sum + r.steps, 0)
    const totalGoalCompletion = runs.reduce(
      (sum, r) => sum + (r.goalConditionsMet / r.goalConditionsTotal),
      0
    )

    return {
      successRate: (successes / runs.length) * 100,
      avgSteps: totalSteps / runs.length,
      avgGoalCompletion: (totalGoalCompletion / runs.length) * 100,
    }
  }

  const soloMetrics = calcMetrics(soloRuns)
  const dualMetrics = calcMetrics(dualRuns)

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            Solo vs Dual-Control Comparison
          </h2>
          <p className="text-sm text-foreground-muted mt-0.5">
            {taskName} • {soloRuns.length} solo runs, {dualRuns.length} dual runs
          </p>
        </div>

        {/* Quick verdict */}
        <div
          className={cn(
            'px-4 py-2 rounded-lg text-sm font-medium',
            dualMetrics.successRate > soloMetrics.successRate
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : dualMetrics.successRate < soloMetrics.successRate
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
          )}
        >
          {dualMetrics.successRate > soloMetrics.successRate
            ? '↑ Dual-control performs better'
            : dualMetrics.successRate < soloMetrics.successRate
            ? '↓ Solo performs better'
            : '→ Similar performance'}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Success Rate"
          soloValue={soloMetrics.successRate.toFixed(1)}
          dualValue={dualMetrics.successRate.toFixed(1)}
          unit="%"
          higherIsBetter={true}
        />
        <MetricCard
          label="Avg Steps"
          soloValue={soloMetrics.avgSteps.toFixed(1)}
          dualValue={dualMetrics.avgSteps.toFixed(1)}
          higherIsBetter={false}
        />
        <MetricCard
          label="Goal Completion"
          soloValue={soloMetrics.avgGoalCompletion.toFixed(1)}
          dualValue={dualMetrics.avgGoalCompletion.toFixed(1)}
          unit="%"
          higherIsBetter={true}
        />
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-2 gap-4">
        <PassAtKChart soloRuns={soloRuns} dualRuns={dualRuns} />
        <ErrorBreakdown soloRuns={soloRuns} dualRuns={dualRuns} />
      </div>
    </div>
  )
}

export default SoloDualComparison
