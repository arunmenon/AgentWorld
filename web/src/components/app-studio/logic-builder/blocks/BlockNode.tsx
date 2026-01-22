/**
 * Custom block node component for React Flow
 */

import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { cn } from '@/lib/utils'
import { BLOCK_COLORS, BLOCK_ICONS, type LogicBlockType, type LogicBlock } from '../types'

interface BlockNodeData {
  type: LogicBlockType
  label: string
  config: Partial<LogicBlock>
}

interface BlockNodeProps {
  data: BlockNodeData
  selected?: boolean
}

function BlockNodeComponent({ data, selected }: BlockNodeProps) {
  const { type, label, config } = data
  const color = BLOCK_COLORS[type]
  const icon = BLOCK_ICONS[type]

  const isTerminal = type === 'return' || type === 'error'
  const hasBranch = type === 'validate' || type === 'branch'

  return (
    <div
      className={cn(
        'min-w-[180px] rounded-lg border-2 bg-background shadow-md transition-all',
        selected && 'ring-2 ring-primary ring-offset-2'
      )}
      style={{ borderColor: color }}
    >
      {/* Input handle */}
      {type !== 'start' && (
        <Handle
          type="target"
          position={Position.Top}
          className="!w-3 !h-3 !bg-foreground-muted !border-2 !border-background"
        />
      )}

      {/* Header */}
      <div
        className="px-3 py-2 rounded-t-md flex items-center gap-2"
        style={{ backgroundColor: `${color}20` }}
      >
        <span className="text-lg">{icon}</span>
        <span className="font-medium text-sm">{label}</span>
      </div>

      {/* Content */}
      <div className="px-3 py-2 text-xs">
        {type === 'start' && (
          <span className="text-foreground-muted">Start of action</span>
        )}

        {type === 'validate' && (
          <div className="space-y-1">
            <code className="block text-primary truncate max-w-[160px]">
              {config.condition || 'condition...'}
            </code>
            {config.error_message && (
              <span className="text-foreground-muted block truncate">
                {config.error_message}
              </span>
            )}
          </div>
        )}

        {type === 'update' && (
          <div className="space-y-1">
            <code className="block text-primary truncate max-w-[160px]">
              {config.target || 'target...'}
            </code>
            <span className="text-foreground-muted">
              {config.operation || 'set'} = {String(config.value || '...')}
            </span>
          </div>
        )}

        {type === 'notify' && (
          <div className="space-y-1">
            <span className="text-foreground-muted">
              To: {config.to || '...'}
            </span>
            <span className="block truncate text-foreground-secondary">
              {config.message || 'message...'}
            </span>
          </div>
        )}

        {type === 'return' && (
          <div className="space-y-1">
            <span className="text-green-400">Success result</span>
            {config.value && typeof config.value === 'object' && (
              <code className="block text-xs text-foreground-muted truncate">
                {Object.keys(config.value).join(', ')}
              </code>
            )}
          </div>
        )}

        {type === 'error' && (
          <div className="space-y-1">
            <span className="text-red-400 block truncate">
              {config.error_message || config.message || 'Error message...'}
            </span>
          </div>
        )}

        {type === 'branch' && (
          <div className="space-y-1">
            <code className="block text-primary truncate max-w-[160px]">
              {config.condition || 'condition...'}
            </code>
          </div>
        )}
      </div>

      {/* Output handles */}
      {!isTerminal && !hasBranch && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!w-3 !h-3 !bg-foreground-muted !border-2 !border-background"
        />
      )}

      {/* Branch handles (Yes/No) */}
      {hasBranch && (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="yes"
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-background !left-[30%]"
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="no"
            className="!w-3 !h-3 !bg-red-500 !border-2 !border-background !left-[70%]"
          />
          <div className="flex justify-between px-3 pb-1 text-[10px] text-foreground-muted">
            <span className="text-green-500">Yes</span>
            <span className="text-red-500">No</span>
          </div>
        </>
      )}
    </div>
  )
}

export const BlockNode = memo(BlockNodeComponent)
