import { useRef, useEffect, useMemo, useCallback, memo } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { cn } from '@/lib/utils'

export interface Agent {
  id: string
  name: string
  background?: string | null
  traits?: Record<string, number> | null
}

export interface Message {
  id: string
  sender_id: string
  sender_name: string | null
  receiver_id?: string | null
  receiver_name?: string | null
  content: string
  step: number
}

export interface TopologyGraphProps {
  agents: Agent[]
  messages: Message[]
  selectedAgentId?: string
  onAgentSelect?: (agentId: string) => void
  width?: number
  height?: number
  className?: string
}

interface GraphNode extends NodeObject {
  id: string
  name: string
  color: string
  messageCount: number
  isThinking?: boolean
  isSelected?: boolean
}

interface GraphLink extends LinkObject {
  source: string
  target: string
  messageCount: number
  color: string
}

// Generate consistent colors from agent name
function getAgentColor(name: string): string {
  const colors = [
    '#6366f1', // indigo
    '#10b981', // emerald
    '#f59e0b', // amber
    '#f43f5e', // rose
    '#06b6d4', // cyan
    '#8b5cf6', // violet
    '#f97316', // orange
    '#14b8a6', // teal
    '#ec4899', // pink
    '#84cc16', // lime
  ]

  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

export const TopologyGraph = memo(function TopologyGraph({
  agents,
  messages,
  selectedAgentId,
  onAgentSelect,
  width = 400,
  height = 300,
  className,
}: TopologyGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<ForceGraphMethods<any, any>>()

  // Calculate message counts per agent
  const agentMessageCounts = useMemo(() => {
    const agentCounts = new Map<string, number>()

    for (const msg of messages) {
      // Count messages per agent
      agentCounts.set(msg.sender_id, (agentCounts.get(msg.sender_id) || 0) + 1)
    }

    return agentCounts
  }, [messages])

  // Build graph data
  const graphData = useMemo(() => {
    const nodes: GraphNode[] = agents.map((agent) => ({
      id: agent.id,
      name: agent.name,
      color: getAgentColor(agent.name),
      messageCount: agentMessageCounts.get(agent.id) || 0,
      isSelected: agent.id === selectedAgentId,
    }))

    // Build edges from message flow
    const linkMap = new Map<string, GraphLink>()

    for (const msg of messages) {
      if (!msg.receiver_id) continue

      const edgeKey = `${msg.sender_id}->${msg.receiver_id}`
      const reverseKey = `${msg.receiver_id}->${msg.sender_id}`

      // Use undirected edge (combine both directions)
      const combinedKey =
        msg.sender_id < msg.receiver_id ? edgeKey : reverseKey

      if (!linkMap.has(combinedKey)) {
        linkMap.set(combinedKey, {
          source: msg.sender_id < msg.receiver_id ? msg.sender_id : msg.receiver_id,
          target: msg.sender_id < msg.receiver_id ? msg.receiver_id : msg.sender_id,
          messageCount: 0,
          color: 'rgba(100, 116, 139, 0.4)',
        })
      }

      const link = linkMap.get(combinedKey)!
      link.messageCount += 1
    }

    const links = Array.from(linkMap.values())

    return { nodes, links }
  }, [agents, messages, selectedAgentId, agentMessageCounts])

  // Node rendering
  const nodeCanvasObject = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      // Guard against undefined/NaN coordinates during initial render
      if (node.x === undefined || node.y === undefined || isNaN(node.x) || isNaN(node.y)) {
        return
      }

      const label = node.name
      const fontSize = 12 / globalScale
      // Make selected nodes slightly larger
      const baseRadius = Math.max(8, Math.min(20, 8 + node.messageCount / 2))
      const nodeRadius = node.isSelected ? baseRadius * 1.2 : baseRadius

      // Draw selection ring/halo first (behind the node)
      if (node.isSelected) {
        // Outer glow ring
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius + 8 / globalScale, 0, 2 * Math.PI)
        ctx.strokeStyle = node.color
        ctx.lineWidth = 3 / globalScale
        ctx.globalAlpha = 0.4
        ctx.stroke()
        ctx.globalAlpha = 1

        // Middle ring
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius + 4 / globalScale, 0, 2 * Math.PI)
        ctx.strokeStyle = '#ffffff'
        ctx.lineWidth = 2 / globalScale
        ctx.stroke()
      }

      // Draw node circle
      ctx.beginPath()
      ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI)

      // Fill with gradient based on activity
      const gradient = ctx.createRadialGradient(
        node.x,
        node.y,
        0,
        node.x,
        node.y,
        nodeRadius
      )
      // Brighter colors for selected node
      if (node.isSelected) {
        gradient.addColorStop(0, '#ffffff')
        gradient.addColorStop(0.3, node.color)
        gradient.addColorStop(1, node.color + 'cc')
      } else {
        gradient.addColorStop(0, node.color)
        gradient.addColorStop(1, node.color + '80')
      }
      ctx.fillStyle = gradient
      ctx.fill()

      // Add white border for selected node
      if (node.isSelected) {
        ctx.strokeStyle = '#ffffff'
        ctx.lineWidth = 2 / globalScale
        ctx.stroke()
      }

      // Draw label
      ctx.font = `${fontSize}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#fff'

      // Draw label background
      const textWidth = ctx.measureText(label).width
      const bgPadding = 2 / globalScale
      const bgHeight = fontSize + bgPadding * 2
      const bgY = node.y + nodeRadius + 4 / globalScale

      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
      ctx.fillRect(
        node.x - textWidth / 2 - bgPadding,
        bgY - bgHeight / 2,
        textWidth + bgPadding * 2,
        bgHeight
      )

      // Draw label text
      ctx.fillStyle = '#fff'
      ctx.fillText(label, node.x, bgY)

      // Draw message count badge if > 0
      if (node.messageCount > 0) {
        const badgeRadius = 6 / globalScale
        const badgeX = node.x + nodeRadius * 0.7
        const badgeY = node.y - nodeRadius * 0.7

        ctx.beginPath()
        ctx.arc(badgeX, badgeY, badgeRadius, 0, 2 * Math.PI)
        ctx.fillStyle = '#22c55e'
        ctx.fill()

        ctx.font = `bold ${8 / globalScale}px Inter, sans-serif`
        ctx.fillStyle = '#fff'
        ctx.fillText(String(node.messageCount), badgeX, badgeY)
      }
    },
    []
  )

  // Link rendering
  const linkCanvasObject = useCallback(
    (link: GraphLink, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const source = link.source as unknown as GraphNode
      const target = link.target as unknown as GraphNode

      // Guard against undefined/NaN coordinates
      if (source.x === undefined || source.y === undefined || target.x === undefined || target.y === undefined) return
      if (isNaN(source.x) || isNaN(source.y) || isNaN(target.x) || isNaN(target.y)) return

      // Calculate line width based on message count
      const lineWidth = Math.max(1, Math.min(5, link.messageCount / 2)) / globalScale

      ctx.beginPath()
      ctx.moveTo(source.x, source.y)
      ctx.lineTo(target.x, target.y)

      // Create gradient along the link
      const gradient = ctx.createLinearGradient(source.x, source.y, target.x, target.y)
      gradient.addColorStop(0, source.color + '60')
      gradient.addColorStop(1, target.color + '60')

      ctx.strokeStyle = gradient
      ctx.lineWidth = lineWidth
      ctx.stroke()
    },
    []
  )

  // Handle node click
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      if (onAgentSelect) {
        onAgentSelect(node.id)
      }
    },
    [onAgentSelect]
  )

  // Center graph on mount
  useEffect(() => {
    if (graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400)
      }, 500)
    }
  }, [agents.length])

  if (agents.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-foreground-secondary bg-secondary/50 rounded-lg',
          className
        )}
        style={{ width, height }}
      >
        No agents to display
      </div>
    )
  }

  return (
    <div
      className={cn('rounded-lg overflow-hidden bg-background-secondary', className)}
      style={{ width, height }}
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={width}
        height={height}
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        onNodeClick={handleNodeClick}
        nodeRelSize={8}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        cooldownTicks={100}
        onEngineStop={() => graphRef.current?.zoomToFit(200)}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        backgroundColor="transparent"
      />
    </div>
  )
})

export default TopologyGraph
