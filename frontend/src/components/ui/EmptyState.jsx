export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-cream-200 border border-cream-300 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-graphite-400" />
        </div>
      )}
      <h3 className="text-base font-semibold text-graphite-700 mb-1">{title}</h3>
      {description && <p className="text-sm text-graphite-400 max-w-xs mb-4">{description}</p>}
      {action}
    </div>
  )
}
