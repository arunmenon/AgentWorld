import { memo, useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Info,
  Filter,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Button, Badge, Card, Input } from '@/components/ui'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface EvaluationPanelProps {
  simulationId: string
  className?: string
}

interface Evaluation {
  id: string
  message_id: string
  evaluator_name: string
  score: number
  explanation: string | null
  evaluator_version: string
  passed: boolean
  created_at: string | null
}

interface EvaluatorSummary {
  evaluator_name: string
  count: number
  average_score: number
  min_score: number
  max_score: number
  pass_rate: number
  total_cost_usd: number
}

interface EvaluationSummary {
  simulation_id: string
  evaluator_summaries: Record<string, EvaluatorSummary>
  total_evaluations: number
  average_score: number
  pass_rate: number
  total_cost_usd: number
  total_latency_ms: number
}

const EVALUATOR_OPTIONS = [
  { id: 'persona_adherence', name: 'Persona Adherence', description: 'Checks if response matches persona traits' },
  { id: 'coherence', name: 'Coherence', description: 'Evaluates logical consistency' },
  { id: 'relevance', name: 'Relevance', description: 'Measures response relevance to stimulus' },
  { id: 'consistency', name: 'Consistency', description: 'Checks consistency with conversation history' },
  { id: 'length_check', name: 'Length Check', description: 'Validates response length (heuristic)' },
  { id: 'keyword_filter', name: 'Keyword Filter', description: 'Filters inappropriate content (heuristic)' },
]

