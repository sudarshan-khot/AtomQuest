import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Award, Download } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getGoals } from '../api/goals'
import { getCheckIns } from '../api/checkins'
import { getCycles } from '../api/cycles'
import { ProgressBar } from '../components/ui/ProgressBar'
import { Badge } from '../components/ui/Badge'
import { PageLoader } from '../components/ui/Spinner'
import { EmptyState } from '../components/ui/EmptyState'

const CHART_COLORS = ['#A3E635', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0284c7']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-cream-300 rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-graphite-700 font-medium mb-0.5">{label}</p>
      <p className="text-primary-600 font-semibold">{payload[0].value.toFixed(1)}%</p>
    </div>
  )
}

function StatCard({ label, value, colorClass }) {
  return (
    <div className="glass-card p-5">
      <p className="text-xs text-graphite-500 font-medium mb-1">{label}</p>
      <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
    </div>
  )
}

function exportCSV(goals, checkins) {
  const rows = [['Title', 'Status', 'Weightage (%)', 'Target', 'UoM', 'Progress (%)']]
  goals.forEach(g => {
    const ci = checkins.filter(c => c.goal === g.id).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    rows.push([
      `"${g.title}"`,
      g.status,
      g.weightage,
      g.target_value,
      g.uom_type_name || '',
      ci?.progress_percentage ?? 0,
    ])
  })
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `atomquest-report-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function Reports() {
  const [cycleFilter, setCycleFilter] = useState('')

  const { data: goalsData,   isLoading: gl } = useQuery({ queryKey: ['goals'],   queryFn: getGoals })
  const { data: checkinsData, isLoading: cl } = useQuery({ queryKey: ['checkins'], queryFn: getCheckIns })
  const { data: cyclesData }                  = useQuery({ queryKey: ['cycles'],   queryFn: getCycles })

  if (gl || cl) return <PageLoader />

  const allGoals   = Array.isArray(goalsData)    ? goalsData    : goalsData?.results    || []
  const allCIs     = Array.isArray(checkinsData)  ? checkinsData : checkinsData?.results || []
  const cycles     = Array.isArray(cyclesData)    ? cyclesData   : cyclesData?.results   || []

  const goals    = cycleFilter ? allGoals.filter(g => String(g.cycle) === cycleFilter) : allGoals
  const checkins = cycleFilter ? allCIs.filter(c => String(c.cycle) === cycleFilter)   : allCIs

  const approvedGoals = goals.filter(g => g.status === 'approved')

  const latestCI = (goalId) =>
    checkins.filter(c => c.goal === goalId).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]

  const chartData = approvedGoals.map(g => ({
    name: g.title.length > 18 ? g.title.slice(0, 18) + '…' : g.title,
    progress: latestCI(g.id)?.progress_percentage || 0,
    weightage: g.weightage,
  }))

  const weightedScore = approvedGoals.length
    ? approvedGoals.reduce((sum, g) => {
        const p = latestCI(g.id)?.progress_percentage || 0
        return sum + (p * g.weightage) / 100
      }, 0)
    : 0

  const statusCounts = goals.reduce((acc, g) => {
    acc[g.status] = (acc[g.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Reports</h1>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Cycle filter */}
          <select
            value={cycleFilter}
            onChange={e => setCycleFilter(e.target.value)}
            className="input-field w-auto text-sm py-2"
          >
            <option value="">All Cycles</option>
            {cycles.map(c => <option key={c.id} value={String(c.id)}>{c.name}</option>)}
          </select>
          {/* Export */}
          <button
            onClick={() => exportCSV(goals, checkins)}
            className="btn-secondary"
            disabled={goals.length === 0}
          >
            <Download size={15} /> Export CSV
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Goals"    value={goals.length}                   colorClass="text-graphite-900" />
        <StatCard label="Approved"       value={approvedGoals.length}           colorClass="text-green-700" />
        <StatCard label="Check-ins"      value={checkins.length}                colorClass="text-sky-700" />
        <StatCard label="Weighted Score" value={`${weightedScore.toFixed(1)}%`} colorClass="text-primary-600" />
      </div>

      {approvedGoals.length === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="No data yet"
          description="Approve goals and submit check-ins to see your progress reports."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Progress chart */}
          <div className="glass-card p-5">
            <h2 className="section-title mb-4">Goal Progress</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: '#424a53', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#424a53', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(163,230,53,0.08)' }} />
                <Bar dataKey="progress" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Goal breakdown */}
          <div className="glass-card p-5">
            <h2 className="section-title mb-4">Goal Breakdown</h2>
            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {approvedGoals.map(g => {
                const progress = latestCI(g.id)?.progress_percentage || 0
                return (
                  <div key={g.id} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-graphite-800 truncate flex-1">{g.title}</p>
                      <span className="text-xs text-graphite-500 font-medium flex-shrink-0">{g.weightage}% wt</span>
                    </div>
                    <ProgressBar value={progress} size="sm" />
                  </div>
                )
              })}
            </div>
          </div>

          {/* Status distribution */}
          <div className="glass-card p-5">
            <h2 className="section-title mb-4">Status Distribution</h2>
            <div className="space-y-2">
              {Object.entries(statusCounts).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between p-3 rounded-lg bg-cream-100 border border-cream-200">
                  <Badge status={status} />
                  <span className="text-sm font-bold text-graphite-900">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Weighted achievement */}
          <div className="glass-card p-5 flex flex-col items-center justify-center text-center gap-3">
            <Award className="w-10 h-10 text-primary-600" />
            <p className="text-sm text-graphite-600 font-medium">Overall Weighted Achievement</p>
            <p className="text-5xl font-bold text-graphite-900">{weightedScore.toFixed(1)}%</p>
            <ProgressBar value={weightedScore} size="lg" className="w-full max-w-xs" />
          </div>
        </div>
      )}
    </div>
  )
}
