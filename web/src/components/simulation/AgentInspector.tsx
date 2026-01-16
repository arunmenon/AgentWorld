import { memo, useState, useMemo } from 'react'
import { X, User, MessageSquare, Brain, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { AgentStats, type Message } from './AgentStats'
import { AgentMemoryList, type Memory } from './AgentMemoryList'
import { ConversationStream } from './ConversationStream'

export interface Agent {
  id: string
  name: string
  background?: string | null
  traits?: Record<string, number> | null
  memory_count?: number
  model?: string | null
}

export interface AgentInspectorProps {
  agent: Agent | null
  messages: Message[]
  memories: Memory[]
  totalSteps: number
  onClose: () => void
  isOpen: boolean
  className?: string
}

type TabId = 'overview' | 'messages' | 'memories' | 'stats'

interface Tab {
  id: TabId
  label: string
  icon: React.ElementType
}

const tabs: Tab[] = [
  { id: 'overview', label: 'Overview', icon: User },
  { id: 'messages', label: 'Messages', icon: MessageSquare },
  { id: 'memories', label: 'Memories', icon: Brain },
  { id: 'stats', label: 'Stats', icon: BarChart3 },
]

// Simple radar chart for traits
function TraitsRadarChart({ traits }: { traits: Record<string, number> }) {
  const traitEntries = Object.entries(traits)
  if (traitEntries.length === 0) return null

  // Larger viewBox to accommodate labels, but display at reasonable size
  const viewBoxSize = 280
  const displaySize = 200
  const center = viewBoxSize / 2
  const radius = 55
  const angleStep = (2 * Math.PI) / traitEntries.length

  // Calculate points for the trait polygon
  const points = traitEntries.map(([, value], index) => {
    const angle = index * angleStep - Math.PI / 2
    const r = radius * value
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    }
  })

  // Create path for the polygon
  const pathData = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ') + ' Z'

  // Helper to get text anchor based on angle position
  const getTextAnchor = (angle: number): 'start' | 'middle' | 'end' => {
    // Normalize angle to 0-2PI range
    const normalized = ((angle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)
    // Top and bottom labels are centered
    if (normalized < Math.PI * 0.15 || normalized > Math.PI * 1.85) return 'middle'
    if (normalized > Math.PI * 0.85 && normalized < Math.PI * 1.15) return 'middle'
    // Right side labels are left-aligned (start)
    if (normalized < Math.PI) return 'start'
    // Left side labels are right-aligned (end)
    return 'end'
  }

  // Create labels with proper positioning
  const labels = traitEntries.map(([name, value], index) => {
    const angle = index * angleStep - Math.PI / 2
    const labelRadius = radius + 22
    const x = center + labelRadius * Math.cos(angle)
    const y = center + labelRadius * Math.sin(angle)

    // Capitalize first letter
    const displayName = name.charAt(0).toUpperCase() + name.slice(1)

    // Calculate text anchor based on position around the circle
    const textAnchor = getTextAnchor(angle + Math.PI / 2)

    // Adjust y position for top/bottom labels to avoid overlap
    let dy = 0
    const normalizedAngle = ((angle + Math.PI / 2) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI)
    if (normalizedAngle < Math.PI * 0.15 || normalizedAngle > Math.PI * 1.85) {
      dy = -8 // Top label - move up
    } else if (normalizedAngle > Math.PI * 0.85 && normalizedAngle < Math.PI * 1.15) {
      dy = 8 // Bottom label - move down
    }

    return {
      x,
      y,
      name: displayName,
      value,
      textAnchor,
      dy,
    }
  })

  return (
    <svg
      width={displaySize}
      height={displaySize}
      viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      className="mx-auto"
      style={{ overflow: 'visible' }}
    >
      {/* Background circles */}
      {[0.25, 0.5, 0.75, 1].map((scale) => (
        <circle
          key={scale}
          cx={center}
          cy={center}
          r={radius * scale}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.1}
        />
      ))}

      {/* Axis lines */}
      {traitEntries.map((_, index) => {
        const angle = index * angleStep - Math.PI / 2
        return (
          <line
            key={index}
            x1={center}
            y1={center}
            x2={center + radius * Math.cos(angle)}
            y2={center + radius * Math.sin(angle)}
            stroke="currentColor"
            strokeOpacity={0.1}
          />
        )
      })}

      {/* Trait polygon */}
      <path
        d={pathData}
        fill="currentColor"
        fillOpacity={0.2}
        stroke="currentColor"
        strokeWidth={2}
        className="text-primary"
      />

      {/* Data points */}
      {points.map((p, index) => (
        <circle
          key={index}
          cx={p.x}
          cy={p.y}
          r={4}
          className="fill-primary"
        />
      ))}

      {/* Labels */}
      {labels.map((label, index) => (
        <text
          key={index}
          x={label.x}
          y={label.y + label.dy}
          textAnchor={label.textAnchor}
          dominantBaseline="middle"
          className="fill-foreground-secondary text-[11px]"
        >
          {label.name}
        </text>
      ))}
    </svg>
  )
}

