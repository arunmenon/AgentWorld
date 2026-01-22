import { cn } from '@/lib/utils'
import type { AppCategory } from '@/lib/api'

interface CategoryOption {
  value: AppCategory | 'all'
  label: string
  icon: string
}

const categories: CategoryOption[] = [
  { value: 'all', label: 'All', icon: '📋' },
  { value: 'payment', label: 'Payments', icon: '💳' },
  { value: 'shopping', label: 'Shopping', icon: '🛒' },
  { value: 'communication', label: 'Communication', icon: '📧' },
  { value: 'calendar', label: 'Calendar', icon: '📅' },
  { value: 'social', label: 'Social', icon: '💬' },
  { value: 'custom', label: 'Custom', icon: '🔧' },
]

interface AppCategoryTabsProps {
  value: AppCategory | 'all'
  onChange: (value: AppCategory | 'all') => void
  className?: string
}

export function AppCategoryTabs({ value, onChange, className }: AppCategoryTabsProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {categories.map((category) => (
        <button
          key={category.value}
          onClick={() => onChange(category.value)}
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium',
            'transition-colors border',
            value === category.value
              ? 'bg-primary text-primary-foreground border-primary'
              : 'bg-background-secondary border-border text-foreground-secondary hover:bg-secondary hover:text-foreground'
          )}
        >
          <span>{category.icon}</span>
          <span>{category.label}</span>
        </button>
      ))}
    </div>
  )
}
