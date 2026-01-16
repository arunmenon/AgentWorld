import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Play, Pause, Trash2, Eye } from 'lucide-react'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
} from '@/components/ui'
import { formatDate, formatCurrency } from '@/lib/utils'
import { api } from '@/lib/api'
import { EmptyState } from '@/components/EmptyState'

function SimulationStatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
    running: 'success',
    paused: 'warning',
    completed: 'default',
    pending: 'default',
    failed: 'error',
  }
  return <Badge variant={variants[status] || 'default'}>{status}</Badge>
}

export default function Simulations() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['simulations', statusFilter],
    queryFn: () => api.getSimulations({ status: statusFilter || undefined }),
  })

  const simulations = data?.simulations || []
  const filteredSimulations = simulations.filter((sim) =>
    sim.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Simulations</h1>
          <p className="text-foreground-secondary">
            Create, run, and manage your agent simulations.
          </p>
        </div>
        <Link to="/simulations/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Simulation
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
          <Input
            placeholder="Search simulations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={statusFilter === null ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter(null)}
          >
            All
          </Button>
          <Button
            variant={statusFilter === 'running' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('running')}
          >
            Running
          </Button>
          <Button
            variant={statusFilter === 'paused' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('paused')}
          >
            Paused
          </Button>
          <Button
            variant={statusFilter === 'completed' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('completed')}
          >
            Completed
          </Button>
        </div>
      </div>

      {/* Simulations List */}
      {isLoading ? (
        <div className="text-center py-12 text-foreground-secondary">
          Loading simulations...
        </div>
      ) : filteredSimulations.length === 0 ? (
        <EmptyState
          title="No simulations found"
          description={
            searchQuery || statusFilter
              ? 'Try adjusting your search or filters.'
              : 'Create your first simulation to get started.'
          }
          action={
            !searchQuery && !statusFilter ? (
              <Link to="/simulations/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Simulation
                </Button>
              </Link>
            ) : null
          }
        />
      ) : (
        <div className="grid gap-4">
          {filteredSimulations.map((sim) => (
            <Card key={sim.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Link
                        to={`/simulations/${sim.id}`}
                        className="text-lg font-semibold hover:text-primary transition-colors"
                      >
                        {sim.name}
                      </Link>
                      <SimulationStatusBadge status={sim.status} />
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-foreground-secondary">
                      <span>{sim.agent_count} agents</span>
                      <span>{sim.message_count} messages</span>
                      <span>
                        Step {sim.current_step} / {sim.total_steps}
                      </span>
                      <span>{formatCurrency(sim.total_cost)}</span>
                    </div>
                    {sim.progress_percent !== null && (
                      <div className="mt-3">
                        <div className="h-1.5 w-full max-w-xs bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${sim.progress_percent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Link to={`/simulations/${sim.id}`}>
                      <Button variant="ghost" size="icon">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>
                    {sim.status === 'running' ? (
                      <Button variant="ghost" size="icon">
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : sim.status === 'paused' ? (
                      <Button variant="ghost" size="icon">
                        <Play className="h-4 w-4" />
                      </Button>
                    ) : null}
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4 text-error" />
                    </Button>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs text-foreground-muted">
                  <span>Created {formatDate(sim.created_at)}</span>
                  {sim.updated_at && <span>Updated {formatDate(sim.updated_at)}</span>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
