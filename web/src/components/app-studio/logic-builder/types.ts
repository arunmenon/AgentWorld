/**
 * Type definitions for the Visual Logic Builder
 */

export type LogicBlockType =
  | 'start'
  | 'validate'
  | 'update'
  | 'notify'
  | 'return'
  | 'error'
  | 'branch'
  | 'loop'

export interface LogicBlock {
  type: LogicBlockType
  // Validate block
  condition?: string
  error_message?: string
  // Update block
  target?: string
  operation?: 'set' | 'add' | 'subtract' | 'append' | 'remove'
  value?: string | Record<string, unknown>
  // Notify block
  to?: string
  message?: string
  data?: Record<string, unknown>
  // Return/Error block
  // Branch block
  then?: LogicBlock[]
  else?: LogicBlock[]
  // Loop block
  collection?: string
  item?: string
  body?: LogicBlock[]
}

export interface BlockNodeData {
  type: LogicBlockType
  label: string
  config: Partial<LogicBlock>
  isSelected?: boolean
  [key: string]: unknown
}

export interface BlockPaletteItem {
  type: LogicBlockType
  label: string
  icon: string
  description: string
  color: string
}

export const BLOCK_PALETTE: BlockPaletteItem[] = [
  {
    type: 'validate',
    label: 'Validate',
    icon: '❓',
    description: 'Check a condition',
    color: '#f59e0b', // amber
  },
  {
    type: 'update',
    label: 'Update',
    icon: '📝',
    description: 'Modify state',
    color: '#3b82f6', // blue
  },
  {
    type: 'notify',
    label: 'Notify',
    icon: '🔔',
    description: 'Send notification',
    color: '#8b5cf6', // violet
  },
  {
    type: 'return',
    label: 'Return',
    icon: '✅',
    description: 'Return success',
    color: '#22c55e', // green
  },
  {
    type: 'error',
    label: 'Error',
    icon: '❌',
    description: 'Return error',
    color: '#ef4444', // red
  },
  {
    type: 'branch',
    label: 'Branch',
    icon: '🔀',
    description: 'Conditional branch',
    color: '#06b6d4', // cyan
  },
]

export const BLOCK_COLORS: Record<LogicBlockType, string> = {
  start: '#6b7280',
  validate: '#f59e0b',
  update: '#3b82f6',
  notify: '#8b5cf6',
  return: '#22c55e',
  error: '#ef4444',
  branch: '#06b6d4',
  loop: '#ec4899',
}

export const BLOCK_ICONS: Record<LogicBlockType, string> = {
  start: '▶️',
  validate: '❓',
  update: '📝',
  notify: '🔔',
  return: '✅',
  error: '❌',
  branch: '🔀',
  loop: '🔁',
}
