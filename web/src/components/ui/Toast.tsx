import { useEffect, useState } from 'react'
import { create } from 'zustand'
import { cn } from '@/lib/utils'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
}

interface ToastStore {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).slice(2)
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }))
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
}))

// Convenience function for showing toasts
export function toast(type: ToastType, title: string, description?: string, duration = 4000) {
  useToastStore.getState().addToast({ type, title, description, duration })
}

// Type-specific helpers
toast.success = (title: string, description?: string) => toast('success', title, description)
toast.error = (title: string, description?: string) => toast('error', title, description, 6000)
toast.warning = (title: string, description?: string) => toast('warning', title, description)
toast.info = (title: string, description?: string) => toast('info', title, description)

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
}

const styles = {
  success: 'border-success/30 bg-success/10',
  error: 'border-error/30 bg-error/10',
  warning: 'border-warning/30 bg-warning/10',
  info: 'border-primary/30 bg-primary/10',
}

const iconStyles = {
  success: 'text-success',
  error: 'text-error',
  warning: 'text-warning',
  info: 'text-primary',
}

function ToastItem({ toast: t, onRemove }: { toast: Toast; onRemove: () => void }) {
  const [isExiting, setIsExiting] = useState(false)
  const Icon = icons[t.type]

  useEffect(() => {
    const duration = t.duration || 4000
    const timer = setTimeout(() => {
      setIsExiting(true)
      setTimeout(onRemove, 200)
    }, duration)

    return () => clearTimeout(timer)
  }, [t.duration, onRemove])

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur-sm transition-all duration-200',
        styles[t.type],
        isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
      )}
    >
      <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', iconStyles[t.type])} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground">{t.title}</p>
        {t.description && (
          <p className="mt-1 text-sm text-foreground-secondary">{t.description}</p>
        )}
      </div>
      <button
        onClick={() => {
          setIsExiting(true)
          setTimeout(onRemove, 200)
        }}
        className="p-1 rounded hover:bg-white/10 transition-colors"
      >
        <X className="h-4 w-4 text-foreground-muted" />
      </button>
    </div>
  )
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
      ))}
    </div>
  )
}
