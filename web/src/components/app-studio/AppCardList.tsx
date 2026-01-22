import { MoreVertical, Edit, Eye, Copy, Trash2, Download, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Card,
  Button,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui'
import type { AppDefinition } from '@/lib/api'

interface AppCardListProps {
  apps: AppDefinition[]
  loading?: boolean
  onEdit?: (app: AppDefinition) => void
  onView?: (app: AppDefinition) => void
  onDuplicate?: (app: AppDefinition) => void
  onDelete?: (app: AppDefinition) => void
  onExport?: (app: AppDefinition) => void
  className?: string
}

const categoryColors: Record<string, string> = {
  payment: 'bg-emerald-500/10 border-emerald-500/20',
  shopping: 'bg-orange-500/10 border-orange-500/20',
  communication: 'bg-blue-500/10 border-blue-500/20',
  calendar: 'bg-purple-500/10 border-purple-500/20',
  social: 'bg-pink-500/10 border-pink-500/20',
  custom: 'bg-slate-500/10 border-slate-500/20',
}

const categoryTextColors: Record<string, string> = {
  payment: 'text-emerald-500',
  shopping: 'text-orange-500',
  communication: 'text-blue-500',
  calendar: 'text-purple-500',
  social: 'text-pink-500',
  custom: 'text-slate-500',
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
  return date.toLocaleDateString()
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 p-4 border border-border rounded-lg animate-pulse">
      <div className="h-12 w-12 rounded-lg bg-secondary" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-32 bg-secondary rounded" />
        <div className="h-3 w-48 bg-secondary rounded" />
      </div>
      <div className="h-6 w-16 bg-secondary rounded" />
      <div className="h-8 w-16 bg-secondary rounded" />
    </div>
  )
}

interface AppListItemProps {
  app: AppDefinition
  onEdit?: () => void
  onView?: () => void
  onDuplicate?: () => void
  onDelete?: () => void
  onExport?: () => void
}

function AppListItem({
  app,
  onEdit,
  onView,
  onDuplicate,
  onDelete,
  onExport,
}: AppListItemProps) {
  const actionCount = app.actions?.length ?? 0
  const isBuiltin = app.is_builtin

  return (
    <Card className="group flex items-center gap-4 p-4 transition-all hover:shadow-md hover:border-primary/30">
      {/* Icon */}
      <div
        className={cn(
          'flex items-center justify-center h-12 w-12 rounded-lg text-2xl border',
          categoryColors[app.category] || categoryColors.custom
        )}
      >
        {app.icon || '📦'}
      </div>

      {/* Main Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="font-semibold truncate" title={app.name}>
            {app.name}
          </h3>
          <Badge
            className={cn(
              'capitalize text-xs',
              categoryTextColors[app.category] || categoryTextColors.custom
            )}
            variant="outline"
          >
            {app.category}
          </Badge>
        </div>
        <p className="text-sm text-foreground-secondary truncate">
          {app.description || 'No description'}
        </p>
      </div>

      {/* Action Count */}
      <div className="hidden sm:block text-sm text-foreground-secondary whitespace-nowrap">
        {actionCount} action{actionCount !== 1 ? 's' : ''}
      </div>

      {/* Status */}
      <div className="hidden md:flex items-center">
        {isBuiltin ? (
          <Badge variant="outline" className="gap-1">
            <Lock className="h-3 w-3" />
            Built-in
          </Badge>
        ) : (
          <span className="text-xs text-foreground-muted whitespace-nowrap">
            Updated {formatTimeAgo(app.updated_at || app.created_at)}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant={isBuiltin ? 'secondary' : 'primary'}
          size="sm"
          onClick={isBuiltin ? onView : onEdit}
        >
          {isBuiltin ? (
            <>
              <Eye className="h-3.5 w-3.5 mr-1" />
              View
            </>
          ) : (
            <>
              <Edit className="h-3.5 w-3.5 mr-1" />
              Edit
            </>
          )}
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onView}>
              <Eye className="h-4 w-4 mr-2" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onDuplicate}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onExport}>
              <Download className="h-4 w-4 mr-2" />
              Export as JSON
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={onDelete}
              disabled={isBuiltin}
              className={cn(!isBuiltin && 'text-error')}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </Card>
  )
}

export function AppCardList({
  apps,
  loading,
  onEdit,
  onView,
  onDuplicate,
  onDelete,
  onExport,
  className,
}: AppCardListProps) {
  if (loading) {
    return (
      <div className={cn('space-y-3', className)}>
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className={cn('space-y-3', className)}>
      {apps.map((app) => (
        <AppListItem
          key={app.id}
          app={app}
          onEdit={() => onEdit?.(app)}
          onView={() => onView?.(app)}
          onDuplicate={() => onDuplicate?.(app)}
          onDelete={() => onDelete?.(app)}
          onExport={() => onExport?.(app)}
        />
      ))}
    </div>
  )
}
