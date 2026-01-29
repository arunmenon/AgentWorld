/**
 * State Diff View - Show state changes between steps.
 *
 * Used as a modal or inline component to display what changed
 * between two state snapshots in an episode.
 */

import { useState } from 'react'
import { ArrowRight, Plus, Minus, Edit } from 'lucide-react'
import { Modal, ModalHeader, ModalContent, Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import {
  computeStateDiff,
  formatValue,
  getChangeColor,
  getChangeBgColor,
  type ChangedField,
  type StateDiff,
} from '@/lib/state-diff'
import type { StateSnapshot } from '@/lib/api'

interface StateDiffViewProps {
  before: StateSnapshot
  after: StateSnapshot
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function StateDiffView({ before, after, open, onOpenChange }: StateDiffViewProps) {
  const diff = computeStateDiff(
    before.state as Record<string, unknown>,
    after.state as Record<string, unknown>
  )

  const handleClose = () => onOpenChange?.(false)

  return (
    <Modal open={open ?? false} onClose={handleClose} className="max-w-3xl max-h-[80vh] overflow-auto">
      <ModalHeader onClose={handleClose}>
        State Changes: Step {before.step} → {after.step}
      </ModalHeader>
      <ModalContent>
        <div className="flex items-center gap-2 mb-4 text-foreground-secondary">
          {after.action && (
            <>
              Action: <code className="bg-muted px-1.5 py-0.5 rounded">{after.action}</code>
            </>
          )}
          {after.params && Object.keys(after.params).length > 0 && (
            <span className="text-xs text-foreground-muted">
              ({JSON.stringify(after.params)})
            </span>
          )}
        </div>
        <StateDiffContent diff={diff} />
      </ModalContent>
    </Modal>
  )
}

// Inline version without dialog
export function StateDiffInline({
  before,
  after,
  className,
}: {
  before: Record<string, unknown>
  after: Record<string, unknown>
  className?: string
}) {
  const diff = computeStateDiff(before, after)
  return <StateDiffContent diff={diff} className={className} />
}

// Core diff content component
function StateDiffContent({
  diff,
  className,
}: {
  diff: StateDiff
  className?: string
}) {
  if (!diff.hasChanges) {
    return (
      <div className={cn('text-center text-muted-foreground py-8', className)}>
        No state changes detected
      </div>
    )
  }

  // Group changes by type
  const added = diff.changes.filter((c) => c.type === 'added')
  const removed = diff.changes.filter((c) => c.type === 'removed')
  const modified = diff.changes.filter((c) => c.type === 'modified')

  return (
    <div className={cn('space-y-4', className)}>
      {/* Summary badges */}
      <div className="flex gap-2">
        {added.length > 0 && (
          <Badge variant="outline" className="text-green-600 border-green-600">
            <Plus className="h-3 w-3 mr-1" />
            {added.length} added
          </Badge>
        )}
        {removed.length > 0 && (
          <Badge variant="outline" className="text-red-600 border-red-600">
            <Minus className="h-3 w-3 mr-1" />
            {removed.length} removed
          </Badge>
        )}
        {modified.length > 0 && (
          <Badge variant="outline" className="text-amber-600 border-amber-600">
            <Edit className="h-3 w-3 mr-1" />
            {modified.length} modified
          </Badge>
        )}
      </div>

      {/* Changes list */}
      <div className="space-y-2">
        {diff.changes.map((change) => (
          <ChangeRow key={change.path} change={change} />
        ))}
      </div>
    </div>
  )
}

// Individual change row
function ChangeRow({ change }: { change: ChangedField }) {
  const icon = change.type === 'added' ? Plus :
    change.type === 'removed' ? Minus : Edit

  const Icon = icon

  return (
    <div className={cn(
      'flex items-start gap-3 p-3 rounded-lg',
      getChangeBgColor(change.type)
    )}>
      <Icon className={cn('h-4 w-4 mt-0.5', getChangeColor(change.type))} />

      <div className="flex-1 min-w-0">
        <div className="font-mono text-sm font-medium mb-1">{change.path}</div>

        {change.type === 'added' && (
          <div className="text-green-600 text-sm">
            {formatValue(change.after)}
          </div>
        )}

        {change.type === 'removed' && (
          <div className="text-red-600 text-sm line-through">
            {formatValue(change.before)}
          </div>
        )}

        {change.type === 'modified' && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-red-500 line-through">
              {formatValue(change.before)}
            </span>
            <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
            <span className="text-green-500">
              {formatValue(change.after)}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

// Compact badges for inline display in tables
export function StateDiffBadges({
  before,
  after,
  maxBadges = 3,
}: {
  before: Record<string, unknown>
  after: Record<string, unknown>
  maxBadges?: number
}) {
  const diff = computeStateDiff(before, after)

  if (!diff.hasChanges) {
    return <span className="text-muted-foreground text-xs">—</span>
  }

  const displayChanges = diff.changes.slice(0, maxBadges)
  const remaining = diff.changes.length - maxBadges

  return (
    <div className="flex flex-wrap gap-1">
      {displayChanges.map((change) => (
        <Badge
          key={change.path}
          variant="default"
          className={cn('text-xs', getChangeColor(change.type))}
        >
          {change.path}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="default" className="text-xs text-muted-foreground">
          +{remaining} more
        </Badge>
      )}
    </div>
  )
}

// Full state view toggle component
export function StateViewToggle({
  snapshot,
  prevSnapshot,
  defaultMode = 'diff',
}: {
  snapshot: StateSnapshot
  prevSnapshot?: StateSnapshot
  defaultMode?: 'full' | 'diff'
}) {
  const [mode, setMode] = useState<'full' | 'diff'>(defaultMode)

  return (
    <div>
      <div className="flex gap-2 mb-3">
        <Button
          variant={mode === 'full' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setMode('full')}
        >
          Full State
        </Button>
        <Button
          variant={mode === 'diff' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setMode('diff')}
          disabled={!prevSnapshot}
        >
          Changes Only
        </Button>
      </div>

      {mode === 'full' ? (
        <pre className="font-mono text-xs bg-muted p-4 rounded-lg overflow-auto max-h-64">
          {JSON.stringify(snapshot.state, null, 2)}
        </pre>
      ) : prevSnapshot ? (
        <StateDiffInline
          before={prevSnapshot.state as Record<string, unknown>}
          after={snapshot.state as Record<string, unknown>}
        />
      ) : (
        <div className="text-sm text-muted-foreground p-4 text-center">
          No previous state to compare
        </div>
      )}
    </div>
  )
}

