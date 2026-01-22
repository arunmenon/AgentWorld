import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface WizardStep {
  id: string
  label: string
  description?: string
}

interface WizardStepsProps {
  steps: WizardStep[]
  currentStep: number
  onStepClick?: (index: number) => void
  className?: string
}

export function WizardSteps({
  steps,
  currentStep,
  onStepClick,
  className,
}: WizardStepsProps) {
  return (
    <div className={cn('flex items-center justify-center', className)}>
      {steps.map((step, index) => {
        const isCompleted = index < currentStep
        const isCurrent = index === currentStep
        const isClickable = onStepClick && index <= currentStep

        return (
          <div key={step.id} className="flex items-center">
            {/* Step Circle */}
            <button
              type="button"
              onClick={() => isClickable && onStepClick(index)}
              disabled={!isClickable}
              className={cn(
                'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all',
                isCompleted && 'bg-primary border-primary text-primary-foreground',
                isCurrent && 'border-primary text-primary',
                !isCompleted && !isCurrent && 'border-border text-foreground-muted',
                isClickable && 'cursor-pointer hover:scale-105',
                !isClickable && 'cursor-default'
              )}
            >
              {isCompleted ? (
                <Check className="h-5 w-5" />
              ) : (
                <span className="text-sm font-medium">{index + 1}</span>
              )}
            </button>

            {/* Step Label (shown below on mobile, inline on desktop) */}
            <div className="hidden sm:block ml-3">
              <p
                className={cn(
                  'text-sm font-medium',
                  isCurrent && 'text-primary',
                  !isCurrent && 'text-foreground-secondary'
                )}
              >
                {step.label}
              </p>
            </div>

            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'w-12 sm:w-24 h-0.5 mx-2 sm:mx-4',
                  index < currentStep ? 'bg-primary' : 'bg-border'
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
