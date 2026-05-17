import { Send, Trash2, Edit2, Lock, RefreshCw } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'

export function GoalCard({ goal, role, onEdit, onDelete, onSubmit }) {
  const isDraft     = goal.status === 'draft'
  const isRejected  = goal.status === 'rejected'
  const canAct      = role !== 'viewer'

  const canEdit     = isDraft && canAct
  const canSubmit   = isDraft && canAct
  const canDelete   = isDraft && canAct
  const canResubmit = isRejected && canAct

  return (
    <div className="glass-card-hover p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-graphite-900 break-words">{goal.title}</h3>
            <Badge status={goal.status} />
            {goal.is_shared && <Badge status="info" label="Shared" />}
            {goal.status === 'locked' && <Lock size={12} className="text-violet-600" />}
          </div>

          {goal.description && (
            <p className="text-sm text-graphite-600 line-clamp-2 mb-3">{goal.description}</p>
          )}

          <div className="flex items-center gap-3 sm:gap-4 text-xs text-graphite-500 flex-wrap">
            <span>Weightage: <span className="text-graphite-800 font-semibold">{goal.weightage}%</span></span>
            <span>Target: <span className="text-graphite-800 font-semibold">{goal.target_value}</span></span>
            {goal.uom_type_name    && <span>UoM: <span className="text-graphite-700 font-medium">{goal.uom_type_name}</span></span>}
            {goal.thrust_area_name && <span>Area: <span className="text-graphite-700 font-medium">{goal.thrust_area_name}</span></span>}
            {goal.cycle_name       && <span>Cycle: <span className="text-graphite-700 font-medium">{goal.cycle_name}</span></span>}
          </div>

          {goal.rejection_reason && (
            <div className="mt-3 p-2.5 rounded-lg bg-red-50 border border-red-200">
              <p className="text-xs text-red-700">
                <span className="font-semibold">Rejected: </span>{goal.rejection_reason}
              </p>
            </div>
          )}
          {goal.approval_comments && (
            <div className="mt-3 p-2.5 rounded-lg bg-green-50 border border-green-200">
              <p className="text-xs text-green-700">
                <span className="font-semibold">Approved: </span>{goal.approval_comments}
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
          {canSubmit && (
            <button onClick={onSubmit} className="btn-primary btn-sm">
              <Send size={13} /> Submit
            </button>
          )}
          {canResubmit && (
            <button onClick={onSubmit} className="btn-primary btn-sm">
              <RefreshCw size={13} /> Resubmit
            </button>
          )}
          {canEdit && (
            <button onClick={onEdit} className="btn-secondary btn-sm" aria-label="Edit goal">
              <Edit2 size={13} />
            </button>
          )}
          {canDelete && (
            <button onClick={onDelete} className="btn-danger btn-sm" aria-label="Delete goal">
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
