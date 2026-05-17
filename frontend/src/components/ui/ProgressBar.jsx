import { clsx } from 'clsx'

export function ProgressBar({ value = 0, size = 'md', showLabel = true, className }) {
  const clamped = Math.min(100, Math.max(0, value))
  const color = clamped >= 80 ? 'bg-emerald-500' : clamped >= 50 ? 'bg-primary-500' : clamped >= 25 ? 'bg-amber-500' : 'bg-rose-500'
  const heights = { sm: 'h-1.5', md: 'h-2', lg: 'h-3' }

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      <div className={clsx('flex-1 bg-slate-700/60 rounded-full overflow-hidden', heights[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-700 ease-out', color)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-slate-400 w-10 text-right tabular-nums">
          {clamped.toFixed(0)}%
        </span>
      )}
    </div>
  )
}
