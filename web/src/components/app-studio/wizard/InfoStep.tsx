import { AlertCircle } from 'lucide-react'
import { Input, Textarea, Label } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { AppCategory } from '@/lib/api'

interface AppInfoData {
  name: string
  app_id: string
  description: string
  category: AppCategory
  icon: string
}

interface ValidationErrors {
  name?: string
  app_id?: string
}

interface InfoStepProps {
  data: AppInfoData
  onChange: (data: Partial<AppInfoData>) => void
  errors: ValidationErrors
  touched: Record<string, boolean>
  onBlur: (field: string) => void
}

const categories: { value: AppCategory; label: string; icon: string }[] = [
  { value: 'payment', label: 'Payment', icon: '💳' },
  { value: 'shopping', label: 'Shopping', icon: '🛒' },
  { value: 'communication', label: 'Communication', icon: '📧' },
  { value: 'calendar', label: 'Calendar', icon: '📅' },
  { value: 'social', label: 'Social', icon: '💬' },
  { value: 'custom', label: 'Custom', icon: '🔧' },
]

const commonIcons = ['💳', '🛒', '📧', '📅', '💬', '📝', '🏦', '🎮', '📱', '🔧', '🎯', '📊', '🔔', '⚡', '🎁', '🏠']

function generateAppId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 50)
}

export function InfoStep({
  data,
  onChange,
  errors,
  touched,
  onBlur,
}: InfoStepProps) {
  const handleNameChange = (name: string) => {
    onChange({ name })
    // Auto-generate app_id if it hasn't been manually edited
    if (!touched.app_id) {
      onChange({ name, app_id: generateAppId(name) })
    } else {
      onChange({ name })
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-xl font-semibold mb-2">App Details</h2>
        <p className="text-foreground-secondary">
          Give your app a name and description
        </p>
      </div>

      {/* App Name */}
      <div className="space-y-2">
        <Label htmlFor="name">App Name *</Label>
        <Input
          id="name"
          value={data.name}
          onChange={(e) => handleNameChange(e.target.value)}
          onBlur={() => onBlur('name')}
          placeholder="My Awesome App"
          className={cn(
            touched.name && errors.name && 'border-error focus:ring-error'
          )}
        />
        <p className="text-sm text-foreground-muted">
          This will be shown to agents
        </p>
        {touched.name && errors.name && (
          <p className="text-sm text-error flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {errors.name}
          </p>
        )}
      </div>

      {/* App ID */}
      <div className="space-y-2">
        <Label htmlFor="app_id">App ID *</Label>
        <Input
          id="app_id"
          value={data.app_id}
          onChange={(e) => onChange({ app_id: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })}
          onBlur={() => onBlur('app_id')}
          placeholder="my_awesome_app"
          className={cn(
            'font-mono text-sm',
            touched.app_id && errors.app_id && 'border-error focus:ring-error'
          )}
        />
        <p className="text-sm text-foreground-muted">
          Unique identifier (auto-generated from name)
        </p>
        {touched.app_id && errors.app_id && (
          <p className="text-sm text-error flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {errors.app_id}
          </p>
        )}
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={data.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="Describe what this app does..."
          rows={3}
        />
        <p className="text-sm text-foreground-muted">
          Helps agents understand what this app does
        </p>
      </div>

      {/* Category and Icon Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Category */}
        <div className="space-y-2">
          <Label>Category</Label>
          <div className="grid grid-cols-3 gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => onChange({ category: cat.value })}
                className={cn(
                  'p-2 rounded-lg border text-center transition-all',
                  data.category === cat.value
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:border-primary/40'
                )}
              >
                <span className="text-xl block">{cat.icon}</span>
                <span className="text-xs">{cat.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Icon */}
        <div className="space-y-2">
          <Label>Icon</Label>
          <div className="flex flex-wrap gap-2">
            {commonIcons.map((icon) => (
              <button
                key={icon}
                type="button"
                onClick={() => onChange({ icon })}
                className={cn(
                  'w-10 h-10 rounded-lg border text-xl flex items-center justify-center transition-all',
                  data.icon === icon
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/40'
                )}
              >
                {icon}
              </button>
            ))}
          </div>
          <p className="text-sm text-foreground-muted">
            Or type a custom emoji:
            <input
              type="text"
              value={data.icon}
              onChange={(e) => onChange({ icon: e.target.value.slice(0, 2) })}
              className="ml-2 w-12 px-2 py-1 border border-border rounded text-center"
              maxLength={2}
            />
          </p>
        </div>
      </div>
    </div>
  )
}
