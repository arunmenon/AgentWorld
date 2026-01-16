import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Grid, List, Trash2, Edit2 } from 'lucide-react'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  confirm,
  toast,
} from '@/components/ui'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { EmptyState } from '@/components/EmptyState'
import { PersonaWizard, PersonaFormData } from '@/components/PersonaWizard'

// Trait-derived avatar colors based on UI-ADR-001
function getTraitColor(traits?: { openness?: number; conscientiousness?: number; extraversion?: number; agreeableness?: number; neuroticism?: number }) {
  if (!traits) return { bg: 'bg-slate-500/20', text: 'text-slate-400' }

  const traitColors = [
    { trait: traits.openness || 0, bg: 'bg-violet-500/20', text: 'text-violet-400' },       // Purple - Creative
    { trait: traits.conscientiousness || 0, bg: 'bg-blue-500/20', text: 'text-blue-400' },  // Blue - Organized
    { trait: traits.extraversion || 0, bg: 'bg-orange-500/20', text: 'text-orange-400' },   // Orange - Outgoing
    { trait: traits.agreeableness || 0, bg: 'bg-emerald-500/20', text: 'text-emerald-400' }, // Green - Cooperative
    { trait: traits.neuroticism || 0, bg: 'bg-rose-500/20', text: 'text-rose-400' },        // Red - Sensitive
  ]

  const dominant = traitColors.reduce((max, curr) => curr.trait > max.trait ? curr : max)
  return dominant.trait > 0.7 ? dominant : { bg: 'bg-slate-500/20', text: 'text-slate-400' }
}

// Persona type for editing
interface EditingPersona {
  id: string
  data: Partial<PersonaFormData>
}

export default function Personas() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isWizardOpen, setIsWizardOpen] = useState(false)
  const [editingPersona, setEditingPersona] = useState<EditingPersona | null>(null)

  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['personas'],
    queryFn: () => api.getPersonas(),
  })

  const createMutation = useMutation({
    mutationFn: api.createPersona,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personas'] })
      setIsWizardOpen(false)
      toast.success('Persona created', 'Your new persona has been added to the library.')
    },
    onError: () => {
      toast.error('Failed to create persona', 'Please try again.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.createPersona>[0] }) =>
      api.updatePersona(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personas'] })
      setEditingPersona(null)
      toast.success('Persona updated', 'Your changes have been saved.')
    },
    onError: () => {
      toast.error('Failed to update persona', 'Please try again.')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: api.deletePersona,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personas'] })
      toast.success('Persona deleted', 'The persona has been removed from your library.')
    },
    onError: () => {
      toast.error('Failed to delete persona', 'Please try again.')
    },
  })

  const handleDelete = async (personaId: string, personaName: string) => {
    const confirmed = await confirm({
      type: 'danger',
      title: `Delete "${personaName}"?`,
      description: 'This action cannot be undone. The persona will be permanently removed from your library.',
      confirmLabel: 'Delete',
    })
    if (confirmed) {
      deleteMutation.mutate(personaId)
    }
  }

  const personas = data?.personas || []
  const filteredPersonas = personas.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.occupation?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreate = (formData: PersonaFormData) => {
    createMutation.mutate({
      ...formData,
      age: formData.age || undefined,
    })
  }

  const handleEdit = (persona: typeof personas[0]) => {
    const traits = persona.traits || {}
    setEditingPersona({
      id: persona.id,
      data: {
        name: persona.name,
        description: persona.description || '',
        occupation: persona.occupation || '',
        age: persona.age || null,
        location: persona.location || '',
        background: persona.background || '',
        traits: {
          openness: (traits.openness as number) ?? 0.5,
          conscientiousness: (traits.conscientiousness as number) ?? 0.5,
          extraversion: (traits.extraversion as number) ?? 0.5,
          agreeableness: (traits.agreeableness as number) ?? 0.5,
          neuroticism: (traits.neuroticism as number) ?? 0.3,
        },
        tags: persona.tags || [],
      },
    })
  }

  const handleUpdate = (formData: PersonaFormData) => {
    if (!editingPersona) return
    updateMutation.mutate({
      id: editingPersona.id,
      data: {
        ...formData,
        age: formData.age || undefined,
      },
    })
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Personas</h1>
          <p className="text-foreground-secondary">
            Manage your agent persona library.
          </p>
        </div>
        <Button onClick={() => setIsWizardOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Persona
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
          <Input
            placeholder="Search personas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Personas */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="h-12 w-12 rounded-full bg-slate-700/50 animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-24 bg-slate-700/50 animate-pulse rounded" />
                    <div className="h-3 w-32 bg-slate-700/50 animate-pulse rounded" />
                  </div>
                </div>
                <div className="mt-3 h-8 bg-slate-700/50 animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredPersonas.length === 0 ? (
        <EmptyState
          title="No personas found"
          description={
            searchQuery
              ? 'Try adjusting your search.'
              : 'Create your first persona to get started.'
          }
          action={
            !searchQuery ? (
              <Button onClick={() => setIsWizardOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Persona
              </Button>
            ) : null
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredPersonas.map((persona) => {
            const traitColor = getTraitColor(persona.traits)
            return (
              <Card key={persona.id} className="hover:border-primary/50 transition-colors group">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={cn(
                      "h-12 w-12 rounded-full flex items-center justify-center flex-shrink-0 text-lg font-semibold",
                      traitColor.bg,
                      traitColor.text
                    )}>
                      {persona.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold truncate">{persona.name}</h3>
                      {persona.occupation && (
                        <p className="text-sm text-foreground-secondary">
                          {persona.occupation}
                        </p>
                      )}
                      {persona.age && (
                        <p className="text-xs text-foreground-muted">
                          Age {persona.age}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEdit(persona)}
                      >
                        <Edit2 className="h-4 w-4 text-foreground-muted" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(persona.id, persona.name)}
                      >
                        <Trash2 className="h-4 w-4 text-error" />
                      </Button>
                    </div>
                  </div>
                  {persona.description && (
                    <p className="mt-3 text-sm text-foreground-secondary line-clamp-2">
                      {persona.description}
                    </p>
                  )}
                  {persona.tags?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {persona.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredPersonas.map((persona) => {
            const traitColor = getTraitColor(persona.traits)
            return (
              <Card key={persona.id} className="hover:border-primary/50 transition-colors group">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className={cn(
                    "h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 font-semibold",
                    traitColor.bg,
                    traitColor.text
                  )}>
                    {persona.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium">{persona.name}</h3>
                    <p className="text-sm text-foreground-secondary truncate">
                      {persona.occupation || persona.description || 'No description'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{persona.usage_count || 0} uses</Badge>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEdit(persona)}
                      >
                        <Edit2 className="h-4 w-4 text-foreground-muted" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(persona.id, persona.name)}
                      >
                        <Trash2 className="h-4 w-4 text-error" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Wizard */}
      <PersonaWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onSubmit={handleCreate}
        isSubmitting={createMutation.isPending}
        mode="create"
      />

      {/* Edit Wizard */}
      <PersonaWizard
        isOpen={!!editingPersona}
        onClose={() => setEditingPersona(null)}
        onSubmit={handleUpdate}
        isSubmitting={updateMutation.isPending}
        initialData={editingPersona?.data}
        mode="edit"
      />
    </div>
  )
}
