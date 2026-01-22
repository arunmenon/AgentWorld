import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Grid, List } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Button, confirm, toast } from '@/components/ui'
import { api, type AppDefinition, type AppCategory } from '@/lib/api'
import {
  AppCardGrid,
  AppCardList,
  AppCategoryTabs,
  AppSearchInput,
  AppEmptyState,
} from '@/components/app-studio'

const VIEW_MODE_KEY = 'app-studio-view-mode'

function getStoredViewMode(): 'grid' | 'list' {
  try {
    const stored = localStorage.getItem(VIEW_MODE_KEY)
    if (stored === 'grid' || stored === 'list') return stored
  } catch {
    // localStorage not available
  }
  return 'grid'
}

export default function Apps() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()

  // Initialize view mode from localStorage
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(getStoredViewMode)
  const [searchQuery, setSearchQuery] = useState('')

  // Get category from URL params, default to 'all'
  const categoryParam = searchParams.get('category')
  const selectedCategory: AppCategory | 'all' =
    categoryParam && ['payment', 'shopping', 'communication', 'calendar', 'social', 'custom'].includes(categoryParam)
      ? (categoryParam as AppCategory)
      : 'all'

  // Persist view mode to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(VIEW_MODE_KEY, viewMode)
    } catch {
      // localStorage not available
    }
  }, [viewMode])

  // Update URL when category changes
  const handleCategoryChange = (category: AppCategory | 'all') => {
    if (category === 'all') {
      searchParams.delete('category')
    } else {
      searchParams.set('category', category)
    }
    setSearchParams(searchParams)
  }

  // Fetch app definitions
  const { data, isLoading } = useQuery({
    queryKey: ['app-definitions', selectedCategory],
    queryFn: () =>
      api.getAppDefinitions({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
      }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: api.deleteAppDefinition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-definitions'] })
      toast.success('App deleted', 'The app has been removed.')
    },
    onError: () => {
      toast.error('Failed to delete app', 'Please try again.')
    },
  })

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: ({ id, newAppId, newName }: { id: string; newAppId: string; newName: string }) =>
      api.duplicateAppDefinition(id, { new_app_id: newAppId, new_name: newName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-definitions'] })
      toast.success('App duplicated', 'A copy has been created.')
    },
    onError: () => {
      toast.error('Failed to duplicate app', 'Please try again.')
    },
  })

  // Filter apps by search query
  const apps = data?.definitions || []
  const filteredApps = useMemo(() => {
    if (!searchQuery) return apps
    const query = searchQuery.toLowerCase()
    return apps.filter(
      (app) =>
        app.name.toLowerCase().includes(query) ||
        app.description?.toLowerCase().includes(query) ||
        app.app_id.toLowerCase().includes(query)
    )
  }, [apps, searchQuery])

  // Separate system apps and user apps
  const systemApps = filteredApps.filter((app) => app.is_builtin)
  const userApps = filteredApps.filter((app) => !app.is_builtin)

  // Handlers
  const handleCreateApp = () => {
    navigate('/apps/new')
  }

  const handleEditApp = (app: AppDefinition) => {
    navigate(`/apps/${app.id}`)
  }

  const handleViewApp = (app: AppDefinition) => {
    navigate(`/apps/${app.id}`)
  }

  const handleDuplicateApp = async (app: AppDefinition) => {
    const newName = `${app.name} (Copy)`
    const newAppId = `${app.app_id}_copy_${Date.now()}`
    duplicateMutation.mutate({
      id: app.id,
      newAppId,
      newName,
    })
  }

  const handleDeleteApp = async (app: AppDefinition) => {
    if (app.is_builtin) {
      toast.error('Cannot delete', 'Built-in apps cannot be deleted.')
      return
    }

    const confirmed = await confirm({
      type: 'danger',
      title: `Delete "${app.name}"?`,
      description:
        'This action cannot be undone. The app will be permanently removed.',
      confirmLabel: 'Delete',
    })
    if (confirmed) {
      deleteMutation.mutate(app.id)
    }
  }

  const handleExportApp = (app: AppDefinition) => {
    // Export as JSON
    const exportData = {
      app_id: app.app_id,
      name: app.name,
      description: app.description,
      category: app.category,
      icon: app.icon,
      actions: app.actions,
      state_schema: app.state_schema,
      initial_config: app.initial_config,
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${app.app_id}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Exported', `${app.name} has been exported as JSON.`)
  }

  const isEmpty = apps.length === 0 && !isLoading
  const noResults = filteredApps.length === 0 && apps.length > 0

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">App Studio</h1>
          <p className="text-foreground-secondary mt-1">
            Create and manage simulated apps for your agents
          </p>
        </div>
        <Button onClick={handleCreateApp}>
          <Plus className="h-4 w-4 mr-2" />
          Create App
        </Button>
      </div>

      {/* Search and Filters */}
      {!isEmpty && (
        <div className="flex flex-col lg:flex-row gap-4">
          <AppSearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            className="w-full lg:w-80"
          />
          <div className="flex items-center justify-between flex-1 gap-4">
            <AppCategoryTabs
              value={selectedCategory}
              onChange={handleCategoryChange}
            />
            <div className="flex items-center border border-border rounded-md">
              <Button
                variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                size="icon"
                onClick={() => setViewMode('grid')}
                className="rounded-r-none"
              >
                <Grid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                size="icon"
                onClick={() => setViewMode('list')}
                className="rounded-l-none"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Empty States */}
      {isEmpty && (
        <AppEmptyState
          type="no-apps"
          onCreateApp={handleCreateApp}
        />
      )}

      {noResults && (
        <AppEmptyState
          type="no-results"
          searchQuery={searchQuery}
          onCreateApp={handleCreateApp}
        />
      )}

      {/* App Grid/List */}
      {!isEmpty && !noResults && (
        <div className="space-y-8">
          {/* System Apps */}
          {systemApps.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-4">
                System Apps ({systemApps.length})
              </h2>
              {viewMode === 'grid' ? (
                <AppCardGrid
                  apps={systemApps}
                  loading={isLoading}
                  onEdit={handleEditApp}
                  onView={handleViewApp}
                  onDuplicate={handleDuplicateApp}
                  onDelete={handleDeleteApp}
                  onExport={handleExportApp}
                />
              ) : (
                <AppCardList
                  apps={systemApps}
                  loading={isLoading}
                  onEdit={handleEditApp}
                  onView={handleViewApp}
                  onDuplicate={handleDuplicateApp}
                  onDelete={handleDeleteApp}
                  onExport={handleExportApp}
                />
              )}
            </section>
          )}

          {/* User Apps */}
          {userApps.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-4">
                My Apps ({userApps.length})
              </h2>
              {viewMode === 'grid' ? (
                <AppCardGrid
                  apps={userApps}
                  loading={isLoading}
                  onEdit={handleEditApp}
                  onView={handleViewApp}
                  onDuplicate={handleDuplicateApp}
                  onDelete={handleDeleteApp}
                  onExport={handleExportApp}
                />
              ) : (
                <AppCardList
                  apps={userApps}
                  loading={isLoading}
                  onEdit={handleEditApp}
                  onView={handleViewApp}
                  onDuplicate={handleDuplicateApp}
                  onDelete={handleDeleteApp}
                  onExport={handleExportApp}
                />
              )}
            </section>
          )}

          {/* Show all if no separation needed */}
          {systemApps.length === 0 && userApps.length === 0 && (
            viewMode === 'grid' ? (
              <AppCardGrid
                apps={filteredApps}
                loading={isLoading}
                onEdit={handleEditApp}
                onView={handleViewApp}
                onDuplicate={handleDuplicateApp}
                onDelete={handleDeleteApp}
                onExport={handleExportApp}
              />
            ) : (
              <AppCardList
                apps={filteredApps}
                loading={isLoading}
                onEdit={handleEditApp}
                onView={handleViewApp}
                onDuplicate={handleDuplicateApp}
                onDelete={handleDeleteApp}
                onExport={handleExportApp}
              />
            )
          )}
        </div>
      )}
    </div>
  )
}
