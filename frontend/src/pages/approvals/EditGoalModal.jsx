import { useQuery } from '@tanstack/react-query'
import { Modal } from '../../components/ui/Modal'
import { GoalForm } from '../goals/GoalForm'
import { getCycles, getThrustAreas, getUoMTypes } from '../../api/cycles'

function normalise(data) {
  return Array.isArray(data) ? data : data?.results || []
}

export function EditGoalModal({ open, goal, onClose, onSubmit, loading }) {
  const { data: cyclesData }  = useQuery({ queryKey: ['cycles'],       queryFn: getCycles })
  const { data: thrustData }  = useQuery({ queryKey: ['thrust-areas'], queryFn: getThrustAreas })
  const { data: uomData }     = useQuery({ queryKey: ['uom-types'],    queryFn: getUoMTypes })

  const cycles      = normalise(cyclesData)
  const thrustAreas = normalise(thrustData)
  const uomTypes    = normalise(uomData)

  return (
    <Modal open={open} onClose={onClose} title="Edit Goal During Review" size="lg">
      {goal && (
        <GoalForm
          defaultValues={goal}
          cycles={cycles}
          thrustAreas={thrustAreas}
          uomTypes={uomTypes}
          loading={loading}
          onSubmit={onSubmit}
          onCancel={onClose}
        />
      )}
    </Modal>
  )
}
