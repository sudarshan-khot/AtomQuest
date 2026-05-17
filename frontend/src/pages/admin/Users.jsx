import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, UserX, UserCheck, Users } from 'lucide-react'
import { getUsers, deactivateUser, reactivateUser } from '../../api/users'
import { useToast } from '../../context/ToastContext'
import { Badge } from '../../components/ui/Badge'
import { PageLoader } from '../../components/ui/Spinner'
import { EmptyState } from '../../components/ui/EmptyState'
import { RegisterUserModal } from '../../components/admin/RegisterUserModal'

export default function AdminUsers() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: getUsers })
  const users = Array.isArray(data) ? data : data?.results || []

  const invalidate = () => qc.invalidateQueries({ queryKey: ['users'] })

  const deactivateMut = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'User deactivated.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to deactivate user.' }),
  })
  const reactivateMut = useMutation({
    mutationFn: reactivateUser,
    onSuccess: () => { invalidate(); toast({ type: 'success', message: 'User reactivated.' }) },
    onError: () => toast({ type: 'error', message: 'Failed to reactivate user.' }),
  })

  if (isLoading) return <PageLoader />

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="text-sm text-graphite-500 font-medium mt-0.5">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus size={16} /> Add User
        </button>
      </div>

      {users.length === 0 ? (
        <EmptyState icon={Users} title="No users" description="Add your first user to get started." />
      ) : (
        <div className="glass-card overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th className="hidden sm:table-cell">Department</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-graphite-900 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-primary-400">{u.username?.[0]?.toUpperCase()}</span>
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-graphite-900 truncate">{u.username}</p>
                        <p className="text-xs text-graphite-500 truncate">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <Badge status={u.profile?.role} label={u.profile?.role_display || u.profile?.role} />
                  </td>
                  <td className="hidden sm:table-cell text-graphite-700 font-medium">
                    {u.profile?.department_name || '—'}
                  </td>
                  <td>
                    <Badge
                      status={u.profile?.is_active ? 'active' : 'closed'}
                      label={u.profile?.is_active ? 'Active' : 'Inactive'}
                    />
                  </td>
                  <td className="text-right">
                    {u.profile?.is_active ? (
                      <button onClick={() => deactivateMut.mutate(u.id)} className="btn-danger btn-sm">
                        <UserX size={13} /> <span className="hidden sm:inline">Deactivate</span>
                      </button>
                    ) : (
                      <button onClick={() => reactivateMut.mutate(u.id)} className="btn-success btn-sm">
                        <UserCheck size={13} /> <span className="hidden sm:inline">Reactivate</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <RegisterUserModal open={showCreate} onClose={() => setShowCreate(false)} onSuccess={invalidate} />
    </div>
  )
}
