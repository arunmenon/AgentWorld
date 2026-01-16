import { memo, useMemo } from 'react'
import { MessageSquare, Clock, Activity, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Message {
  id: string
  sender_id: string
  sender_name: string | null
  receiver_id?: string | null
  receiver_name?: string | null
  content: string
  step: number
  timestamp?: string | Date | null
}

export interface AgentStatsProps {
  agentId: string
  agentName: string
  messages: Message[]
  totalSteps: number
  className?: string
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  subValue?: string
}

function StatCard({ icon, label, value, subValue }: StatCardProps) {
  return (
    <div className="bg-secondary/50 rounded-lg p-4">
      <div className="flex items-center gap-2 text-foreground-muted mb-2">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subValue && (
        <div className="text-xs text-foreground-muted mt-1">{subValue}</div>
      )}
    </div>
  )
}

export const AgentStats = memo(function AgentStats({
  agentId,
  messages,
  totalSteps,
  className,
}: AgentStatsProps) {
  const stats = useMemo(() => {
    const sentMessages = messages.filter((m) => m.sender_id === agentId)
    const receivedMessages = messages.filter((m) => m.receiver_id === agentId)

    // Calculate activity per step
    const activityByStep = new Map<number, number>()
    for (const msg of sentMessages) {
      activityByStep.set(msg.step, (activityByStep.get(msg.step) || 0) + 1)
    }

    // Calculate average message length
    const totalLength = sentMessages.reduce((sum, m) => sum + m.content.length, 0)
    const avgLength = sentMessages.length > 0 ? Math.round(totalLength / sentMessages.length) : 0

    // Calculate response rate (messages received vs sent)
    const responseRate =
      receivedMessages.length > 0
        ? Math.round((sentMessages.length / receivedMessages.length) * 100)
        : 0

    // Get most active step
    let mostActiveStep = 0
    let maxActivity = 0
    activityByStep.forEach((count, step) => {
      if (count > maxActivity) {
        maxActivity = count
        mostActiveStep = step
      }
    })

    // Calculate activity timeline for sparkline
    const activityTimeline: number[] = []
    for (let step = 1; step <= totalSteps; step++) {
      activityTimeline.push(activityByStep.get(step) || 0)
    }

    return {
      messagesSent: sentMessages.length,
      messagesReceived: receivedMessages.length,
      avgLength,
      responseRate,
      mostActiveStep,
      maxActivity,
      activityTimeline,
      activeSteps: activityByStep.size,
    }
  }, [agentId, messages, totalSteps])

  // Simple sparkline renderer
  const sparkline = useMemo(() => {
    const { activityTimeline } = stats
    if (activityTimeline.length === 0) return null

    const max = Math.max(...activityTimeline, 1)
    const width = 200
    const height = 40
    const barWidth = width / activityTimeline.length - 1

    return (
      <svg width={width} height={height} className="mt-2">
        {activityTimeline.map((value, index) => {
          const barHeight = (value / max) * height
          return (
            <rect
              key={index}
              x={index * (barWidth + 1)}
              y={height - barHeight}
              width={barWidth}
              height={barHeight}
              className={cn(
                'fill-primary/60',
                value === stats.maxActivity && 'fill-primary'
              )}
              rx={1}
            />
          )
        })}
      </svg>
    )
  }, [stats])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<MessageSquare className="h-4 w-4" />}
          label="Messages Sent"
          value={stats.messagesSent}
          subValue={`${stats.messagesReceived} received`}
        />
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          label="Active Steps"
          value={stats.activeSteps}
          subValue={`of ${totalSteps} total`}
        />
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="Avg Message Length"
          value={stats.avgLength}
          subValue="characters"
        />
        <StatCard
          icon={<TrendingUp className="h-4 w-4" />}
          label="Most Active"
          value={`Step ${stats.mostActiveStep || '-'}`}
          subValue={stats.maxActivity > 0 ? `${stats.maxActivity} messages` : undefined}
        />
      </div>

      {/* Activity timeline */}
      <div className="bg-secondary/50 rounded-lg p-4">
        <div className="flex items-center gap-2 text-foreground-muted mb-3">
          <Activity className="h-4 w-4" />
          <span className="text-xs font-medium">Activity Timeline</span>
        </div>
        <div className="flex justify-center">{sparkline}</div>
        <div className="flex justify-between text-xs text-foreground-muted mt-2">
          <span>Step 1</span>
          <span>Step {totalSteps}</span>
        </div>
      </div>
    </div>
  )
})

export default AgentStats
