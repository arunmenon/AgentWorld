import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { Button, Card } from '@/components/ui'
import { api } from '@/lib/api'
import { AppWizard } from '@/components/app-studio'

export default function AppEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['app-definition', id],
    queryFn: () => api.getAppDefinition(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => navigate('/apps')}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to App Studio
        </Button>

        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => navigate('/apps')}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to App Studio
        </Button>

        <Card className="p-8">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">App Not Found</h2>
            <p className="text-foreground-secondary mb-4">
              The app you're looking for doesn't exist or has been deleted.
            </p>
            <Button onClick={() => navigate('/apps')}>
              Return to App Studio
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  const app = data

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <Button
        variant="ghost"
        className="mb-6"
        onClick={() => navigate('/apps')}
      >
        <ChevronLeft className="h-4 w-4 mr-2" />
        Back to App Studio
      </Button>

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">{app.icon || '📦'}</span>
          <h1 className="text-2xl font-bold">
            {app.is_builtin ? 'View' : 'Edit'} {app.name}
          </h1>
        </div>
        <p className="text-foreground-secondary">
          {app.is_builtin
            ? 'View this built-in app configuration'
            : 'Modify your app configuration'}
        </p>
      </div>

      <AppWizard
        existingApp={{
          id: app.id,
          app_id: app.app_id,
          name: app.name,
          description: app.description,
          category: app.category,
          icon: app.icon,
          actions: app.actions,
          state_schema: app.state_schema,
          initial_config: app.initial_config,
          is_builtin: app.is_builtin,
        }}
      />
    </div>
  )
}
