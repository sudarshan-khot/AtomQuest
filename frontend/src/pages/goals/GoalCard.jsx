import { Send, Trash2, Edit2, Lock, RefreshCw } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'

export function GoalCard({ goal, role, onEdit, onDelete, onSubmit }) {
  const isDraft    = goal.status === 'draft'
  const isRejected = goal.status === 'rejected'
  const canAct     = role !== 'viewer'

  const canEdit   = isDraft && canAct
  const canSubmit = isDraft && canAct
  const canDelete = isDraft && canAct
  const canResubmit = isRejected && canAct

  return (
    <div className="glass-card-hover p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-slate-100 break-words">{goal.title}</h3>
            <Badge status={goal.status} />
            {goal.is_shared && <Badge status="info" label="Shared" />}
            {goal.status === 'locked' && <Lock size={12} className="text-violet-400" />}
          </div>

          {goal.description && (
            <p className="text-sm text-slate-400 line-clamp-2 mb-3">{goal.description}</p>
          )}

          <div className="flex items-center gap-3 sm:gap-4 text-xs text-slate-500 flex-wrap">
            <span>Weightage: <span className="text-slate-300 font-medium">{goal.weightage}%</span></span>
            <span>Target: <span className="text-slate-300 font-medium">{goal.target_value}</span></span>
            {goal.uom_type_name   && <span>UoM: <span className="text-slate-300">{goal.uom_type_name}</span></span>}
            {goal.thrust_area_name && <span>Area: <span className="text-slate-300">{goal.thrust_area_name}</span></span>}
            {goal.cycle_name      && <span>Cycle: <span className="text-slate-300">{goal.cycle_name}</span></span>}
          </div>

          {goal.rejection_reason && (
            <div className="mt-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
              <p className="text-xs text-rose-300">
                <span className="font-medium">Rejected: </span>{goal.rejection_reason}
              </p>
            </div>
          )}
          {goal.approval_comments && (
            <div className="mt-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-xs text-emerald-300">
                <span className="font-medium">Approved: </span>{goal.approval_comments}
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
