import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Check, Plus, X, ExternalLink, Lock } from 'lucide-react'
import { Button, Badge, Input, Tooltip } from '@/components/ui'
import { cn } from '@/lib/utils'
import { api, type AppDefinition, type AppCategory } from '@/lib/api'

// Combined app type for picker (can be definition or built-in)
interface PickerApp {
  id: string // definition id for db apps, app_id for built-in
  app_id: string
  name: string
  description: string | null
  category: AppCategory
  icon: string | null
  actions_count: number
  is_builtin: boolean
  // Only for db apps
  initial_config?: Record<string, unknown>
  actions?: { name: string }[]
}

interface AppPickerModalProps {
  selectedAppIds: string[]
  onSelect: (app: AppDefinition) => void
  onClose: () => void
}

const categories: { value: AppCategory | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'payment', label: 'Payments' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'communication', label: 'Communication' },
  { value: 'calendar', label: 'Calendar' },
  { value: 'social', label: 'Social' },
  { value: 'custom', label: 'Custom' },
]

const categoryColors: Record<string, string> = {
  payment: 'bg-emerald-500/10 border-emerald-500/20',
  shopping: 'bg-orange-500/10 border-orange-500/20',
  communication: 'bg-blue-500/10 border-blue-500/20',
  calendar: 'bg-purple-500/10 border-purple-500/20',
  social: 'bg-pink-500/10 border-pink-500/20',
  custom: 'bg-slate-500/10 border-slate-500/20',
}

export function AppPickerModal({
  selectedAppIds,
  onSelect,
  onClose,
}: AppPickerModalProps) {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<AppCategory | 'all'>('all')

  // Fetch app definitions from database
  const { data: definitionsData, isLoading: loadingDefs } = useQuery({
    queryKey: ['app-definitions', selectedCategory],
    queryFn: () =>
      api.getAppDefinitions({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
      }),
  })

  // Fetch built-in available apps
  const { data: availableData, isLoading: loadingAvailable } = useQuery({
    queryKey: ['available-apps'],
    queryFn: () => api.getAvailableApps(),
  })

  const isLoading = loadingDefs || loadingAvailable

  // Merge definitions and built-in apps
  const apps = useMemo(() => {
    const definitions = definitionsData?.definitions || []
    const availableApps = availableData?.apps || []
    const result: PickerApp[] = []
    const seenAppIds = new Set<string>()

    // Add database definitions first
    for (const def of definitions) {
      seenAppIds.add(def.app_id)
      result.push({
        id: def.id,
        app_id: def.app_id,
        name: def.name,
        description: def.description,
        category: def.category,
        icon: def.icon,
        actions_count: def.actions?.length || 0,
        is_builtin: def.is_builtin,
        initial_config: def.initial_config,
        actions: def.actions,
      })
    }

    // Add built-in apps that aren't already in definitions
    for (const app of availableApps) {
      if (!seenAppIds.has(app.app_id)) {
        // Infer category from app_id or default to payment
        let category: AppCategory = 'payment'
        if (app.app_id.includes('mail') || app.app_id.includes('email')) {
          category = 'communication'
        } else if (app.app_id.includes('shop') || app.app_id.includes('cart')) {
          category = 'shopping'
        } else if (app.app_id.includes('calendar')) {
          category = 'calendar'
        }

        result.push({
          id: `builtin-${app.app_id}`, // Use prefixed id for built-in
          app_id: app.app_id,
          name: app.name,
          description: app.description,
          category,
          icon: category === 'payment' ? '💳' : category === 'communication' ? '📧' : '📦',
          actions_count: app.actions?.length || 0,
          is_builtin: true,
          actions: app.actions?.map((a) => ({ name: a.name })),
        })
      }
    }

    return result
  }, [definitionsData, availableData])

  // Filter by search and category
  const filteredApps = apps.filter((app) => {
    // Filter by category
    if (selectedCategory !== 'all' && app.category !== selectedCategory) {
      return false
    }
    // Filter by search
    if (!search) return true
    const query = search.toLowerCase()
    return (
      app.name.toLowerCase().includes(query) ||
      app.description?.toLowerCase().includes(query) ||
      app.app_id.toLowerCase().includes(query)
    )
  })

  const handleSelect = (app: PickerApp) => {
    if (selectedAppIds.includes(app.id)) return

    // Convert to AppDefinition format for the callback
    const appDef: AppDefinition = {
      id: app.id,
      app_id: app.app_id,
      name: app.name,
      description: app.description,
      category: app.category,
      icon: app.icon,
      version: 1,
      actions: (app.actions || []).map((a) => ({
        name: typeof a === 'string' ? a : a.name,
        description: '',
        logic: [],
      })),
      state_schema: [],
      initial_config: app.initial_config || {},
      is_builtin: app.is_builtin,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: null,
    }
    onSelect(appDef)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-50 w-full max-w-2xl max-h-[85vh] overflow-hidden rounded-lg border border-border bg-background shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="text-lg font-semibold">Add App</h3>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Search & Filters */}
        <div className="p-4 space-y-3 border-b border-border">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
            <Input
              type="text"
              placeholder="Search apps..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => setSelectedCategory(cat.value)}
                className={cn(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                  selectedCategory === cat.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-foreground-secondary hover:bg-secondary/80'
                )}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* App List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="grid grid-cols-2 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded-lg bg-secondary/50 animate-pulse"
                />
              ))}
            </div>
          ) : filteredApps.length === 0 ? (
            <div className="text-center py-8 text-foreground-muted">
              <p className="mb-2">No apps found</p>
              <p className="text-sm">
                {search
                  ? `No apps match "${search}"`
                  : 'Create an app in the App Studio first'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {filteredApps.map((app) => {
                const isSelected = selectedAppIds.includes(app.id)

                return (
                  <button
                    key={app.id}
                    type="button"
                    onClick={() => handleSelect(app)}
                    disabled={isSelected}
                    className={cn(
                      'p-4 rounded-lg border text-left transition-all',
                      isSelected
                        ? 'border-primary/50 bg-primary/5 cursor-default'
                        : 'border-border hover:border-primary/40 hover:bg-primary/5'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div
                        className={cn(
                          'flex items-center justify-center h-10 w-10 rounded-lg text-xl border flex-shrink-0',
                          categoryColors[app.category] || categoryColors.custom
                        )}
                      >
                        {app.icon || '📦'}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium truncate">{app.name}</h4>
                          {app.is_builtin && (
                            <Tooltip content="Built-in system app">
                              <Lock className="h-3.5 w-3.5 text-foreground-muted flex-shrink-0" />
                            </Tooltip>
                          )}
                          {isSelected && (
                            <Check className="h-4 w-4 text-primary flex-shrink-0" />
                          )}
                        </div>
                        <p className="text-xs text-foreground-secondary">
                          {app.actions_count} action{app.actions_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>

                    {/* Action */}
                    <div className="mt-3 flex justify-end">
                      {isSelected ? (
                        <Badge variant="outline" className="text-primary border-primary">
                          Added
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          <Plus className="h-3 w-3 mr-1" />
                          Add
                        </Badge>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-border bg-secondary/30">
          <a
            href="/apps/new"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline flex items-center gap-1"
          >
            Create a new app
            <ExternalLink className="h-3 w-3" />
          </a>
          <Button onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  )
}
