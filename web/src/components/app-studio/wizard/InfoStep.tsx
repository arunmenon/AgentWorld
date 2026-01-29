import { AlertCircle, FlaskConical } from 'lucide-react'
import { Input, Textarea, Label } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { AppCategory, StateField, EnvironmentConfig } from '@/lib/api'
import {
  AccessTypeSelector,
  RoleCheckboxes,
  StateTypeSelector,
  StateSchemaEditor,
  type AccessType,
  type AgentRole,
  type StateType,
} from '@/components/app-studio/access'

interface AppInfoData {
  name: string
  app_id: string
  description: string
  category: AppCategory
  icon: string
  // Access control (ADR-020.1)
  access_type?: AccessType
  allowed_roles?: AgentRole[]
  state_type?: StateType
  // State schema (τ²-bench Phase 1)
  state_schema?: StateField[]
  // Environment configuration (Gymnasium-style)
  environment_config?: EnvironmentConfig
}

interface ValidationErrors {
  name?: string
  app_id?: string
}

interface InfoStepProps {
  data: AppInfoData
  onChange: (data: Partial<AppInfoData>) => void
  errors: ValidationErrors
  touched: Record<string, boolean>
  onBlur: (field: string) => void
}

const categories: { value: AppCategory; label: string; icon: string }[] = [
  { value: 'payment', label: 'Payment', icon: '💳' },
  { value: 'shopping', label: 'Shopping', icon: '🛒' },
  { value: 'communication', label: 'Communication', icon: '📧' },
  { value: 'calendar', label: 'Calendar', icon: '📅' },
  { value: 'social', label: 'Social', icon: '💬' },
  { value: 'custom', label: 'Custom', icon: '🔧' },
]

const commonIcons = ['💳', '🛒', '📧', '📅', '💬', '📝', '🏦', '🎮', '📱', '🔧', '🎯', '📊', '🔔', '⚡', '🎁', '🏠']

function generateAppId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 50)
}

