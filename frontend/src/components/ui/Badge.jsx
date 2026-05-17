import { clsx } from 'clsx'

const variants = {
  draft:     'bg-slate-700/60 text-slate-300 border-slate-600/50',
  submitted: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  approved:  'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  rejected:  'bg-rose-500/15 text-rose-300 border-rose-500/30',
  locked:    'bg-violet-500/15 text-violet-300 border-violet-500/30',
  active:    'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  planning:  'bg-sky-500/15 text-sky-300 border-sky-500/30',
  closed:    'bg-slate-700/60 text-slate-400 border-slate-600/50',
  admin:     'bg-violet-500/15 text-violet-300 border-violet-500/30',
  manager:   'bg-sky-500/15 text-sky-300 border-sky-500/30',
  employee:  'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  viewer:    'bg-slate-700/60 text-slate-400 border-slate-600/50',
}

export function Badge({ status, label, className }) {
  const text = label || status
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize',
      variants[status] || 'bg-slate-700/60 text-slate-300 border-slate-600/50',
      className
    )}>
      {text}
    </span>
  )
}
