import { CheckCircle, XCircle, Edit2 } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { ProgressBar } from '../../components/ui/ProgressBar'

export function ApprovalCard({ item, type, onApprove, onReject, onEdit }) {
  return (
    <div className="glass-card p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-graphite-900 break-words">
              {item.title || item.goal_title}
            </h3>
            <Badge status="submitted" />
          </div>

          <div className="flex items-center gap-3 sm:gap-4 text-xs text-graphite-500 flex-wrap mt-1">
            <span>By: <span className="text-graphite-800 font-semibold">{item.user_name}</span></span>
            {item.weightage !== undefined && (
              <span>Weightage: <span className="text-graphite-800 font-semibold">{item.weightage}%</span></span>
            )}
            {item.progress_percentage !== undefined && (
              <span>Progress: <span className="text-graphite-800 font-semibold">{item.progress_percentage}%</span></span>
            )}
            {item.uom_type_name && (
              <span>UoM: <span className="text-graphite-700 font-medium">{item.uom_type_name}</span></span>
            )}
          </div>

          {item.description && (
            <p className="text-sm text-graphite-600 mt-2 line-clamp-2">{item.description}</p>
          )}
          {item.comments && (
            <p className="text-sm text-graphite-600 mt-2 italic">"{item.comments}"</p>
          )}

          {type === 'checkin' && item.progress_percentage !== undefined && (
            <div className="mt-3 max-w-xs">
              <ProgressBar value={item.progress_percentage} size="sm" />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
          {type === 'goal' && onEdit && (
            <button onClick={() => onEdit(item)} className="btn-secondary btn-sm">
              <Edit2 size={13} /> Edit
            </button>
          )}
          <button onClick={() => onApprove(item)} className="btn-success btn-sm">
            <CheckCircle size={13} /> Approve
          </button>
          <button onClick={() => onReject(item)} className="btn-danger btn-sm">
            <XCircle size={13} /> Reject
          </button>
        </div>
      </div>
    </div>
  )
}
