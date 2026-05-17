import { useQuery } from '@tanstack/react-query'
import { Target, CheckSquare, TrendingUp, Clock, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getGoals } from '../api/goals'
import { getCheckIns } from '../api/checkins'
import { useAuth } from '../context/AuthContext'
import { ProgressBar } from '../components/ui/ProgressBar'
import { Badge } from '../components/ui/Badge'
import { PageLoader } from '../components/ui/Spinner'

function StatCard({ icon: Icon, label, value, colorBg, colorText, to }) {
  const inner = (
    <div className="glass-card-hover p-4 sm:p-5 flex items-center gap-4">
      <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${colorBg}`}>
        <Icon size={20} className={colorText} />
      </div>
      <div>
        <p className="text-xl sm:text-2xl font-bold text-graphite-900">{value}</p>
        <p className="text-xs sm:text-sm text-graphite-500 font-medium">{label}</p>
      </div>
    </div>
  )
  return to ? <Link to={to} className="block">{inner}</Link> : inner
}

function SectionHeader({ title, to, linkLabel = 'View all' }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="section-title">{title}</h2>
      {to && (
        <Link to={to} className="text-xs text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1 transition-colors">
          {linkLabel} <ArrowRight size={12} />
        </Link>
      )}
    </div>
  )
}

export default function Dashboard() {
  const { role } = useAuth()

  const { data: goalsData,   isLoading: gl } = useQuery({ queryKey: ['goals'],   queryFn: getGoals })
  const { data: checkinsData, isLoading: cl } = useQuery({ queryKey: ['checkins'], queryFn: getCheckIns })

  if (gl || cl) return <PageLoader />

  const goals    = Array.isArray(goalsData)    ? goalsData    : goalsData?.results    || []
  const checkins = Array.isArray(checkinsData)  ? checkinsData : checkinsData?.results || []

  const approvedGoals = goals.filter(g => g.status === 'approved')
  const pendingGoals  = goals.filter(g => g.status === 'submitted')
  const draftGoals    = goals.filter(g => g.status === 'draft')

  const avgProgress = approvedGoals.length
    ? approvedGoals.reduce((sum, g) => {
        const ci = checkins.filter(c => c.goal === g.id).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
        return sum + (ci?.progress_percentage || 0)
      }, 0) / approvedGoals.length
    : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard icon={Target}      label="Total Goals"    value={goals.length}                   colorBg="bg-primary-100"  colorText="text-primary-700"  to="/goals" />
        <StatCard icon={CheckSquare} label="Approved"       value={approvedGoals.length}           colorBg="bg-green-100"    colorText="text-green-700"    to="/goals" />
        <StatCard icon={Clock}       label="Pending Review" value={pendingGoals.length}             colorBg="bg-amber-100"    colorText="text-amber-700"    to={role !== 'employee' ? '/approvals' : '/goals'} />
        <StatCard icon={TrendingUp}  label="Avg Progress"   value={`${avgProgress.toFixed(0)}%`}   colorBg="bg-sky-100"      colorText="text-sky-700" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Goals */}
        <div className="glass-card p-4 sm:p-5">
          <SectionHeader title="Recent Goals" to="/goals" />
          {goals.length === 0 ? (
            <p className="text-sm text-graphite-400 py-6 text-center">No goals yet</p>
          ) : (
            <div className="space-y-2">
              {goals.slice(0, 5).map(goal => {
                const ci = checkins.filter(c => c.goal === goal.id).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
                return (
                  <div key={goal.id} className="flex items-center gap-3 p-3 rounded-lg bg-cream-100 hover:bg-cream-200 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-graphite-900 truncate">{goal.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge status={goal.status} />
                        <span className="text-xs text-graphite-500 font-medium">{goal.weightage}%</span>
                      </div>
                    </div>
                    {ci && (
                      <div className="w-20 sm:w-24 flex-shrink-0">
                        <ProgressBar value={ci.progress_percentage} size="sm" showLabel={false} />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent Check-ins */}
        <div className="glass-card p-4 sm:p-5">
          <SectionHeader title="Recent Check-ins" to="/checkins" />
          {checkins.length === 0 ? (
            <p className="text-sm text-graphite-400 py-6 text-center">No check-ins yet</p>
          ) : (
            <div className="space-y-2">
              {checkins.slice(0, 5).map(ci => (
                <div key={ci.id} className="flex items-center gap-3 p-3 rounded-lg bg-cream-100 hover:bg-cream-200 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-graphite-900 truncate">{ci.goal_title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge status={ci.status} />
                    </div>
                  </div>
                  <div className="w-20 sm:w-24 flex-shrink-0">
                    <ProgressBar value={ci.progress_percentage} size="sm" showLabel={false} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Draft reminder */}
      {draftGoals.length > 0 && (
        <div className="glass-card p-4 border-amber-300 bg-amber-50 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <p className="text-sm text-graphite-800">
              You have <span className="font-bold text-amber-700">{draftGoals.length}</span> draft goal{draftGoals.length > 1 ? 's' : ''} waiting to be submitted.
            </p>
          </div>
          <Link to="/goals" className="text-xs text-amber-700 hover:text-amber-900 font-semibold flex items-center gap-1 transition-colors whitespace-nowrap">
            Review <ArrowRight size={12} />
          </Link>
        </div>
      )}
    </div>
  )
}
