import type { ReactNode } from 'react'
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { CheckCircle2, Info, XCircle, X } from 'lucide-react'

type ToastVariant = 'success' | 'error' | 'info'

interface ToastInput {
  title: string
  description?: string
  variant?: ToastVariant
}

interface ToastItem extends Required<Omit<ToastInput, 'description'>> {
  id: string
  description: string
}

interface ToastContextValue {
  pushToast: (toast: ToastInput) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

const icons = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const timers = useRef<Record<string, number>>({})

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
    window.clearTimeout(timers.current[id])
    delete timers.current[id]
  }, [])

  const pushToast = useCallback(
    ({ title, description = '', variant = 'info' }: ToastInput) => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`
      setToasts((current) => [...current, { id, title, description, variant }])
      timers.current[id] = window.setTimeout(() => dismiss(id), 4200)
    },
    [dismiss],
  )

  const value = useMemo(() => ({ pushToast }), [pushToast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-[calc(100vw-2rem)] max-w-md flex-col gap-3 sm:right-6 sm:top-6">
        {toasts.map((toast) => {
          const Icon = icons[toast.variant]
          return (
            <div
              key={toast.id}
              className="pointer-events-auto animate-[toast-in_180ms_ease-out] rounded-3xl border border-white/10 bg-slate-950/90 p-4 shadow-2xl backdrop-blur"
            >
              <div className="flex items-start gap-3">
                <div
                  className={[
                    'mt-0.5 flex h-9 w-9 items-center justify-center rounded-2xl',
                    toast.variant === 'success' ? 'bg-emerald-500/15 text-emerald-300' : '',
                    toast.variant === 'error' ? 'bg-rose-500/15 text-rose-300' : '',
                    toast.variant === 'info' ? 'bg-sky-500/15 text-sky-300' : '',
                  ].join(' ')}
                >
                  <Icon size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-white">{toast.title}</p>
                  {toast.description ? <p className="mt-1 text-sm text-muted">{toast.description}</p> : null}
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(toast.id)}
                  className="rounded-full p-1 text-muted transition hover:bg-white/5 hover:text-white"
                  aria-label="Dismiss toast"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}