export const AgentInspector = memo(function AgentInspector({
  agent,
  messages,
  memories,
  totalSteps,
  onClose,
  isOpen,
  className,
}: AgentInspectorProps) {
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  // Filter messages for this agent
  const agentMessages = useMemo(() => {
    if (!agent) return []
    return messages.filter(
      (m) => m.sender_id === agent.id || m.receiver_id === agent.id
    )
  }, [messages, agent])

  // Filter memories for this agent
  const agentMemories = useMemo(() => {
    if (!agent) return []
    return memories.filter((m) => m.agent_id === agent.id)
  }, [memories, agent])

  if (!isOpen || !agent) {
    return null
  }

  return (
    <div
      className={cn(
        'fixed inset-y-0 right-0 w-96 bg-background border-l border-border shadow-xl z-50',
        'transform transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : 'translate-x-full',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
            <span className="text-lg font-bold text-primary-foreground">
              {agent.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <h2 className="font-semibold">{agent.name}</h2>
            {agent.model && (
              <p className="text-xs text-foreground-muted">{agent.model}</p>
            )}
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-foreground-muted hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="p-4 overflow-y-auto h-[calc(100vh-140px)]">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Background */}
            {agent.background && (
              <div>
                <h3 className="text-sm font-medium text-foreground-muted mb-2">
                  Background
                </h3>
                <p className="text-sm">{agent.background}</p>
              </div>
            )}

            {/* Traits */}
            {agent.traits && Object.keys(agent.traits).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-foreground-muted mb-3">
                  Personality Traits
                </h3>
                <TraitsRadarChart traits={agent.traits} />

                {/* Trait list */}
                <div className="mt-4 space-y-2">
                  {Object.entries(agent.traits).map(([trait, value]) => (
                    <div key={trait} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{trait}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-foreground-muted w-8">
                          {(value * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-secondary/50 rounded-lg p-3">
                <div className="text-2xl font-bold">{agentMessages.length}</div>
                <div className="text-xs text-foreground-muted">Messages</div>
              </div>
              <div className="bg-secondary/50 rounded-lg p-3">
                <div className="text-2xl font-bold">{agentMemories.length}</div>
                <div className="text-xs text-foreground-muted">Memories</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'messages' && (
          <ConversationStream
            messages={agentMessages}
            height={500}
          />
        )}

        {activeTab === 'memories' && (
          <AgentMemoryList
            memories={agentMemories}
            agentId={agent.id}
          />
        )}

        {activeTab === 'stats' && (
          <AgentStats
            agentId={agent.id}
            agentName={agent.name}
            messages={messages}
            totalSteps={totalSteps}
          />
        )}
      </div>
    </div>
  )
})

export default AgentInspector
