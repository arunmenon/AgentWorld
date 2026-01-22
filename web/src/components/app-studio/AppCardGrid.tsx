import { cn } from '@/lib/utils'
import { AppCard } from './AppCard'
import { SkeletonCard } from '@/components/ui'
import type { AppDefinition } from '@/lib/api'

interface AppCardGridProps {
  apps: AppDefinition[]
  loading?: boolean
  onEdit?: (app: AppDefinition) => void
  onView?: (app: AppDefinition) => void
  onDuplicate?: (app: AppDefinition) => void
  onDelete?: (app: AppDefinition) => void
  onExport?: (app: AppDefinition) => void
  className?: string
}

export function AppCardGrid({
  apps,
  loading,
  onEdit,
  onView,
  onDuplicate,
  onDelete,
  onExport,
  className,
}: AppCardGridProps) {
  if (loading) {
    return (
      <div
        className={cn(
          'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
          className
        )}
      >
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  return (
    <div
      className={cn(
        'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
        className
      )}
    >
      {apps.map((app) => (
        <AppCard
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
