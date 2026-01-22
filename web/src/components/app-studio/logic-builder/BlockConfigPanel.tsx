/**
 * Block Configuration Panel - Edit selected block properties
 */

import { Input, Label } from '@/components/ui'
import type { LogicBlock, LogicBlockType } from './types'
import { BLOCK_ICONS } from './types'

interface BlockConfigPanelProps {
  blockId: string
  blockType: LogicBlockType
  config: Partial<LogicBlock>
  onChange: (blockId: string, config: Partial<LogicBlock>) => void
}

export function BlockConfigPanel({
  blockId,
  blockType,
  config,
  onChange,
}: BlockConfigPanelProps) {
  const handleChange = (key: string, value: unknown) => {
    onChange(blockId, { ...config, [key]: value })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <span className="text-xl">{BLOCK_ICONS[blockType]}</span>
        <h4 className="font-semibold capitalize">{blockType} Block</h4>
      </div>

      {blockType === 'validate' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="condition">Condition *</Label>
            <Input
              id="condition"
              value={config.condition || ''}
              onChange={(e) => handleChange('condition', e.target.value)}
              placeholder="params.amount > 0"
              className="font-mono text-sm"
            />
            <p className="text-xs text-foreground-muted">
              Expression that must be true to continue
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="error_message">Error Message *</Label>
            <Input
              id="error_message"
              value={config.error_message || ''}
              onChange={(e) => handleChange('error_message', e.target.value)}
              placeholder="Amount must be positive"
            />
            <p className="text-xs text-foreground-muted">
              Message shown if validation fails
            </p>
          </div>
        </>
      )}

      {blockType === 'update' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="target">Target *</Label>
            <Input
              id="target"
              value={config.target || ''}
              onChange={(e) => handleChange('target', e.target.value)}
              placeholder="agent.balance"
              className="font-mono text-sm"
            />
            <p className="text-xs text-foreground-muted">
              State path to update (e.g., agent.balance)
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="operation">Operation</Label>
            <select
              id="operation"
              value={config.operation || 'set'}
              onChange={(e) => handleChange('operation', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-sm"
            >
              <option value="set">Set (=)</option>
              <option value="add">Add (+)</option>
              <option value="subtract">Subtract (-)</option>
              <option value="append">Append to array</option>
              <option value="remove">Remove from array</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="value">Value *</Label>
            <Input
              id="value"
              value={String(config.value || '')}
              onChange={(e) => handleChange('value', e.target.value)}
              placeholder="params.amount"
              className="font-mono text-sm"
            />
            <p className="text-xs text-foreground-muted">
              Value or expression to use
            </p>
          </div>
        </>
      )}

      {blockType === 'notify' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="to">To (Agent ID) *</Label>
            <Input
              id="to"
              value={config.to || ''}
              onChange={(e) => handleChange('to', e.target.value)}
              placeholder="params.to"
              className="font-mono text-sm"
            />
            <p className="text-xs text-foreground-muted">
              Agent to notify (expression)
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="message">Message *</Label>
            <Input
              id="message"
              value={config.message || ''}
              onChange={(e) => handleChange('message', e.target.value)}
              placeholder="You received $${params.amount}"
            />
            <p className="text-xs text-foreground-muted">
              Use ${'{expression}'} for interpolation
            </p>
          </div>
        </>
      )}

      {blockType === 'return' && (
        <div className="space-y-2">
          <Label htmlFor="returnValue">Return Value</Label>
          <textarea
            id="returnValue"
            value={
              typeof config.value === 'object'
                ? JSON.stringify(config.value, null, 2)
                : String(config.value || '{}')
            }
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value)
                handleChange('value', parsed)
              } catch {
                handleChange('value', e.target.value)
              }
            }}
            placeholder='{"success": true}'
            className="w-full h-24 px-3 py-2 border border-border rounded-md bg-background font-mono text-sm resize-none"
          />
          <p className="text-xs text-foreground-muted">
            JSON object with expression values
          </p>
        </div>
      )}

      {blockType === 'error' && (
        <div className="space-y-2">
          <Label htmlFor="errorMessage">Error Message *</Label>
          <Input
            id="errorMessage"
            value={config.message || config.error_message || ''}
            onChange={(e) => handleChange('message', e.target.value)}
            placeholder="Something went wrong"
          />
          <p className="text-xs text-foreground-muted">
            Error message to return
          </p>
        </div>
      )}

      {blockType === 'branch' && (
        <div className="space-y-2">
          <Label htmlFor="branchCondition">Condition *</Label>
          <Input
            id="branchCondition"
            value={config.condition || ''}
            onChange={(e) => handleChange('condition', e.target.value)}
            placeholder="agent.vip == true"
            className="font-mono text-sm"
          />
          <p className="text-xs text-foreground-muted">
            If true, follows "Yes" path; otherwise "No" path
          </p>
        </div>
      )}

      <div className="pt-4 border-t border-border">
        <h5 className="text-xs font-semibold text-foreground-secondary uppercase tracking-wider mb-2">
          Available Variables
        </h5>
        <div className="space-y-1 text-xs font-mono text-foreground-muted">
          <div>params.* - Action parameters</div>
          <div>agent.* - Current agent state</div>
          <div>agents[id].* - Other agent state</div>
          <div>state.* - Shared app state</div>
          <div>config.* - App configuration</div>
        </div>
      </div>
    </div>
  )
}
