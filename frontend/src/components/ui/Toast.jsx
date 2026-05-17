import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'
import { clsx } from 'clsx'

const CONFIG = {
  success: {
    icon: CheckCircle,
    iconClass: 'text-green-600',
    wrapClass: 'border-green-200 bg-green-50',
    textClass: 'text-green-900',
  },
  error: {
    icon: XCircle,
    iconClass: 'text-red-600',
    wrapClass: 'border-red-200 bg-red-50',
    textClass: 'text-red-900',
  },
  warning: {
    icon: AlertCircle,
    iconClass: 'text-amber-600',
    wrapClass: 'border-amber-200 bg-amber-50',
    textClass: 'text-amber-900',
  },
  info: {
    icon: Info,
    iconClass: 'text-sky-600',
    wrapClass: 'border-sky-200 bg-sky-50',
    textClass: 'text-sky-900',
  },
}

function Toast({ toast, dismiss }) {
  const cfg = CONFIG[toast.type] || CONFIG.info
  const Icon = cfg.icon
  return (
    <div className={clsx(
      'flex items-start gap-3 p-4 rounded-xl border shadow-md toast-enter',
      cfg.wrapClass,
    )}>
      <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', cfg.iconClass)} />
      <p className={clsx('flex-1 text-sm leading-relaxed font-medium', cfg.textClass)}>{toast.message}</p>
      <button
        onClick={() => dismiss(toast.id)}
        className="text-graphite-400 hover:text-graphite-700 transition-colors flex-shrink-0"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export function ToastContainer({ toasts, dismiss }) {
  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm pointer-events-none"
      aria-live="polite"
    >
      {toasts.map(t => (
        <div key={t.id} className="pointer-events-auto">
          <Toast toast={t} dismiss={dismiss} />
        </div>
      ))}
    </div>
  )
}