export const EvaluationPanel = memo(function EvaluationPanel({
  simulationId,
  className,
}: EvaluationPanelProps) {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [selectedEvaluators, setSelectedEvaluators] = useState<string[]>(['coherence', 'relevance'])
  const [minScoreFilter, setMinScoreFilter] = useState<string>('')
  const [maxScoreFilter, setMaxScoreFilter] = useState<string>('')
  const [evaluatorFilter, setEvaluatorFilter] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)
  const [expandedEval, setExpandedEval] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<{
    success: boolean
    message: string
  } | null>(null)

  const loadSummary = useCallback(async () => {
    try {
      const result = await api.getEvaluationSummary(simulationId)
      setSummary(result)
    } catch (error) {
      console.error('Failed to load evaluation summary:', error)
    }
  }, [simulationId])

  const loadEvaluations = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await api.getEvaluations(simulationId, {
        evaluator_name: evaluatorFilter || undefined,
        min_score: minScoreFilter ? parseFloat(minScoreFilter) : undefined,
        max_score: maxScoreFilter ? parseFloat(maxScoreFilter) : undefined,
      })
      setEvaluations(result.evaluations)
    } catch (error) {
      console.error('Failed to load evaluations:', error)
    } finally {
      setIsLoading(false)
    }
  }, [simulationId, evaluatorFilter, minScoreFilter, maxScoreFilter])

  useEffect(() => {
    loadSummary()
    loadEvaluations()
  }, [loadSummary, loadEvaluations])

  const handleRunEvaluators = async () => {
    if (selectedEvaluators.length === 0) return

    setIsRunning(true)
    setError(null)
    setRunResult(null)

    try {
      const result = await api.runEvaluation(simulationId, {
        evaluator_names: selectedEvaluators,
        async_mode: false,
      })

      setRunResult({
        success: true,
        message: `Ran ${result.evaluations_run} evaluations`,
      })

      // Reload data
      await loadSummary()
      await loadEvaluations()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Evaluation failed')
      setRunResult({
        success: false,
        message: error instanceof Error ? error.message : 'Evaluation failed',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const toggleEvaluator = (evaluatorId: string) => {
    setSelectedEvaluators(prev =>
      prev.includes(evaluatorId)
        ? prev.filter(id => id !== evaluatorId)
        : [...prev, evaluatorId]
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-success'
    if (score >= 0.5) return 'text-warning'
    return 'text-error'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 0.8) return 'bg-success/10'
    if (score >= 0.5) return 'bg-warning/10'
    return 'bg-error/10'
  }

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`

  return (
    <Card className={cn('p-4 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          <h3 className="font-medium">Evaluation</h3>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            loadSummary()
            loadEvaluations()
          }}
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && summary.total_evaluations > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-secondary/50">
            <p className="text-xs text-foreground-muted">Total Evaluations</p>
            <p className="text-xl font-bold">{summary.total_evaluations}</p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50">
            <p className="text-xs text-foreground-muted">Average Score</p>
            <p className={cn('text-xl font-bold', getScoreColor(summary.average_score))}>
              {formatPercent(summary.average_score)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50">
            <p className="text-xs text-foreground-muted">Pass Rate</p>
            <p className={cn('text-xl font-bold', getScoreColor(summary.pass_rate))}>
              {formatPercent(summary.pass_rate)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50">
            <p className="text-xs text-foreground-muted">Total Cost</p>
            <p className="text-xl font-bold">${summary.total_cost_usd.toFixed(4)}</p>
          </div>
        </div>
      )}

      {/* Per-Evaluator Summary */}
      {summary && Object.keys(summary.evaluator_summaries).length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-foreground-secondary">By Evaluator</p>
          <div className="space-y-2">
            {Object.values(summary.evaluator_summaries).map((evalSummary) => (
              <div
                key={evalSummary.evaluator_name}
                className="p-3 rounded-lg border border-border bg-secondary/30"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">{evalSummary.evaluator_name}</span>
                  <Badge variant="default">{evalSummary.count} runs</Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-foreground-muted">
                  <span>
                    Avg: <span className={getScoreColor(evalSummary.average_score)}>
                      {formatPercent(evalSummary.average_score)}
                    </span>
                  </span>
                  <span>
                    Pass: <span className={getScoreColor(evalSummary.pass_rate)}>
                      {formatPercent(evalSummary.pass_rate)}
                    </span>
                  </span>
                  <span>
                    Range: {formatPercent(evalSummary.min_score)} - {formatPercent(evalSummary.max_score)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Run Evaluators Section */}
      <div className="space-y-3 pt-2 border-t border-border">
        <p className="text-sm text-foreground-secondary">Run Evaluators</p>
        <div className="flex flex-wrap gap-2">
          {EVALUATOR_OPTIONS.map((evaluator) => (
            <button
              key={evaluator.id}
              onClick={() => toggleEvaluator(evaluator.id)}
              className={cn(
                'px-3 py-1.5 rounded-lg border text-xs transition-colors',
                selectedEvaluators.includes(evaluator.id)
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-border-hover'
              )}
              title={evaluator.description}
            >
              {evaluator.name}
            </button>
          ))}
        </div>
        <Button
          onClick={handleRunEvaluators}
          disabled={isRunning || selectedEvaluators.length === 0}
          className="w-full"
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          Run Selected Evaluators
        </Button>
      </div>

      {/* Run Result */}
      {runResult && (
        <div
          className={cn(
            'p-3 rounded-lg flex items-center gap-2 text-sm',
            runResult.success
              ? 'bg-success/10 text-success'
              : 'bg-error/10 text-error'
          )}
        >
          {runResult.success ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          {runResult.message}
        </div>
      )}

      {/* Filters */}
      <div className="space-y-3 pt-2 border-t border-border">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm text-foreground-secondary hover:text-foreground"
        >
          <Filter className="h-4 w-4" />
          Filters
          {showFilters ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {showFilters && (
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-foreground-muted">Evaluator:</label>
              <select
                value={evaluatorFilter}
                onChange={(e) => setEvaluatorFilter(e.target.value)}
                className="px-2 py-1 rounded border border-border bg-background text-xs"
              >
                <option value="">All</option>
                {EVALUATOR_OPTIONS.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-foreground-muted">Min Score:</label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={minScoreFilter}
                onChange={(e) => setMinScoreFilter(e.target.value)}
                placeholder="0.0"
                className="w-16 h-7 text-xs"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-foreground-muted">Max Score:</label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={maxScoreFilter}
                onChange={(e) => setMaxScoreFilter(e.target.value)}
                placeholder="1.0"
                className="w-16 h-7 text-xs"
              />
            </div>
            <Button size="sm" variant="outline" onClick={loadEvaluations}>
              Apply
            </Button>
          </div>
        )}
      </div>

      {/* Evaluations List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-foreground-muted" />
        </div>
      ) : evaluations.length === 0 ? (
        <div className="text-center py-8 text-foreground-muted">
          <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No evaluations yet</p>
          <p className="text-xs mt-1">
            Run evaluators to analyze message quality
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {evaluations.slice(0, 50).map((evaluation) => (
            <div
              key={evaluation.id}
              className={cn(
                'p-3 rounded-lg border border-border',
                getScoreBgColor(evaluation.score)
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="default" className={getScoreColor(evaluation.score)}>
                    {formatPercent(evaluation.score)}
                  </Badge>
                  <span className="text-sm font-medium">{evaluation.evaluator_name}</span>
                  {evaluation.passed ? (
                    <CheckCircle className="h-3 w-3 text-success" />
                  ) : (
                    <AlertCircle className="h-3 w-3 text-error" />
                  )}
                </div>
                <button
                  onClick={() =>
                    setExpandedEval(
                      expandedEval === evaluation.id ? null : evaluation.id
                    )
                  }
                  className="text-foreground-muted hover:text-foreground"
                >
                  <Info className="h-4 w-4" />
                </button>
              </div>

              <p className="text-xs text-foreground-muted mt-1">
                Message: {evaluation.message_id}
              </p>

              {/* Expanded Details (Provenance) */}
              {expandedEval === evaluation.id && (
                <div className="mt-3 pt-3 border-t border-border space-y-2">
                  {evaluation.explanation && (
                    <div>
                      <p className="text-xs text-foreground-muted">Explanation</p>
                      <p className="text-sm">{evaluation.explanation}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-foreground-muted">Version: </span>
                      <span>{evaluation.evaluator_version}</span>
                    </div>
                    {evaluation.created_at && (
                      <div>
                        <span className="text-foreground-muted">Created: </span>
                        <span>{new Date(evaluation.created_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          {evaluations.length > 50 && (
            <p className="text-xs text-center text-foreground-muted">
              Showing 50 of {evaluations.length} evaluations
            </p>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-3 rounded-lg bg-error/10 text-error text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
    </Card>
  )
})

export default EvaluationPanel
