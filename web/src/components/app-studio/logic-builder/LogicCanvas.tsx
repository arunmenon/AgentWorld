/**
 * LogicCanvas - Visual logic builder using React Flow
 */

import { useCallback, useRef, useState, useMemo, type DragEvent } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
  ReactFlowProvider,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { Button } from '@/components/ui'
import { Code, Eye } from 'lucide-react'
import { BlockNode } from './blocks/BlockNode'
import { BlockPalette } from './BlockPalette'
import { BlockConfigPanel } from './BlockConfigPanel'
import type { LogicBlock, LogicBlockType } from './types'
import { BLOCK_COLORS } from './types'

interface LogicCanvasProps {
  logic: LogicBlock[]
  onChange: (logic: LogicBlock[]) => void
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes: any = {
  blockNode: BlockNode,
}

let nodeId = 0
const getNodeId = () => `node_${nodeId++}`

interface BlockNodeData {
  type: LogicBlockType
  label: string
  config: Partial<LogicBlock>
  [key: string]: unknown
}

function logicToNodes(logic: LogicBlock[]): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // Add start node
  nodes.push({
    id: 'start',
    type: 'blockNode',
    position: { x: 250, y: 0 },
    data: {
      type: 'start',
      label: 'Start',
      config: {},
    } as BlockNodeData,
  })

  let y = 100
  let prevNodeId = 'start'

  logic.forEach((block, index) => {
    const id = `block_${index}`
    nodes.push({
      id,
      type: 'blockNode',
      position: { x: 250, y },
      data: {
        type: block.type as LogicBlockType,
        label: block.type.charAt(0).toUpperCase() + block.type.slice(1),
        config: block,
      } as BlockNodeData,
    })

    edges.push({
      id: `edge_${prevNodeId}_${id}`,
      source: prevNodeId,
      target: id,
      type: 'smoothstep',
    })

    prevNodeId = id
    y += 120
  })

  return { nodes, edges }
}

function nodesToLogic(nodes: Node[], edges: Edge[]): LogicBlock[] {
  const adjacency: Record<string, string[]> = {}
  edges.forEach((edge) => {
    if (!adjacency[edge.source]) {
      adjacency[edge.source] = []
    }
    adjacency[edge.source].push(edge.target)
  })

  const logic: LogicBlock[] = []
  let currentId = adjacency['start']?.[0]

  while (currentId) {
    const node = nodes.find((n) => n.id === currentId)
    if (!node) break

    const data = node.data as unknown as BlockNodeData
    if (data.type === 'start') break

    const block: LogicBlock = {
      type: data.type,
      ...data.config,
    }
    logic.push(block)

    currentId = adjacency[currentId]?.[0]
  }

  return logic
}

function LogicCanvasInner({ logic, onChange }: LogicCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [viewMode, setViewMode] = useState<'visual' | 'json'>('visual')
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  const initialData = useMemo(() => logicToNodes(logic), [])
  const [nodes, setNodes, onNodesChange] = useNodesState(initialData.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialData.edges)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault()

      const type = event.dataTransfer.getData(
        'application/reactflow'
      ) as LogicBlockType
      if (!type) return

      const bounds = reactFlowWrapper.current?.getBoundingClientRect()
      const position = {
        x: event.clientX - (bounds?.left || 0) - 90,
        y: event.clientY - (bounds?.top || 0) - 20,
      }

      const newNode: Node = {
        id: getNodeId(),
        type: 'blockNode',
        position,
        data: {
          type,
          label: type.charAt(0).toUpperCase() + type.slice(1),
          config: {},
        } as BlockNodeData,
      }

      setNodes((nds) => [...nds, newNode])
    },
    [setNodes]
  )

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const data = node.data as unknown as BlockNodeData
      if (data.type !== 'start') {
        setSelectedNode(node)
      }
    },
    []
  )

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleConfigChange = useCallback(
    (nodeId: string, config: Partial<LogicBlock>) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            return {
              ...node,
              data: {
                ...(node.data as unknown as BlockNodeData),
                config,
              },
            }
          }
          return node
        })
      )
    },
    [setNodes]
  )

  const handleDeleteNode = useCallback(() => {
    if (!selectedNode) return
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id))
    setEdges((eds) =>
      eds.filter(
        (e) => e.source !== selectedNode.id && e.target !== selectedNode.id
      )
    )
    setSelectedNode(null)
  }, [selectedNode, setNodes, setEdges])

  const handleSave = useCallback(() => {
    const newLogic = nodesToLogic(nodes, edges)
    onChange(newLogic)
  }, [nodes, edges, onChange])

  const handleJsonChange = useCallback(
    (jsonStr: string) => {
      try {
        const parsed = JSON.parse(jsonStr)
        if (Array.isArray(parsed)) {
          const { nodes: newNodes, edges: newEdges } = logicToNodes(parsed)
          setNodes(newNodes)
          setEdges(newEdges)
        }
      } catch {
        // Invalid JSON, ignore
      }
    },
    [setNodes, setEdges]
  )

  const selectedData = selectedNode?.data as BlockNodeData | undefined

  return (
    <div className="h-[500px] flex flex-col border border-border rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-secondary/30">
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'visual' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('visual')}
          >
            <Eye className="h-4 w-4 mr-1" />
            Visual
          </Button>
          <Button
            variant={viewMode === 'json' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('json')}
          >
            <Code className="h-4 w-4 mr-1" />
            JSON
          </Button>
        </div>
        <div className="flex items-center gap-2">
          {selectedNode && (
            <Button variant="ghost" size="sm" onClick={handleDeleteNode}>
              Delete Block
            </Button>
          )}
          <Button size="sm" onClick={handleSave}>
            Apply Changes
          </Button>
        </div>
      </div>

      {viewMode === 'visual' ? (
        <div className="flex-1 flex">
          {/* Canvas */}
          <div className="flex-1" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDragOver={onDragOver}
              onDrop={onDrop}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              snapToGrid
              snapGrid={[15, 15]}
              defaultEdgeOptions={{
                type: 'smoothstep',
                style: { stroke: '#6b7280', strokeWidth: 2 },
              }}
            >
              <Background gap={15} size={1} color="#374151" />
              <Controls />
              <MiniMap
                nodeColor={(node) => {
                  const data = node.data as unknown as BlockNodeData
                  return BLOCK_COLORS[data.type] || '#6b7280'
                }}
                maskColor="rgba(0, 0, 0, 0.8)"
              />
            </ReactFlow>
          </div>

          {/* Side Panel */}
          <div className="w-64 border-l border-border bg-background p-3 overflow-y-auto">
            {selectedNode && selectedData ? (
              <BlockConfigPanel
                blockId={selectedNode.id}
                blockType={selectedData.type}
                config={selectedData.config}
                onChange={handleConfigChange}
              />
            ) : (
              <BlockPalette />
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 p-3">
          <textarea
            className="w-full h-full font-mono text-sm p-3 border border-border rounded-md bg-secondary/30 resize-none"
            value={JSON.stringify(nodesToLogic(nodes, edges), null, 2)}
            onChange={(e) => handleJsonChange(e.target.value)}
            spellCheck={false}
          />
        </div>
      )}
    </div>
  )
}

export function LogicCanvas(props: LogicCanvasProps) {
  return (
    <ReactFlowProvider>
      <LogicCanvasInner {...props} />
    </ReactFlowProvider>
  )
}
