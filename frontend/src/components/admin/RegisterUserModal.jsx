import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers, getDepartments, createUser } from '../../api/users'
import { useToast } from '../../context/ToastContext'
import { Modal } from '../../components/ui/Modal'
import { Spinner } from '../../components/ui/Spinner'

/**
 * RegisterUserModal
 *
 * Admin-only modal for creating new users.
 *
 * Props:
 *   open      - boolean, controls modal visibility
 *   onClose   - () => void, called to close the modal
 *   onSuccess - () => void, called after a successful user creation
 */
export function RegisterUserModal({ open, onClose, onSuccess }) {
  const { toast } = useToast()
  const qc = useQueryClient()

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      role: 'employee',
      department_id: '',
      manager_id: '',
    },
  })

  // Fetch departments — only when modal is open
  const { data: departmentsData, isLoading: depsLoading } = useQuery({
    queryKey: ['departments'],
    queryFn: getDepartments,
    enabled: open,
  })

  // Fetch all users — only when modal is open; filter client-side for manager dropdown
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: open,
  })

  const departments = Array.isArray(departmentsData)
    ? departmentsData
    : departmentsData?.results || []

  const allUsers = Array.isArray(usersData) ? usersData : usersData?.results || []
  const managers = allUsers.filter(
    (u) => u.profile?.role === 'manager' || u.profile?.role === 'admin'
  )

  const createMut = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast({ type: 'success', message: 'User created successfully.' })
      reset()
      onSuccess()
      onClose()
    },
    onError: (error) => {
      const status = error.response?.status
      const data = error.response?.data

      if (status === 400 && data && typeof data === 'object') {
        // Map server-side field errors to react-hook-form
        const fieldMap = {
          username: 'username',
          email: 'email',
          password: 'password',
          role: 'role',
          first_name: 'first_name',
          last_name: 'last_name',
          department_id: 'department_id',
          manager_id: 'manager_id',
        }

        let hasFieldError = false
        Object.entries(data).forEach(([key, messages]) => {
          const fieldName = fieldMap[key]
          if (fieldName) {
            const message = Array.isArray(messages) ? messages[0] : messages
            setError(fieldName, { type: 'server', message })
            hasFieldError = true
          }
        })

        // If there's a non-field error or generic error key, show a toast
        if (!hasFieldError) {
          const msg =
            data.error ||
            data.non_field_errors?.[0] ||
            data.detail ||
            'Validation error. Please check your input.'
          toast({ type: 'error', message: msg })
        }
      } else {
        // Network / 500 error
        toast({ type: 'error', message: 'Something went wrong. Please try again.' })
      }
    },
  })

  const onSubmit = (formData) => {
    // Convert empty strings to null for optional FK fields
    const payload = {
      ...formData,
      department_id: formData.department_id ? Number(formData.department_id) : null,
      manager_id: formData.manager_id ? Number(formData.manager_id) : null,
    }
    createMut.mutate(payload)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const dropdownsLoading = depsLoading || usersLoading

  return (
    <Modal open={open} onClose={handleClose} title="Add New User" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Username & Email */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Username *</label>
            <input
              {...register('username', { required: 'Username is required' })}
              className="input-field"
              placeholder="john.doe"
              autoComplete="off"
            />
            {errors.username && (
              <p className="field-error">{errors.username.message}</p>
            )}
          </div>
          <div>
            <label className="label">Email *</label>
            <input
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Enter a valid email address',
                },
              })}
              type="email"
              className="input-field"
              placeholder="john@company.com"
              autoComplete="off"
            />
            {errors.email && (
              <p className="field-error">{errors.email.message}</p>
            )}
          </div>
        </div>

        {/* Password */}
        <div>
          <label className="label">Password *</label>
          <input
            {...register('password', {
              required: 'Password is required',
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
            })}
            type="password"
            className="input-field"
            placeholder="Min 8 characters"
            autoComplete="new-password"
          />
          {errors.password && (
            <p className="field-error">{errors.password.message}</p>
          )}
        </div>

        {/* First Name & Last Name */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">First Name</label>
            <input
              {...register('first_name')}
              className="input-field"
              placeholder="John"
            />
            {errors.first_name && (
              <p className="field-error">{errors.first_name.message}</p>
            )}
          </div>
          <div>
            <label className="label">Last Name</label>
            <input
              {...register('last_name')}
              className="input-field"
              placeholder="Doe"
            />
            {errors.last_name && (
              <p className="field-error">{errors.last_name.message}</p>
            )}
          </div>
        </div>

        {/* Role */}
        <div>
          <label className="label">Role *</label>
          <select
            {...register('role', { required: 'Role is required' })}
            className="input-field"
          >
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>
          {errors.role && (
            <p className="field-error">{errors.role.message}</p>
          )}
        </div>

        {/* Department & Manager */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Department</label>
            <select
              {...register('department_id')}
              className="input-field"
              disabled={dropdownsLoading}
            >
              <option value="">
                {depsLoading ? 'Loading…' : '— None —'}
              </option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
            {errors.department_id && (
              <p className="field-error">{errors.department_id.message}</p>
            )}
          </div>
          <div>
            <label className="label">Reporting Manager</label>
            <select
              {...register('manager_id')}
              className="input-field"
              disabled={dropdownsLoading}
            >
              <option value="">
                {usersLoading ? 'Loading…' : '— None —'}
              </option>
              {managers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.username}
                </option>
              ))}
            </select>
            {errors.manager_id && (
              <p className="field-error">{errors.manager_id.message}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={handleClose}
            className="btn-secondary"
            disabled={createMut.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMut.isPending}
            className="btn-primary"
          >
            {createMut.isPending ? <Spinner size="sm" /> : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
