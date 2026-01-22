import { useState, useRef, useEffect, type ReactNode, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface DropdownMenuProps {
  children: ReactNode
}

interface DropdownMenuTriggerProps {
  children: ReactNode
  asChild?: boolean
}

interface DropdownMenuContentProps {
  children: ReactNode
  align?: 'start' | 'end' | 'center'
  className?: string
}

interface DropdownMenuItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  className?: string
}

interface DropdownMenuSeparatorProps {
  className?: string
}

// Context to share state between components
import { createContext, useContext } from 'react'

interface DropdownContextType {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownContext = createContext<DropdownContextType | null>(null)

function useDropdown() {
  const context = useContext(DropdownContext)
  if (!context) {
    throw new Error('Dropdown components must be used within a DropdownMenu')
  }
  return context
}

export function DropdownMenu({ children }: DropdownMenuProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [open])

  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div ref={containerRef} className="relative inline-block">
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

export function DropdownMenuTrigger({ children, asChild }: DropdownMenuTriggerProps) {
  const { open, setOpen } = useDropdown()

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setOpen(!open)
  }

  if (asChild && children) {
    // Clone the child element and add onClick handler
    const child = children as React.ReactElement
    return (
      <span onClick={handleClick}>
        {child}
      </span>
    )
  }

  return (
    <button onClick={handleClick} type="button">
      {children}
    </button>
  )
}

export function DropdownMenuContent({ children, align = 'end', className }: DropdownMenuContentProps) {
  const { open, setOpen } = useDropdown()

  if (!open) return null

  const alignClasses = {
    start: 'left-0',
    center: 'left-1/2 -translate-x-1/2',
    end: 'right-0',
  }

  return (
    <div
      className={cn(
        'absolute z-50 mt-1 min-w-[160px] rounded-md border border-border bg-background-secondary shadow-lg',
        'animate-in fade-in-0 zoom-in-95',
        alignClasses[align],
        className
      )}
      onClick={() => setOpen(false)}
    >
      <div className="py-1">{children}</div>
    </div>
  )
}

export function DropdownMenuItem({
  children,
  className,
  disabled,
  onClick,
  ...props
}: DropdownMenuItemProps) {
  const { setOpen } = useDropdown()

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    onClick?.(e)
    setOpen(false)
  }

  return (
    <button
      type="button"
      className={cn(
        'flex w-full items-center px-3 py-2 text-sm',
        'hover:bg-secondary focus:bg-secondary outline-none',
        'transition-colors',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled}
      onClick={handleClick}
      {...props}
    >
      {children}
    </button>
  )
}

export function DropdownMenuSeparator({ className }: DropdownMenuSeparatorProps) {
  return <div className={cn('my-1 h-px bg-border', className)} />
}
