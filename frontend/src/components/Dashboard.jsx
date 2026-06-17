import { useState, useEffect, useCallback } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { motion } from 'framer-motion'
import {
  TrendingUp, IndianRupee, Server,
  PiggyBank, RefreshCw, AlertCircle, ArrowUpRight, ArrowDownRight
} from 'lucide-react'
import clsx from 'clsx'

const CHART_COLORS = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#a371f7', '#79c0ff', '#56d364', '#e3b341']

function fmt(val) {
  if (val == null || isNaN(val)) return '₹0'
  if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
  if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`
  return `₹${Math.round(val)}`
}

function fmtDate(str) {
  if (!str) return ''
  const d = new Date(str)
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function KPICard({ title, value, change, icon: Icon, accent }) {
  const up = change > 0
  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-4 flex flex-col justify-between min-h-[110px] hover:border-border transition-colors">
      <div className="flex items-center justify-between">
        <div className={clsx("w-9 h-9 rounded-lg flex items-center justify-center", accent)}>
          <Icon size={18} />
        </div>
        {change != null && change !== 0 && (
          <span className={clsx(
            "flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded-md",
            up ? "bg-danger/10 text-danger" : "bg-success/10 text-success"
          )}>
            {up ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="mt-2">
        <p className="text-xl font-bold text-text-primary tracking-tight leading-none">{value}</p>
        <p className="text-[11px] text-text-muted mt-1">{title}</p>
      </div>
    </div>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-2 border border-border rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="text-text-muted mb-0.5">{fmtDate(label) || label}</p>
      {payload.map((e, i) => (
        <p key={i} className="font-semibold text-text-primary">{fmt(e.value)}</p>
      ))}
    </div>
  )
}

function Skeleton() {
  return (
    <div className="p-5 space-y-5">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-4 h-[110px]">
            <div className="w-9 h-9 rounded-lg animate-shimmer mb-2" />
            <div className="h-6 w-20 rounded animate-shimmer mb-1" />
            <div className="h-3 w-14 rounded animate-shimmer" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2 bg-surface-1 border border-border-subtle rounded-xl p-4 h-64">
          <div className="h-4 w-36 rounded animate-shimmer mb-4" />
          <div className="h-48 w-full rounded-lg animate-shimmer" />
        </div>
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-4 h-64">
          <div className="h-4 w-24 rounded animate-shimmer mb-4" />
          <div className="h-48 w-full rounded-lg animate-shimmer" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/dashboard')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  if (loading) return <Skeleton />

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center">
          <AlertCircle size={36} className="text-danger mx-auto mb-3" />
          <p className="text-sm text-text-secondary mb-2">Failed to load dashboard</p>
          <p className="text-xs text-text-muted mb-4">{error}</p>
          <button onClick={() => fetchData()} className="px-4 py-2 rounded-lg bg-accent text-white text-sm hover:bg-accent/80 transition">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const { kpis, daily_trend, by_environment, by_resource, comparison } = data

  return (
    <div className="p-4 sm:p-6 lg:p-8 xl:p-10 space-y-5 sm:space-y-6 w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Cost Dashboard</h1>
          <p className="text-[11px] text-text-muted mt-0.5">Real-time Azure cost analytics</p>
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-text-secondary hover:bg-surface-2 hover:text-text-primary transition disabled:opacity-50"
        >
          <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* KPIs - always fills the full row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 xl:gap-4">
        <KPICard title="Weekly Spend" value={fmt(kpis?.weekly_spend)} change={kpis?.change_pct} icon={IndianRupee} accent="bg-accent/15 text-accent" />
        <KPICard title="Monthly Projection" value={fmt(kpis?.monthly_projection)} icon={TrendingUp} accent="bg-[#a371f7]/15 text-[#a371f7]" />
        <KPICard title="Resources Tracked" value={kpis?.resources_tracked || 0} icon={Server} accent="bg-success/15 text-success" />
        <KPICard title="Potential Savings" value={fmt(kpis?.potential_savings)} icon={PiggyBank} accent="bg-warning/15 text-warning" />
      </div>

      {/* Row 1: Trend + Pie — spans full width */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 xl:gap-6">
        {/* Area chart — takes 2/3 on xl */}
        <div className="xl:col-span-2 bg-surface-1 border border-border-subtle rounded-xl p-5">
          <h3 className="text-xs font-semibold text-text-primary mb-3">Daily Cost Trend (3 weeks)</h3>
          <div className="h-56 xl:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={daily_trend || []} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#58a6ff" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#58a6ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
                <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: '#6e7681', fontSize: 10 }} axisLine={{ stroke: '#21262d' }} tickLine={false} interval="preserveStartEnd" />
                <YAxis tickFormatter={fmt} tick={{ fill: '#6e7681', fontSize: 10 }} axisLine={false} tickLine={false} width={55} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cost" stroke="#58a6ff" strokeWidth={2} fill="url(#areaGrad)" dot={false} activeDot={{ r: 3, fill: '#58a6ff', strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie — takes 1/3 on xl */}
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-5">
          <h3 className="text-xs font-semibold text-text-primary mb-3">Cost by Service</h3>
          <div className="h-48 xl:h-52">
            {by_environment?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={by_environment} dataKey="cost" nameKey="environment" cx="50%" cy="50%" outerRadius="75%" innerRadius="50%" paddingAngle={2} stroke="none">
                    {by_environment.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    return (
                      <div className="bg-surface-2 border border-border rounded-lg px-3 py-2 shadow-xl text-xs">
                        <p className="text-text-muted">{payload[0].name}</p>
                        <p className="font-semibold text-text-primary">{fmt(payload[0].value)}</p>
                      </div>
                    )
                  }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted text-xs">No data</div>
            )}
          </div>
          {by_environment?.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-x-2 gap-y-1">
              {by_environment.slice(0, 6).map((item, i) => (
                <div key={i} className="flex items-center gap-1.5 min-w-0">
                  <div className="w-2 h-2 rounded-full shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-[10px] text-text-muted truncate">{item.environment}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Bar + Table — each takes half the full width */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 xl:gap-6">
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-5">
          <h3 className="text-xs font-semibold text-text-primary mb-3">Top Resources by Cost</h3>
          <div className="h-60 xl:h-72">
            {by_resource?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={by_resource.slice(0, 10)} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262d" horizontal={false} />
                  <XAxis type="number" tickFormatter={fmt} tick={{ fill: '#6e7681', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="resource" tick={{ fill: '#8b949e', fontSize: 10 }} axisLine={false} tickLine={false} width={110} tickFormatter={v => v.length > 16 ? v.slice(0, 16) + '…' : v} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="cost" fill="#58a6ff" radius={[0, 4, 4, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted text-xs">No resource data</div>
            )}
          </div>
        </div>

        <div className="bg-surface-1 border border-border-subtle rounded-xl p-5">
          <h3 className="text-xs font-semibold text-text-primary mb-3">Week-over-Week Comparison</h3>
          <div className="h-60 xl:h-72 overflow-y-auto">
            {comparison?.length > 0 ? (
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-surface-1 z-10">
                  <tr className="border-b border-border">
                    <th className="text-left text-text-muted font-medium py-2 pr-2">Resource</th>
                    <th className="text-right text-text-muted font-medium py-2 px-1">This Week</th>
                    <th className="text-right text-text-muted font-medium py-2 px-1">Last Week</th>
                    <th className="text-right text-text-muted font-medium py-2 pl-1 w-16">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.slice(0, 15).map((row, i) => {
                    const ch = row.change_pct || 0
                    return (
                      <tr key={i} className="border-b border-border-subtle/50 hover:bg-surface-2/40 transition-colors">
                        <td className="py-1.5 pr-2 text-text-secondary truncate max-w-[160px]">{row.resource}</td>
                        <td className="py-1.5 px-1 text-right text-text-primary font-medium">{fmt(row.this_week || 0)}</td>
                        <td className="py-1.5 px-1 text-right text-text-muted">{fmt(row.last_week || 0)}</td>
                        <td className="py-1.5 pl-1 text-right">
                          <span className={clsx(
                            "font-semibold",
                            ch > 5 ? "text-danger" : ch < -5 ? "text-success" : "text-text-muted"
                          )}>
                            {ch > 0 ? '+' : ''}{ch.toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted text-xs">No comparison data</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
