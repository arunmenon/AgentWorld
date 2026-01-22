import { Layers, Plus } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import { Search } from 'lucide-react'

interface AppEmptyStateProps {
  type: 'no-apps' | 'no-results'
  searchQuery?: string
  onCreateApp?: () => void
  className?: string
}

export function AppEmptyState({
  type,
  searchQuery,
  onCreateApp,
  className,
}: AppEmptyStateProps) {
  if (type === 'no-results') {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center py-16 text-center',
          className
        )}
      >
        <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mb-4">
          <Search className="h-8 w-8 text-foreground-muted" />
        </div>
        <h3 className="text-lg font-semibold mb-1">No apps found</h3>
        <p className="text-foreground-secondary mb-4 max-w-sm">
          {searchQuery
            ? `No apps match "${searchQuery}". Try a different search term.`
            : 'No apps match your current filters.'}
        </p>
        {onCreateApp && (
          <Button onClick={onCreateApp}>
            <Plus className="h-4 w-4 mr-2" />
            Create New App
          </Button>
        )}
      </div>
    )
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 text-center',
        className
      )}
    >
      <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
        <Layers className="h-10 w-10 text-primary" />
      </div>
      <h3 className="text-xl font-semibold mb-2">No apps yet</h3>
      <p className="text-foreground-secondary mb-6 max-w-md">
        Apps let your agents interact with simulated services like payment systems,
        shopping carts, and email. Create your first app to get started.
      </p>
      {onCreateApp && (
        <Button onClick={onCreateApp}>
          <Plus className="h-4 w-4 mr-2" />
          Create Your First App
        </Button>
      )}
    </div>
  )
}
