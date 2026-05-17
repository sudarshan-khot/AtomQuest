import { clsx } from 'clsx'

export function Spinner({ size = 'md', className }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8', xl: 'w-12 h-12' }
  return (
    <div className={clsx(
      'animate-spin rounded-full border-2 border-cream-300 border-t-graphite-900',
      sizes[size],
      className,
    )} />
  )
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="xl" />
        <p className="text-graphite-400 text-sm">Loading…</p>
      </div>
    </div>
  )
}
