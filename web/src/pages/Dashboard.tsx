import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Play, Users, MessageSquare, DollarSign, Plus, ArrowRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Skeleton } from '@/components/ui'
import { formatDate, formatCurrency } from '@/lib/utils'
import { api } from '@/lib/api'

interface StatCardProps {
  title: string
  value: string | number
  icon: typeof Play
  trend?: { value: number; label: string }
  isLoading?: boolean
}

function StatCard({ title, value, icon: Icon, trend, isLoading }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground-secondary">{title}</p>
            {isLoading ? (
              <Skeleton className="h-8 w-16 mt-1" />
            ) : (
              <p className="text-2xl font-bold mt-1">{value}</p>
            )}
            {trend && (
              <p className="text-xs text-foreground-muted mt-1">
                <span className={trend.value >= 0 ? 'text-success' : 'text-error'}>
                  {trend.value >= 0 ? '+' : ''}{trend.value}%
                </span>{' '}
                {trend.label}
              </p>
            )}
          </div>
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Progress bar component for running simulations
function ProgressBar({ current, total }: { current: number; total: number }) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-success rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-foreground-muted whitespace-nowrap">
        {current}/{total}
      </span>
    </div>
  )
}

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

export default function Dashboard() {
  const { data: simulations, isLoading } = useQuery({
    queryKey: ['simulations', 'recent'],
    queryFn: () => api.getSimulations({ limit: 5 }),
  })

  const stats = {
    totalSimulations: simulations?.total || 0,
    totalAgents: simulations?.simulations?.reduce((acc, s) => acc + (s.agent_count || 0), 0) || 0,
    totalMessages: simulations?.simulations?.reduce((acc, s) => acc + (s.message_count || 0), 0) || 0,
    totalCost: simulations?.simulations?.reduce((acc, s) => acc + (s.total_cost || 0), 0) || 0,
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-foreground-secondary">
            Welcome to AgentWorld. Create and manage multi-agent simulations.
          </p>
        </div>
        <Link to="/simulations/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Simulation
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Simulations"
          value={stats.totalSimulations}
          icon={Play}
          isLoading={isLoading}
        />
        <StatCard
          title="Total Agents"
          value={stats.totalAgents}
          icon={Users}
          isLoading={isLoading}
        />
        <StatCard
          title="Total Messages"
          value={stats.totalMessages}
          icon={MessageSquare}
          isLoading={isLoading}
        />
        <StatCard
          title="Total Cost"
          value={formatCurrency(stats.totalCost)}
          icon={DollarSign}
          isLoading={isLoading}
        />
      </div>

      {/* Recent Simulations */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Simulations</CardTitle>
          <Link to="/simulations">
            <Button variant="ghost" size="sm">
              View all
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="divide-y divide-border">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between py-4">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-6 w-20 rounded-full" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                </div>
              ))}
            </div>
          ) : !simulations?.simulations?.length ? (
            <div className="text-center py-8">
              <p className="text-foreground-secondary mb-4">
                No simulations yet. Create your first one to get started.
              </p>
              <Link to="/simulations/new">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Simulation
                </Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {simulations.simulations.map((sim) => (
                <Link
                  key={sim.id}
                  to={`/simulations/${sim.id}`}
                  className="flex items-center justify-between py-4 hover:bg-secondary/50 -mx-6 px-6 transition-colors"
                >
                  <div>
                    <p className="font-medium">{sim.name}</p>
                    <p className="text-sm text-foreground-secondary">
                      {sim.agent_count} agents · {sim.message_count} messages
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {sim.status === 'running' && sim.current_step !== undefined && sim.max_steps ? (
                      <ProgressBar current={sim.current_step} total={sim.max_steps} />
                    ) : (
                      <SimulationStatusBadge status={sim.status} />
                    )}
                    <span className="text-sm text-foreground-muted">
                      {formatDate(sim.created_at)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link to="/simulations/new">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Play className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Run Simulation</p>
                <p className="text-sm text-foreground-secondary">
                  Create and execute a new simulation
                </p>
              </div>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link to="/personas">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center">
                <Users className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="font-medium">Manage Personas</p>
                <p className="text-sm text-foreground-secondary">
                  Create and organize agent personas
                </p>
              </div>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer">
          <Link to="/docs">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center">
                <MessageSquare className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="font-medium">Documentation</p>
                <p className="text-sm text-foreground-secondary">
                  Learn how to use AgentWorld
                </p>
              </div>
            </CardContent>
          </Link>
        </Card>
      </div>
    </div>
  )
}
