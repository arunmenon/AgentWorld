import { useState, memo } from 'react'
import { Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

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
}: MessageBubbleProps) {
  const displayName = senderName || 'Unknown'
  const colors = getAgentColor(displayName)

  return (
    <div
      className={cn(
        'group flex gap-3',
        isAlternate && 'flex-row-reverse',
        isHighlighted && 'ring-2 ring-primary/50 rounded-lg p-2 -m-2'
      )}
    >
      {/* Avatar */}
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
          <span className="font-semibold text-sm">{displayName}</span>
          {receiverName && (
            <span className="text-xs text-foreground-muted">to {receiverName}</span>
          )}
          {timestamp && (
            <span className="text-xs text-foreground-muted">
              {formatMessageTime(timestamp)}
            </span>
          )}
          <CopyButton text={content} />
        </div>

        {/* Bubble */}
        <div
          className={cn(
            'p-4 rounded-2xl border',
            colors.bg,
            colors.border,
            isAlternate ? 'rounded-tr-md' : 'rounded-tl-md'
          )}
        >
          <div className="text-sm leading-relaxed">
            <MessageContent content={content} />
          </div>
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
