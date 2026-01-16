import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { X } from 'lucide-react'
import { Button } from './Button'

export interface ModalProps {
  open: boolean
  onClose: () => void
  children: ReactNode
  className?: string
}

function Modal({ open, onClose, children, className }: ModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal content */}
      <div
        className={cn(
          'relative z-50 w-full max-w-lg rounded-lg border border-border bg-background-secondary p-6 shadow-lg animate-in',
          className
        )}
      >
        {children}
      </div>
    </div>
  )
}

function ModalHeader({
  className,
  children,
  onClose,
}: {
  className?: string
  children: ReactNode
  onClose?: () => void
}) {
  return (
    <div className={cn('flex items-center justify-between mb-4', className)}>
      <div className="text-lg font-semibold">{children}</div>
      {onClose && (
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}

function ModalContent({
  className,
  children,
}: {
  className?: string
  children: ReactNode
}) {
  return <div className={cn('text-foreground-secondary', className)}>{children}</div>
}

function ModalFooter({
  className,
  children,
}: {
  className?: string
  children: ReactNode
}) {
  return (
    <div className={cn('flex items-center justify-end gap-2 mt-6', className)}>
      {children}
    </div>
  )
}

export { Modal, ModalHeader, ModalContent, ModalFooter }
