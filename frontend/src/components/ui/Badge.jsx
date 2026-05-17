import { clsx } from 'clsx'

const variants = {
  draft:     'bg-cream-200 text-graphite-600 border-cream-300',
  submitted: 'bg-amber-100 text-amber-700 border-amber-200',
  approved:  'bg-green-100 text-green-700 border-green-200',
  rejected:  'bg-red-100 text-red-700 border-red-200',
  locked:    'bg-violet-100 text-violet-700 border-violet-200',
  active:    'bg-green-100 text-green-700 border-green-200',
  planning:  'bg-sky-100 text-sky-700 border-sky-200',
  closed:    'bg-cream-200 text-graphite-500 border-cream-300',
  admin:     'bg-violet-100 text-violet-700 border-violet-200',
  manager:   'bg-sky-100 text-sky-700 border-sky-200',
  employee:  'bg-primary-100 text-primary-700 border-primary-200',
  viewer:    'bg-cream-200 text-graphite-500 border-cream-300',
}

export function Badge({ status, label, className }) {
  const text = label || status
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize',
      variants[status] || 'bg-cream-200 text-graphite-600 border-cream-300',
      className
    )}>
      {text}
    </span>
  )
}
