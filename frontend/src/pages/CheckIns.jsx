import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Plus, CheckSquare } from 'lucide-react'
import { getCheckIns, createCheckIn } from '../api/checkins'
import { getGoals } from '../api/goals'
import { getCycles } from '../api/cycles'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Badge } from '../components/ui/Badge'
import { ProgressBar } from '../components/ui/ProgressBar'
import { Modal } from '../components/ui/Modal'
import { PageLoader, Spinner } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'

function CheckInCard({ ci }) {
  return (
    <div className="glass-card-hover p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-slate-100 break-words">{ci.goal_title}</h3>
            <Badge status={ci.status} />
          </div>
          <div className="flex items-center gap-3 sm:gap-4 text-xs text-slate-500 mt-1 flex-wrap">
            <span>By: <span className="text-slate-300">{ci.user_name}</span></span>
            <span>Value: <span className="text-slate-300">{ci.progress_value}</span></span>
            {ci.cycle_name && <span>Cycle: <span className="text-slate-300">{ci.cycle_name}</span></span>}
          </div>
          {ci.comments && (
            <p className="text-sm text-slate-400 mt-2 italic">"{ci.comments}"</p>
          )}
          {ci.rejection_comments && (
            <div className="mt-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
              <p className="text-xs text-rose-300">
                <span className="font-medium">Rejected: </span>{ci.rejection_comments}
              </p>
            </div>
          )}
          {ci.approval_comments && (
            <div className="mt-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-xs text-emerald-300">
                <span className="font-medium">Approved: </span>{ci.approval_comments}
              </p>
            </div>
          )}
        </div>
        <div className="w-full sm:w-32 flex-shrink-0">
          <ProgressBar value={ci.progress_percentage} />
        </div>
      </div>
    </div>
  )
}

export default function CheckIns() {
  const { role } = useAuth()
  const { toast } = useToast()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)

  const { data: checkinsData, isLoading } = useQuery({ queryKey: ['checkins'], queryFn: getCheckIns })
  const { data: goalsData }  = useQuery({ queryKey: ['goals'],  queryFn: getGoals })
  const { data: cyclesData } = useQuery({ queryKey: ['cycles'], queryFn: getCycles })

  const checkins     = (Array.isArray(checkinsData) ? checkinsData : checkinsData?.results || [])
  const approvedGoals = (Array.isArray(goalsData) ? goalsData : goalsData?.results || []).filter(g => g.status === 'approved')
  const activeCycles  = (Array.isArray(cyclesData) ? cyclesData : cyclesData?.results || []).filter(c => c.status === 'active')

  const createMut = useMutation({
    mutationFn: createCheckIn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['checkins'] })
      setShowCreate(false)
      reset()
      toast({ type: 'success', message: 'Check-in submitted.' })
    },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to submit check-in.' }),
  })

  const { register, handleSubmit, formState: { errors }, reset } = useForm()

  const onSubmit = (data) => {
    createMut.mutate({
      ...data,
      goal: Number(data.goal),
      cycle: Number(data.cycle),
      progress_value: Number(data.progress_value),
    })
  }

  if (isLoading) return <PageLoader />

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Check-ins</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {checkins.length} check-in{checkins.length !== 1 ? 's' : ''}
          </p>
        </div>
        {role !== 'viewer' && (
          <button onClick={() => { setShowCreate(true); reset() }} className="btn-primary">
            <Plus size={16} /> New Check-in
          </button>
        )}
      </div>

      {checkins.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title="No check-ins yet"
          description="Submit your first progress check-in for an approved goal."
          action={role !== 'viewer' && approvedGoals.length > 0 && (
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus size={16} /> New Check-in
            </button>
          )}
        />
      ) : (
        <div className="grid gap-4">
          {checkins.map(ci => <CheckInCard key={ci.id} ci={ci} />)}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Submit Check-in" size="md">
        {approvedGoals.length === 0 ? (
          <div className="py-6 text-center">
            <p className="text-sm text-slate-400">No approved goals available for check-in.</p>
            <p className="text-xs text-slate-500 mt-1">Goals must be approved before you can submit a check-in.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">Goal *</label>
              <select {...register('goal', { required: 'Goal is required' })} className="input-field">
                <option value="">Select goal</option>
                {approvedGoals.map(g => <option key={g.id} value={g.id}>{g.title}</option>)}
              </select>
              {errors.goal && <p className="field-error">{errors.goal.message}</p>}
            </div>
            <div>
              <label className="label">Cycle *</label>
              <select {...register('cycle', { required: 'Cycle is required' })} className="input-field">
                <option value="">Select cycle</option>
                {activeCycles.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              {errors.cycle && <p className="field-error">{errors.cycle.message}</p>}
            </div>
            <div>
              <label className="label">Progress Value *</label>
              <input
                {...register('progress_value', { required: 'Progress value is required', min: { value: 0, message: 'Must be ≥ 0' } })}
                type="number" step="any" className="input-field" placeholder="e.g. 75"
              />
              {errors.progress_value && <p className="field-error">{errors.progress_value.message}</p>}
            </div>
            <div>
              <label className="label">Comments</label>
              <textarea {...register('comments')} className="input-field resize-none" rows={3} placeholder="Optional notes…" />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={createMut.isPending} className="btn-primary">
                {createMut.isPending ? <Spinner size="sm" /> : 'Submit Check-in'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
