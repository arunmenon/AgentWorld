import { useRef, useEffect, useMemo, useCallback, memo, useState } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { cn } from '@/lib/utils'

// Threshold for hiding labels (show only on hover when exceeded)
const LABEL_THRESHOLD = 20

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
  isHovered?: boolean
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
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)

  // Determine if we should show labels for all nodes or only on hover
  const showAllLabels = agents.length <= LABEL_THRESHOLD

  // Calculate dynamic node size based on agent count and container size
  // This ensures nodes always fit properly regardless of how many agents there are
  const nodeConfig = useMemo(() => {
    const agentCount = agents.length
    const containerArea = width * height
    const minDimension = Math.min(width, height)

    // Base radius scales inversely with agent count
    // For 1-2 agents: smaller nodes (they'd otherwise dominate)
    // For 3-10 agents: medium nodes
    // For 10+ agents: even smaller nodes
    let baseRadius: number
    let maxRadius: number

    if (agentCount <= 2) {
      // Very few agents - use small fixed size to prevent dominating the view
      baseRadius = 4
      maxRadius = 6
    } else if (agentCount <= 5) {
      baseRadius = 3.5
      maxRadius = 5
    } else if (agentCount <= 10) {
      baseRadius = 3
      maxRadius = 4.5
    } else if (agentCount <= 20) {
      baseRadius = 2.5
      maxRadius = 4
    } else {
      // Many agents - very small nodes
      baseRadius = 2
      maxRadius = 3
    }

    // Font size also scales with agent count
    const fontSize = agentCount <= 5 ? 9 : agentCount <= 15 ? 7 : 5

    // Padding for zoomToFit - much larger padding for fewer agents to prevent nodes at edges
    const zoomPadding = agentCount <= 2 ? 120 : agentCount <= 5 ? 80 : agentCount <= 10 ? 50 : 30

    return { baseRadius, maxRadius, fontSize, zoomPadding }
  }, [agents.length, width, height])

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
      isHovered: agent.id === hoveredNodeId,
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
  }, [agents, messages, selectedAgentId, hoveredNodeId, agentMessageCounts])

  // Node rendering
  const nodeCanvasObject = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      // Guard against undefined/NaN coordinates during initial render
      if (node.x === undefined || node.y === undefined || isNaN(node.x) || isNaN(node.y)) {
        return
      }

      const label = node.name
      const fontSize = nodeConfig.fontSize / globalScale
      // Dynamic node size based on agent count (from nodeConfig) plus activity bonus
      const activityBonus = Math.min(node.messageCount / 10, nodeConfig.maxRadius - nodeConfig.baseRadius)
      const baseRadius = nodeConfig.baseRadius + activityBonus
      const nodeRadius = (node.isSelected || node.isHovered) ? baseRadius * 1.15 : baseRadius

      // Determine if we should show the label for this node
      const shouldShowLabel = showAllLabels || node.isSelected || node.isHovered

      // Draw selection ring/halo first (behind the node)
      if (node.isSelected) {
        // Outer glow ring
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius + 5 / globalScale, 0, 2 * Math.PI)
        ctx.strokeStyle = node.color
        ctx.lineWidth = 2 / globalScale
        ctx.globalAlpha = 0.4
        ctx.stroke()
        ctx.globalAlpha = 1

        // Middle ring
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius + 2.5 / globalScale, 0, 2 * Math.PI)
        ctx.strokeStyle = '#ffffff'
        ctx.lineWidth = 1.5 / globalScale
        ctx.stroke()
      }

      // Draw hover ring (subtle)
      if (node.isHovered && !node.isSelected) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius + 2.5 / globalScale, 0, 2 * Math.PI)
        ctx.strokeStyle = node.color
        ctx.lineWidth = 1.5 / globalScale
        ctx.globalAlpha = 0.6
        ctx.stroke()
        ctx.globalAlpha = 1
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
      // Brighter colors for selected/hovered node
      if (node.isSelected || node.isHovered) {
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

      // Draw label only when appropriate
      if (shouldShowLabel) {
        ctx.font = `${fontSize}px Inter, sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = '#fff'

        // Draw label background
        const textWidth = ctx.measureText(label).width
        const bgPadding = 1.5 / globalScale
        const bgHeight = fontSize + bgPadding * 2
        const bgY = node.y + nodeRadius + 3 / globalScale

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
      }

      // Draw message count badge if > 0
      if (node.messageCount > 0) {
        const badgeRadius = 4 / globalScale
        const badgeX = node.x + nodeRadius * 0.8
        const badgeY = node.y - nodeRadius * 0.8

        ctx.beginPath()
        ctx.arc(badgeX, badgeY, badgeRadius, 0, 2 * Math.PI)
        ctx.fillStyle = '#22c55e'
        ctx.fill()

        ctx.font = `bold ${6 / globalScale}px Inter, sans-serif`
        ctx.fillStyle = '#fff'
        ctx.fillText(String(node.messageCount), badgeX, badgeY)
      }
    },
    [showAllLabels, nodeConfig]
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

  // Handle node hover
  const handleNodeHover = useCallback(
    (node: GraphNode | null) => {
      setHoveredNodeId(node ? node.id : null)
    },
    []
  )

  // Configure d3 forces when graph mounts
  useEffect(() => {
    if (graphRef.current) {
      // Increase charge force to push nodes apart but keep them centered
      graphRef.current.d3Force('charge')?.strength(-100)
      // Add center force to keep graph centered
      graphRef.current.d3Force('center')?.strength(0.1)
      // Reduce link distance to keep connected nodes closer
      graphRef.current.d3Force('link')?.distance(50)
    }
  }, [])

  // Center graph on mount and when agent count changes
  useEffect(() => {
    if (graphRef.current) {
      // Initial fit with padding
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, nodeConfig.zoomPadding)
      }, 300)
      // Second fit after simulation settles more
      setTimeout(() => {
        graphRef.current?.zoomToFit(200, nodeConfig.zoomPadding)
      }, 800)
      // Final fit
      setTimeout(() => {
        graphRef.current?.zoomToFit(100, nodeConfig.zoomPadding)
      }, 1500)
    }
  }, [agents.length, nodeConfig.zoomPadding])

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
        onNodeHover={handleNodeHover}
        nodeRelSize={2}
        linkDirectionalParticles={1}
        linkDirectionalParticleWidth={1}
        linkDirectionalParticleSpeed={0.005}
        cooldownTicks={100}
        onEngineStop={() => graphRef.current?.zoomToFit(200, nodeConfig.zoomPadding)}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.5}
        maxZoom={8}
        backgroundColor="transparent"
      />
    </div>
  )
})

export default TopologyGraph
