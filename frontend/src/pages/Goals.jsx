import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Target } from 'lucide-react'
import { getGoals, createGoal, updateGoal, deleteGoal, submitGoal } from '../api/goals'
import { getCycles, getThrustAreas, getUoMTypes } from '../api/cycles'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Modal } from '../components/ui/Modal'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'
import { GoalForm } from './goals/GoalForm'
import { GoalCard } from './goals/GoalCard'

function normalise(data) {
  return Array.isArray(data) ? data : data?.results || []
}

export default function Goals() {
  const { role } = useAuth()
  const { toast } = useToast()
  const qc = useQueryClient()

  const [showCreate, setShowCreate] = useState(false)
  const [editGoal, setEditGoal]     = useState(null)

  const { data: goalsData, isLoading } = useQuery({ queryKey: ['goals'], queryFn: getGoals })
  const { data: cyclesData }    = useQuery({ queryKey: ['cycles'],      queryFn: getCycles })
  const { data: thrustData }    = useQuery({ queryKey: ['thrust-areas'], queryFn: getThrustAreas })
  const { data: uomData }       = useQuery({ queryKey: ['uom-types'],   queryFn: getUoMTypes })

  const goals        = normalise(goalsData)
  const activeCycles = normalise(cyclesData).filter(c => c.status === 'active')
  const thrustAreas  = normalise(thrustData)
  const uomTypes     = normalise(uomData)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['goals'] })

  const createMut = useMutation({
    mutationFn: createGoal,
    onSuccess: () => { invalidate(); setShowCreate(false); toast({ type: 'success', message: 'Goal created.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to create goal.' }),
  })

  const updateMut = useMutation({
    mutationFn: updateGoal,
    onSuccess: () => { invalidate(); setEditGoal(null); toast({ type: 'success', message: 'Goal updated.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to update goal.' }),
  })

  const deleteMut = useMutation({
    mutationFn: deleteGoal,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'Goal deleted.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to delete goal.' }),
  })

  const submitMut = useMutation({
    mutationFn: submitGoal,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'Goal submitted for approval.' }) },
    onError: (e) => toast({ type: 'error', message: e.response?.data?.error || 'Failed to submit goal.' }),
  })

  const handleDelete = (id) => {
    if (window.confirm('Delete this goal? This cannot be undone.')) deleteMut.mutate(id)
  }

  if (isLoading) return <PageLoader />

  const formProps = { cycles: activeCycles, thrustAreas, uomTypes }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Goals</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {goals.length} goal{goals.length !== 1 ? 's' : ''} total
          </p>
        </div>
        {role !== 'viewer' && (
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus size={16} /> New Goal
          </button>
        )}
      </div>

      {goals.length === 0 ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Create your first goal to get started."
          action={role !== 'viewer' && (
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              <Plus size={16} /> Create Goal
            </button>
          )}
        />
      ) : (
        <div className="grid gap-4">
          {goals.map(goal => (
            <GoalCard
              key={goal.id}
              goal={goal}
              role={role}
              onEdit={() => setEditGoal(goal)}
              onDelete={() => handleDelete(goal.id)}
              onSubmit={() => submitMut.mutate(goal.id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Goal" size="lg">
        <GoalForm
          {...formProps}
          loading={createMut.isPending}
          onSubmit={(data) => createMut.mutate(data)}
          onCancel={() => setShowCreate(false)}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editGoal} onClose={() => setEditGoal(null)} title="Edit Goal" size="lg">
        {editGoal && (
          <GoalForm
            {...formProps}
            defaultValues={editGoal}
            loading={updateMut.isPending}
            onSubmit={(data) => updateMut.mutate({ id: editGoal.id, ...data })}
            onCancel={() => setEditGoal(null)}
          />
        )}
      </Modal>
    </div>
  )
}
