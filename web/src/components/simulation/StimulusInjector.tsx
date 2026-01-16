import { useState, memo } from 'react'
import { Zap, ChevronDown, ChevronUp, Send, Users } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

export interface Agent {
  id: string
  name: string
}

export interface StimulusInjectorProps {
  agents: Agent[]
  onInject: (content: string, targetAgents: string[]) => Promise<void>
  disabled?: boolean
  className?: string
}

export const StimulusInjector = memo(function StimulusInjector({
  agents,
  onInject,
  disabled = false,
  className,
}: StimulusInjectorProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [content, setContent] = useState('')
  const [targetAgents, setTargetAgents] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  const toggleAgent = (agentId: string) => {
    setTargetAgents((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId]
    )
  }

  const selectAllAgents = () => {
    setTargetAgents(agents.map((a) => a.id))
  }

  const clearSelection = () => {
    setTargetAgents([])
  }

  const handleSubmit = async () => {
    if (!content.trim() || isSubmitting) return

    setIsSubmitting(true)
    try {
      await onInject(content, targetAgents.length > 0 ? targetAgents : agents.map((a) => a.id))
      setContent('')
      setTargetAgents([])
      setIsExpanded(false)
    } catch (error) {
      console.error('Failed to inject stimulus:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={cn('border border-border rounded-lg', className)}>
      {/* Header (always visible) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between p-3 text-sm font-medium',
          'hover:bg-secondary/50 transition-colors rounded-t-lg',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-400" />
          <span>Inject Stimulus</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {/* Expanded content */}
      {isExpanded && !disabled && (
        <div className="p-3 pt-0 space-y-3">
          {/* Content input */}
          <div>
            <label className="text-xs text-foreground-muted mb-1 block">
              Stimulus Content
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter an event, announcement, or prompt to inject..."
              className="w-full p-2 text-sm bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              rows={3}
            />
          </div>

          {/* Target agents */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-foreground-muted flex items-center gap-1">
                <Users className="h-3 w-3" />
                Target Agents
              </label>
              <div className="flex gap-1">
                <button
                  onClick={selectAllAgents}
                  className="text-xs text-primary hover:underline"
                >
                  All
                </button>
                <span className="text-foreground-muted">|</span>
                <button
                  onClick={clearSelection}
                  className="text-xs text-primary hover:underline"
                >
                  None
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-1">
              {agents.map((agent) => {
                const isSelected = targetAgents.includes(agent.id)
                return (
                  <Badge
                    key={agent.id}
                    variant={isSelected ? 'default' : 'outline'}
                    className={cn(
                      'cursor-pointer transition-colors',
                      isSelected && 'bg-primary text-primary-foreground'
                    )}
                    onClick={() => toggleAgent(agent.id)}
                  >
                    {agent.name}
                  </Badge>
                )
              })}
            </div>

            {targetAgents.length === 0 && (
              <p className="text-xs text-foreground-muted mt-1">
                All agents will receive the stimulus
              </p>
            )}
          </div>

          {/* Submit button */}
          <Button
            onClick={handleSubmit}
            disabled={!content.trim() || isSubmitting}
            className="w-full"
            size="sm"
          >
            {isSubmitting ? (
              <>
                <span className="animate-spin mr-2">...</span>
                Injecting...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Inject Stimulus
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  )
})

export default StimulusInjector
