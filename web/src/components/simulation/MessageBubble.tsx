import { useState, memo } from 'react'
import { Copy, Check, ChevronDown, ChevronUp, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentRole } from '@/lib/api'

export interface MessageBubbleProps {
  id: string
  senderName: string | null
  receiverName?: string | null
  content: string
  timestamp?: Date | string | null
  step: number
  isHighlighted?: boolean
  isAlternate?: boolean
  avatarColor?: string
  onCopy?: (content: string) => void
  /** Agent role for dual-control styling (τ²-bench) */
  senderRole?: AgentRole
  receiverRole?: AgentRole
  /** Coordination event marker */
  coordination?: {
    type: 'instruction' | 'action' | 'confirmation'
    expectedAction?: string
    actualAction?: string
    status?: 'pending' | 'complete' | 'failed'
  }
  /** App action performed in this message */
  appAction?: {
    appId: string
    appName?: string
    appIcon?: string
    action: string
    status: 'success' | 'error'
  }
}

// Role configuration for dual-control styling
const roleConfig: Record<AgentRole, { emoji: string; color: string; label: string }> = {
  service_agent: {
    emoji: '🎧',
    color: 'text-purple-600 dark:text-purple-400',
    label: 'Service Agent',
  },
  customer: {
    emoji: '📱',
    color: 'text-green-600 dark:text-green-400',
    label: 'Customer',
  },
  peer: {
    emoji: '👥',
    color: 'text-blue-600 dark:text-blue-400',
    label: 'Peer',
  },
}

