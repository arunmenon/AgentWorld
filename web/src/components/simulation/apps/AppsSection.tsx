import { useState } from 'react'
import { Plus, Info } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button } from '@/components/ui'
import { AppConfigCard } from './AppConfigCard'
import { AppPickerModal } from './AppPickerModal'
import { AppConfigModal } from './AppConfigModal'
import type { AppDefinition, AppCategory } from '@/lib/api'

export interface SimulationAppConfig {
  app_id: string
  definition_id: string
  name: string
  icon: string | null
  category: AppCategory
  actions_count: number
  config: Record<string, unknown>
}

interface AppsSectionProps {
  apps: SimulationAppConfig[]
  onChange: (apps: SimulationAppConfig[]) => void
}

export function AppsSection({ apps, onChange }: AppsSectionProps) {
  const [showPicker, setShowPicker] = useState(false)
  const [configuring, setConfiguring] = useState<{
    index: number
    app: SimulationAppConfig
  } | null>(null)

  const handleAddApp = (appDef: AppDefinition) => {
    // Check if already added
    if (apps.some((a) => a.definition_id === appDef.id)) {
      return
    }

    const newApp: SimulationAppConfig = {
      app_id: appDef.app_id,
      definition_id: appDef.id,
      name: appDef.name,
      icon: appDef.icon,
      category: appDef.category,
      actions_count: appDef.actions?.length || 0,
      config: { ...appDef.initial_config },
    }

    onChange([...apps, newApp])
  }

  const handleRemoveApp = (index: number) => {
    onChange(apps.filter((_, i) => i !== index))
  }

  const handleConfigureApp = (index: number) => {
    setConfiguring({ index, app: apps[index] })
  }

  const handleSaveConfig = (config: Record<string, unknown>) => {
    if (configuring === null) return

    onChange(
      apps.map((app, i) =>
        i === configuring.index ? { ...app, config } : app
      )
    )
    setConfiguring(null)
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Apps (Optional)</CardTitle>
            <CardDescription>
              Add simulated apps that agents can interact with
            </CardDescription>
          </div>
          <Button type="button" variant="outline" onClick={() => setShowPicker(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add App
          </Button>
        </CardHeader>
        <CardContent>
          {apps.length === 0 ? (
            <div className="text-center py-8 text-foreground-muted">
              <p className="mb-2">No apps added yet</p>
              <p className="text-sm">
                Apps let agents interact with simulated services like payment systems, shopping carts, and email.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {apps.map((app, index) => (
                <AppConfigCard
                  key={`${app.definition_id}-${index}`}
                  app={app}
                  onConfigure={() => handleConfigureApp(index)}
                  onRemove={() => handleRemoveApp(index)}
                />
              ))}
            </div>
          )}

          {/* Info box */}
          {apps.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-sm text-foreground-secondary">
                  Agents will see instructions for using these apps in their system prompt
                  and can interact via APP_ACTION directives.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* App Picker Modal */}
      {showPicker && (
        <AppPickerModal
          selectedAppIds={apps.map((a) => a.definition_id)}
          onSelect={handleAddApp}
          onClose={() => setShowPicker(false)}
        />
      )}

      {/* App Config Modal */}
      {configuring && (
        <AppConfigModal
          app={configuring.app}
          onSave={handleSaveConfig}
          onClose={() => setConfiguring(null)}
        />
      )}
    </>
  )
}
