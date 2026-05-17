import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Spinner } from '../components/ui/Spinner'
import logoSvg from '../static/logo.svg'

export default function Login() {
  const { login }   = useAuth()
  const navigate    = useNavigate()
  const [showPw, setShowPw]   = useState(false)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setError('')
    setLoading(true)
    try {
      await login(data)
      navigate('/dashboard')
    } catch (e) {
      setError(e.response?.data?.non_field_errors?.[0] || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2.5 mb-1">
            <img src={logoSvg} alt="" aria-hidden="true" className="h-10 w-auto" />
            <span className="font-bold text-graphite-900 text-2xl tracking-tight">AtomQuest</span>
          </div>
          <p className="text-graphite-500 text-sm">Goal Setting &amp; Tracking Portal</p>
        </div>

        {/* Card */}
        <div className="bg-white border border-cream-300 rounded-2xl p-6 sm:p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-graphite-900 mb-6">Sign in to your account</h2>

          {error && (
            <div className="alert-error mb-5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <label className="label" htmlFor="username">Username</label>
              <input
                id="username"
                {...register('username', { required: 'Username is required' })}
                className="input-field"
                placeholder="Enter your username"
                autoComplete="username"
                autoFocus
              />
              {errors.username && <p className="field-error">{errors.username.message}</p>}
            </div>

            <div>
              <label className="label" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  {...register('password', { required: 'Password is required' })}
                  type={showPw ? 'text' : 'password'}
                  className="input-field pr-10"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-graphite-400 hover:text-graphite-700 transition-colors"
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="field-error">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center mt-2 py-2.5 text-graphite-900 font-semibold"
            >
              {loading ? <Spinner size="sm" /> : 'Sign in'}
            </button>
          </form>
        </div>

        <div className="text-center mt-6 space-y-2">
          <Link to="/" className="text-xs text-graphite-400 hover:text-graphite-700 transition-colors">
            ← Back to home
          </Link>
          <p className="text-xs text-graphite-300">AtomQuest © {new Date().getFullYear()}</p>
        </div>
      </div>
    </div>
  )
}
