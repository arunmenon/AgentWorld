import { memo, useMemo } from 'react'
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Wifi,
  WifiOff,
  Loader2,
} from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { StimulusInjector, type Agent as StimulusAgent } from './StimulusInjector'

type SimulationStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed'

export interface SimulationControlsProps {
  status: SimulationStatus
  currentStep: number
  totalSteps: number
  isConnected?: boolean
  isStepPending?: boolean
  agents?: StimulusAgent[]
  onStart: () => void
  onPause: () => void
  onStep: (count?: number) => void
  onReset?: () => void
  onInjectStimulus?: (content: string, targetAgents: string[]) => Promise<void>
  className?: string
}

const statusConfig: Record<
  SimulationStatus,
  { label: string; color: string; variant: 'success' | 'warning' | 'error' | 'default' }
> = {
  pending: { label: 'Pending', color: 'text-foreground-muted', variant: 'default' },
  running: { label: 'Running', color: 'text-success', variant: 'success' },
  paused: { label: 'Paused', color: 'text-warning', variant: 'warning' },
  completed: { label: 'Completed', color: 'text-foreground-muted', variant: 'default' },
  failed: { label: 'Failed', color: 'text-error', variant: 'error' },
}

export const SimulationControls = memo(function SimulationControls({
  status,
  currentStep,
  totalSteps,
  isConnected = false,
  isStepPending = false,
  agents = [],
  onStart,
  onPause,
  onStep,
  onReset,
  onInjectStimulus,
  className,
}: SimulationControlsProps) {
  const progress = useMemo(() => {
    if (totalSteps === 0) return 0
    return (currentStep / totalSteps) * 100
  }, [currentStep, totalSteps])

  const canStart = status === 'pending' || status === 'paused'
  const canPause = status === 'running'
  const canStep = status !== 'completed' && status !== 'failed' && !isStepPending
  const canReset = status === 'completed' || status === 'failed'
  const canInject = status === 'running' || status === 'paused'

  const statusInfo = statusConfig[status]

  return (
    <div className={cn('space-y-4', className)}>
      {/* Status and connection indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
          {status === 'running' && (
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
          )}
        </div>

        <div className="flex items-center gap-2">
          {isConnected ? (
            <div className="flex items-center gap-1 text-xs text-success">
              <Wifi className="h-3 w-3" />
              <span>Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-xs text-foreground-muted">
              <WifiOff className="h-3 w-3" />
              <span>Offline</span>
            </div>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-foreground-secondary">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="font-medium">{progress.toFixed(0)}%</span>
        </div>
        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-300',
              status === 'running' ? 'bg-primary animate-pulse' : 'bg-primary'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Control buttons */}
      <div className="flex items-center gap-2">
        {/* Start/Resume button */}
        {canStart && (
          <Button onClick={onStart} className="flex-1">
            <Play className="h-4 w-4 mr-2" />
            {status === 'paused' ? 'Resume' : 'Start'}
          </Button>
        )}

        {/* Pause button */}
        {canPause && (
          <Button onClick={onPause} variant="outline" className="flex-1">
            <Pause className="h-4 w-4 mr-2" />
            Pause
          </Button>
        )}

        {/* Step button */}
        <Button
          variant="outline"
          onClick={() => onStep(1)}
          disabled={!canStep}
          className="flex-1"
        >
          {isStepPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <SkipForward className="h-4 w-4 mr-2" />
              Step
            </>
          )}
        </Button>

        {/* Reset button (only when completed/failed) */}
        {canReset && onReset && (
          <Button variant="ghost" onClick={onReset}>
            <RotateCcw className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Quick step options */}
      {canStep && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-foreground-muted">Quick steps:</span>
          {[5, 10, 25].map((count) => (
            <Button
              key={count}
              variant="ghost"
              size="sm"
              onClick={() => onStep(count)}
              disabled={isStepPending || currentStep + count > totalSteps}
              className="text-xs"
            >
              +{count}
            </Button>
          ))}
        </div>
      )}

      {/* Stimulus injector */}
      {onInjectStimulus && agents.length > 0 && (
        <StimulusInjector
          agents={agents}
          onInject={onInjectStimulus}
          disabled={!canInject}
        />
      )}
    </div>
  )
})

export default SimulationControls
