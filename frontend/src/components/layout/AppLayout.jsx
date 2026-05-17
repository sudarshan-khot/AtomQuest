import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { clsx } from 'clsx'

export const PAGE_TITLES = {
  '/dashboard':    'Dashboard',
  '/goals':        'Goals',
  '/approvals':    'Approvals',
  '/checkins':     'Check-ins',
  '/reports':      'Reports',
  '/admin/users':  'User Management',
  '/admin/cycles': 'Cycle Management',
}

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] || 'AtomQuest'

  // Close mobile sidebar on route change
  useEffect(() => { setMobileOpen(false) }, [pathname])

  // Close mobile sidebar on wide screens
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)')
    const handler = (e) => { if (e.matches) setMobileOpen(false) }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return (
    <div className="gradient-bg min-h-screen">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(c => !c)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* Main content — offset by sidebar on desktop */}
      <div className={clsx(
        'transition-all duration-300 min-h-screen flex flex-col',
        collapsed ? 'lg:ml-16' : 'lg:ml-60',
      )}>
        <TopBar
          title={title}
          onMenuClick={() => setMobileOpen(o => !o)}
        />
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
