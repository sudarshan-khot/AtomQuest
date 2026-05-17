import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard, Target, CheckSquare, BarChart3,
  Users, Settings, LogOut, ChevronLeft, ChevronRight, ClipboardCheck,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const NAV = {
  employee: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/goals',     icon: Target,          label: 'My Goals'  },
    { to: '/checkins',  icon: CheckSquare,     label: 'Check-ins' },
    { to: '/reports',   icon: BarChart3,       label: 'Reports'   },
  ],
  manager: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/goals',     icon: Target,          label: 'My Goals'  },
    { to: '/approvals', icon: ClipboardCheck,  label: 'Approvals' },
    { to: '/checkins',  icon: CheckSquare,     label: 'Check-ins' },
    { to: '/reports',   icon: BarChart3,       label: 'Reports'   },
  ],
  admin: [
    { to: '/dashboard',    icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/goals',        icon: Target,          label: 'Goals'     },
    { to: '/approvals',    icon: ClipboardCheck,  label: 'Approvals' },
    { to: '/checkins',     icon: CheckSquare,     label: 'Check-ins' },
    { to: '/reports',      icon: BarChart3,       label: 'Reports'   },
    { to: '/admin/users',  icon: Users,           label: 'Users'     },
    { to: '/admin/cycles', icon: Settings,        label: 'Cycles'    },
  ],
  viewer: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/goals',     icon: Target,          label: 'Goals'     },
    { to: '/reports',   icon: BarChart3,       label: 'Reports'   },
  ],
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { user, role, logout } = useAuth()
  const items = NAV[role] || NAV.employee

  return (
    <aside className={clsx(
      'flex flex-col h-screen bg-graphite-900 border-r border-graphite-800',
      'sidebar-transition fixed left-0 top-0 z-30',
      'hidden lg:flex',
      collapsed ? 'lg:w-16' : 'lg:w-60',
      mobileOpen && '!flex w-64',
    )}>
      {/* Logo */}
      <div className={clsx(
        'flex items-center h-16 px-4 border-b border-graphite-800 flex-shrink-0',
        collapsed ? 'lg:justify-center' : 'gap-3',
      )}>
        {collapsed && !mobileOpen ? (
          /* Collapsed: lime monogram */
          <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center flex-shrink-0">
            <span className="text-graphite-900 font-black text-sm leading-none">A</span>
          </div>
        ) : (
          /* Expanded: lime monogram + white text name */
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center flex-shrink-0">
              <span className="text-graphite-900 font-black text-sm leading-none">A</span>
            </div>
            <span className="font-bold text-white text-lg tracking-tight">AtomQuest</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-0.5 overflow-y-auto">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onMobileClose}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
              (collapsed && !mobileOpen) ? 'lg:justify-center' : '',
              isActive
                ? 'bg-primary-500 text-graphite-900'
                : 'text-graphite-300 hover:text-white hover:bg-graphite-800',
            )}
            title={(collapsed && !mobileOpen) ? label : undefined}
          >
            <Icon size={18} className="flex-shrink-0" />
            {(!collapsed || mobileOpen) && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User + collapse */}
      <div className="border-t border-graphite-800 p-3 space-y-1 flex-shrink-0">
        {(collapsed && !mobileOpen) ? (
          <div className="flex justify-center px-3 py-2 mb-2" title={user?.username}>
            <div className="w-8 h-8 rounded-full bg-primary-500/20 border border-primary-500/40 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-primary-400">
                {user?.username?.[0]?.toUpperCase()}
              </span>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-graphite-800 mb-2">
            <div className="w-8 h-8 rounded-full bg-primary-500/20 border border-primary-500/40 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold text-primary-400">
                {user?.username?.[0]?.toUpperCase()}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate">{user?.username}</p>
              <p className="text-xs text-graphite-400 capitalize">{role}</p>
            </div>
          </div>
        )}

        <button
          onClick={() => { logout(); onMobileClose?.() }}
          className={clsx(
            'flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm',
            'text-graphite-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-150',
            (collapsed && !mobileOpen) ? 'lg:justify-center' : '',
          )}
          title={(collapsed && !mobileOpen) ? 'Logout' : undefined}
        >
          <LogOut size={16} />
          {(!collapsed || mobileOpen) && <span>Logout</span>}
        </button>

        <button
          onClick={onToggle}
          className={clsx(
            'hidden lg:flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm',
            'text-graphite-500 hover:text-graphite-200 hover:bg-graphite-800 transition-all duration-150',
            collapsed ? 'justify-center' : '',
          )}
        >
          {collapsed
            ? <ChevronRight size={16} />
            : <><ChevronLeft size={16} /><span>Collapse</span></>
          }
        </button>
      </div>
    </aside>
  )
}
