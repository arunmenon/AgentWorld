import { useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface TooltipProps {
  content: ReactNode
  children: ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
  maxWidth?: number
}

function Tooltip({ content, children, position = 'top', className, maxWidth }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  const arrows = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-background-tertiary border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-background-tertiary border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-background-tertiary border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-background-tertiary border-y-transparent border-l-transparent',
  }

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className={cn(
            'absolute z-50 rounded-md bg-background-tertiary px-3 py-1.5 text-xs text-foreground shadow-md',
            maxWidth ? 'whitespace-normal' : 'whitespace-nowrap',
            positions[position],
            className
          )}
          style={maxWidth ? { maxWidth: `${maxWidth}px` } : undefined}
        >
          {content}
          <div
            className={cn(
              'absolute h-0 w-0 border-4',
              arrows[position]
            )}
          />
        </div>
      )}
    </div>
  )
}

export { Tooltip }
