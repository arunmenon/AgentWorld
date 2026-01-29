/**
 * Reward Chart - Visualize reward progression for episodes.
 *
 * Shows cumulative reward over time for single or multiple episodes,
 * with comparison views and statistics.
 */

import { useMemo } from 'react'
import { TrendingUp, Award, Target, Percent } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Card, Badge } from '@/components/ui'
import { api, type EpisodeHistory } from '@/lib/api'
import { cn } from '@/lib/utils'

// Episode colors for multi-episode comparison
const EPISODE_COLORS = [
  '#22c55e', // green
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
]

interface RewardChartProps {
  simulationId: string
  appId: string
  selectedEpisodeId?: string
  className?: string
}

export function RewardChart({
  simulationId,
  appId,
  selectedEpisodeId,
  className,
}: RewardChartProps) {
  // Fetch episodes
  const { data: episodesData, isLoading } = useQuery({
    queryKey: ['episodes', simulationId, appId],
    queryFn: () => api.listEpisodes(simulationId, appId, true),
    refetchInterval: 5000,
  })

  const episodes = episodesData?.episodes ?? []

  // Prepare chart data for each episode
  const chartData = useMemo(() => {
    return episodes.map((ep) => {
      let cumulative = 0
      return {
        episodeId: ep.episode_id,
        data: ep.snapshots.map((s) => {
          cumulative += s.reward
          return {
            step: s.step,
            reward: s.reward,
            cumulative,
            action: s.action,
          }
        }),
        totalReward: ep.total_reward,
        terminated: ep.terminated,
        truncated: ep.truncated,
      }
    })
  }, [episodes])

  // Calculate stats
  const stats = useMemo(() => {
    if (episodes.length === 0) return null

    const completed = episodes.filter((e) => e.ended_at)
    const successful = completed.filter((e) => e.terminated)
    const rewards = completed.map((e) => e.total_reward)
    const avgReward = rewards.length > 0
      ? rewards.reduce((a, b) => a + b, 0) / rewards.length
      : 0
    const bestIdx = rewards.indexOf(Math.max(...rewards))

    return {
      total: episodes.length,
      completed: completed.length,
      successful: successful.length,
      successRate: completed.length > 0
        ? Math.round((successful.length / completed.length) * 100)
        : 0,
      avgReward,
      bestEpisode: bestIdx >= 0 ? { index: bestIdx, reward: rewards[bestIdx] } : null,
    }
  }, [episodes])

  // Get max values for scaling
  const maxStep = useMemo(() => {
    return Math.max(...chartData.map((ep) => ep.data.length), 1)
  }, [chartData])

  const [minReward, maxReward] = useMemo(() => {
    const allRewards = chartData.flatMap((ep) => ep.data.map((d) => d.cumulative))
    if (allRewards.length === 0) return [-1, 1]
    return [Math.min(...allRewards, 0), Math.max(...allRewards, 0)]
  }, [chartData])

  // SVG dimensions
  const width = 500
  const height = 200
  const padding = { top: 20, right: 20, bottom: 30, left: 50 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  // Scale functions
  const xScale = (step: number) => (step / maxStep) * chartWidth + padding.left
  const yScale = (reward: number) => {
    const range = maxReward - minReward || 1
    return height - padding.bottom - ((reward - minReward) / range) * chartHeight
  }

  if (isLoading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary animate-pulse" />
          <span>Loading rewards...</span>
        </div>
      </Card>
    )
  }

  if (episodes.length === 0) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-semibold">Reward Progression</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          No episodes recorded yet.
        </p>
      </Card>
    )
  }

  return (
    <Card className={cn('p-6', className)}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Reward Progression</h3>
      </div>

      {/* Chart */}
      <div className="mb-4">
        <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
          {/* Grid lines */}
          <g className="text-muted-foreground/30">
            {/* Horizontal grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct) => {
              const y = padding.top + chartHeight * (1 - pct)
              const value = minReward + (maxReward - minReward) * pct
              return (
                <g key={pct}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke="currentColor"
                    strokeDasharray="4,4"
                  />
                  <text
                    x={padding.left - 5}
                    y={y}
                    textAnchor="end"
                    alignmentBaseline="middle"
                    className="text-xs fill-muted-foreground"
                  >
                    {value.toFixed(2)}
                  </text>
                </g>
              )
            })}
            {/* Zero line */}
            {minReward < 0 && maxReward > 0 && (
              <line
                x1={padding.left}
                y1={yScale(0)}
                x2={width - padding.right}
                y2={yScale(0)}
                stroke="currentColor"
                strokeWidth={2}
              />
            )}
          </g>

          {/* X-axis label */}
          <text
            x={width / 2}
            y={height - 5}
            textAnchor="middle"
            className="text-xs fill-muted-foreground"
          >
            Step
          </text>

          {/* Y-axis label */}
          <text
            x={15}
            y={height / 2}
            textAnchor="middle"
            transform={`rotate(-90, 15, ${height / 2})`}
            className="text-xs fill-muted-foreground"
          >
            Cumulative Reward
          </text>

          {/* Episode lines */}
          {chartData.map((ep, epIdx) => {
            if (ep.data.length < 2) return null

            const isSelected = selectedEpisodeId === ep.episodeId || !selectedEpisodeId
            const color = EPISODE_COLORS[epIdx % EPISODE_COLORS.length]
            const opacity = isSelected ? 1 : 0.3
            const strokeWidth = isSelected && selectedEpisodeId ? 3 : 2

            // Create path
            const pathD = ep.data
              .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(d.step)} ${yScale(d.cumulative)}`)
              .join(' ')

            return (
              <g key={ep.episodeId}>
                <path
                  d={pathD}
                  fill="none"
                  stroke={color}
                  strokeWidth={strokeWidth}
                  opacity={opacity}
                />
                {/* Dots at each step */}
                {isSelected && ep.data.map((d) => (
                  <circle
                    key={d.step}
                    cx={xScale(d.step)}
                    cy={yScale(d.cumulative)}
                    r={3}
                    fill={color}
                    opacity={opacity}
                  />
                ))}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 mb-4">
        {chartData.map((ep, idx) => (
          <Badge
            key={ep.episodeId}
            variant="outline"
            className={cn(
              'text-xs',
              selectedEpisodeId === ep.episodeId && 'ring-2 ring-primary'
            )}
            style={{ borderColor: EPISODE_COLORS[idx % EPISODE_COLORS.length] }}
          >
            <span
              className="w-2 h-2 rounded-full mr-1"
              style={{ backgroundColor: EPISODE_COLORS[idx % EPISODE_COLORS.length] }}
            />
            Episode {idx + 1}
            {ep.terminated && ' ✅'}
            {ep.truncated && ' ⏱️'}
          </Badge>
        ))}
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="p-2 bg-muted rounded-lg">
            <div className="flex items-center gap-1 text-muted-foreground">
              <Award className="h-4 w-4" />
              Best Episode
            </div>
            <div className="font-medium">
              {stats.bestEpisode
                ? `Episode ${stats.bestEpisode.index + 1} (${stats.bestEpisode.reward.toFixed(2)})`
                : '—'
              }
            </div>
          </div>
          <div className="p-2 bg-muted rounded-lg">
            <div className="flex items-center gap-1 text-muted-foreground">
              <Target className="h-4 w-4" />
              Average Reward
            </div>
            <div className={cn(
              'font-medium',
              stats.avgReward >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {stats.avgReward.toFixed(3)}
            </div>
          </div>
          <div className="p-2 bg-muted rounded-lg">
            <div className="flex items-center gap-1 text-muted-foreground">
              <Percent className="h-4 w-4" />
              Success Rate
            </div>
            <div className="font-medium">
              {stats.successRate}% ({stats.successful}/{stats.completed})
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

// Compact version for embedding in other panels
export function RewardChartCompact({
  episodes,
  selectedEpisodeId,
}: {
  episodes: EpisodeHistory[]
  selectedEpisodeId?: string
}) {
  // Same logic but smaller size
  const chartData = useMemo(() => {
    return episodes.map((ep) => {
      let cumulative = 0
      return {
        episodeId: ep.episode_id,
        data: ep.snapshots.map((s) => {
          cumulative += s.reward
          return { step: s.step, cumulative }
        }),
      }
    })
  }, [episodes])

  const maxStep = Math.max(...chartData.map((ep) => ep.data.length), 1)
  const allRewards = chartData.flatMap((ep) => ep.data.map((d) => d.cumulative))
  const [minReward, maxReward] = allRewards.length > 0
    ? [Math.min(...allRewards, 0), Math.max(...allRewards, 0)]
    : [-1, 1]

  const width = 200
  const height = 60
  const xScale = (step: number) => (step / maxStep) * (width - 10) + 5
  const yScale = (reward: number) => {
    const range = maxReward - minReward || 1
    return height - 5 - ((reward - minReward) / range) * (height - 10)
  }

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`}>
      {chartData.map((ep, idx) => {
        if (ep.data.length < 2) return null
        const isSelected = selectedEpisodeId === ep.episodeId
        const color = EPISODE_COLORS[idx % EPISODE_COLORS.length]
        const pathD = ep.data
          .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(d.step)} ${yScale(d.cumulative)}`)
          .join(' ')

        return (
          <path
            key={ep.episodeId}
            d={pathD}
            fill="none"
            stroke={color}
            strokeWidth={isSelected ? 2 : 1}
            opacity={isSelected || !selectedEpisodeId ? 1 : 0.3}
          />
        )
      })}
    </svg>
  )
}