// Generate consistent colors from agent name
function getAgentColor(name: string): { bg: string; border: string; avatar: string } {
  const colors = [
    { bg: 'bg-indigo-500/10', border: 'border-indigo-500/30', avatar: 'bg-indigo-500' },
    { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', avatar: 'bg-emerald-500' },
    { bg: 'bg-amber-500/10', border: 'border-amber-500/30', avatar: 'bg-amber-500' },
    { bg: 'bg-rose-500/10', border: 'border-rose-500/30', avatar: 'bg-rose-500' },
    { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', avatar: 'bg-cyan-500' },
    { bg: 'bg-violet-500/10', border: 'border-violet-500/30', avatar: 'bg-violet-500' },
    { bg: 'bg-orange-500/10', border: 'border-orange-500/30', avatar: 'bg-orange-500' },
    { bg: 'bg-teal-500/10', border: 'border-teal-500/30', avatar: 'bg-teal-500' },
    { bg: 'bg-pink-500/10', border: 'border-pink-500/30', avatar: 'bg-pink-500' },
    { bg: 'bg-lime-500/10', border: 'border-lime-500/30', avatar: 'bg-lime-500' },
  ]

  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

function formatMessageTime(timestamp: Date | string): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function MessageContent({ content }: { content: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const previewLength = 400
  const needsExpansion = content.length > previewLength

  if (!needsExpansion) {
    return <span className="whitespace-pre-wrap">{content}</span>
  }

  return (
    <>
      <span className="whitespace-pre-wrap">
        {isExpanded ? content : `${content.slice(0, previewLength)}...`}
      </span>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 mt-2 text-xs font-medium text-primary hover:text-primary-hover transition-colors"
      >
        {isExpanded ? (
          <>
            <ChevronUp className="h-3 w-3" />
            Show less
          </>
        ) : (
          <>
            <ChevronDown className="h-3 w-3" />
            Read more
          </>
        )}
      </button>
    </>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="p-1.5 rounded-md hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
      title="Copy message"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-success" />
      ) : (
        <Copy className="h-3.5 w-3.5 text-foreground-muted" />
      )}
    </button>
  )
}

export const MessageBubble = memo(function MessageBubble({
  senderName,
  receiverName,
  content,
  timestamp,
  isHighlighted = false,
  isAlternate = false,
  senderRole,
  receiverRole,
  coordination,
  appAction,
}: MessageBubbleProps) {
  const displayName = senderName || 'Unknown'
  const colors = getAgentColor(displayName)
  const senderRoleConfig = senderRole ? roleConfig[senderRole] : null

  // Check if this is a coordination instruction (service agent giving instructions)
  const isCoordinationInstruction = coordination?.type === 'instruction'
  const isCoordinationAction = coordination?.type === 'action'

  return (
    <div
      className={cn(
        'group flex gap-3',
        isAlternate && 'flex-row-reverse',
        isHighlighted && 'ring-2 ring-primary/50 rounded-lg p-2 -m-2'
      )}
    >
      {/* Avatar */}
      <div className="relative">
        <div
          className={cn(
            'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center',
            colors.avatar
          )}
        >
          <span className="text-sm font-semibold text-white">
            {displayName.charAt(0).toUpperCase()}
          </span>
        </div>
        {/* Role indicator badge */}
        {senderRoleConfig && senderRole !== 'peer' && (
          <span
            className="absolute -bottom-1 -right-1 text-xs"
            title={senderRoleConfig.label}
          >
            {senderRoleConfig.emoji}
          </span>
        )}
      </div>

      {/* Message content */}
      <div
        className={cn('flex-1 max-w-[85%]', isAlternate && 'flex flex-col items-end')}
      >
        {/* Header */}
        <div
          className={cn(
            'flex items-center gap-2 mb-1',
            isAlternate && 'flex-row-reverse'
          )}
        >
          <span className={cn('font-semibold text-sm', senderRoleConfig?.color)}>
            {displayName}
          </span>
          {/* Role badge for non-peer roles */}
          {senderRoleConfig && senderRole !== 'peer' && (
            <span
              className={cn(
                'text-xs px-1.5 py-0.5 rounded',
                senderRole === 'service_agent'
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
                  : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              )}
            >
              {senderRoleConfig.label}
            </span>
          )}
          {receiverName && (
            <span className="text-xs text-foreground-muted">
              to {receiverRole && receiverRole !== 'peer' ? `${roleConfig[receiverRole].emoji} ` : ''}{receiverName}
            </span>
          )}
          {timestamp && (
            <span className="text-xs text-foreground-muted">
              {formatMessageTime(timestamp)}
            </span>
          )}
          <CopyButton text={content} />
        </div>

        {/* Coordination instruction indicator */}
        {isCoordinationInstruction && (
          <div className="flex items-center gap-1 mb-1 text-xs text-yellow-600 dark:text-yellow-400">
            <Target className="h-3 w-3" />
            <span>Coordination instruction</span>
            {coordination.expectedAction && (
              <code className="px-1 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/30 text-xs">
                {coordination.expectedAction}
              </code>
            )}
          </div>
        )}

        {/* Bubble */}
        <div
          className={cn(
            'p-4 rounded-2xl border',
            colors.bg,
            colors.border,
            isAlternate ? 'rounded-tr-md' : 'rounded-tl-md',
            // Coordination styling
            isCoordinationInstruction && 'ring-2 ring-yellow-400/50',
            isCoordinationAction && coordination.status === 'complete' && 'ring-2 ring-green-400/50',
            isCoordinationAction && coordination.status === 'failed' && 'ring-2 ring-red-400/50'
          )}
        >
          <div className="text-sm leading-relaxed">
            <MessageContent content={content} />
          </div>

          {/* App action display */}
          {appAction && (
            <div
              className={cn(
                'mt-3 pt-3 border-t flex items-center gap-2 text-xs',
                appAction.status === 'success'
                  ? 'border-green-200 dark:border-green-800'
                  : 'border-red-200 dark:border-red-800'
              )}
            >
              <span>{appAction.appIcon || '🔧'}</span>
              <code className="px-1.5 py-0.5 rounded bg-background">
                {appAction.action}
              </code>
              <span
                className={cn(
                  'font-medium',
                  appAction.status === 'success'
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                )}
              >
                {appAction.status === 'success' ? '✓ Success' : '✗ Failed'}
              </span>
            </div>
          )}

          {/* Coordination action result */}
          {isCoordinationAction && coordination.status && (
            <div
              className={cn(
                'mt-3 pt-3 border-t flex items-center gap-2 text-xs',
                coordination.status === 'complete'
                  ? 'border-green-200 dark:border-green-800 text-green-600 dark:text-green-400'
                  : 'border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
              )}
            >
              {coordination.status === 'complete' ? (
                <>✅ Handoff complete</>
              ) : (
                <>
                  ❌ Handoff failed
                  {coordination.actualAction && (
                    <span className="text-foreground-muted">
                      (performed: <code>{coordination.actualAction}</code>)
                    </span>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
})

export interface StepDividerProps {
  step: number
}

export const StepDivider = memo(function StepDivider({ step }: StepDividerProps) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-border" />
      <span className="text-xs font-medium text-foreground-muted px-2 py-1 bg-secondary rounded-full">
        Step {step}
      </span>
      <div className="flex-1 h-px bg-border" />
    </div>
  )
})

export default MessageBubble
