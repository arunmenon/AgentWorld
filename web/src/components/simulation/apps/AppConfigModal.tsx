import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { Button, Input, Label, Badge } from '@/components/ui'
import { api } from '@/lib/api'
import type { SimulationAppConfig } from './AppsSection'

interface AppConfigModalProps {
  app: SimulationAppConfig
  onSave: (config: Record<string, unknown>) => void
  onClose: () => void
}

export function AppConfigModal({ app, onSave, onClose }: AppConfigModalProps) {
  const [config, setConfig] = useState<Record<string, unknown>>(app.config || {})

  // Fetch full app definition for initial_config schema
  const { data: appDefinition } = useQuery({
    queryKey: ['app-definition', app.definition_id],
    queryFn: () => api.getAppDefinition(app.definition_id),
  })

  const handleChange = (key: string, value: unknown) => {
    setConfig({ ...config, [key]: value })
  }

  const handleSave = () => {
    onSave(config)
  }

  // Get config fields from initial_config
  const configFields = Object.entries(appDefinition?.initial_config || app.config || {})

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-50 w-full max-w-lg max-h-[85vh] overflow-hidden rounded-lg border border-border bg-background shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{app.icon || '📦'}</span>
            <div>
              <h3 className="font-semibold">Configure: {app.name}</h3>
              <p className="text-sm text-foreground-secondary capitalize">
                {app.category} app
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Initial Configuration */}
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-3">
                Initial Configuration
              </h4>

              {configFields.length === 0 ? (
                <p className="text-sm text-foreground-muted text-center py-4">
                  This app has no configurable options
                </p>
              ) : (
                <div className="space-y-4">
                  {configFields.map(([key, defaultValue]) => (
                    <ConfigField
                      key={key}
                      name={key}
                      value={config[key] ?? defaultValue}
                      defaultValue={defaultValue}
                      onChange={(value) => handleChange(key, value)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Available Actions */}
            {appDefinition && appDefinition.actions.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-3">
                  Available Actions
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {appDefinition.actions.map((action) => (
                    <div
                      key={action.name}
                      className="p-3 rounded-lg bg-secondary/50 text-sm"
                    >
                      <div className="flex items-center gap-2">
                        <code className="font-mono text-primary">{action.name}</code>
                        <Badge variant="outline" className="text-xs">
                          {Object.keys(action.parameters || {}).length} params
                        </Badge>
                      </div>
                      {action.description && (
                        <p className="text-foreground-secondary mt-1">
                          {action.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-border">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  )
}

// Config Field Component
function ConfigField({
  name,
  value,
  defaultValue,
  onChange,
}: {
  name: string
  value: unknown
  defaultValue: unknown
  onChange: (value: unknown) => void
}) {
  const type = typeof defaultValue
  const label = name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>

      {type === 'number' ? (
        <Input
          id={name}
          type="number"
          value={String(value ?? '')}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        />
      ) : type === 'boolean' ? (
        <select
          id={name}
          value={String(value ?? false)}
          onChange={(e) => onChange(e.target.value === 'true')}
          className="w-full px-3 py-2 border border-border rounded-md bg-background"
        >
          <option value="false">No</option>
          <option value="true">Yes</option>
        </select>
      ) : (
        <Input
          id={name}
          type="text"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      <p className="text-xs text-foreground-muted">
        Default: {String(defaultValue)}
      </p>
    </div>
  )
}
