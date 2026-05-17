import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Plus, Play, Square, Settings, Calendar } from 'lucide-react'
import { getCycles, createCycle, activateCycle, closeCycle } from '../../api/cycles'
import { useToast } from '../../context/ToastContext'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/ui/Modal'
import { PageLoader, Spinner } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'
import { format, parseISO } from 'date-fns'

function safeFormat(dateStr, fmt) {
  try { return format(parseISO(dateStr), fmt) } catch { return dateStr }
}

export default function AdminCycles() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({ queryKey: ['cycles'], queryFn: getCycles })
  const cycles = Array.isArray(data) ? data : data?.results || []

  const invalidate = () => qc.invalidateQueries({ queryKey: ['cycles'] })

  const createMut = useMutation({
    mutationFn: createCycle,
    onSuccess: () => { invalidate(); setShowCreate(false); reset(); toast({ type: 'success', message: 'Cycle created.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to create cycle.' }),
  })
  const activateMut = useMutation({
    mutationFn: activateCycle,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'Cycle activated.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to activate cycle.' }),
  })
  const closeMut = useMutation({
    mutationFn: closeCycle,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'Cycle closed.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to close cycle.' }),
  })

  const { register, handleSubmit, formState: { errors }, reset } = useForm()
  const onSubmit = (data) => createMut.mutate(data)

  if (isLoading) return <PageLoader />

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Cycle Management</h1>
          <p className="text-sm text-graphite-500 font-medium mt-0.5">{cycles.length} cycle{cycles.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => { setShowCreate(true); reset() }} className="btn-primary">
          <Plus size={16} /> New Cycle
        </button>
      </div>

      {cycles.length === 0 ? (
        <EmptyState icon={Settings} title="No cycles" description="Create your first performance cycle." />
      ) : (
        <div className="grid gap-4">
          {cycles.map(cycle => (
            <div key={cycle.id} className="glass-card-hover p-4 sm:p-5">
              <div className="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <h3 className="font-semibold text-graphite-900">{cycle.name}</h3>
                    <Badge status={cycle.status} />
                  </div>
                  <div className="flex items-center gap-2 text-xs text-graphite-500 font-medium mt-1">
                    <Calendar size={12} />
                    <span>
                      {safeFormat(cycle.start_date, 'MMM d, yyyy')} — {safeFormat(cycle.end_date, 'MMM d, yyyy')}
                    </span>
                  </div>
                  {cycle.checkin_date_q1 && (
                    <div className="flex items-center gap-3 mt-2 text-xs text-graphite-500 flex-wrap">
                      {['q1','q2','q3','q4'].map(q => cycle[`checkin_date_${q}`] && (
                        <span key={q}>
                          {q.toUpperCase()}: <span className="text-graphite-700 font-semibold">{safeFormat(cycle[`checkin_date_${q}`], 'MMM d')}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {cycle.status === 'planning' && (
                    <button onClick={() => activateMut.mutate(cycle.id)} className="btn-success btn-sm">
                      <Play size={13} /> Activate
                    </button>
                  )}
                  {cycle.status === 'active' && (
                    <button
                      onClick={() => { if (window.confirm('Close this cycle? This cannot be undone.')) closeMut.mutate(cycle.id) }}
                      className="btn-danger btn-sm"
                    >
                      <Square size={13} /> Close
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Cycle" size="md">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="label">Cycle Name *</label>
            <input {...register('name', { required: 'Name is required' })} className="input-field" placeholder="e.g. FY2025" />
            {errors.name && <p className="field-error">{errors.name.message}</p>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Start Date *</label>
              <input {...register('start_date', { required: 'Required' })} type="date" className="input-field" />
              {errors.start_date && <p className="field-error">{errors.start_date.message}</p>}
            </div>
            <div>
              <label className="label">End Date *</label>
              <input {...register('end_date', { required: 'Required' })} type="date" className="input-field" />
              {errors.end_date && <p className="field-error">{errors.end_date.message}</p>}
            </div>
          </div>
          <p className="form-hint">Check-in dates (Q1–Q4) will be automatically calculated from the cycle dates.</p>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={createMut.isPending} className="btn-primary">
              {createMut.isPending ? <Spinner size="sm" /> : 'Create Cycle'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
