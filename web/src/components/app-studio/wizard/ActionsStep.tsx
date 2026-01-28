import { useState } from 'react'
import { Plus, Edit, Trash2, ChevronDown, ChevronUp, Workflow } from 'lucide-react'
import { Button, Badge, Card, Input, Textarea, Label } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { ActionDefinition, ParamSpec } from '@/lib/api'
import { LogicCanvas, type LogicBlock } from '../logic-builder'
import { ToolTypeBadge, ToolTypeSelector, type ToolType } from '../ToolTypeBadge'

interface ActionsStepProps {
  actions: ActionDefinition[]
  onChange: (actions: ActionDefinition[]) => void
}

interface ActionCardProps {
  action: ActionDefinition
  onEdit: () => void
  onDelete: () => void
  onMoveUp: () => void
  onMoveDown: () => void
  isFirst: boolean
  isLast: boolean
}

function ActionCard({
  action,
  onEdit,
  onDelete,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast,
}: ActionCardProps) {
  const [expanded, setExpanded] = useState(false)
  const paramCount = Object.keys(action.parameters || {}).length
  const requiredParams = Object.entries(action.parameters || {}).filter(
    ([, spec]) => spec.required
  )
  const hasLogic = action.logic && action.logic.length > 0

  return (
    <Card className="group">
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Drag handle */}
          <div className="flex flex-col gap-1 pt-1">
            <button
              type="button"
              onClick={onMoveUp}
              disabled={isFirst}
              className={cn(
                'p-0.5 rounded hover:bg-secondary transition-colors',
                isFirst && 'opacity-30 cursor-not-allowed'
              )}
            >
              <ChevronUp className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onMoveDown}
              disabled={isLast}
              className={cn(
                'p-0.5 rounded hover:bg-secondary transition-colors',
                isLast && 'opacity-30 cursor-not-allowed'
              )}
            >
              <ChevronDown className="h-4 w-4" />
            </button>
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <code className="font-mono text-sm font-semibold text-primary">
                {action.name}
              </code>
              <ToolTypeBadge toolType={(action as ActionDefinition & { toolType?: ToolType }).toolType || 'write'} />
              {hasLogic && (
                <Badge variant="outline" className="text-xs">
                  Has logic
                </Badge>
              )}
            </div>
            <p className="text-sm text-foreground-secondary mb-2">
              {action.description || 'No description'}
            </p>
            <div className="flex items-center gap-4 text-xs text-foreground-muted">
              <span>
                {paramCount} parameter{paramCount !== 1 ? 's' : ''}
                {requiredParams.length > 0 && ` (${requiredParams.length} required)`}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Collapse' : 'Expand'}
            </Button>
            <Button variant="ghost" size="icon" onClick={onEdit}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onDelete}
              className="text-error hover:text-error"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Expanded details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-border space-y-4">
            {/* Parameters */}
            {paramCount > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Parameters</h4>
                <div className="space-y-2">
                  {Object.entries(action.parameters || {}).map(([name, spec]) => (
                    <div
                      key={name}
                      className="flex items-center gap-2 text-sm bg-secondary/50 rounded px-3 py-2"
                    >
                      <code className="font-mono">{name}</code>
                      {spec.required && (
                        <span className="text-error">*</span>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {spec.type}
                      </Badge>
                      {spec.description && (
                        <span className="text-foreground-muted">
                          — {spec.description}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Logic summary */}
            {hasLogic && (
              <div>
                <h4 className="text-sm font-medium mb-2">Logic</h4>
                <div className="text-sm text-foreground-muted bg-secondary/50 rounded px-3 py-2">
                  {action.logic!.length} step{action.logic!.length !== 1 ? 's' : ''}:{' '}
                  {action.logic!.map((block) => block.type).join(' → ')}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

// Simple Action Builder Modal
interface ActionBuilderModalProps {
  action: ActionDefinition | null
  onSave: (action: ActionDefinition) => void
  onClose: () => void
}

function ActionBuilderModal({ action, onSave, onClose }: ActionBuilderModalProps) {
  const [name, setName] = useState(action?.name || '')
  const [description, setDescription] = useState(action?.description || '')
  const [toolType, setToolType] = useState<ToolType>(
    (action as ActionDefinition & { toolType?: ToolType })?.toolType || 'write'
  )
  const [parameters, setParameters] = useState<Record<string, ParamSpec>>(
    action?.parameters || {}
  )
  const [logic, setLogic] = useState<LogicBlock[]>(
    (action?.logic as LogicBlock[] | undefined) || [{ type: 'return', value: { success: true } }]
  )
  const [showLogicBuilder, setShowLogicBuilder] = useState(false)
  const [newParamName, setNewParamName] = useState('')
  const [newParamType, setNewParamType] = useState<ParamSpec['type']>('string')
  const [newParamRequired, setNewParamRequired] = useState(false)
  const [newParamDescription, setNewParamDescription] = useState('')

  const handleAddParameter = () => {
    if (!newParamName.trim()) return
    const paramKey = newParamName.toLowerCase().replace(/[^a-z0-9_]/g, '_')
    setParameters({
      ...parameters,
      [paramKey]: {
        type: newParamType,
        required: newParamRequired,
        description: newParamDescription || undefined,
      },
    })
    setNewParamName('')
    setNewParamType('string')
    setNewParamRequired(false)
    setNewParamDescription('')
  }

  const handleRemoveParameter = (key: string) => {
    const { [key]: _, ...rest } = parameters
    setParameters(rest)
  }

  const handleSave = () => {
    if (!name.trim()) return
    // Filter out 'start' blocks when saving since they're UI-only
    const filteredLogic = logic.filter(b => b.type !== 'start')
    onSave({
      name: name.toLowerCase().replace(/[^a-z0-9_]/g, '_'),
      description,
      parameters,
      returns: action?.returns || {},
      // Cast to api LogicBlock type (same structure, just different type declaration)
      logic: filteredLogic as unknown as import('@/lib/api').LogicBlock[],
      // ADR-020.1: Include tool type
      toolType,
    } as ActionDefinition & { toolType: ToolType })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-50 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg border border-border bg-background p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-6">
          {action ? 'Edit Action' : 'Add Action'}
        </h3>

        <div className="space-y-6">
          {/* Action Name */}
          <div className="space-y-2">
            <Label htmlFor="action-name">Action Name *</Label>
            <Input
              id="action-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my_action"
              className="font-mono"
            />
            <p className="text-sm text-foreground-muted">
              Use snake_case (e.g., send_message, get_balance)
            </p>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="action-desc">Description</Label>
            <Textarea
              id="action-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this action do?"
              rows={2}
            />
          </div>

          {/* Tool Type (ADR-020.1) */}
          <ToolTypeSelector
            value={toolType}
            onChange={setToolType}
          />

          {/* Parameters */}
          <div className="space-y-4">
            <Label>Parameters</Label>

            {/* Existing parameters */}
            {Object.entries(parameters).length > 0 && (
              <div className="space-y-2">
                {Object.entries(parameters).map(([key, spec]) => (
                  <div
                    key={key}
                    className="flex items-center gap-2 p-3 bg-secondary/50 rounded-lg"
                  >
                    <code className="font-mono text-sm flex-1">{key}</code>
                    <Badge variant="outline">{spec.type}</Badge>
                    {spec.required && <Badge variant="outline" className="text-error border-error">Required</Badge>}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveParameter(key)}
                      className="h-8 w-8"
                    >
                      <Trash2 className="h-4 w-4 text-error" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Add new parameter */}
            <div className="p-4 border border-dashed border-border rounded-lg space-y-3">
              <p className="text-sm font-medium">Add Parameter</p>
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="Parameter name"
                  value={newParamName}
                  onChange={(e) => setNewParamName(e.target.value)}
                  className="font-mono text-sm"
                />
                <select
                  value={newParamType}
                  onChange={(e) => setNewParamType(e.target.value as ParamSpec['type'])}
                  className="px-3 py-2 border border-border rounded-md bg-background text-sm"
                >
                  <option value="string">String</option>
                  <option value="number">Number</option>
                  <option value="boolean">Boolean</option>
                  <option value="array">Array</option>
                  <option value="object">Object</option>
                </select>
              </div>
              <Input
                placeholder="Description (optional)"
                value={newParamDescription}
                onChange={(e) => setNewParamDescription(e.target.value)}
                className="text-sm"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={newParamRequired}
                    onChange={(e) => setNewParamRequired(e.target.checked)}
                    className="rounded border-border"
                  />
                  Required
                </label>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleAddParameter}
                  disabled={!newParamName.trim()}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
            </div>
          </div>

          {/* Action Logic */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Action Logic</Label>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowLogicBuilder(!showLogicBuilder)}
              >
                <Workflow className="h-4 w-4 mr-1" />
                {showLogicBuilder ? 'Hide Builder' : 'Visual Builder'}
              </Button>
            </div>

            {showLogicBuilder ? (
              <LogicCanvas logic={logic} onChange={setLogic} />
            ) : (
              <div className="p-3 bg-secondary/50 rounded-lg">
                <p className="text-sm text-foreground-muted mb-2">
                  {logic.length} step{logic.length !== 1 ? 's' : ''}: {logic.map(b => b.type).join(' → ')}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowLogicBuilder(true)}
                >
                  Open Visual Builder
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-border">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            {action ? 'Save Changes' : 'Add Action'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export function ActionsStep({ actions, onChange }: ActionsStepProps) {
  const [showModal, setShowModal] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)

  const handleAddAction = () => {
    setEditingIndex(null)
    setShowModal(true)
  }

  const handleEditAction = (index: number) => {
    setEditingIndex(index)
    setShowModal(true)
  }

  const handleDeleteAction = (index: number) => {
    onChange(actions.filter((_, i) => i !== index))
  }

  const handleSaveAction = (action: ActionDefinition) => {
    if (editingIndex !== null) {
      // Editing existing
      onChange(actions.map((a, i) => (i === editingIndex ? action : a)))
    } else {
      // Adding new
      onChange([...actions, action])
    }
    setShowModal(false)
    setEditingIndex(null)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingIndex(null)
  }

  const handleMoveUp = (index: number) => {
    if (index === 0) return
    const newActions = [...actions]
    ;[newActions[index - 1], newActions[index]] = [newActions[index], newActions[index - 1]]
    onChange(newActions)
  }

  const handleMoveDown = (index: number) => {
    if (index === actions.length - 1) return
    const newActions = [...actions]
    ;[newActions[index], newActions[index + 1]] = [newActions[index + 1], newActions[index]]
    onChange(newActions)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Actions</h2>
          <p className="text-foreground-secondary">
            Define what agents can do with this app
          </p>
        </div>
        <Button onClick={handleAddAction}>
          <Plus className="h-4 w-4 mr-2" />
          Add Action
        </Button>
      </div>

      {actions.length === 0 ? (
        <Card className="p-8">
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
              <Plus className="h-8 w-8 text-foreground-muted" />
            </div>
            <h3 className="font-semibold mb-1">No actions yet</h3>
            <p className="text-foreground-secondary mb-4">
              Actions define what agents can do with your app
            </p>
            <Button onClick={handleAddAction}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Action
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {actions.map((action, index) => (
            <ActionCard
              key={`${action.name}-${index}`}
              action={action}
              onEdit={() => handleEditAction(index)}
              onDelete={() => handleDeleteAction(index)}
              onMoveUp={() => handleMoveUp(index)}
              onMoveDown={() => handleMoveDown(index)}
              isFirst={index === 0}
              isLast={index === actions.length - 1}
            />
          ))}
        </div>
      )}

      {/* Action Builder Modal */}
      {showModal && (
        <ActionBuilderModal
          action={editingIndex !== null ? actions[editingIndex] : null}
          onSave={handleSaveAction}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}
