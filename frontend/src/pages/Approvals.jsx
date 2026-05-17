import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle } from 'lucide-react'
import { getPendingGoals, approveGoal, rejectGoal, editDuringReview } from '../api/goals'
import { getPendingCheckIns, approveCheckIn, rejectCheckIn } from '../api/checkins'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { ApprovalCard } from './approvals/ApprovalCard'
import { ApproveModal, RejectModal } from './approvals/ApprovalModals'
import { EditGoalModal } from './approvals/EditGoalModal'

function normalise(data) {
  return Array.isArray(data) ? data : data?.results || []
}

export default function Approvals() {
  const { role } = useAuth()
  const { toast } = useToast()
  const qc = useQueryClient()

  const [tab, setTab]                 = useState('goals')
  const [approveTarget, setApprove]   = useState(null)
  const [rejectTarget, setReject]     = useState(null)
  const [editTarget, setEdit]         = useState(null)

  const enabled = role !== 'employee'

  const { data: pendingGoals, isLoading: gl } = useQuery({
    queryKey: ['pending-goals'],
    queryFn: getPendingGoals,
    enabled,
  })
  const { data: pendingCIs, isLoading: cl } = useQuery({
    queryKey: ['pending-checkins'],
    queryFn: getPendingCheckIns,
    enabled,
  })

  const invalidateGoals = () => {
    qc.invalidateQueries({ queryKey: ['pending-goals'] })
    qc.invalidateQueries({ queryKey: ['goals'] })
  }
  const invalidateCIs = () => {
    qc.invalidateQueries({ queryKey: ['pending-checkins'] })
    qc.invalidateQueries({ queryKey: ['checkins'] })
  }

  const approveMut = useMutation({
    mutationFn: ({ id, comments }) => approveGoal({ id, approval_comments: comments }),
    onSuccess: () => { invalidateGoals(); setApprove(null); toast({ type: 'success', message: 'Goal approved.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to approve goal.' }),
  })
  const rejectMut = useMutation({
    mutationFn: ({ id, reason }) => rejectGoal({ id, rejection_reason: reason }),
    onSuccess: () => { invalidateGoals(); setReject(null); toast({ type: 'success', message: 'Goal rejected.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to reject goal.' }),
  })
  const editMut = useMutation({
    mutationFn: ({ id, ...data }) => editDuringReview({ id, ...data }),
    onSuccess: () => { invalidateGoals(); setEdit(null); toast({ type: 'success', message: 'Goal updated.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to update goal.' }),
  })

  const approveCIMut = useMutation({
    mutationFn: ({ id, comments }) => approveCheckIn({ id, approval_comments: comments }),
    onSuccess: () => { invalidateCIs(); setApprove(null); toast({ type: 'success', message: 'Check-in approved.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to approve check-in.' }),
  })
  const rejectCIMut = useMutation({
    mutationFn: ({ id, reason }) => rejectCheckIn({ id, rejection_comments: reason }),
    onSuccess: () => { invalidateCIs(); setReject(null); toast({ type: 'success', message: 'Check-in rejected.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to reject check-in.' }),
  })

  if (gl || cl) return <PageLoader />

  const goals    = normalise(pendingGoals)
  const checkins = normalise(pendingCIs)
  const isGoalTab = tab === 'goals'
  const items     = isGoalTab ? goals : checkins

  const approveLoading = approveMut.isPending || approveCIMut.isPending
  const rejectLoading  = rejectMut.isPending  || rejectCIMut.isPending

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Approvals</h1>
          <p className="text-sm text-graphite-500 font-medium mt-0.5">
            {goals.length} goal{goals.length !== 1 ? 's' : ''} · {checkins.length} check-in{checkins.length !== 1 ? 's' : ''} pending
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="tab-bar">
        {['goals', 'checkins'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={tab === t ? 'tab-item-active' : 'tab-item'}
          >
            {t} ({t === 'goals' ? goals.length : checkins.length})
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={CheckCircle}
          title={`No pending ${tab}`}
          description="All caught up! Nothing to review right now."
        />
      ) : (
        <div className="grid gap-4">
          {items.map(item => (
            <ApprovalCard
              key={item.id}
              item={item}
              type={isGoalTab ? 'goal' : 'checkin'}
              onApprove={setApprove}
              onReject={setReject}
              onEdit={isGoalTab ? setEdit : undefined}
            />
          ))}
        </div>
      )}

      <ApproveModal
        open={!!approveTarget}
        onClose={() => setApprove(null)}
        loading={approveLoading}
        onConfirm={(comments) => {
          if (isGoalTab) approveMut.mutate({ id: approveTarget.id, comments })
          else approveCIMut.mutate({ id: approveTarget.id, comments })
        }}
      />

      <RejectModal
        open={!!rejectTarget}
        onClose={() => setReject(null)}
        loading={rejectLoading}
        onConfirm={(reason) => {
          if (isGoalTab) rejectMut.mutate({ id: rejectTarget.id, reason })
          else rejectCIMut.mutate({ id: rejectTarget.id, reason })
        }}
      />

      <EditGoalModal
        open={!!editTarget}
        goal={editTarget}
        onClose={() => setEdit(null)}
        loading={editMut.isPending}
        onSubmit={(data) => editMut.mutate({ id: editTarget.id, ...data })}
      />
    </div>
  )
}
