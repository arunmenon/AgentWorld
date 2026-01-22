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

interface AppCardProps {
  app: AppDefinition
  onEdit?: () => void
  onView?: () => void
  onDuplicate?: () => void
  onDelete?: () => void
  onExport?: () => void
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

export function AppCard({
  app,
  onEdit,
  onView,
  onDuplicate,
  onDelete,
  onExport,
  className,
}: AppCardProps) {
  const actionCount = app.actions?.length ?? 0
  const isBuiltin = app.is_builtin

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
    return date.toLocaleDateString()
  }

  return (
    <Card
      className={cn(
        'group relative flex flex-col overflow-hidden transition-all hover:shadow-md hover:border-primary/30',
        className
      )}
    >
      {/* Icon Header */}
      <div
        className={cn(
          'flex items-center justify-center h-20 text-4xl border-b',
          categoryColors[app.category] || categoryColors.custom
        )}
      >
        {app.icon || '📦'}
      </div>

      {/* Content */}
      <div className="flex flex-col flex-1 p-4">
        {/* Title and Actions */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-semibold text-base truncate" title={app.name}>
            {app.name}
          </h3>
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

        {/* Action Count */}
        <p className="text-sm text-foreground-secondary mb-2">
          {actionCount} action{actionCount !== 1 ? 's' : ''}
        </p>

        {/* Description */}
        <p className="text-sm text-foreground-secondary line-clamp-2 flex-1 mb-3">
          {app.description || 'No description'}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-border">
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

          {isBuiltin ? (
            <Badge variant="outline" className="gap-1">
              <Lock className="h-3 w-3" />
              Built-in
            </Badge>
          ) : (
            <span className="text-xs text-foreground-muted">
              Updated {formatTimeAgo(app.updated_at || app.created_at)}
            </span>
          )}
        </div>
      </div>

      {/* Category Badge - positioned absolute */}
      <Badge
        className={cn(
          'absolute top-2 right-2 capitalize',
          categoryTextColors[app.category] || categoryTextColors.custom
        )}
        variant="outline"
      >
        {app.category}
      </Badge>
    </Card>
  )
}
