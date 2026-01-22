/**
 * Block Palette - Draggable blocks for the logic builder
 */

import type { DragEvent } from 'react'
import { BLOCK_PALETTE, BLOCK_COLORS } from './types'

export function BlockPalette() {
  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
        Blocks
      </h4>
      <div className="space-y-1">
        {BLOCK_PALETTE.map((item) => (
          <div
            key={item.type}
            className="flex items-center gap-2 p-2 rounded-md border border-border bg-secondary/30 cursor-grab hover:bg-secondary/50 transition-colors"
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
          >
            <div
              className="w-8 h-8 rounded flex items-center justify-center text-lg"
              style={{ backgroundColor: `${BLOCK_COLORS[item.type]}20` }}
            >
              {item.icon}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium block">{item.label}</span>
              <span className="text-xs text-foreground-muted truncate block">
                {item.description}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
