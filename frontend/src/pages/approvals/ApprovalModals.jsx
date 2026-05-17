import { useForm } from 'react-hook-form'
import { Modal } from '../../components/ui/Modal'
import { Spinner } from '../../components/ui/Spinner'

export function ApproveModal({ open, onClose, onConfirm, loading }) {
  const { register, handleSubmit, reset } = useForm()
  const submit = (data) => { onConfirm(data.comments || ''); reset() }
  const close  = () => { reset(); onClose() }

  return (
    <Modal open={open} onClose={close} title="Approve — Add Comments (optional)" size="sm">
      <form onSubmit={handleSubmit(submit)} className="space-y-4">
        <div>
          <label className="label">Comments</label>
          <textarea
            {...register('comments')}
            className="input-field resize-none"
            rows={3}
            placeholder="Optional approval comments…"
          />
        </div>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={close} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-success">
            {loading ? <Spinner size="sm" /> : 'Approve'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function RejectModal({ open, onClose, onConfirm, loading }) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm()
  const submit = (data) => { onConfirm(data.reason); reset() }
  const close  = () => { reset(); onClose() }

  return (
    <Modal open={open} onClose={close} title="Reject — Provide Reason" size="sm">
      <form onSubmit={handleSubmit(submit)} className="space-y-4">
        <div>
          <label className="label">Reason *</label>
          <textarea
            {...register('reason', { required: 'Reason is required' })}
            className="input-field resize-none"
            rows={3}
            placeholder="Explain why this is being rejected…"
          />
          {errors.reason && <p className="field-error">{errors.reason.message}</p>}
        </div>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={close} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={loading} className="btn-danger">
            {loading ? <Spinner size="sm" /> : 'Reject'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
