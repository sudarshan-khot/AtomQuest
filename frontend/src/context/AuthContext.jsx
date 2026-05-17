import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'

const AuthContext = createContext(null)

/**
 * The /api/users/me/ endpoint returns a UserProfile-shaped object:
 *   { id, role, department_name, user: { id, username, email, ... }, ... }
 *
 * We normalize this into a flat shape that all components expect:
 *   { id, username, email, profile: { role, ... }, ... }
 */
function normalizeUser(raw) {
  if (!raw) return null
  // Already normalized (has username at top level)
  if (raw.username) return raw
  // Profile-shaped response: { role, user: { username, ... }, ... }
  const { user: userFields, ...profileFields } = raw
  return {
    ...userFields,
    profile: profileFields,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return normalizeUser(JSON.parse(localStorage.getItem('user'))) } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token && !user) {
      getMe()
        .then(raw => setUser(normalizeUser(raw)))
        .catch(() => { localStorage.removeItem('token'); setUser(null) })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (credentials) => {
    const data = await apiLogin(credentials)
    localStorage.setItem('token', data.token)
    const raw = await getMe()
    const me = normalizeUser(raw)
    localStorage.setItem('user', JSON.stringify(me))
    setUser(me)
    return me
  }

  const logout = () => {
    apiLogout()
    setUser(null)
  }

  const role = user?.profile?.role

  return (
    <AuthContext.Provider value={{ user, role, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
