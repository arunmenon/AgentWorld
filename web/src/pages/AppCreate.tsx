import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { Button } from '@/components/ui'
import { AppWizard } from '@/components/app-studio'

export default function AppCreate() {
  const navigate = useNavigate()

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
        <h1 className="text-2xl font-bold">Create New App</h1>
        <p className="text-foreground-secondary mt-1">
          Build a simulated app that agents can interact with
        </p>
      </div>

      <AppWizard />
    </div>
  )
}
