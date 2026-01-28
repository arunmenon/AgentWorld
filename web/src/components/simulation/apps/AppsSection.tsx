import { useState } from 'react'
import { Plus, Info, AlertTriangle, Headphones, Smartphone, Users } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button } from '@/components/ui'
import { AppConfigCard } from './AppConfigCard'
import { AppPickerModal } from './AppPickerModal'
import { AppConfigModal } from './AppConfigModal'
import type { AppDefinition, AppCategory, AccessType, AgentRole } from '@/lib/api'
import { cn } from '@/lib/utils'

export interface SimulationAppConfig {
  app_id: string
  definition_id: string
  name: string
  icon: string | null
  category: AppCategory
  actions_count: number
  config: Record<string, unknown>
  /** Access control: who can use this app (τ²-bench) */
  access_type?: AccessType
  /** Roles allowed to access when access_type is 'role_restricted' */
  allowed_roles?: AgentRole[]
}

interface AppsSectionProps {
  apps: SimulationAppConfig[]
  onChange: (apps: SimulationAppConfig[]) => void
  /** Agent roles in the simulation for compatibility checking */
  agentRoles?: AgentRole[]
}

/** Get icon for access type */
function getAccessTypeIcon(accessType?: AccessType) {
  switch (accessType) {
    case 'role_restricted':
      return <Headphones className="h-3 w-3" />
    case 'per_agent':
      return <Smartphone className="h-3 w-3" />
    default:
      return <Users className="h-3 w-3" />
  }
}

/** Check if any agent can access this app */
function canAnyAgentAccess(app: SimulationAppConfig, agentRoles: AgentRole[]): boolean {
  if (!app.access_type || app.access_type === 'shared') {
    return true
  }
  if (app.access_type === 'per_agent') {
    return true // Per-agent apps are accessible to all
  }
  if (app.access_type === 'role_restricted' && app.allowed_roles) {
    return agentRoles.some((role) => app.allowed_roles?.includes(role))
  }
  return true
}

/** Get roles that can access this app */
function getAccessibleRoles(app: SimulationAppConfig): AgentRole[] | 'all' {
  if (!app.access_type || app.access_type === 'shared' || app.access_type === 'per_agent') {
    return 'all'
  }
  return app.allowed_roles || []
}

export function AppsSection({ apps, onChange, agentRoles = [] }: AppsSectionProps) {
  const [showPicker, setShowPicker] = useState(false)
  const [configuring, setConfiguring] = useState<{
    index: number
    app: SimulationAppConfig
  } | null>(null)

  // Check for role compatibility issues
  const hasRoleIssues = agentRoles.length > 0 && apps.some((app) => !canAnyAgentAccess(app, agentRoles))

  // Group apps by access type for display
  const groupedApps = {
    restricted: apps.filter((a) => a.access_type === 'role_restricted'),
    perAgent: apps.filter((a) => a.access_type === 'per_agent'),
    shared: apps.filter((a) => !a.access_type || a.access_type === 'shared'),
  }

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
      access_type: appDef.access_type,
      allowed_roles: appDef.allowed_roles,
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

  /** Render a single app card with role compatibility info */
  const renderAppCard = (app: SimulationAppConfig, index: number) => {
    const accessibleRoles = getAccessibleRoles(app)
    const hasAccess = agentRoles.length === 0 || canAnyAgentAccess(app, agentRoles)

    return (
      <div
        key={`${app.definition_id}-${index}`}
        className={cn(
          'relative',
          !hasAccess && 'opacity-60'
        )}
      >
        <AppConfigCard
          app={app}
          onConfigure={() => handleConfigureApp(apps.indexOf(app))}
          onRemove={() => handleRemoveApp(apps.indexOf(app))}
        />
        {/* Role access indicator */}
        {app.access_type && app.access_type !== 'shared' && (
          <div className="absolute top-2 right-12 flex items-center gap-1">
            <span
              className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                app.access_type === 'role_restricted'
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              )}
            >
              {getAccessTypeIcon(app.access_type)}
              {accessibleRoles === 'all'
                ? 'All agents'
                : accessibleRoles.map((r) => r === 'service_agent' ? '🎧' : r === 'customer' ? '📱' : '👥').join(' ')}
            </span>
          </div>
        )}
        {/* Warning if no agent can access */}
        {!hasAccess && (
          <div className="absolute -top-2 -right-2">
            <span
              className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-warning text-warning-foreground"
              title="No agent in simulation has access to this app"
            >
              <AlertTriangle className="h-3 w-3" />
            </span>
          </div>
        )}
      </div>
    )
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
            <div className="space-y-6">
              {/* Role compatibility warning */}
              {hasRoleIssues && (
                <div className="p-3 rounded-lg bg-warning/10 border border-warning/30">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-warning mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-warning">Role Compatibility Issue</p>
                      <p className="text-xs text-foreground-secondary mt-0.5">
                        Some apps are restricted to roles not present in your simulation.
                        These apps will not be accessible to any agent.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Grouped display when there are restricted apps */}
              {(groupedApps.restricted.length > 0 || groupedApps.perAgent.length > 0) ? (
                <>
                  {/* Role-Restricted Apps */}
                  {groupedApps.restricted.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-foreground-secondary flex items-center gap-2">
                        <Headphones className="h-4 w-4" />
                        Role-Restricted Apps ({groupedApps.restricted.length})
                      </h4>
                      <div className="space-y-3 pl-2 border-l-2 border-purple-200 dark:border-purple-800">
                        {groupedApps.restricted.map((app) => renderAppCard(app, apps.indexOf(app)))}
                      </div>
                    </div>
                  )}

                  {/* Per-Agent Apps */}
                  {groupedApps.perAgent.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-foreground-secondary flex items-center gap-2">
                        <Smartphone className="h-4 w-4" />
                        Per-Agent Apps ({groupedApps.perAgent.length})
                      </h4>
                      <div className="space-y-3 pl-2 border-l-2 border-blue-200 dark:border-blue-800">
                        {groupedApps.perAgent.map((app) => renderAppCard(app, apps.indexOf(app)))}
                      </div>
                    </div>
                  )}

                  {/* Shared Apps */}
                  {groupedApps.shared.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-foreground-secondary flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        Shared Apps ({groupedApps.shared.length})
                      </h4>
                      <div className="space-y-3 pl-2 border-l-2 border-border">
                        {groupedApps.shared.map((app) => renderAppCard(app, apps.indexOf(app)))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Simple list when all apps are shared */
                <div className="space-y-3">
                  {apps.map((app, index) => renderAppCard(app, index))}
                </div>
              )}
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
                  {agentRoles.length > 0 && agentRoles.some((r) => r !== 'peer') && (
                    <span className="block mt-1 text-xs">
                      <strong>τ²-bench mode:</strong> Role-restricted apps are only accessible to agents with matching roles.
                    </span>
                  )}
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
