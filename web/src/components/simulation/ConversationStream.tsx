import { useRef, useEffect, useCallback, useState, useMemo, memo } from 'react'
import { VariableSizeList as List, ListChildComponentProps } from 'react-window'
import { MessageBubble, StepDivider } from './MessageBubble'
import { EpisodeEventBubble } from './EpisodeEventBubble'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { Search, Filter, ArrowDown } from 'lucide-react'

export type MessageType = 'message' | 'episode_reset' | 'episode_step' | 'episode_close' | 'episode_action' | 'episode_turn'

export interface EpisodeEventMetadata {
  app_id?: string
  episode_id?: string
  episode_step?: number
  action_number?: number
  turn_number?: number
  agent_id?: string
  agent_name?: string
  action?: string
  params?: Record<string, unknown>
  reward?: number
  cumulative_reward?: number
  terminated?: boolean
  truncated?: boolean
  status?: 'running' | 'terminated' | 'truncated'
  agents?: string[]
  max_steps?: number
}

export interface Message {
  id: string
  sender_id: string
  sender_name: string | null
  receiver_id?: string | null
  receiver_name?: string | null
  content: string
  step: number
  timestamp?: string | Date | null
  message_type?: MessageType
  metadata?: EpisodeEventMetadata | null
}

export interface ConversationStreamProps {
  messages: Message[]
  selectedAgentId?: string
  searchQuery?: string
  onSearchChange?: (query: string) => void
  agentFilter?: string | null
  onAgentFilterChange?: (agentId: string | null) => void
  autoScroll?: boolean
  className?: string
  height?: number
}

// Row types for the virtualized list
type RowType = 'step-divider' | 'message' | 'episode-event'

interface RowData {
  type: RowType
  step?: number
  message?: Message
  index: number
  isAlternate: boolean
}

// Check if a message is an episode event
function isEpisodeEvent(message: Message): boolean {
  return message.message_type !== undefined && message.message_type !== 'message'
}

// Estimate message height based on content length
// Messages are truncated in the UI with "Read more", so cap height
function estimateMessageHeight(content: string): number {
  const baseHeight = 100 // Avatar, header, padding
  const charsPerLine = 60
  const lineHeight = 24
  const maxVisibleLines = 6 // Messages truncate after ~4-6 lines
  const lines = Math.min(Math.ceil(content.length / charsPerLine), maxVisibleLines)
  return baseHeight + lines * lineHeight
}

// Step divider height is constant
const STEP_DIVIDER_HEIGHT = 48

// Episode event height - includes content + margins (my-2 = 16px)
// Action events with metadata can have 3 rows of content
const EPISODE_EVENT_HEIGHT = 110

// Minimum row height
const MIN_ROW_HEIGHT = 80

const Row = memo(function Row({
  data,
  index,
  style,
}: ListChildComponentProps<{
  rows: RowData[]
  selectedAgentId?: string
}>) {
  const row = data.rows[index]

  if (row.type === 'step-divider') {
    return (
      <div style={style}>
        <StepDivider step={row.step!} />
      </div>
    )
  }

  const message = row.message!

  // Handle episode events
  if (row.type === 'episode-event') {
    return (
      <div style={style} className="px-2">
        <EpisodeEventBubble
          id={message.id}
          messageType={message.message_type!}
          content={message.content}
          timestamp={message.timestamp}
          step={message.step}
          metadata={message.metadata}
        />
      </div>
    )
  }

  // Regular message
  const isHighlighted = data.selectedAgentId === message.sender_id

  return (
    <div style={style} className="px-2">
      <MessageBubble
        id={message.id}
        senderName={message.sender_name}
        receiverName={message.receiver_name}
        content={message.content}
        timestamp={message.timestamp}
        step={message.step}
        isHighlighted={isHighlighted}
        isAlternate={row.isAlternate}
      />
    </div>
  )
})

