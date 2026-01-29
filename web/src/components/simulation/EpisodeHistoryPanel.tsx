/**
 * Episode History Panel - View past episodes and state at each step.
 *
 * Shows all completed and current episodes for an app environment,
 * with the ability to view state snapshots at any step.
 */

import { useState, useMemo } from 'react'
import { History, Download, Check, Clock, Play, ArrowRight } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Button, Card, Badge } from '@/components/ui'
import { api, type StateSnapshot } from '@/lib/api'
import { cn } from '@/lib/utils'
import { computeStateDiff, formatValue, getDiffSummary } from '@/lib/state-diff'

interface EpisodeHistoryPanelProps {
  simulationId: string
  appId: string
  className?: string
}

export function EpisodeHistoryPanel({ simulationId, appId, className }: EpisodeHistoryPanelProps) {
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string | null>(null)
  const [selectedSnapshot, setSelectedSnapshot] = useState<StateSnapshot | null>(null)
  const [viewMode, setViewMode] = useState<'full' | 'diff'>('diff')

  // Fetch episodes
  const { data: episodesData, isLoading } = useQuery({
    queryKey: ['episodes', simulationId, appId],
    queryFn: () => api.listEpisodes(simulationId, appId, true),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  })

  const episodes = episodesData?.episodes ?? []
  const currentEpisode = useMemo(
    () => selectedEpisodeId
      ? episodes.find((e) => e.episode_id === selectedEpisodeId)
      : episodes[episodes.length - 1],
    [episodes, selectedEpisodeId]
  )

  // Export episode history as JSON
  const handleExport = () => {
    if (!currentEpisode) return

    const blob = new Blob([JSON.stringify(currentEpisode, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `episode-${currentEpisode.episode_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Format duration
  const formatDuration = (startedAt: string, endedAt: string | null): string => {
    if (!endedAt) return 'Running...'
    const start = new Date(startedAt).getTime()
    const end = new Date(endedAt).getTime()
    const seconds = Math.floor((end - start) / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m ${seconds % 60}s`
  }

  // Get state diff between snapshots
  const getSnapshotDiff = (snapshotIndex: number) => {
    if (!currentEpisode || snapshotIndex === 0) return null
    const prev = currentEpisode.snapshots[snapshotIndex - 1]
    const curr = currentEpisode.snapshots[snapshotIndex]
    if (!prev || !curr) return null
    return computeStateDiff(
      prev.state as Record<string, unknown>,
      curr.state as Record<string, unknown>
    )
  }

  if (isLoading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center gap-2 mb-4">
          <History className="h-5 w-5 text-primary animate-pulse" />
          <span>Loading episodes...</span>
        </div>
      </Card>
    )
  }

  if (episodes.length === 0) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center gap-2 mb-2">
          <History className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-semibold">Episode History</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          No episodes recorded yet. Use the environment API to start an episode.
        </p>
      </Card>
    )
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Episode History</h3>
        </div>
        <Button variant="outline" size="sm" onClick={handleExport} disabled={!currentEpisode}>
          <Download className="h-4 w-4 mr-1" />
          Export JSON
        </Button>
      </div>

      {/* Episode Tab Buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {episodes.map((ep, idx) => {
          const isSelected = (selectedEpisodeId ?? episodes[episodes.length - 1]?.episode_id) === ep.episode_id
          return (
            <button
              key={ep.episode_id}
              onClick={() => setSelectedEpisodeId(ep.episode_id)}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                isSelected
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80 text-foreground-secondary'
              )}
            >
              Episode {idx + 1}
              {ep.terminated && <Check className="h-3 w-3 text-green-500" />}
              {ep.truncated && <Clock className="h-3 w-3 text-yellow-500" />}
              {!ep.ended_at && <Play className="h-3 w-3 text-blue-500" />}
            </button>
          )
        })}
      </div>

      {currentEpisode && (
        <>
          {/* Episode Summary */}
          <div className="grid grid-cols-4 gap-4 mb-4 text-sm p-3 bg-muted rounded-lg">
            <div>
              <span className="text-muted-foreground">Duration:</span>{' '}
              {formatDuration(currentEpisode.started_at, currentEpisode.ended_at)}
            </div>
            <div>
              <span className="text-muted-foreground">Total Steps:</span>{' '}
              {currentEpisode.step_count}
            </div>
            <div>
              <span className="text-muted-foreground">Total Reward:</span>{' '}
              <span className={currentEpisode.total_reward >= 0 ? 'text-green-600' : 'text-red-600'}>
                {currentEpisode.total_reward.toFixed(3)}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Outcome:</span>{' '}
              {currentEpisode.terminated ? '✅ Success' :
                currentEpisode.truncated ? '⏱️ Truncated' : '▶️ Running'}
            </div>
          </div>

          {/* State Timeline Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-3 py-2 text-left w-16">Step</th>
                  <th className="px-3 py-2 text-left">Action</th>
                  <th className="px-3 py-2 text-left">State Changes</th>
                  <th className="px-3 py-2 text-right w-20">Reward</th>
                </tr>
              </thead>
              <tbody>
                {currentEpisode.snapshots.map((snapshot, idx) => {
                  const diff = getSnapshotDiff(idx)
                  return (
                    <SnapshotRow
                      key={snapshot.step}
                      snapshot={snapshot}
                      diff={diff}
                      isSelected={selectedSnapshot?.step === snapshot.step}
                      onSelect={() => setSelectedSnapshot(
                        selectedSnapshot?.step === snapshot.step ? null : snapshot
                      )}
                    />
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Selected Snapshot Detail */}
          {selectedSnapshot && (
            <div className="mt-4 border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium">State at Step {selectedSnapshot.step}</h4>
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === 'full' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('full')}
                  >
                    Full State
                  </Button>
                  <Button
                    variant={viewMode === 'diff' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('diff')}
                    disabled={selectedSnapshot.step === 0}
                  >
                    Changes Only
                  </Button>
                </div>
              </div>

              {viewMode === 'full' ? (
                <pre className="font-mono text-xs bg-muted p-4 rounded-lg overflow-auto max-h-64">
                  {JSON.stringify(selectedSnapshot.state, null, 2)}
                </pre>
              ) : (
                <DiffView
                  snapshot={selectedSnapshot}
                  prevSnapshot={currentEpisode.snapshots[selectedSnapshot.step - 1]}
                />
              )}
            </div>
          )}
        </>
      )}
    </Card>
  )
}

