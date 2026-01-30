/**
 * EpisodeEventBubble - Displays episode events in the conversation stream.
 *
 * Shows reset, step, and close events with appropriate styling and metadata.
 */

import { memo } from 'react'
import { Play, Zap, StopCircle, Check, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { MessageType, EpisodeEventMetadata } from './ConversationStream'

export interface EpisodeEventBubbleProps {
  id: string
  messageType: MessageType
  content: string
  timestamp?: Date | string | null
  step: number
  metadata?: EpisodeEventMetadata | null
}

function formatEventTime(timestamp: Date | string): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

export const EpisodeEventBubble = memo(function EpisodeEventBubble({
  messageType,
  content,
  timestamp,
  metadata,
}: EpisodeEventBubbleProps) {
  const isReset = messageType === 'episode_reset'
  const isStep = messageType === 'episode_step'
  const isClose = messageType === 'episode_close'
  const isAction = messageType === 'episode_action'
  const isTurn = messageType === 'episode_turn'

  // Determine icon and colors based on event type
  let Icon = Zap
  let bgColor = 'bg-blue-500/10'
  let borderColor = 'border-blue-500/30'
  let iconColor = 'text-blue-500'
  let label = 'Episode Event'

  if (isReset) {
    Icon = Play
    bgColor = 'bg-green-500/10'
    borderColor = 'border-green-500/30'
    iconColor = 'text-green-500'
    label = 'Episode Started'
  } else if (isStep || isAction) {
    Icon = Zap
    bgColor = 'bg-amber-500/10'
    borderColor = 'border-amber-500/30'
    iconColor = 'text-amber-500'
    label = isAction ? 'App Action' : 'Environment Action'
  } else if (isTurn) {
    Icon = Zap
    bgColor = 'bg-purple-500/10'
    borderColor = 'border-purple-500/30'
    iconColor = 'text-purple-500'
    label = 'Agent Turn'
  } else if (isClose) {
    Icon = StopCircle
    bgColor = 'bg-gray-500/10'
    borderColor = 'border-gray-500/30'
    iconColor = 'text-gray-500'
    label = 'Episode Ended'
  }

  // Status indicator for steps
  const status = metadata?.status
  const reward = metadata?.reward

  return (
    <div className="flex justify-center my-2">
      <div
        className={cn(
          'flex items-center gap-3 px-4 py-2 rounded-lg border',
          bgColor,
          borderColor
        )}
      >
        {/* Icon */}
        <div className={cn('flex-shrink-0', iconColor)}>
          <Icon className="h-4 w-4" />
        </div>

        {/* Content */}
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-foreground-muted">
              {label}
            </span>
            {timestamp && (
              <span className="text-xs text-foreground-muted">
                {formatEventTime(timestamp)}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* App and Episode ID */}
            {metadata?.app_id && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-background font-mono">
                {metadata.app_id}
              </span>
            )}

            {/* Action content for steps and actions */}
            {(isStep || isAction) && (
              <code className="text-sm font-mono text-foreground">
                {metadata?.action ? `${metadata.app_id}.${metadata.action}()` : content}
              </code>
            )}

            {/* Turn info */}
            {isTurn && metadata?.agent_name && (
              <span className="text-sm text-foreground">
                {metadata.agent_name}
              </span>
            )}

            {/* Episode ID for reset */}
            {isReset && metadata?.episode_id && (
              <span className="text-sm font-mono text-foreground">
                Episode: {metadata.episode_id}
              </span>
            )}

            {/* Close status */}
            {isClose && (
              <span className="text-sm text-foreground">
                Episode completed
              </span>
            )}
          </div>

          {/* Step/Action metadata */}
          {(isStep || isAction) && (
            <div className="flex items-center gap-3 mt-1">
              {/* Episode step number */}
              {metadata?.episode_step !== undefined && (
                <span className="text-xs text-foreground-muted">
                  Step {metadata.episode_step}
                </span>
              )}

              {/* Reward */}
              {reward !== undefined && (
                <span
                  className={cn(
                    'text-xs font-mono',
                    reward >= 0 ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  Reward: {reward.toFixed(3)}
                </span>
              )}

              {/* Status indicator */}
              {status === 'terminated' && (
                <span className="flex items-center gap-1 text-xs text-green-600">
                  <Check className="h-3 w-3" />
                  Goal achieved
                </span>
              )}
              {status === 'truncated' && (
                <span className="flex items-center gap-1 text-xs text-yellow-600">
                  <AlertTriangle className="h-3 w-3" />
                  Max steps reached
                </span>
              )}
            </div>
          )}

          {/* Reset metadata */}
          {isReset && metadata?.agents && (
            <div className="flex items-center gap-2 mt-1 text-xs text-foreground-muted">
              <span>Agents: {metadata.agents.join(', ')}</span>
              {metadata.max_steps && (
                <span>Max steps: {metadata.max_steps}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
})

export default EpisodeEventBubble
