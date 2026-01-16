import { memo, useState, useMemo } from 'react'
import { Brain, Eye, Lightbulb, Target, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button, Badge } from '@/components/ui'

export interface Memory {
  id: string
  agent_id: string
  type: 'observation' | 'reflection' | 'plan' | 'fact'
  content: string
  importance?: number
  created_at?: string
  step?: number
}

export interface AgentMemoryListProps {
  memories: Memory[]
  agentId: string
  className?: string
}

const memoryTypeConfig: Record<
  Memory['type'],
  { icon: React.ElementType; color: string; label: string }
> = {
  observation: {
    icon: Eye,
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    label: 'Observation',
  },
  reflection: {
    icon: Brain,
    color: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    label: 'Reflection',
  },
  plan: {
    icon: Target,
    color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    label: 'Plan',
  },
  fact: {
    icon: Lightbulb,
    color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    label: 'Fact',
  },
}

interface MemoryItemProps {
  memory: Memory
  isExpanded: boolean
  onToggle: () => void
}

const MemoryItem = memo(function MemoryItem({
  memory,
  isExpanded,
  onToggle,
}: MemoryItemProps) {
  const config = memoryTypeConfig[memory.type] || memoryTypeConfig.observation
  const Icon = config.icon

  const preview = memory.content.length > 100
    ? memory.content.slice(0, 100) + '...'
    : memory.content

  return (
    <div
      className={cn(
        'border rounded-lg p-3 transition-colors cursor-pointer hover:bg-secondary/50',
        config.color.split(' ').slice(1).join(' ')
      )}
      onClick={onToggle}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'flex-shrink-0 p-1.5 rounded-md',
            config.color.split(' ').slice(1, 2).join(' ')
          )}
        >
          <Icon className={cn('h-4 w-4', config.color.split(' ')[0])} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="text-xs">
              {config.label}
            </Badge>
            {memory.importance !== undefined && (
              <span className="text-xs text-foreground-muted">
                Importance: {(memory.importance * 100).toFixed(0)}%
              </span>
            )}
            {memory.step !== undefined && (
              <span className="text-xs text-foreground-muted">
                Step {memory.step}
              </span>
            )}
          </div>

          <div className="text-sm">
            {isExpanded ? (
              <p className="whitespace-pre-wrap">{memory.content}</p>
            ) : (
              <p className="text-foreground-secondary">{preview}</p>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 text-foreground-muted">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </div>
      </div>
    </div>
  )
})

export const AgentMemoryList = memo(function AgentMemoryList({
  memories,
  agentId,
  className,
}: AgentMemoryListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [filterType, setFilterType] = useState<Memory['type'] | 'all'>('all')

  // Filter memories by agent and type
  const filteredMemories = useMemo(() => {
    return memories
      .filter((m) => m.agent_id === agentId)
      .filter((m) => filterType === 'all' || m.type === filterType)
      .sort((a, b) => {
        // Sort by step (descending) then by importance (descending)
        if (a.step !== b.step) {
          return (b.step || 0) - (a.step || 0)
        }
        return (b.importance || 0) - (a.importance || 0)
      })
  }, [memories, agentId, filterType])

  // Count memories by type
  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: 0 }
    for (const memory of memories.filter((m) => m.agent_id === agentId)) {
      counts.all++
      counts[memory.type] = (counts[memory.type] || 0) + 1
    }
    return counts
  }, [memories, agentId])

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  if (typeCounts.all === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center py-8 text-foreground-secondary',
          className
        )}
      >
        <Brain className="h-8 w-8 mb-2 opacity-50" />
        <p className="text-sm">No memories recorded yet</p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Type filters */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={filterType === 'all' ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setFilterType('all')}
          className="text-xs"
        >
          All ({typeCounts.all})
        </Button>
        {(['observation', 'reflection', 'plan', 'fact'] as const).map((type) => {
          const count = typeCounts[type] || 0
          if (count === 0) return null

          const config = memoryTypeConfig[type]
          const Icon = config.icon

          return (
            <Button
              key={type}
              variant={filterType === type ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setFilterType(type)}
              className="text-xs gap-1"
            >
              <Icon className="h-3 w-3" />
              {config.label} ({count})
            </Button>
          )
        })}
      </div>

      {/* Memory list */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {filteredMemories.map((memory) => (
          <MemoryItem
            key={memory.id}
            memory={memory}
            isExpanded={expandedIds.has(memory.id)}
            onToggle={() => toggleExpanded(memory.id)}
          />
        ))}
      </div>

      {filteredMemories.length === 0 && filterType !== 'all' && (
        <div className="text-center py-4 text-foreground-secondary text-sm">
          No {memoryTypeConfig[filterType].label.toLowerCase()}s found
        </div>
      )}
    </div>
  )
})

export default AgentMemoryList
