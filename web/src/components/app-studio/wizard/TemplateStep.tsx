import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui'
import { appTemplates, type AppTemplate } from '@/lib/app-templates'

interface TemplateStepProps {
  selectedTemplate: string | null
  onSelectTemplate: (template: AppTemplate) => void
}

const categoryColors: Record<string, string> = {
  payment: 'bg-emerald-500/10 border-emerald-500/30',
  shopping: 'bg-orange-500/10 border-orange-500/30',
  communication: 'bg-blue-500/10 border-blue-500/30',
  calendar: 'bg-purple-500/10 border-purple-500/30',
  social: 'bg-pink-500/10 border-pink-500/30',
  custom: 'bg-slate-500/10 border-slate-500/30',
}

export function TemplateStep({
  selectedTemplate,
  onSelectTemplate,
}: TemplateStepProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold mb-2">Choose a Template</h2>
        <p className="text-foreground-secondary">
          Start with a pre-built app or create one from scratch
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {appTemplates.map((template) => {
          const isSelected = selectedTemplate === template.id
          const actionCount = template.actions.length

          return (
            <button
              key={template.id}
              type="button"
              onClick={() => onSelectTemplate(template)}
              className={cn(
                'relative p-6 rounded-xl border-2 text-left transition-all',
                'hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary/50',
                isSelected
                  ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                  : 'border-border hover:border-primary/40',
                categoryColors[template.category]
              )}
            >
              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3">
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-primary-foreground"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                </div>
              )}

              {/* Icon */}
              <div className="text-4xl mb-4">{template.icon}</div>

              {/* Name */}
              <h3 className="font-semibold text-lg mb-1">{template.name}</h3>

              {/* Action count */}
              <Badge variant="outline" className="mb-3">
                {actionCount} action{actionCount !== 1 ? 's' : ''}
              </Badge>

              {/* Description */}
              <p className="text-sm text-foreground-secondary line-clamp-2">
                {template.description}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
