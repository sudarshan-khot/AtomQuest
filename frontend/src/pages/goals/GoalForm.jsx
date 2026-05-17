import { useForm, useWatch } from 'react-hook-form'
import { Spinner } from '../../components/ui/Spinner'

// UoM-specific guidance for the target value field
const UOM_HINTS = {
  numeric:    { label: 'Target Value',          hint: 'Enter the numeric target (e.g. 1000 units, ₹5,00,000 revenue)', placeholder: '1000' },
  percentage: { label: 'Target (%)',             hint: 'Enter a percentage between 0 and 100', placeholder: '100' },
  timeline:   { label: 'Duration (days)',        hint: 'Total number of days for this timeline goal', placeholder: '90' },
  zero_based: { label: 'Target (1 = achieved)', hint: 'Enter 1 when the milestone is achieved, 0 otherwise', placeholder: '1' },
}

export function GoalForm({ onSubmit, onCancel, defaultValues, cycles, thrustAreas, uomTypes, loading }) {
  const { register, handleSubmit, control, formState: { errors } } = useForm({ defaultValues })
  const isEdit = !!defaultValues?.id

  // Watch selected UoM to update target field hints dynamically
  const selectedUomId = useWatch({ control, name: 'uom_type' })
  const selectedUom = uomTypes?.find(u => String(u.id) === String(selectedUomId))
  const uomHint = UOM_HINTS[selectedUom?.name] || { label: 'Target Value', hint: '', placeholder: '100' }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="label">Title *</label>
        <input
          {...register('title', { required: 'Title is required', maxLength: { value: 255, message: 'Max 255 chars' } })}
          className="input-field"
          placeholder="e.g. Increase quarterly revenue by 20%"
        />
        {errors.title && <p className="field-error">{errors.title.message}</p>}
      </div>

      <div>
        <label className="label">Description</label>
        <textarea
          {...register('description', { maxLength: { value: 2000, message: 'Max 2000 chars' } })}
          className="input-field resize-none"
          rows={3}
          placeholder="Describe your goal…"
        />
        {errors.description && <p className="field-error">{errors.description.message}</p>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Cycle *</label>
          <select {...register('cycle', { required: 'Cycle is required' })} className="input-field">
            <option value="">Select cycle</option>
            {cycles?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          {errors.cycle && <p className="field-error">{errors.cycle.message}</p>}
        </div>
        <div>
          <label className="label">Thrust Area</label>
          <select {...register('thrust_area')} className="input-field">
            <option value="">Select area</option>
            {thrustAreas?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">UoM Type *</label>
          <select {...register('uom_type', { required: 'UoM type is required' })} className="input-field">
            <option value="">Select type</option>
            {uomTypes?.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
          <p className="form-hint">Determines how progress is measured and scored</p>
          {errors.uom_type && <p className="field-error">{errors.uom_type.message}</p>}
        </div>
        <div>
          <label className="label">{uomHint.label} *</label>
          <input
            {...register('target_value', { required: 'Target is required', min: { value: 0, message: 'Must be ≥ 0' } })}
            type="number" step="any" className="input-field" placeholder={uomHint.placeholder}
          />
          {uomHint.hint && <p className="form-hint">{uomHint.hint}</p>}
          {errors.target_value && <p className="field-error">{errors.target_value.message}</p>}
        </div>
      </div>

      <div>
        <label className="label">Weightage (10–100%) *</label>
        <input
          {...register('weightage', {
            required: 'Weightage is required',
            min: { value: 10, message: 'Min 10%' },
            max: { value: 100, message: 'Max 100%' },
          })}
          type="number" step="any" className="input-field" placeholder="50"
        />
        {errors.weightage && <p className="field-error">{errors.weightage.message}</p>}
      </div>

      <div className="flex justify-end gap-3 pt-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? <Spinner size="sm" /> : isEdit ? 'Update Goal' : 'Create Goal'}
        </button>
      </div>
    </form>
  )
}
