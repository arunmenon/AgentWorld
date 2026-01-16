import { create } from 'zustand'
import { cn } from '@/lib/utils'
import { AlertTriangle, Trash2, Info } from 'lucide-react'
import { Button } from './Button'

type DialogType = 'danger' | 'warning' | 'info'

interface ConfirmDialogState {
  isOpen: boolean
  type: DialogType
  title: string
  description: string
  confirmLabel: string
  cancelLabel: string
  onConfirm: () => void | Promise<void>
  onCancel: () => void
  isLoading: boolean
}

interface ConfirmDialogStore extends ConfirmDialogState {
  open: (options: Omit<ConfirmDialogState, 'isOpen' | 'isLoading' | 'onCancel'>) => Promise<boolean>
  close: () => void
  setLoading: (loading: boolean) => void
}

const defaultState: ConfirmDialogState = {
  isOpen: false,
  type: 'info',
  title: '',
  description: '',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  onConfirm: () => {},
  onCancel: () => {},
  isLoading: false,
}

export const useConfirmDialogStore = create<ConfirmDialogStore>((set, get) => ({
  ...defaultState,
  open: (options) => {
    return new Promise((resolve) => {
      set({
        isOpen: true,
        ...options,
        onConfirm: async () => {
          set({ isLoading: true })
          try {
            await options.onConfirm()
            resolve(true)
          } finally {
            get().close()
          }
        },
        onCancel: () => {
          resolve(false)
          get().close()
        },
      })
    })
  },
  close: () => set(defaultState),
  setLoading: (loading) => set({ isLoading: loading }),
}))

// Convenience function for confirming actions
export async function confirm(options: {
  title: string
  description: string
  type?: DialogType
  confirmLabel?: string
  cancelLabel?: string
}): Promise<boolean> {
  return useConfirmDialogStore.getState().open({
    type: options.type || 'info',
    title: options.title,
    description: options.description,
    confirmLabel: options.confirmLabel || 'Confirm',
    cancelLabel: options.cancelLabel || 'Cancel',
    onConfirm: () => {},
  })
}

// Shorthand for delete confirmations
confirm.delete = (itemName: string) =>
  confirm({
    type: 'danger',
    title: `Delete ${itemName}?`,
    description: `This action cannot be undone. Are you sure you want to delete this ${itemName.toLowerCase()}?`,
    confirmLabel: 'Delete',
  })

const icons: Record<DialogType, typeof AlertTriangle> = {
  danger: Trash2,
  warning: AlertTriangle,
  info: Info,
}

const iconStyles: Record<DialogType, string> = {
  danger: 'text-error bg-error/10',
  warning: 'text-warning bg-warning/10',
  info: 'text-primary bg-primary/10',
}

const buttonVariants: Record<DialogType, 'danger' | 'primary' | 'secondary'> = {
  danger: 'danger',
  warning: 'primary',
  info: 'primary',
}

export function ConfirmDialog() {
  const {
    isOpen,
    type,
    title,
    description,
    confirmLabel,
    cancelLabel,
    onConfirm,
    onCancel,
    isLoading,
  } = useConfirmDialogStore()

  if (!isOpen) return null

  const Icon = icons[type]

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-md rounded-lg border border-border bg-background-secondary p-6 shadow-lg animate-in zoom-in-95">
        <div className="flex gap-4">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0',
              iconStyles[type]
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
            <p className="mt-2 text-sm text-foreground-secondary">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="ghost" onClick={onCancel} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={buttonVariants[type]}
            onClick={onConfirm}
            loading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
