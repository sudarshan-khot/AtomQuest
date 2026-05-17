import { useState, useRef, useEffect } from 'react'
import { Bell, Menu, X, CheckCircle } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { useAuth } from '../../context/AuthContext'
import { getNotifications } from '../../api/users'
import api from '../../api/index'

const ROLE_CLASSES = {
  admin:    'bg-red-100 text-red-700 border border-red-200',
  manager:  'bg-amber-100 text-amber-700 border border-amber-200',
  employee: 'bg-primary-100 text-primary-700 border border-primary-200',
  viewer:   'bg-cream-300 text-graphite-600 border border-cream-400',
}

function RoleBadge({ role }) {
  const classes = ROLE_CLASSES[role]
  if (!classes) return null
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold capitalize',
      classes,
    )}>
      {role}
    </span>
  )
}

function NotificationPanel({ onClose }) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    refetchInterval: 30000,
  })

  const markAllMut = useMutation({
    mutationFn: () => api.post('/api/notifications/mark_all_read/'),
    onSuccess: () => qc.invalidateQueries(['notifications']),
  })

  const notifications = Array.isArray(data) ? data : data?.results || []
  const unread = notifications.filter(n => !n.is_read)

  return (
    <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-cream-300 rounded-xl shadow-lg z-50 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cream-200">
        <span className="text-sm font-semibold text-graphite-900">Notifications</span>
        <div className="flex items-center gap-2">
          {unread.length > 0 && (
            <button
              onClick={() => markAllMut.mutate()}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium transition-colors"
            >
              Mark all read
            </button>
          )}
          <button onClick={onClose} className="btn-icon p-1">
            <X size={14} />
          </button>
        </div>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {isLoading ? (
          <p className="text-xs text-graphite-400 text-center py-6">Loading…</p>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center py-8 gap-2">
            <CheckCircle className="w-8 h-8 text-cream-400" />
            <p className="text-xs text-graphite-400">All caught up!</p>
          </div>
        ) : (
          notifications.map(n => (
            <div
              key={n.id}
              className={`px-4 py-3 border-b border-cream-200 last:border-0 transition-colors ${
                n.is_read ? 'opacity-60' : 'bg-primary-50'
              }`}
            >
              <p className="text-xs text-graphite-800 leading-relaxed">{n.message}</p>
              {n.created_at && (
                <p className="text-xs text-graphite-400 mt-1">
                  {new Date(n.created_at).toLocaleDateString()}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export function TopBar({ title, onMenuClick }) {
  const { user, role } = useAuth()
  const [showNotifs, setShowNotifs] = useState(false)
  const panelRef = useRef(null)

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    refetchInterval: 60000,
  })
  const notifications = Array.isArray(data) ? data : data?.results || []
  const unreadCount = notifications.filter(n => !n.is_read).length

  useEffect(() => {
    if (!showNotifs) return
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setShowNotifs(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showNotifs])

  return (
    <header className="h-16 flex items-center justify-between px-4 sm:px-6 border-b border-cream-300 bg-white sticky top-0 z-20 flex-shrink-0">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="btn-icon lg:hidden" aria-label="Open menu">
          <Menu size={20} />
        </button>
        <h1 className="text-base sm:text-lg font-semibold text-graphite-900">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Notifications */}
        <div className="relative" ref={panelRef}>
          <button
            onClick={() => setShowNotifs(v => !v)}
            className="btn-icon relative"
            aria-label="Notifications"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white" />
            )}
          </button>
          {showNotifs && <NotificationPanel onClose={() => setShowNotifs(false)} />}
        </div>

        {/* Role badge */}
        <RoleBadge role={user?.profile?.role || role} />

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-graphite-900 border-2 border-primary-400 flex items-center justify-center">
          <span className="text-xs font-bold text-primary-400">
            {user?.username?.[0]?.toUpperCase()}
          </span>
        </div>
      </div>
    </header>
  )
}