export function InfoStep({
  data,
  onChange,
  errors,
  touched,
  onBlur,
}: InfoStepProps) {
  const handleNameChange = (name: string) => {
    onChange({ name })
    // Auto-generate app_id if it hasn't been manually edited
    if (!touched.app_id) {
      onChange({ name, app_id: generateAppId(name) })
    } else {
      onChange({ name })
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-xl font-semibold mb-2">App Details</h2>
        <p className="text-foreground-secondary">
          Give your app a name and description
        </p>
      </div>

      {/* App Name */}
      <div className="space-y-2">
        <Label htmlFor="name">App Name *</Label>
        <Input
          id="name"
          value={data.name}
          onChange={(e) => handleNameChange(e.target.value)}
          onBlur={() => onBlur('name')}
          placeholder="My Awesome App"
          className={cn(
            touched.name && errors.name && 'border-error focus:ring-error'
          )}
        />
        <p className="text-sm text-foreground-muted">
          This will be shown to agents
        </p>
        {touched.name && errors.name && (
          <p className="text-sm text-error flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {errors.name}
          </p>
        )}
      </div>

      {/* App ID */}
      <div className="space-y-2">
        <Label htmlFor="app_id">App ID *</Label>
        <Input
          id="app_id"
          value={data.app_id}
          onChange={(e) => onChange({ app_id: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })}
          onBlur={() => onBlur('app_id')}
          placeholder="my_awesome_app"
          className={cn(
            'font-mono text-sm',
            touched.app_id && errors.app_id && 'border-error focus:ring-error'
          )}
        />
        <p className="text-sm text-foreground-muted">
          Unique identifier (auto-generated from name)
        </p>
        {touched.app_id && errors.app_id && (
          <p className="text-sm text-error flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {errors.app_id}
          </p>
        )}
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={data.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Describe what this app does..."
          rows={3}
        />
        <p className="text-sm text-foreground-muted">
          Helps agents understand what this app does
        </p>
      </div>

      {/* Category and Icon Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Category */}
        <div className="space-y-2">
          <Label>Category</Label>
          <div className="grid grid-cols-3 gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => onChange({ category: cat.value })}
                className={cn(
                  'p-2 rounded-lg border text-center transition-all',
                  data.category === cat.value
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:border-primary/40'
                )}
              >
                <span className="text-xl block">{cat.icon}</span>
                <span className="text-xs">{cat.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Icon */}
        <div className="space-y-2">
          <Label>Icon</Label>
          <div className="flex flex-wrap gap-2">
            {commonIcons.map((icon) => (
              <button
                key={icon}
                type="button"
                onClick={() => onChange({ icon })}
                className={cn(
                  'w-10 h-10 rounded-lg border text-xl flex items-center justify-center transition-all',
                  data.icon === icon
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/40'
                )}
              >
                {icon}
              </button>
            ))}
          </div>
          <p className="text-sm text-foreground-muted">
            Or type a custom emoji:
            <input
              type="text"
              value={data.icon}
              onChange={(e) => onChange({ icon: e.target.value.slice(0, 2) })}
              className="ml-2 w-12 px-2 py-1 border border-border rounded text-center"
              maxLength={2}
            />
          </p>
        </div>
      </div>

      {/* Access Control Section (ADR-020.1) */}
      <div className="space-y-4 pt-4 border-t border-border">
        <div className="text-center">
          <h3 className="text-lg font-medium mb-1">Access Control</h3>
          <p className="text-sm text-foreground-secondary">
            Configure who can access this app and how state is managed
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Access Type */}
          <AccessTypeSelector
            value={data.access_type || 'shared'}
            onChange={(access_type) => {
              onChange({ access_type })
              // If PER_AGENT access, force PER_AGENT state
              if (access_type === 'per_agent') {
                onChange({ access_type, state_type: 'per_agent' })
              }
            }}
          />

          {/* State Type */}
          <StateTypeSelector
            value={data.state_type || 'shared'}
            onChange={(state_type) => onChange({ state_type })}
            accessType={data.access_type || 'shared'}
          />
        </div>

        {/* Role Selection (shown when role_restricted) */}
        {data.access_type === 'role_restricted' && (
          <RoleCheckboxes
            value={data.allowed_roles || []}
            onChange={(allowed_roles) => onChange({ allowed_roles })}
          />
        )}
      </div>

      {/* State Schema Section (τ²-bench Phase 1) */}
      {data.state_schema && data.state_schema.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-border">
          <div className="text-center">
            <h3 className="text-lg font-medium mb-1">State Schema</h3>
            <p className="text-sm text-foreground-secondary">
              Configure state fields and their visibility to user agents
            </p>
          </div>

          <StateSchemaEditor
            fields={data.state_schema}
            onChange={(state_schema) => onChange({ state_schema })}
          />
        </div>
      )}

      {/* Environment Settings Section (Gymnasium-style) */}
      <div className="space-y-4 pt-4 border-t border-border">
        <div className="flex items-center gap-2 justify-center mb-2">
          <FlaskConical className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-medium">Environment Settings</h3>
        </div>
        <p className="text-sm text-foreground-secondary text-center mb-4">
          Configure Gymnasium-style environment behavior for RL training and evaluation
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Max Steps per Episode */}
          <div className="space-y-2">
            <Label htmlFor="max_steps">Max Steps per Episode</Label>
            <Input
              id="max_steps"
              type="number"
              value={data.environment_config?.max_steps_per_episode ?? 100}
              onChange={(e) =>
                onChange({
                  environment_config: {
                    ...data.environment_config,
                    max_steps_per_episode: parseInt(e.target.value) || 100,
                    reward_type: data.environment_config?.reward_type ?? 'per_step',
                    supports_reset: data.environment_config?.supports_reset ?? true,
                  },
                })
              }
              min={1}
              max={10000}
              className="font-mono"
            />
            <p className="text-xs text-foreground-muted">
              Episode truncates after this many steps (1-10000)
            </p>
          </div>

          {/* Reward Type */}
          <div className="space-y-2">
            <Label>Reward Type</Label>
            <div className="space-y-2">
              {([
                { value: 'per_step', label: 'Per Step (-0.01 per step)', desc: 'Small penalty each step, encourages efficiency' },
                { value: 'completion', label: 'Completion Only (+1 on success)', desc: 'Sparse reward only when goal is achieved' },
                { value: 'custom', label: 'Custom (defined in actions)', desc: 'Actions return custom reward values' },
              ] as const).map((option) => (
                <label
                  key={option.value}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all',
                    (data.environment_config?.reward_type ?? 'per_step') === option.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/40'
                  )}
                >
                  <input
                    type="radio"
                    name="reward_type"
                    value={option.value}
                    checked={(data.environment_config?.reward_type ?? 'per_step') === option.value}
                    onChange={() =>
                      onChange({
                        environment_config: {
                          ...data.environment_config,
                          reward_type: option.value,
                          max_steps_per_episode: data.environment_config?.max_steps_per_episode ?? 100,
                          supports_reset: data.environment_config?.supports_reset ?? true,
                        },
                      })
                    }
                    className="mt-1 accent-primary"
                  />
                  <div>
                    <div className="font-medium text-sm">{option.label}</div>
                    <div className="text-xs text-foreground-muted">{option.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Supports Reset Toggle */}
        <label className="flex items-center justify-between p-3 rounded-lg border border-border cursor-pointer hover:border-primary/40 transition-all">
          <div className="space-y-0.5">
            <span className="text-sm font-medium">Supports Episode Reset</span>
            <p className="text-xs text-foreground-muted">
              Allow resetting to initial state for new episodes
            </p>
          </div>
          <input
            type="checkbox"
            id="supports_reset"
            checked={data.environment_config?.supports_reset ?? true}
            onChange={(e) =>
              onChange({
                environment_config: {
                  ...data.environment_config,
                  supports_reset: e.target.checked,
                  max_steps_per_episode: data.environment_config?.max_steps_per_episode ?? 100,
                  reward_type: data.environment_config?.reward_type ?? 'per_step',
                },
              })
            }
            className="h-5 w-5 accent-primary rounded"
          />
        </label>
      </div>
    </div>
  )
}
