import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'
import { clsx } from 'clsx'

const CONFIG = {
  success: {
    icon: CheckCircle,
    iconClass: 'text-emerald-400',
    wrapClass: 'border-emerald-500/30 bg-emerald-500/10',
  },
  error: {
    icon: XCircle,
    iconClass: 'text-rose-400',
    wrapClass: 'border-rose-500/30 bg-rose-500/10',
  },
  warning: {
    icon: AlertCircle,
    iconClass: 'text-amber-400',
    wrapClass: 'border-amber-500/30 bg-amber-500/10',
  },
  info: {
    icon: Info,
    iconClass: 'text-sky-400',
    wrapClass: 'border-sky-500/30 bg-sky-500/10',
  },
}

function Toast({ toast, dismiss }) {
  const cfg = CONFIG[toast.type] || CONFIG.info
  const Icon = cfg.icon
  return (
    <div className={clsx(
      'flex items-start gap-3 p-4 rounded-xl border backdrop-blur-sm shadow-xl toast-enter',
      cfg.wrapClass,
    )}>
      <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', cfg.iconClass)} />
      <p className="flex-1 text-sm text-slate-200 leading-relaxed">{toast.message}</p>
      <button
        onClick={() => dismiss(toast.id)}
        className="text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
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