export function ConversationStream({
  messages,
  selectedAgentId,
  searchQuery = '',
  onSearchChange,
  agentFilter,
  onAgentFilterChange,
  autoScroll = true,
  className,
  height = 600,
}: ConversationStreamProps) {
  const listRef = useRef<List>(null)
  const outerRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [userScrolled, setUserScrolled] = useState(false)
  const rowHeightsRef = useRef<Map<number, number>>(new Map())

  // Get unique agent names for filter
  const agentNames = useMemo(() => {
    const names = new Set(messages.map((m) => m.sender_name).filter(Boolean) as string[])
    return Array.from(names)
  }, [messages])

  // Filter messages
  const filteredMessages = useMemo(() => {
    return messages.filter((msg) => {
      const matchesSearch =
        !searchQuery ||
        msg.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (msg.sender_name && msg.sender_name.toLowerCase().includes(searchQuery.toLowerCase()))

      const matchesAgent = !agentFilter || msg.sender_name === agentFilter

      return matchesSearch && matchesAgent
    })
  }, [messages, searchQuery, agentFilter])

  // Build row data with step dividers
  const rows = useMemo(() => {
    const result: RowData[] = []
    let currentStep = -1
    let messageIndex = 0

    for (const message of filteredMessages) {
      if (message.step !== currentStep) {
        result.push({
          type: 'step-divider',
          step: message.step,
          index: result.length,
          isAlternate: false,
        })
        currentStep = message.step
      }

      // Determine row type based on message type
      const rowType: RowType = isEpisodeEvent(message) ? 'episode-event' : 'message'

      result.push({
        type: rowType,
        message,
        index: result.length,
        isAlternate: messageIndex % 2 === 1,
      })
      messageIndex++
    }

    return result
  }, [filteredMessages])

  // Get item size for virtualization
  const getItemSize = useCallback(
    (index: number) => {
      // Return cached height if available
      if (rowHeightsRef.current.has(index)) {
        return rowHeightsRef.current.get(index)!
      }

      const row = rows[index]
      let height: number

      if (row.type === 'step-divider') {
        height = STEP_DIVIDER_HEIGHT
      } else if (row.type === 'episode-event') {
        // Episode events vary in height based on content
        const msgType = row.message?.message_type
        if (msgType === 'episode_action' || msgType === 'episode_step') {
          // Actions/steps have metadata row with step number, reward, status
          height = EPISODE_EVENT_HEIGHT
        } else if (msgType === 'episode_reset') {
          // Reset may have agents list
          height = EPISODE_EVENT_HEIGHT - 10
        } else {
          // Turn/close are simpler
          height = EPISODE_EVENT_HEIGHT - 20
        }
      } else {
        height = Math.max(MIN_ROW_HEIGHT, estimateMessageHeight(row.message!.content))
      }

      rowHeightsRef.current.set(index, height)
      return height
    },
    [rows]
  )

  // Reset row heights when messages change
  useEffect(() => {
    rowHeightsRef.current.clear()
    listRef.current?.resetAfterIndex(0)
  }, [filteredMessages])

  // Handle scroll events
  const handleScroll = useCallback(
    ({ scrollOffset, scrollUpdateWasRequested }: { scrollOffset: number; scrollUpdateWasRequested: boolean }) => {
      if (scrollUpdateWasRequested) return

      const list = listRef.current
      if (!list || !outerRef.current) return

      const scrollHeight = outerRef.current.scrollHeight
      const clientHeight = outerRef.current.clientHeight
      const atBottom = scrollOffset + clientHeight >= scrollHeight - 50

      setIsAtBottom(atBottom)
      if (!atBottom && !scrollUpdateWasRequested) {
        setUserScrolled(true)
      }
    },
    []
  )

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && isAtBottom && !userScrolled && rows.length > 0) {
      listRef.current?.scrollToItem(rows.length - 1, 'end')
    }
  }, [rows.length, autoScroll, isAtBottom, userScrolled])

  // Scroll to bottom handler
  const scrollToBottom = useCallback(() => {
    listRef.current?.scrollToItem(rows.length - 1, 'end')
    setUserScrolled(false)
    setIsAtBottom(true)
  }, [rows.length])

  // Item data for Row component
  const itemData = useMemo(
    () => ({
      rows,
      selectedAgentId,
    }),
    [rows, selectedAgentId]
  )

  if (messages.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-foreground-secondary',
          className
        )}
        style={{ height }}
      >
        No messages yet. Start the simulation to begin.
      </div>
    )
  }

  if (filteredMessages.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-foreground-secondary',
          className
        )}
        style={{ height }}
      >
        No messages match your filters.
      </div>
    )
  }

  return (
    <div className={cn('relative', className)}>
      {/* Search and filters */}
      {(onSearchChange || onAgentFilterChange) && (
        <div className="flex gap-3 mb-3 pb-3 border-b border-border items-center">
          {onSearchChange && (
            <div className="relative w-40 flex-shrink-0">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          )}

          {onAgentFilterChange && (
            <div className="relative flex-1 min-w-0">
              {/* Scrollable filter container */}
              <div
                className="flex gap-1 overflow-x-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent pb-1"
                style={{
                  scrollbarWidth: 'thin',
                  msOverflowStyle: 'none',
                }}
              >
                <Button
                  variant={agentFilter === null ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => onAgentFilterChange(null)}
                  className="text-xs flex-shrink-0"
                >
                  All
                </Button>
                {agentNames.map((name) => (
                  <Button
                    key={name}
                    variant={agentFilter === name ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() =>
                      onAgentFilterChange(agentFilter === name ? null : name)
                    }
                    className="text-xs flex-shrink-0"
                  >
                    <Filter className="h-3 w-3 mr-1" />
                    {name}
                  </Button>
                ))}
              </div>
              {/* Right fade indicator for overflow */}
              {agentNames.length > 5 && (
                <div className="absolute right-0 top-0 bottom-1 w-8 bg-gradient-to-l from-background to-transparent pointer-events-none" />
              )}
            </div>
          )}
        </div>
      )}

      {/* Message count */}
      <div className="flex justify-between items-center mb-2 text-xs text-foreground-muted">
        <span>
          {filteredMessages.length === messages.length
            ? `${messages.length} messages`
            : `${filteredMessages.length} of ${messages.length} messages`}
        </span>
      </div>

      {/* Virtualized list */}
      <List
        ref={listRef}
        outerRef={outerRef}
        height={height - 80} // Account for header
        itemCount={rows.length}
        itemSize={getItemSize}
        itemData={itemData}
        width="100%"
        onScroll={handleScroll}
        overscanCount={5}
      >
        {Row}
      </List>

      {/* Scroll to bottom button */}
      {!isAtBottom && rows.length > 10 && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 p-2 bg-primary text-primary-foreground rounded-full shadow-lg hover:bg-primary-hover transition-colors"
          title="Scroll to bottom"
        >
          <ArrowDown className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

export default ConversationStream