// Snapshot row in the timeline table
function SnapshotRow({
  snapshot,
  diff,
  isSelected,
  onSelect,
}: {
  snapshot: StateSnapshot
  diff: ReturnType<typeof computeStateDiff> | null
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <tr
      className={cn(
        'border-t hover:bg-muted/50 cursor-pointer',
        isSelected && 'bg-primary/5'
      )}
      onClick={onSelect}
    >
      <td className="px-3 py-2 font-mono">{snapshot.step}</td>
      <td className="px-3 py-2">
        {snapshot.action ? (
          <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
            {snapshot.action}({JSON.stringify(snapshot.params)})
          </code>
        ) : (
          <span className="text-muted-foreground">(initial)</span>
        )}
      </td>
      <td className="px-3 py-2">
        {diff ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {getDiffSummary(diff)}
            </span>
            {diff.changes.slice(0, 2).map((change) => (
              <Badge key={change.path} variant="default" className="text-xs">
                {change.path}
              </Badge>
            ))}
            {diff.changes.length > 2 && (
              <span className="text-xs text-muted-foreground">
                +{diff.changes.length - 2} more
              </span>
            )}
          </div>
        ) : (
          <span className="text-muted-foreground text-xs">—</span>
        )}
      </td>
      <td className={cn(
        'px-3 py-2 text-right font-mono',
        snapshot.reward >= 0 ? 'text-green-600' : 'text-red-600'
      )}>
        {snapshot.reward.toFixed(3)}
      </td>
    </tr>
  )
}

// Diff view component
function DiffView({
  snapshot,
  prevSnapshot,
}: {
  snapshot: StateSnapshot
  prevSnapshot?: StateSnapshot
}) {
  if (!prevSnapshot) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center">
        Initial state - no previous snapshot to compare
      </div>
    )
  }

  const diff = computeStateDiff(
    prevSnapshot.state as Record<string, unknown>,
    snapshot.state as Record<string, unknown>
  )

  if (!diff.hasChanges) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center">
        No state changes
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Diff header */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Step {prevSnapshot.step}</span>
        <ArrowRight className="h-4 w-4" />
        <span>Step {snapshot.step}</span>
        <span className="ml-auto">
          Action: <code>{snapshot.action}</code>
        </span>
      </div>

      {/* Changed fields */}
      <div className="space-y-2">
        {diff.changes.map((change) => (
          <div
            key={change.path}
            className={cn(
              'flex items-center gap-2 p-2 rounded text-sm',
              change.type === 'added' && 'bg-green-100 dark:bg-green-900/20',
              change.type === 'removed' && 'bg-red-100 dark:bg-red-900/20',
              change.type === 'modified' && 'bg-amber-100 dark:bg-amber-900/20'
            )}
          >
            <Badge variant="outline" className="font-mono">
              {change.path}
            </Badge>
            {change.type === 'added' ? (
              <span className="text-green-600">+ {formatValue(change.after)}</span>
            ) : change.type === 'removed' ? (
              <span className="text-red-600">- {formatValue(change.before)}</span>
            ) : (
              <>
                <span className="text-red-500 line-through">{formatValue(change.before)}</span>
                <ArrowRight className="h-3 w-3" />
                <span className="text-green-500">{formatValue(change.after)}</span>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
