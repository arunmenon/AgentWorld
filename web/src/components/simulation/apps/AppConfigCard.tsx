import { Settings, X } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { SimulationAppConfig } from './AppsSection'

interface AppConfigCardProps {
  app: SimulationAppConfig
  onConfigure: () => void
  onRemove: () => void
}

const categoryColors: Record<string, string> = {
  payment: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600',
  shopping: 'bg-orange-500/10 border-orange-500/20 text-orange-600',
  communication: 'bg-blue-500/10 border-blue-500/20 text-blue-600',
  calendar: 'bg-purple-500/10 border-purple-500/20 text-purple-600',
  social: 'bg-pink-500/10 border-pink-500/20 text-pink-600',
  custom: 'bg-slate-500/10 border-slate-500/20 text-slate-600',
}

export function AppConfigCard({ app, onConfigure, onRemove }: AppConfigCardProps) {
  const configSummary = Object.entries(app.config || {})
    .slice(0, 2)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' • ')

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border border-border hover:border-primary/30 transition-colors">
      {/* Icon */}
      <div
        className={cn(
          'flex items-center justify-center h-12 w-12 rounded-lg text-2xl border',
          categoryColors[app.category] || categoryColors.custom
        )}
      >
        {app.icon || '📦'}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium truncate">{app.name}</h4>
          <Badge variant="outline" className="text-xs capitalize">
            {app.category}
          </Badge>
        </div>
        <p className="text-sm text-foreground-secondary">
          {app.actions_count} action{app.actions_count !== 1 ? 's' : ''}
          {configSummary && ` • ${configSummary}`}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onConfigure}
        >
          <Settings className="h-4 w-4 mr-1" />
          Configure
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          className="h-8 w-8 text-foreground-muted hover:text-error"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
